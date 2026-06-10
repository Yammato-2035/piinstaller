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
from rescue.rescue_grub_branding import generate_grub_cfg_branding_lines, stage_grub_theme_to_fat32_staging

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
BOOTX64_SOURCE_MKSTANDALONE = "grub_mkstandalone"
BOOTX64_MKSTANDALONE_MODULES = (
    "part_gpt fat search search_fs_uuid search_label normal linux gzio configfile boot "
    "gfxterm png all_video efi_gop"
)
BOOTX64_ERROR_MKSTANDALONE_MISSING = "RESCUE-FAT32-BOOTX64-MKSTANDALONE-MISSING"
BOOTX64_ERROR_ISO_COPIED = "RESCUE-FAT32-BOOTX64-ISO-COPIED-001"
BOOTX64_ERROR_STANDALONE_MISSING = "RESCUE-FAT32-BOOTX64-STANDALONE-MISSING-001"
BOOTX64_ERROR_PARTITION_MODULES = "RESCUE-FAT32-GRUB-PARTITION-MODULES-MISSING-001"
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

STAGING_REQUIRED_PATHS = (
    "EFI/BOOT/BOOTX64.EFI",
    "boot/grub/grub.cfg",
    "live/vmlinuz",
    "live/initrd.img",
    "live/filesystem.squashfs",
)

FAT32_ESP_EXECUTION_STEP_IDS: tuple[str, ...] = (
    "wipefs_probe",
    "wipefs_full",
    "sgdisk_zap",
    "sgdisk_create_esp",
    "partprobe",
    "udev_settle",
    "mkfs_vfat",
    "partprobe_after_mkfs",
    "udev_settle_after_mkfs",
    "blkid_fat_uuid",
    "patch_grub_uuid",
    "mount_esp",
    "rsync_staging",
    "sync",
    "umount_esp",
    "verify_fat32_esp",
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


def generate_fat32_esp_embedded_bootstrap_cfg(*, fat_label: str = FAT_VOLUME_LABEL) -> str:
    """Minimal GRUB bootstrap embedded in BOOTX64.EFI for FAT32 ESP (GPT+FAT modules)."""
    assert_valid_fat_volume_label(fat_label)
    return f"""set timeout=5
set default=0

insmod part_gpt
insmod fat
insmod search
insmod search_fs_uuid
insmod search_label
insmod normal
insmod linux
insmod gzio
insmod configfile

search --no-floppy --label {fat_label} --set=root

if [ -n "$root" ]; then
    set prefix=($root)/boot/grub
    if [ -f ($root)/boot/grub/grub.cfg ]; then
        configfile ($root)/boot/grub/grub.cfg
    fi
fi

menuentry "Setuphelfer Rettung starten (embedded fallback)" {{
    search --no-floppy --label {fat_label} --set=root
    linux ($root)/live/vmlinuz boot=live components quiet setuphelfer_rescue=1 setuphelfer_start_assistant=1
    initrd ($root)/live/initrd.img
}}

menuentry "Setuphelfer MSI/NVIDIA kompatibel (embedded fallback)" {{
    search --no-floppy --label {fat_label} --set=root
    linux ($root)/live/vmlinuz boot=live components pci=noaer nouveau.modeset=0 nomodeset quiet setuphelfer_rescue=1 setuphelfer_msi_compat=1
    initrd ($root)/live/initrd.img
}}
"""


def grub_mkstandalone_tooling() -> dict[str, Any]:
    """Report host GRUB EFI tooling availability (no apt install)."""
    tools = ("grub-mkstandalone", "grub-mkimage")
    available: dict[str, bool] = {}
    for tool in tools:
        proc = _run(["bash", "-lc", f"command -v {tool}"])
        available[tool] = proc.returncode == 0
    ok = available.get("grub-mkstandalone", False)
    hint = None
    if not ok:
        hint = "sudo apt install grub-efi-amd64-bin grub-common"
    return {
        "available": ok,
        "tools": available,
        "operator_hint": hint,
        "modules_requested": list(BOOTX64_MKSTANDALONE_MODULES.split()),
    }


def build_fat32_esp_bootx64_efi(
    output_path: Path,
    *,
    fat_label: str = FAT_VOLUME_LABEL,
    runner: Runner | None = None,
) -> dict[str, Any]:
    """Build standalone BOOTX64.EFI for FAT32 ESP — not ISO El-Torito copy."""
    tooling = grub_mkstandalone_tooling()
    if not tooling["available"]:
        raise FileNotFoundError(BOOTX64_ERROR_MKSTANDALONE_MISSING)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    embed_cfg = generate_fat32_esp_embedded_bootstrap_cfg(fat_label=fat_label)
    tmp_dir = output_path.parent / ".bootx64.build"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    embed_path = tmp_dir / "embedded_grub.cfg"
    embed_path.write_text(embed_cfg, encoding="utf-8")

    cmd = [
        "grub-mkstandalone",
        "--format=x86_64-efi",
        f"--output={output_path}",
        "--locales=",
        "--fonts=",
        f"--modules={BOOTX64_MKSTANDALONE_MODULES}",
        f"boot/grub/grub.cfg={embed_path}",
    ]
    proc = _run(cmd, runner=runner, timeout=180)
    if proc.returncode != 0 or not output_path.is_file() or output_path.stat().st_size < 100_000:
        detail = (proc.stderr or proc.stdout or "grub-mkstandalone failed").strip()
        raise OSError(f"{BOOTX64_ERROR_MKSTANDALONE_MISSING}: {detail}")

    embed_path.unlink(missing_ok=True)
    if tmp_dir.exists() and not any(tmp_dir.iterdir()):
        tmp_dir.rmdir()

    meta = {
        "bootx64_source": BOOTX64_SOURCE_MKSTANDALONE,
        "bootx64_embedded_bootstrap": True,
        "bootx64_iso_copied": False,
        "label": fat_label,
        "modules_requested": tooling["modules_requested"],
        "output_path": str(output_path),
        "output_size": output_path.stat().st_size,
        "sha256": sha256_file(output_path),
        "secrets_exposed": False,
    }
    return meta


def extract_iso_bootx64_sha256(iso_path: Path, *, runner: Runner | None = None) -> str | None:
    tmp = iso_path.parent / ".bootx64.iso.extract.tmp"
    proc = _run(
        [
            "xorriso",
            "-osirrox",
            "on",
            "-indev",
            str(iso_path),
            "-extract",
            "/EFI/BOOT/BOOTX64.EFI",
            str(tmp),
        ],
        runner=runner,
    )
    if proc.returncode != 0 or not tmp.is_file():
        tmp.unlink(missing_ok=True)
        return None
    digest = sha256_file(tmp)
    tmp.unlink(missing_ok=True)
    return digest


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
        *generate_grub_cfg_branding_lines(),
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


def partition_path_for_target(target_device: str, part_number: int = 1) -> str:
    """Map parent block device to partition path (sdX→sdX1, nvme→p1, mmcblk→p1)."""
    dev = (target_device or "").rstrip("/")
    if not dev.startswith("/dev/"):
        raise ValueError(f"not a block device path: {target_device!r}")
    if part_number < 1:
        raise ValueError(f"invalid partition number: {part_number}")
    if re.search(r"mmcblk\d+$", dev):
        return f"{dev}p{part_number}"
    if re.search(r"nvme\d+n\d+$", dev):
        return f"{dev}p{part_number}"
    return f"{dev}{part_number}"


def staging_required_paths_ok(staging_dir: Path) -> tuple[bool, list[str]]:
    missing = [rel for rel in STAGING_REQUIRED_PATHS if not (staging_dir / rel).is_file()]
    return not missing, missing


def validate_fat32_execute_write_gates(
    *,
    target_device: str,
    iso_path: Path,
    staging_dir: Path,
    operator_evidence: Mapping[str, Any] | None,
    confirm_phrase: str | None,
    execute_write: bool,
    confirm_write: bool,
    expected_iso_sha256: str | None = None,
    runner: Runner | None = None,
) -> dict[str, Any]:
    """All gates required before --execute-write may run destructive steps."""
    safety = validate_fat32_write_target(
        target_device,
        operator_evidence=operator_evidence,
        confirm_phrase=confirm_phrase,
        dry_run=False,
        runner=runner,
    )
    blockers: list[str] = list(safety.get("blockers") or [])
    errors: list[str] = list(safety.get("errors") or [])

    if not confirm_write:
        blockers.append("OPERATOR_CONFIRM_WRITE_MISSING")
    if not execute_write:
        blockers.append("EXECUTE_WRITE_FLAG_MISSING")
    if confirm_phrase != CONFIRM_PHRASE_FAT32_ESP:
        if "CONFIRM_PHRASE_MISMATCH" not in blockers:
            blockers.append("CONFIRM_PHRASE_MISMATCH")

    iso = iso_path.resolve()
    actual_sha: str | None = None
    if not iso.is_file():
        blockers.append("ISO_MISSING")
        errors.append("iso_missing")
    else:
        actual_sha = sha256_file(iso)
        if expected_iso_sha256 and actual_sha != expected_iso_sha256.strip().lower():
            blockers.append("ISO_SHA256_MISMATCH")
            errors.append("iso_sha256_mismatch")

    staging_ok, staging_missing = staging_required_paths_ok(staging_dir)
    if not staging_ok:
        blockers.append("STAGING_INCOMPLETE")
        errors.append(f"staging_missing:{','.join(staging_missing)}")

    classified = {d.id: d for d in list_classified_devices(runner=runner)}
    cd = classified.get(target_device.strip())
    if cd is not None:
        if cd.mountpoints:
            blockers.append("TARGET_DEVICE_MOUNTED")
            errors.append("target_device_mounted")
        for part in cd.partitions:
            if part.mountpoints:
                blockers.append("TARGET_PARTITION_MOUNTED")
                errors.append("target_partition_mounted")
                break

    blockers = sorted(set(blockers))
    partition = partition_path_for_target(target_device.strip(), 1)
    return {
        "target_device": target_device.strip(),
        "target_partition": partition,
        "execute_write": execute_write,
        "confirm_write": confirm_write,
        "blocked": bool(blockers),
        "blockers": blockers,
        "errors": errors,
        "write_allowed": not blockers,
        "iso_path": str(iso),
        "iso_sha256": actual_sha,
        "expected_iso_sha256": expected_iso_sha256,
        "staging_dir": str(staging_dir),
        "staging_complete": staging_ok,
        "staging_missing": staging_missing,
        "execution_step_ids": list(FAT32_ESP_EXECUTION_STEP_IDS),
        "secrets_exposed": False,
    }


RS001_FAT32_ESP_MD_REL = "docs/evidence/rescue/RS_001_FAT32_ESP_WRITE_RESULT.md"
FAT32_ESP_WRITE_LATEST_NAME = "fat32_esp_write_latest.json"


def _rs001_reason_for_result(*, write_status: str, verify_status: str) -> str:
    if write_status == "success" and verify_status == "success":
        return "USB written and verified, hardware boot not yet proven"
    if write_status == "success":
        return "USB written but verify incomplete, hardware boot not yet proven"
    return "USB write not completed, hardware boot not yet proven"


def load_evidence_state_snippets(evidence_dir: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    pre: dict[str, Any] = {}
    post: dict[str, Any] = {}
    pre_path = evidence_dir / "pre_lsblk.txt"
    post_path = evidence_dir / "post_lsblk.txt"
    if pre_path.is_file():
        pre["lsblk"] = pre_path.read_text(encoding="utf-8", errors="replace")
    if post_path.is_file():
        post["lsblk"] = post_path.read_text(encoding="utf-8", errors="replace")
    return pre, post


def render_rs001_fat32_esp_write_result_md(
    result: Mapping[str, Any],
    *,
    evidence_dir: Path,
    evidence_root: Path,
) -> str:
    """Render operator-facing markdown — no shell/Python template placeholders."""
    latest_path = evidence_root / FAT32_ESP_WRITE_LATEST_NAME
    lines = [
        "# RS-001 FAT32-ESP USB Write Result",
        "",
        f"**Updated:** {result.get('completed_at') or result.get('started_at') or 'unknown'}",
        f"**Evidence dir:** `{evidence_dir}`",
        "",
        "## Summary",
        "",
        "| Field | Value |",
        "|-------|-------|",
        f"| target_device | `{result.get('target_device', '')}` |",
        f"| target_partition | `{result.get('target_partition', '')}` |",
        f"| write_executed | `{result.get('write_executed')}` |",
        f"| write_status | `{result.get('write_status', '')}` |",
        f"| verify_status | `{result.get('verify_status', '')}` |",
        f"| evidence_status | `{result.get('evidence_status', '')}` |",
        f"| fat_uuid | `{result.get('fat_uuid', '')}` |",
        f"| rs001_status | `{result.get('rs001_status', 'red')}` |",
        "",
        f"**rs001_reason:** {result.get('rs001_reason', '')}",
        "",
        "## Operator assessment",
        "",
        f"- USB write: **{result.get('write_status', 'unknown')}**",
        f"- USB verify: **{result.get('verify_status', 'unknown')}**",
        f"- RS-001: **{result.get('rs001_status', 'red')}** / hardware boot not yet proven",
        "- Next: physical UEFI boot on MSI/reference hardware",
        "",
        "## Artifacts",
        "",
        f"- `{evidence_dir / 'plan.json'}`",
        f"- `{evidence_dir / 'write_steps.log'}`",
        f"- `{evidence_dir / 'verify.log'}`",
        f"- `{latest_path}`",
        "",
        "## Hardware boot",
        "",
        "RS-001 remains **red** until operator documents UEFI boot to Setuphelfer menu/TUI on reference hardware.",
        "",
    ]
    return "\n".join(lines) + "\n"


def build_fat32_esp_write_result(
    *,
    target_device: str,
    iso_path: Path,
    iso_sha256: str | None,
    started_at: str,
    completed_at: str | None,
    write_executed: bool,
    write_status: str,
    failed_step: str | None,
    fat_uuid: str | None,
    pre_state: Mapping[str, Any] | None,
    post_state: Mapping[str, Any] | None,
    verify_status: str,
    evidence_dir: str | None = None,
    evidence_status: str = "complete",
    evidence_errors: Sequence[str] | None = None,
) -> dict[str, Any]:
    partition = partition_path_for_target(target_device.strip(), 1)
    iso_resolved = iso_path.resolve()
    return {
        "schema_version": 1,
        "writer": "fat32_esp",
        "target_device": target_device.strip(),
        "target_partition": partition,
        "iso_path": str(iso_resolved),
        "iso_sha256": iso_sha256,
        "started_at": started_at,
        "completed_at": completed_at,
        "write_executed": bool(write_executed),
        "write_status": write_status,
        "failed_step": failed_step,
        "fat_uuid": fat_uuid,
        "pre_state": dict(pre_state or {}),
        "post_state": dict(post_state or {}),
        "verify_status": verify_status,
        "evidence_status": evidence_status,
        "evidence_errors": list(evidence_errors or []),
        "rs001_status": "red",
        "rs001_reason": _rs001_reason_for_result(
            write_status=write_status,
            verify_status=verify_status,
        ),
        "evidence_dir": evidence_dir,
        "secrets_exposed": False,
    }


def persist_fat32_esp_write_evidence(
    result: Mapping[str, Any],
    *,
    evidence_dir: Path,
    evidence_root: Path,
    repo_root: Path,
    write_latest: bool = True,
    write_md: bool = True,
) -> list[str]:
    """Write result.json, optional latest symlink file and RS-001 markdown."""
    errors: list[str] = []
    evidence_dir.mkdir(parents=True, exist_ok=True)
    result_path = evidence_dir / "result.json"
    try:
        result_path.write_text(
            json.dumps(dict(result), indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
    except OSError as exc:
        errors.append(f"result_json:{exc}")

    if write_latest:
        latest_path = evidence_root / FAT32_ESP_WRITE_LATEST_NAME
        try:
            latest_path.parent.mkdir(parents=True, exist_ok=True)
            latest_path.write_text(
                json.dumps(dict(result), indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )
        except OSError as exc:
            errors.append(f"latest_json:{exc}")

    if write_md:
        md_path = repo_root / RS001_FAT32_ESP_MD_REL
        try:
            md_path.parent.mkdir(parents=True, exist_ok=True)
            md_text = render_rs001_fat32_esp_write_result_md(
                result,
                evidence_dir=evidence_dir,
                evidence_root=evidence_root,
            )
            md_path.write_text(md_text, encoding="utf-8")
        except OSError as exc:
            errors.append(f"rs001_md:{exc}")

    return errors


def finalize_fat32_esp_write_evidence(
    *,
    evidence_dir: Path,
    evidence_root: Path,
    repo_root: Path,
    iso_path: Path,
    target_device: str,
    started_at: str,
    write_executed: bool,
    write_status: str,
    verify_status: str,
    failed_step: str | None = None,
    fat_uuid: str | None = None,
    write_latest: bool = True,
    write_md: bool = True,
) -> dict[str, Any]:
    """Build and persist post-write evidence; never downgrades write_status on report errors."""
    pre_state, post_state = load_evidence_state_snippets(evidence_dir)
    completed_at = datetime.now(tz=timezone.utc).isoformat()
    iso_sha = sha256_file(iso_path) if iso_path.is_file() else None
    base_result = build_fat32_esp_write_result(
        target_device=target_device,
        iso_path=iso_path,
        iso_sha256=iso_sha,
        started_at=started_at,
        completed_at=completed_at,
        write_executed=write_executed,
        write_status=write_status,
        failed_step=failed_step,
        fat_uuid=fat_uuid,
        pre_state=pre_state,
        post_state=post_state,
        verify_status=verify_status,
        evidence_dir=str(evidence_dir.resolve()),
        evidence_status="complete",
    )
    persist_errors = persist_fat32_esp_write_evidence(
        base_result,
        evidence_dir=evidence_dir,
        evidence_root=evidence_root,
        repo_root=repo_root,
        write_latest=write_latest,
        write_md=write_md,
    )
    if persist_errors:
        base_result = build_fat32_esp_write_result(
            target_device=target_device,
            iso_path=iso_path,
            iso_sha256=iso_sha,
            started_at=started_at,
            completed_at=completed_at,
            write_executed=write_executed,
            write_status=write_status,
            failed_step=failed_step,
            fat_uuid=fat_uuid,
            pre_state=pre_state,
            post_state=post_state,
            verify_status=verify_status,
            evidence_dir=str(evidence_dir.resolve()),
            evidence_status="review_required",
            evidence_errors=persist_errors,
        )
        extra = persist_fat32_esp_write_evidence(
            base_result,
            evidence_dir=evidence_dir,
            evidence_root=evidence_root,
            repo_root=repo_root,
            write_latest=write_latest,
            write_md=False,
        )
        err_log = evidence_dir / "evidence_errors.log"
        err_log.write_text("\n".join(persist_errors + extra) + "\n", encoding="utf-8")
        if extra:
            base_result["evidence_errors"] = list(base_result.get("evidence_errors") or []) + extra

    return {
        "result": base_result,
        "evidence_status": base_result.get("evidence_status"),
        "evidence_errors": list(base_result.get("evidence_errors") or []),
        "secrets_exposed": False,
    }


def rebuild_fat32_esp_evidence_reports(
    evidence_dir: Path,
    *,
    evidence_root: Path | None = None,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    """Rebuild result/latest/md from an existing evidence run directory."""
    ws = repo_root or _workspace_root()
    root = evidence_root or (ws / "docs/evidence/runtime-results/rescue")
    result_path = evidence_dir / "result.json"
    pre_state, post_state = load_evidence_state_snippets(evidence_dir)

    if result_path.is_file():
        try:
            existing = json.loads(result_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            existing = {}
    else:
        existing = {}

    write_steps = evidence_dir / "write_steps.log"
    verify_log = evidence_dir / "verify.log"
    fat_uuid = existing.get("fat_uuid")
    if not fat_uuid and write_steps.is_file():
        for line in write_steps.read_text(encoding="utf-8", errors="replace").splitlines():
            if line.startswith("FAT_UUID="):
                fat_uuid = line.split("=", 1)[1].strip()
                break

    write_status = existing.get("write_status") or (
        "success" if verify_log.is_file() and "OK: FAT32 ESP rescue USB verified" in verify_log.read_text(encoding="utf-8", errors="replace") else "unknown"
    )
    verify_status = existing.get("verify_status") or (
        "success" if verify_log.is_file() and "OK: FAT32 ESP rescue USB verified" in verify_log.read_text(encoding="utf-8", errors="replace") else "not_run"
    )

    run_id = evidence_dir.name
    started_at = existing.get("started_at") or ""
    if not started_at and run_id.startswith("fat32_esp_write_"):
        stamp = run_id.removeprefix("fat32_esp_write_")
        if len(stamp) == 15 and stamp[8] == "_":
            started_at = f"{stamp[0:4]}-{stamp[4:6]}-{stamp[6:8]}T{stamp[9:11]}:{stamp[11:13]}:{stamp[13:15]}Z"

    iso_path = Path(existing.get("iso_path") or (ws / DEFAULT_ISO_REL))
    if not iso_path.is_absolute():
        iso_path = (ws / iso_path).resolve()

    result = build_fat32_esp_write_result(
        target_device=str(existing.get("target_device") or "/dev/sdb"),
        iso_path=iso_path,
        iso_sha256=existing.get("iso_sha256") or (sha256_file(iso_path) if iso_path.is_file() else None),
        started_at=started_at,
        completed_at=existing.get("completed_at") or datetime.now(tz=timezone.utc).isoformat(),
        write_executed=bool(existing.get("write_executed", True)),
        write_status=str(write_status),
        failed_step=existing.get("failed_step"),
        fat_uuid=fat_uuid,
        pre_state=pre_state or existing.get("pre_state") or {},
        post_state=post_state or existing.get("post_state") or {},
        verify_status=str(verify_status),
        evidence_dir=str(evidence_dir.resolve()),
        evidence_status="complete",
    )
    errors = persist_fat32_esp_write_evidence(
        result,
        evidence_dir=evidence_dir,
        evidence_root=root,
        repo_root=ws,
    )
    if errors:
        result = build_fat32_esp_write_result(
            target_device=result["target_device"],
            iso_path=iso_path,
            iso_sha256=result.get("iso_sha256"),
            started_at=result["started_at"],
            completed_at=result["completed_at"],
            write_executed=result["write_executed"],
            write_status=result["write_status"],
            failed_step=result.get("failed_step"),
            fat_uuid=result.get("fat_uuid"),
            pre_state=result.get("pre_state") or {},
            post_state=result.get("post_state") or {},
            verify_status=result["verify_status"],
            evidence_dir=result.get("evidence_dir"),
            evidence_status="review_required",
            evidence_errors=errors,
        )
        (evidence_dir / "evidence_errors.log").write_text("\n".join(errors) + "\n", encoding="utf-8")

    return {"result": result, "evidence_errors": errors, "secrets_exposed": False}


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
    theme_meta = stage_grub_theme_to_fat32_staging(output_dir, _workspace_root())

    extract_list = [
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

    bootx64_path = output_dir / "EFI/BOOT/BOOTX64.EFI"
    bootx64_meta = build_fat32_esp_bootx64_efi(bootx64_path, runner=runner)
    files_meta.append(
        {
            "iso_path": None,
            "staging_path": "EFI/BOOT/BOOTX64.EFI",
            "size_bytes": bootx64_meta["output_size"],
            "sha256": bootx64_meta["sha256"],
            "bootx64_source": bootx64_meta["bootx64_source"],
        }
    )
    iso_bootx64_sha256 = extract_iso_bootx64_sha256(iso_path, runner=runner)
    if iso_bootx64_sha256 and iso_bootx64_sha256 == bootx64_meta["sha256"]:
        raise OSError(BOOTX64_ERROR_ISO_COPIED)

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
        "bootx64_source": bootx64_meta["bootx64_source"],
        "bootx64_embedded_bootstrap": True,
        "bootx64_iso_copied": False,
        "bootx64_modules_requested": bootx64_meta["modules_requested"],
        "grub_theme_staged": theme_meta,
        "bootx64_sha256": bootx64_meta["sha256"],
        "iso_bootx64_sha256": iso_bootx64_sha256,
        "bootx64_differs_from_iso": bool(
            iso_bootx64_sha256 and iso_bootx64_sha256 != bootx64_meta["sha256"]
        ),
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
        "schema_version": 2,
        "staging_root": str(output_dir),
        "iso_path": str(iso_path),
        "iso_sha256": evidence_payload["iso_sha256"],
        "live_cfg_parsed": bool(params.base_append or params.labels),
        "grub_menu_entries": 7,
        "bootx64_source": bootx64_meta["bootx64_source"],
        "bootx64_embedded_bootstrap": True,
        "bootx64_iso_copied": False,
        "bootx64_sha256": bootx64_meta["sha256"],
        "iso_bootx64_sha256": iso_bootx64_sha256,
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
            f'--confirm-phrase "{CONFIRM_PHRASE_FAT32_ESP}" '
            f"--execute-write"
        ),
        "write_manual": manual_write,
        "write_prepared": (
            f"cd {ws}\n"
            f"./scripts/rescue-live/write-fat32-esp-rescue-usb.sh "
            f'--iso "{rel_iso}" --target {target_device} '
            f"--operator-confirm-write "
            f'--confirm-phrase "{CONFIRM_PHRASE_FAT32_ESP}"'
        ),
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
