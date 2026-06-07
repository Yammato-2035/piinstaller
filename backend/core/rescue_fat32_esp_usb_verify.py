"""FAT32 ESP Rescue USB read-only verification helpers (no device writes)."""

from __future__ import annotations

import json
import re
import subprocess
from typing import Any, Callable, Mapping, Sequence

from pathlib import Path

from core.rescue_fat32_esp_usb_writer import (
    EFI_PARTTYPE_UUID,
    FAT_VOLUME_LABEL,
    GPT_PARTITION_NAME,
)

Runner = Callable[..., Any]

STALE_PARENT_ISO9660_WARN = "RESCUE-FAT32-WARN-STALE-PARENT-ISO9660-SIGNATURE"
STALE_PARENT_ISO9660_REPAIR = "sudo wipefs -a -t iso9660 {target}"

GRUB_ERROR_ROOT = "RESCUE-FAT32-GRUB-ROOT-001"
GRUB_ERROR_KERNEL = "RESCUE-FAT32-GRUB-KERNEL-PATH-001"
GRUB_ERROR_INITRD = "RESCUE-FAT32-GRUB-INITRD-PATH-001"
BOOTX64_ERROR_ISO_COPIED = "RESCUE-FAT32-BOOTX64-ISO-COPIED-001"
BOOTX64_ERROR_STANDALONE_MISSING = "RESCUE-FAT32-BOOTX64-STANDALONE-MISSING-001"
BOOTX64_ERROR_PARTITION_MODULES = "RESCUE-FAT32-GRUB-PARTITION-MODULES-MISSING-001"

_EMBEDDED_BOOTSTRAP_TOKENS = (
    "insmod part_gpt",
    "insmod fat",
    "insmod search_label",
    "insmod configfile",
    "search --no-floppy --label",
)

_GRUB_LINUX_RE = re.compile(r"^\s*linux\s+(\S+)", re.I | re.M)
_GRUB_INITRD_RE = re.compile(r"^\s*initrd\s+(\S+)", re.I | re.M)


def _run(cmd: list[str], *, runner: Runner | None = None, timeout: int = 30) -> subprocess.CompletedProcess[str]:
    if runner is not None:
        return runner(cmd, timeout=timeout)
    return subprocess.run(cmd, capture_output=True, text=True, check=False, timeout=timeout)


def parse_blkid_label_output(stdout: str) -> str:
    label = (stdout or "").strip()
    if label.startswith('"') and label.endswith('"'):
        label = label[1:-1]
    return label


def parse_wipefs_signature_types(wipefs_output: str) -> list[str]:
    """Extract filesystem type tokens from wipefs --no-act output."""
    types: list[str] = []
    for line in (wipefs_output or "").splitlines():
        line = line.strip()
        if not line:
            continue
        # wipefs: /dev/sdb: 8 bytes offset 0x00000200 iso9660 ...
        m = re.search(r"\b(iso9660|vfat|gpt|dos|exfat|ext[234]|swap)\b", line, re.I)
        if m:
            types.append(m.group(1).lower())
        elif ":" in line:
            tail = line.split(":", 1)[-1].strip()
            parts = tail.split()
            if len(parts) >= 4:
                types.append(parts[-1].lower())
    return types


def partition_is_efi_system(parttype: str) -> bool:
    pt = (parttype or "").lower()
    return (
        "efi" in pt
        or "ef00" in pt
        or EFI_PARTTYPE_UUID.lower() in pt
    )


def detect_stale_parent_iso9660(
    *,
    parent_pttype: str | None,
    parent_signature_types: Sequence[str],
) -> bool:
    """True when parent still carries iso9660 from prior dd while GPT layout exists."""
    if (parent_pttype or "").lower() != "gpt":
        return False
    return any("iso9660" in str(t).lower() for t in parent_signature_types)


def evaluate_verify_probe(
    *,
    parent_pttype: str | None,
    parent_signature_types: Sequence[str] | None = None,
    part_parttype: str | None,
    part_partlabel: str | None,
    part_fstype: str | None,
    part_fat_label: str | None,
    target_device: str = "/dev/sdb",
) -> dict[str, Any]:
    """Pure evaluation of block-layer probes (unit-testable)."""
    errors: list[dict[str, Any]] = []
    warnings: list[str] = []
    sig_types = list(parent_signature_types or [])

    if (parent_pttype or "").lower() != "gpt":
        errors.append(
            {
                "code": "NO_GPT",
                "message": f"no GPT on target (PTTYPE={parent_pttype or 'missing'})",
                "exit_code": 20,
            }
        )

    if not part_parttype:
        errors.append(
            {
                "code": "NO_ESP_PARTITION",
                "message": "no ESP partition found",
                "exit_code": 21,
            }
        )
    elif not partition_is_efi_system(part_parttype):
        errors.append(
            {
                "code": "NOT_EFI_SYSTEM",
                "message": f"partition not EFI System (PARTTYPE={part_parttype})",
                "exit_code": 21,
            }
        )

    fstype = (part_fstype or "").lower()
    if fstype not in ("vfat", "msdos"):
        errors.append(
            {
                "code": "NOT_VFAT",
                "message": f"partition not FAT32/vfat (FSTYPE={part_fstype or 'missing'})",
                "exit_code": 22,
            }
        )

    if (part_partlabel or "") != GPT_PARTITION_NAME:
        errors.append(
            {
                "code": "GPT_PARTNAME_MISMATCH",
                "message": (
                    f"GPT partition name expected {GPT_PARTITION_NAME} "
                    f"got {part_partlabel or 'missing'}"
                ),
                "exit_code": 22,
            }
        )

    label = (part_fat_label or "").strip()
    if not label:
        errors.append(
            {
                "code": "FAT_LABEL_MISSING",
                "message": (
                    f"FAT volume label expected {FAT_VOLUME_LABEL} got missing "
                    f"— repair: sudo fatlabel {target_device}1 {FAT_VOLUME_LABEL}"
                ),
                "exit_code": 22,
            }
        )
    elif label != FAT_VOLUME_LABEL:
        errors.append(
            {
                "code": "FAT_LABEL_MISMATCH",
                "message": (
                    f"FAT volume label expected {FAT_VOLUME_LABEL} got {label} "
                    f"— repair: sudo fatlabel {target_device}1 {FAT_VOLUME_LABEL}"
                ),
                "exit_code": 22,
            }
        )

    label_errors = [e for e in errors if e["code"].startswith("FAT_LABEL")]
    if detect_stale_parent_iso9660(parent_pttype=parent_pttype, parent_signature_types=sig_types):
        if not label_errors:
            warnings.append(STALE_PARENT_ISO9660_WARN)
            warnings.append(STALE_PARENT_ISO9660_REPAIR.format(target=target_device))

    exit_code = 0 if not errors else int(errors[0]["exit_code"])
    return {
        "ok": not errors,
        "errors": errors,
        "warnings": warnings,
        "exit_code": exit_code,
        "part_fat_label": label or None,
        "stale_parent_iso9660": detect_stale_parent_iso9660(
            parent_pttype=parent_pttype,
            parent_signature_types=sig_types,
        ),
    }


def probe_fat_volume_label(partition: str, *, runner: Runner | None = None) -> str:
    """Read FAT volume label from partition device only (never parent disk)."""
    attempts: list[list[str]] = [
        ["sudo", "blkid", "-p", "-s", "LABEL", "-o", "value", partition],
        ["blkid", "-p", "-s", "LABEL", "-o", "value", partition],
    ]
    for cmd in attempts:
        proc = _run(cmd, runner=runner)
        label = parse_blkid_label_output(proc.stdout or "")
        if label:
            return label

    for tool, use_sudo in (("fatlabel", True), ("fatlabel", False), ("dosfslabel", True), ("dosfslabel", False)):
        cmd = (["sudo", tool, partition] if use_sudo else [tool, partition])
        proc = _run(cmd, runner=runner)
        label = parse_blkid_label_output(proc.stdout or "")
        if label:
            return label
    return ""


def probe_parent_signature_types(target_device: str, *, runner: Runner | None = None) -> list[str]:
    proc = _run(["sudo", "wipefs", "--no-act", target_device], runner=runner)
    if proc.returncode != 0:
        proc = _run(["wipefs", "--no-act", target_device], runner=runner)
    return parse_wipefs_signature_types((proc.stdout or "") + "\n" + (proc.stderr or ""))


def lsblk_field(device: str, field: str, *, runner: Runner | None = None) -> str:
    proc = _run(["lsblk", "-no", field, device], runner=runner)
    if proc.returncode != 0:
        return ""
    return (proc.stdout or "").strip().splitlines()[0] if (proc.stdout or "").strip() else ""


def _grub_active_lines(grub_text: str) -> list[str]:
    active: list[str] = []
    for raw in grub_text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        active.append(line)
    return active


def _grub_path_to_rel(grub_path: str) -> str:
    path = grub_path.strip()
    if path.startswith("("):
        # (hd0,gpt1)/live/vmlinuz -> live/vmlinuz
        _, _, rest = path.partition(")")
        path = rest or path
    return path.lstrip("/")


def probe_fat_filesystem_uuid(partition: str, *, runner: Runner | None = None) -> str:
    for cmd in (
        ["sudo", "blkid", "-p", "-s", "UUID", "-o", "value", partition],
        ["blkid", "-p", "-s", "UUID", "-o", "value", partition],
    ):
        proc = _run(cmd, runner=runner)
        uuid = parse_blkid_label_output(proc.stdout or "")
        if uuid:
            return uuid
    return ""


def validate_fat32_esp_grub_cfg(
    grub_text: str,
    *,
    mount_root: Path | None = None,
    fat_label: str = FAT_VOLUME_LABEL,
    expected_fat_uuid: str | None = None,
) -> dict[str, Any]:
    """Validate FAT32 ESP grub.cfg root search and kernel/initrd paths."""
    errors: list[str] = []
    active = _grub_active_lines(grub_text)
    active_blob = "\n".join(active)

    uuid = (expected_fat_uuid or "").strip()
    if uuid:
        if f"search --no-floppy --fs-uuid {uuid}" not in active_blob:
            errors.append(GRUB_ERROR_ROOT)
    label_search = f"search --no-floppy --label {fat_label} --set=root"
    if uuid:
        if label_search not in active_blob:
            errors.append(GRUB_ERROR_ROOT)
    elif label_search not in active_blob:
        errors.append(GRUB_ERROR_ROOT)

    forbidden_tokens = ("loopback", "iso-scan", "findiso", "search --set=root --file")
    for token in forbidden_tokens:
        if token in active_blob:
            errors.append(GRUB_ERROR_ROOT)

    for line in active:
        if line.startswith("search") and GPT_PARTITION_NAME in line:
            errors.append(GRUB_ERROR_ROOT)

    linux_paths = [m.group(1) for m in _GRUB_LINUX_RE.finditer("\n".join(active))]
    initrd_paths = [m.group(1) for m in _GRUB_INITRD_RE.finditer("\n".join(active))]

    if not linux_paths:
        errors.append(GRUB_ERROR_KERNEL)
    if not initrd_paths:
        errors.append(GRUB_ERROR_INITRD)

    boot_entries = len(linux_paths)
    if boot_entries != len(initrd_paths):
        errors.append(GRUB_ERROR_INITRD)

    for lp in linux_paths:
        rel = _grub_path_to_rel(lp)
        if rel != "live/vmlinuz":
            errors.append(GRUB_ERROR_KERNEL)
        elif mount_root is not None and not (mount_root / rel).is_file():
            errors.append(GRUB_ERROR_KERNEL)

    for ip in initrd_paths:
        rel = _grub_path_to_rel(ip)
        if rel != "live/initrd.img":
            errors.append(GRUB_ERROR_INITRD)
        elif mount_root is not None and not (mount_root / rel).is_file():
            errors.append(GRUB_ERROR_INITRD)

    return {
        "ok": not errors,
        "errors": sorted(set(errors)),
        "linux_paths": linux_paths,
        "initrd_paths": initrd_paths,
        "boot_menu_entries": boot_entries,
    }


def validate_fat32_esp_grub_cfg_file(
    grub_cfg_path: Path,
    *,
    mount_root: Path | None = None,
    expected_fat_uuid: str | None = None,
) -> dict[str, Any]:
    if not grub_cfg_path.is_file():
        return {
            "ok": False,
            "errors": [GRUB_ERROR_ROOT, GRUB_ERROR_KERNEL, GRUB_ERROR_INITRD],
            "linux_paths": [],
            "initrd_paths": [],
            "boot_menu_entries": 0,
        }
    root = mount_root if mount_root is not None else grub_cfg_path.parent.parent.parent
    return validate_fat32_esp_grub_cfg(
        grub_cfg_path.read_text(encoding="utf-8", errors="replace"),
        mount_root=root,
        expected_fat_uuid=expected_fat_uuid,
    )


def _load_staging_evidence(mount_root: Path) -> dict[str, Any]:
    path = mount_root / "setuphelfer/rescue/evidence.json"
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def validate_fat32_esp_bootx64_on_mount(
    mount_root: Path,
    *,
    iso_bootx64_sha256: str | None = None,
) -> dict[str, Any]:
    """Verify standalone BOOTX64 on real USB/staging — not blind ISO copy."""
    errors: list[str] = []
    boot_path = mount_root / "EFI/BOOT/BOOTX64.EFI"
    if not boot_path.is_file():
        errors.append(BOOTX64_ERROR_STANDALONE_MISSING)
        return {"ok": False, "errors": errors}

    evidence = _load_staging_evidence(mount_root)
    source = evidence.get("bootx64_source")
    if source != "grub_mkstandalone":
        errors.append(BOOTX64_ERROR_STANDALONE_MISSING)
    if evidence.get("bootx64_iso_copied") is True:
        errors.append(BOOTX64_ERROR_ISO_COPIED)

    usb_sha = evidence.get("bootx64_sha256")
    if not usb_sha:
        from core.rescue_fat32_esp_usb_writer import sha256_file

        usb_sha = sha256_file(boot_path)

    iso_sha = iso_bootx64_sha256 or evidence.get("iso_bootx64_sha256")
    if iso_sha and usb_sha == iso_sha:
        errors.append(BOOTX64_ERROR_ISO_COPIED)

    bootstrap_cfg = ""
    try:
        from core.rescue_fat32_esp_usb_writer import generate_fat32_esp_embedded_bootstrap_cfg

        bootstrap_cfg = generate_fat32_esp_embedded_bootstrap_cfg()
    except Exception:
        pass
    for token in _EMBEDDED_BOOTSTRAP_TOKENS:
        if bootstrap_cfg and token not in bootstrap_cfg:
            errors.append(BOOTX64_ERROR_PARTITION_MODULES)

    return {
        "ok": not errors,
        "errors": sorted(set(errors)),
        "bootx64_source": source,
        "bootx64_sha256": usb_sha,
        "iso_bootx64_sha256": iso_sha,
        "bootx64_differs_from_iso": bool(iso_sha and usb_sha and iso_sha != usb_sha),
    }

