"""FAT32 ESP Rescue USB writer — staging, safety, dry-run plans (no device writes from API/DCC)."""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from core.rescue_usb_operator_selection import (
    EVIDENCE_REL,
    REQUIRED_CONFIRMATIONS,
    build_usb_candidates_payload,
    device_blocked_reason,
    load_operator_selection_evidence,
)
from core.safe_device import list_classified_devices

Runner = Callable[..., Any]

CONFIRM_PHRASE_FAT32_ESP = "WRITE SETUPHELFER FAT32 ESP USB"
DEFAULT_ISO_REL = "build/rescue/live-build/setuphelfer-rescue-live/binary.hybrid.iso"
# GPT partition name (sgdisk -c) — may be longer than FAT volume label.
GPT_PARTITION_NAME = "SETUPHELFER_RESCUE"
# FAT/VFAT volume label (mkfs.vfat -n) — max 11 characters.
FAT_VOLUME_LABEL = "SETUPHELFER"
FAT_VOLUME_LABEL_MAX_LEN = 11
EFI_PARTTYPE_UUID = "c12a7328-f81f-11d2-ba4b-00a0c93ec93b"
FAT_RSYNC_EXCLUDE = ".sqtmp/"
FAT_RSYNC_OPTIONS = (
    "-r --delete --info=progress2 --no-owner --no-group --no-perms --omit-dir-times"
)
MIN_USB_BYTES = 2 * 1024 * 1024 * 1024  # 2 GiB
ESP_SIZE_MIB_DEFAULT = 4096

LIVE_FILE_CANDIDATES = {
    "vmlinuz": ("/live/vmlinuz",),
    "initrd": ("/live/initrd.img", "/live/initrd"),
    "squashfs": ("/live/filesystem.squashfs",),
}

FORBIDDEN_TARGET_PATTERNS = (
    re.compile(r"^/dev/sda$"),
    re.compile(r"^/dev/nvme"),
)


def assert_valid_fat_volume_label(label: str) -> None:
    """FAT/VFAT labels are limited to 11 bytes (mkfs.vfat -n)."""
    if len(label) > FAT_VOLUME_LABEL_MAX_LEN:
        raise ValueError(
            f"FAT volume label too long ({len(label)} > {FAT_VOLUME_LABEL_MAX_LEN}): {label!r}"
        )


def fat32_esp_label_spec() -> dict[str, str]:
    assert_valid_fat_volume_label(FAT_VOLUME_LABEL)
    return {
        "gpt_partition_name": GPT_PARTITION_NAME,
        "fat_volume_label": FAT_VOLUME_LABEL,
    }


def fat32_staging_rsync_command(*, staging: str, mount: str, sudo: bool = True) -> str:
    """FAT32-safe rsync — no owner/group/permission preservation."""
    prefix = "sudo " if sudo else ""
    return (
        f"{prefix}rsync {FAT_RSYNC_OPTIONS} --exclude={FAT_RSYNC_EXCLUDE!r} "
        f'"{staging}/" "{mount}/"'
    )


@dataclass(frozen=True)
class LiveBootParams:
    base_append: str
    labels: dict[str, str]


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _workspace_root() -> Path:
    from core.dev_dashboard import _effective_workspace_root

    return _effective_workspace_root(_repo_root())


def _now_iso() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


def _run(cmd: list[str], *, runner: Runner | None = None, timeout: int = 120) -> subprocess.CompletedProcess[str]:
    if runner is not None:
        return runner(cmd, timeout=timeout)
    return subprocess.run(cmd, capture_output=True, text=True, check=False, timeout=timeout)


def parse_live_cfg_boot_params(live_cfg_text: str) -> LiveBootParams:
    """Parse isolinux live.cfg append lines into boot parameter strings."""
    labels: dict[str, str] = {}
    current_label: str | None = None
    base_append = ""

    for raw in live_cfg_text.splitlines():
        line = raw.strip()
        m_label = re.match(r"^label\s+(\S+)", line)
        if m_label:
            current_label = m_label.group(1)
            continue
        if line.startswith("append ") and current_label:
            append = line[7:].strip()
            append = re.sub(r"^initrd=\S+\s+", "", append)
            append = re.sub(r"^kernel\s+\S+\s+", "", append)
            labels[current_label] = append
            if current_label in ("live-", "setuphelfer-rescue-default") and not base_append:
                base_append = append
            if current_label == "setuphelfer-rescue-default":
                base_append = append

    if not base_append and labels:
        base_append = next(iter(labels.values()))
    return LiveBootParams(base_append=base_append, labels=labels)


def _menu_append(params: LiveBootParams, label: str, fallback: str) -> str:
    return params.labels.get(label, fallback)


def fat32_esp_grub_root_block(
    *,
    fat_uuid: str | None = None,
    fat_label: str = FAT_VOLUME_LABEL,
) -> list[str]:
    """GRUB root discovery for FAT32 ESP — UUID primary after mkfs, label/cmdpath fallback."""
    assert_valid_fat_volume_label(fat_label)
    lines: list[str] = []
    if fat_uuid:
        uuid = fat_uuid.strip()
        lines.append(f"search --no-floppy --fs-uuid {uuid} --set=root")
        lines.append('if [ -z "$root" ]; then')
        lines.append(f"  search --no-floppy --label {fat_label} --set=root")
        lines.append("fi")
    else:
        lines.append(f"search --no-floppy --label {fat_label} --set=root")
    lines.append('if [ -z "$root" ]; then')
    lines.append("  set root=($cmdpath)")
    lines.append("fi")
    return lines


def patch_grub_cfg_for_fat_uuid(grub_text: str, fat_uuid: str) -> str:
    """Replace root-search preamble in grub.cfg with UUID-aware FAT32 ESP block."""
    new_root_lines = fat32_esp_grub_root_block(fat_uuid=fat_uuid)
    out: list[str] = []
    i = 0
    lines = grub_text.splitlines()
    while i < len(lines):
        if lines[i].strip() == "set default=0":
            out.append(lines[i])
            i += 1
            while i < len(lines) and lines[i].strip() and not lines[i].strip().startswith("menuentry"):
                i += 1
            out.extend(new_root_lines)
            out.append("")
            if i < len(lines) and not lines[i].strip():
                i += 1
            continue
        out.append(lines[i])
        i += 1
    text = "\n".join(out)
    if not text.endswith("\n"):
        text += "\n"
    return text


def patch_staging_grub_for_fat_uuid(staging_dir: Path, fat_uuid: str) -> Path:
    cfg_path = staging_dir / "boot" / "grub" / "grub.cfg"
    if not cfg_path.is_file():
        raise FileNotFoundError(f"grub.cfg missing: {cfg_path}")
    patched = patch_grub_cfg_for_fat_uuid(cfg_path.read_text(encoding="utf-8"), fat_uuid)
    cfg_path.write_text(patched, encoding="utf-8")
    return cfg_path


def generate_fat32_esp_grub_cfg(
    *,
    fat_label: str = FAT_VOLUME_LABEL,
    fat_uuid: str | None = None,
) -> str:
    """GRUB menu for FAT32 ESP USB — root via FAT UUID/label, not ISO9660."""
    assert_valid_fat_volume_label(fat_label)

    def entry(title: str, append: str) -> str:
        return (
            f'menuentry "{title}" {{\n'
            f"  linux /live/vmlinuz {append}\n"
            f"  initrd /live/initrd.img\n"
            f"}}\n"
        )

    lines = [
        "set timeout=10",
        "set default=0",
        *fat32_esp_grub_root_block(fat_uuid=fat_uuid, fat_label=fat_label),
        "",
        entry(
            "Setuphelfer Rettung starten",
            "boot=live components quiet setuphelfer_rescue=1 setuphelfer_start_assistant=1",
        ),
        entry(
            "Setuphelfer Rettung starten - Netzwerk-Assistent",
            "boot=live components setuphelfer.network=1 quiet setuphelfer_rescue=1 setuphelfer_start_assistant=1",
        ),
        entry(
            "Setuphelfer MSI/NVIDIA Kompatibilitaetsmodus",
            "boot=live components pci=noaer nouveau.modeset=0 nomodeset quiet setuphelfer_rescue=1 setuphelfer_msi_compat=1",
        ),
        entry(
            "Setuphelfer Diagnosemodus",
            "boot=live components systemd.unit=multi-user.target setuphelfer_rescue=1 setuphelfer_diagnose=1",
        ),
        entry(
            "Setuphelfer RAM-Modus / toram + Media-Check",
            "boot=live components toram setuphelfer.media_check=1 quiet setuphelfer_rescue=1",
        ),
        'menuentry "Neustart" { reboot }',
        'menuentry "Herunterfahren" { halt }',
        "",
    ]
    return "\n".join(lines)


def generate_fat32_esp_grub_cfg_legacy_label_only(*, fat_label: str = FAT_VOLUME_LABEL) -> str:
    """Alias kept for tests — staging without UUID uses label-only root block."""
    return generate_fat32_esp_grub_cfg(fat_label=fat_label, fat_uuid=None)


def generate_grub_cfg(params: LiveBootParams) -> str:
    """Legacy ISO-derived GRUB generator — prefer generate_fat32_esp_grub_cfg for FAT32 ESP."""
    base = params.base_append or (
        "boot=live config boot=live components init=/lib/systemd/systemd quiet splash "
        "setuphelfer_rescue=1 hostname=setuphelfer-rescue username=user "
        "user-fullname=Setuphelfer Rescue keyboard-layouts=de locales=de_DE.UTF-8 timezone=Europe/Berlin"
    )

    def entry(title: str, append: str) -> str:
        return (
            f'menuentry "{title}" {{\n'
            f"  linux /live/vmlinuz {append}\n"
            f"  initrd /live/initrd.img\n"
            f"}}\n"
        )

    lines = [
        "set timeout=10",
        "set default=0",
        "search --set=root --file /live/filesystem.squashfs",
        "",
        entry(
            "Setuphelfer Rettung starten",
            _menu_append(
                params,
                "setuphelfer-rescue-default",
                f"{base} setuphelfer_start_assistant=1",
            ),
        ),
        entry(
            "Setuphelfer Rettung starten - Netzwerk-Assistent",
            _menu_append(
                params,
                "setuphelfer-rescue-network",
                f"{base} setuphelfer_network_onboarding=1 setuphelfer_start_assistant=1",
            ),
        ),
        entry(
            "Setuphelfer MSI/NVIDIA Kompatibilitaetsmodus",
            _menu_append(
                params,
                "setuphelfer-rescue-msi-compat",
                f"{base} pci=noaer nomodeset setuphelfer_msi_compat=1",
            ),
        ),
        entry(
            "Setuphelfer Diagnosemodus",
            _menu_append(
                params,
                "setuphelfer-rescue-diagnose",
                f"{base} setuphelfer_diagnose=1 systemd.log_level=debug",
            ),
        ),
        entry(
            "Setuphelfer RAM-Modus / toram + Media-Check",
            _menu_append(
                params,
                "setuphelfer-rescue-toram",
                f"toram {base} setuphelfer_media_check=1",
            ),
        ),
        'menuentry "Neustart" { reboot }',
        'menuentry "Herunterfahren" { halt }',
        "",
    ]
    return "\n".join(lines)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            chunk = f.read(1024 * 1024)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def discover_iso_live_paths(iso_path: Path, *, runner: Runner | None = None) -> dict[str, str]:
    found: dict[str, str] = {}
    for key, candidates in LIVE_FILE_CANDIDATES.items():
        for iso_path_inner in candidates:
            proc = _run(
                ["xorriso", "-osirrox", "on", "-indev", str(iso_path), "-find", iso_path_inner],
                runner=runner,
            )
            if proc.returncode == 0 and (proc.stdout or "").strip():
                found[key] = iso_path_inner
                break
    if len(found) != 3:
        missing = sorted(set(LIVE_FILE_CANDIDATES) - set(found))
        raise FileNotFoundError(f"ISO live artifacts missing: {missing}")
    return found


def extract_iso_files(
    iso_path: Path,
    output_dir: Path,
    *,
    runner: Runner | None = None,
) -> dict[str, Any]:
    """Extract live artifacts + BOOTX64.EFI into ESP staging tree (read-only from ISO)."""
    output_dir.mkdir(parents=True, exist_ok=True)
    live_paths = discover_iso_live_paths(iso_path, runner=runner)

    live_cfg_text = ""
    tmp_live_cfg = output_dir / ".live.cfg.extract"
    _run(
        [
            "xorriso",
            "-osirrox",
            "on",
            "-indev",
            str(iso_path),
            "-extract",
            "/isolinux/live.cfg",
            str(tmp_live_cfg),
        ],
        runner=runner,
    )
    if tmp_live_cfg.is_file():
        live_cfg_text = tmp_live_cfg.read_text(encoding="utf-8", errors="replace")
        tmp_live_cfg.unlink(missing_ok=True)

    params = parse_live_cfg_boot_params(live_cfg_text)
    grub_cfg = generate_fat32_esp_grub_cfg()
    (output_dir / "boot" / "grub").mkdir(parents=True, exist_ok=True)
    (output_dir / "boot" / "grub" / "grub.cfg").write_text(grub_cfg, encoding="utf-8")

    extract_list = [
        ("/EFI/BOOT/BOOTX64.EFI", "EFI/BOOT/BOOTX64.EFI"),
        (live_paths["vmlinuz"], "live/vmlinuz"),
        (live_paths["initrd"], "live/initrd.img"),
        (live_paths["squashfs"], "live/filesystem.squashfs"),
    ]
    files_meta: list[dict[str, Any]] = []
    for iso_inner, rel in extract_list:
        dest = output_dir / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        proc = _run(
            [
                "xorriso",
                "-osirrox",
                "on",
                "-indev",
                str(iso_path),
                "-extract",
                iso_inner,
                str(dest),
            ],
            runner=runner,
        )
        if proc.returncode != 0 or not dest.is_file():
            raise FileNotFoundError(f"extract failed: {iso_inner}")
        files_meta.append(
            {
                "iso_path": iso_inner,
                "staging_path": rel,
                "size_bytes": dest.stat().st_size,
                "sha256": sha256_file(dest),
            }
        )

    setup_dir = output_dir / "setuphelfer" / "rescue"
    setup_dir.mkdir(parents=True, exist_ok=True)
    squash = output_dir / "live" / "filesystem.squashfs"
    branding_dest = setup_dir / "boot-branding.txt"
    unsq = _run(
        [
            "unsquashfs",
            "-f",
            "-d",
            str(output_dir / ".sqtmp"),
            str(squash),
            "usr/share/setuphelfer/rescue/boot-branding.txt",
        ],
        runner=runner,
    )
    branding_src = output_dir / ".sqtmp" / "usr/share/setuphelfer/rescue/boot-branding.txt"
    if unsq.returncode == 0 and branding_src.is_file():
        branding_dest.write_bytes(branding_src.read_bytes())
        files_meta.append(
            {
                "iso_path": "squashfs:usr/share/setuphelfer/rescue/boot-branding.txt",
                "staging_path": "setuphelfer/rescue/boot-branding.txt",
                "size_bytes": branding_dest.stat().st_size,
                "sha256": sha256_file(branding_dest),
            }
        )
    sqtmp = output_dir / ".sqtmp"
    if sqtmp.exists():
        shutil.rmtree(sqtmp, ignore_errors=True)

    version_path = _workspace_root() / "config" / "version.json"
    version_payload: dict[str, Any] = {"project_version": "unknown"}
    if version_path.is_file():
        try:
            version_payload = json.loads(version_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    (setup_dir / "version.json").write_text(
        json.dumps(version_payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    evidence_payload = {
        "built_at": _now_iso(),
        "iso_path": str(iso_path),
        "iso_sha256": sha256_file(iso_path) if iso_path.is_file() else None,
        "writer_mode": "fat32_esp",
        "files": files_meta,
        "secrets_exposed": False,
    }
    (setup_dir / "evidence.json").write_text(
        json.dumps(evidence_payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    required = [
        "EFI/BOOT/BOOTX64.EFI",
        "boot/grub/grub.cfg",
        "live/vmlinuz",
        "live/initrd.img",
        "live/filesystem.squashfs",
    ]
    missing = [r for r in required if not (output_dir / r).is_file()]
    if missing:
        raise FileNotFoundError(f"staging incomplete: {missing}")

    return {
        "schema_version": 1,
        "staging_root": str(output_dir),
        "iso_path": str(iso_path),
        "iso_sha256": evidence_payload["iso_sha256"],
        "live_cfg_parsed": bool(params.base_append or params.labels),
        "grub_menu_entries": 7,
        "files": files_meta,
        "required_paths_present": required,
        "secrets_exposed": False,
    }


def _parse_size_bytes(size: str | None) -> int | None:
    if not size:
        return None
    s = str(size).strip().upper().replace(",", ".")
    m = re.match(r"^([\d.]+)\s*([KMGT])?I?B?$", s)
    if not m:
        return None
    val = float(m.group(1))
    unit = m.group(2) or ""
    mult = {"": 1, "K": 1024, "M": 1024**2, "G": 1024**3, "T": 1024**4}.get(unit, 1)
    return int(val * mult)


def validate_fat32_write_target(
    target_device: str,
    *,
    operator_evidence: Mapping[str, Any] | None,
    confirm_phrase: str | None,
    dry_run: bool,
    runner: Runner | None = None,
) -> dict[str, Any]:
    dev = target_device.strip()
    blockers: list[str] = []
    errors: list[str] = []

    for pat in FORBIDDEN_TARGET_PATTERNS:
        if pat.match(dev):
            blockers.append("FORBIDDEN_SYSTEM_OR_BACKUP_DEVICE")
            errors.append("forbidden_device_pattern")

    classified = {d.id: d for d in list_classified_devices(runner=runner)}
    cd = classified.get(dev)
    row = None
    if cd is None:
        blockers.append("DEVICE_NOT_FOUND")
        errors.append("device_not_classified")
    else:
        candidates_pre = build_usb_candidates_payload(runner=runner)
        row = next((d for d in candidates_pre.get("devices") or [] if d.get("device") == dev), None)
        transport = str((row or {}).get("transport") or "usb").lower()
        reason = device_blocked_reason(device_path=dev, classified=cd, transport=transport)
        if reason:
            blockers.append(reason)
            errors.append(reason)

    candidates = build_usb_candidates_payload(runner=runner)
    if row is None:
        row = next((d for d in candidates.get("devices") or [] if d.get("device") == dev), None)
    if row is None:
        blockers.append("DEVICE_NOT_IN_USB_CANDIDATES")
    elif not row.get("selectable"):
        blockers.append(str(row.get("blocked_reason") or "NOT_SELECTABLE"))

    size_bytes = _parse_size_bytes((row or {}).get("size") if row else cd.size if cd else None)
    if size_bytes is not None and size_bytes < MIN_USB_BYTES:
        blockers.append("DEVICE_TOO_SMALL")
        errors.append("below_min_usb_size")

    if not dry_run:
        if confirm_phrase != CONFIRM_PHRASE_FAT32_ESP:
            blockers.append("CONFIRM_PHRASE_MISMATCH")
        if not operator_evidence or operator_evidence.get("write_allowed") is not True:
            blockers.append("OPERATOR_EVIDENCE_WRITE_NOT_ALLOWED")
        else:
            if operator_evidence.get("selected_device") != dev:
                blockers.append("EVIDENCE_DEVICE_MISMATCH")
            confirmations = operator_evidence.get("operator_confirmations") or {}
            for key in REQUIRED_CONFIRMATIONS:
                if not confirmations.get(key):
                    blockers.append("OPERATOR_CONFIRMATIONS_INCOMPLETE")
                    break

    blockers = sorted(set(blockers))
    return {
        "target_device": dev,
        "dry_run": dry_run,
        "blocked": bool(blockers),
        "blockers": blockers,
        "errors": errors,
        "device_row": row,
        "write_allowed": not blockers and not dry_run,
        "secrets_exposed": False,
    }


def build_write_plan(
    *,
    iso_path: Path,
    target_device: str,
    staging_dir: Path | None = None,
    esp_size_mib: int = ESP_SIZE_MIB_DEFAULT,
    dry_run: bool = True,
    confirm_phrase: str | None = None,
    workspace: Path | None = None,
    runner: Runner | None = None,
) -> dict[str, Any]:
    ws = workspace or _workspace_root()
    evidence = load_operator_selection_evidence(ws)
    safety = validate_fat32_write_target(
        target_device,
        operator_evidence=evidence,
        confirm_phrase=confirm_phrase,
        dry_run=dry_run,
        runner=runner,
    )

    iso = iso_path.resolve()
    if not iso.is_file():
        safety["blockers"] = sorted(set(safety.get("blockers", []) + ["ISO_MISSING"]))
        safety["blocked"] = True

    staging = staging_dir or (ws / "build/rescue/fat32-esp-staging")
    layout: dict[str, Any] | None = None
    layout_error: str | None = None
    if iso.is_file() and dry_run:
        try:
            layout = extract_iso_files(iso, staging, runner=runner)
        except OSError as exc:
            layout_error = str(exc)

    labels = fat32_esp_label_spec()
    plan = {
        "schema_version": 2,
        "mode": "dry_run" if dry_run else "write_prepared",
        "writer": "fat32_esp",
        "iso_path": str(iso),
        "iso_sha256": sha256_file(iso) if iso.is_file() else None,
        "target_device": target_device.strip(),
        "gpt_partition_name": labels["gpt_partition_name"],
        "fat_volume_label": labels["fat_volume_label"],
        "esp_size_mib": esp_size_mib,
        "partition_layout": {
            "table": "GPT",
            "partitions": [
                {
                    "number": 1,
                    "type": "EFI System (EF00)",
                    "fstype": "vfat",
                    "gpt_partition_name": labels["gpt_partition_name"],
                    "fat_volume_label": labels["fat_volume_label"],
                    "size_mib": esp_size_mib,
                    "contents": [
                        "EFI/BOOT/BOOTX64.EFI",
                        "boot/grub/grub.cfg",
                        "live/vmlinuz",
                        "live/initrd.img",
                        "live/filesystem.squashfs",
                        "setuphelfer/rescue/version.json",
                        "setuphelfer/rescue/evidence.json",
                    ],
                }
            ],
            "optional_data_partition": {
                "planned": True,
                "write_in_v1": False,
                "gpt_partition_name": "SETUPHELFER_DATA",
                "purpose": "config/logs/telemetry-spool",
            },
        },
        "staging_dir": str(staging),
        "staging_layout": layout,
        "staging_error": layout_error,
        "safety": safety,
        "operator_evidence_path": EVIDENCE_REL,
        "confirm_phrase_required": CONFIRM_PHRASE_FAT32_ESP,
        "destructive_actions": [
            "wipefs --no-act (log stale signatures on parent device)",
            "wipefs -a (full rebuild) OR wipefs -a -t iso9660 (repair stale dd signature)",
            "sgdisk --zap-all",
            (
                f"sgdisk -n 1:0:+{esp_size_mib}MiB -t 1:EF00 "
                f"-c 1:{labels['gpt_partition_name']}"
            ),
            "partprobe + udevadm settle (after partition)",
            f"mkfs.vfat -F 32 -n {labels['fat_volume_label']}",
            "verify vfat + fat label on ${TARGET}1 via blkid -p (sudo)",
            fat32_staging_rsync_command(staging=str(staging), mount="${MNT}", sudo=True),
        ],
        "signature_wipe": {
            "probe": "sudo wipefs --no-act ${TARGET}",
            "full_rebuild": "sudo wipefs -a ${TARGET}",
            "repair_stale_iso9660": "sudo wipefs -a -t iso9660 ${TARGET}",
        },
        "staging_copy_command": fat32_staging_rsync_command(
            staging=str(staging), mount="${MNT}", sudo=True
        ),
        "staging_copy_exclude": [FAT_RSYNC_EXCLUDE],
        "fat32_copy_note": (
            "FAT32 stores no Unix owner/group/permissions; do not use rsync -a on ESP."
        ),
        "write_executed": False,
        "secrets_exposed": False,
    }
    return plan


def build_operator_terminal_commands(
    *,
    iso_path: Path,
    target_device: str,
    workspace: Path | None = None,
) -> dict[str, str]:
    ws = workspace or _workspace_root()
    rel_iso = iso_path
    try:
        rel_iso = iso_path.relative_to(ws)
    except ValueError:
        pass
    staging = "build/rescue/fat32-esp-staging"
    labels = fat32_esp_label_spec()
    gpt_name = labels["gpt_partition_name"]
    fat_label = labels["fat_volume_label"]
    rsync_cmd = fat32_staging_rsync_command(staging="${STAGING}", mount="$MNT", sudo=True)
    manual_write = (
        f"cd {ws}\n"
        f"STAGING={staging}\n"
        f"TARGET={target_device}\n"
        f"# FAT32: no Unix owner/group/permissions — use FAT-safe rsync flags on ESP\n"
        f"lsblk -o NAME,SIZE,MODEL,SERIAL,TRAN \"$TARGET\"\n"
        f"udisksctl unmount -b ${{TARGET}}1 2>/dev/null || true\n"
        f"sync\n"
        f"sudo wipefs --no-act \"$TARGET\" || true\n"
        f"sudo wipefs -a \"$TARGET\"\n"
        f"sudo sgdisk --zap-all \"$TARGET\"\n"
        f"sudo sgdisk -n 1:0:+4096MiB -t 1:EF00 -c 1:{gpt_name} \"$TARGET\"\n"
        f"sync\n"
        f"sudo partprobe \"$TARGET\" || true\n"
        f"sudo udevadm settle --timeout=30 || true\n"
        f"sleep 2\n"
        f"sudo mkfs.vfat -F 32 -n {fat_label} ${{TARGET}}1\n"
        f"sync\n"
        f"sudo partprobe \"$TARGET\" || true\n"
        f"sudo udevadm settle --timeout=30 || true\n"
        f"sleep 1\n"
        f'FSTYPE=$(lsblk -no FSTYPE "${{TARGET}}1" | head -1)\n'
        f'[[ "$FSTYPE" == "vfat" ]] || {{ echo "ERROR: ${{TARGET}}1 not vfat ($FSTYPE)"; exit 1; }}\n'
        f'LABEL=$(sudo blkid -p -s LABEL -o value "${{TARGET}}1" 2>/dev/null || true)\n'
        f'if [[ "$LABEL" != "{fat_label}" ]]; then\n'
        f"  sudo fatlabel ${{TARGET}}1 {fat_label} 2>/dev/null || "
        f"sudo dosfslabel ${{TARGET}}1 {fat_label}\n"
        f"fi\n"
        f'FAT_UUID=$(sudo blkid -p -s UUID -o value "${{TARGET}}1")\n'
        f'[[ -n "$FAT_UUID" ]] || {{ echo "ERROR: FAT UUID missing on ${{TARGET}}1"; exit 1; }}\n'
        f"./scripts/rescue-live/patch-fat32-esp-grub-for-uuid.sh "
        f'--staging "$STAGING" --fat-uuid "$FAT_UUID"\n'
        f"MNT=$(mktemp -d)\n"
        f"sudo mount ${{TARGET}}1 \"$MNT\"\n"
        f"{rsync_cmd}\n"
        f"sync && sudo umount \"$MNT\" && rmdir \"$MNT\"\n"
        f"sync && sudo partprobe \"$TARGET\" || true\n"
        f"sudo udevadm settle --timeout=30 || true\n"
        f"./scripts/rescue-live/verify-fat32-esp-rescue-usb.sh --target {target_device}"
    )
    return {
        "build_layout": (
            f"cd {ws}\n"
            f"./scripts/rescue-live/build-fat32-esp-usb-layout.sh "
            f'--iso "{rel_iso}" --output-dir {staging}'
        ),
        "dry_run": (
            f"cd {ws}\n"
            f"./scripts/rescue-live/write-fat32-esp-rescue-usb.sh "
            f'--iso "{rel_iso}" --target {target_device} --dry-run'
        ),
        "write": (
            f"cd {ws}\n"
            f"./scripts/rescue-live/write-fat32-esp-rescue-usb.sh "
            f'--iso "{rel_iso}" --target {target_device} '
            f"--operator-confirm-write "
            f'--confirm-phrase "{CONFIRM_PHRASE_FAT32_ESP}"'
        ),
        "write_manual": manual_write,
        "verify": (
            f"cd {ws}\n"
            f"./scripts/rescue-live/verify-fat32-esp-rescue-usb.sh --target {target_device}"
        ),
    }


def build_compact_usb_writer_modes_summary(
    *,
    runner: Runner | None = None,
    workspace: Path | None = None,
) -> dict[str, Any]:
    ws = workspace or _workspace_root()
    gate_path = ws / "docs/evidence/runtime-results/rescue/rescue_iso_usb_gate_status_latest.json"
    gate: dict[str, Any] = {}
    if gate_path.is_file():
        try:
            gate = json.loads(gate_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass

    evidence = load_operator_selection_evidence(ws)
    iso_rel = DEFAULT_ISO_REL
    iso_path = ws / iso_rel
    target = evidence.get("selected_device") if evidence else None
    commands: dict[str, str] = {}
    if target:
        commands = build_operator_terminal_commands(
            iso_path=iso_path,
            target_device=str(target),
            workspace=ws,
        )

    msi_boot_failed = gate.get("target_laptop_booted_from_stick") is False and gate.get(
        "usb_write_sha256_verified"
    ) is True

    return {
        "iso_hybrid_dd": {
            "available": True,
            "current_boot_failed_on_msi": msi_boot_failed,
            "recommended_for_msi": False,
        },
        "fat32_esp": {
            "available": True,
            "implemented": True,
            "dry_run_available": True,
            "write_allowed": False,
            "operator_terminal_required": True,
            "recommended_for_msi": msi_boot_failed,
            "confirm_phrase": CONFIRM_PHRASE_FAT32_ESP,
            "gpt_partition_name": GPT_PARTITION_NAME,
            "fat_volume_label": FAT_VOLUME_LABEL,
            "operator_commands": commands,
            "verify_command": commands.get("verify"),
        },
        "secrets_exposed": False,
    }
