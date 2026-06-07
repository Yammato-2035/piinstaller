"""FAT32 ESP Rescue USB read-only verification helpers (no device writes)."""

from __future__ import annotations

import re
import subprocess
from typing import Any, Callable, Mapping, Sequence

from core.rescue_fat32_esp_usb_writer import (
    EFI_PARTTYPE_UUID,
    FAT_VOLUME_LABEL,
    GPT_PARTITION_NAME,
)

Runner = Callable[..., Any]

STALE_PARENT_ISO9660_WARN = "RESCUE-FAT32-WARN-STALE-PARENT-ISO9660-SIGNATURE"
STALE_PARENT_ISO9660_REPAIR = "sudo wipefs -a -t iso9660 {target}"


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
