"""FAT32 ESP live payload update — squashfs/evidence only, no partition rewrite."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

from core.rescue_fat32_esp_usb_writer import (
    FAT_VOLUME_LABEL,
    GPT_PARTITION_NAME,
    partition_path_for_target,
    sha256_file,
)

CONFIRM_PHRASE_PAYLOAD_UPDATE = "UPDATE SETUPHELFER FAT32 ESP LIVE PAYLOAD"

EXPECTED_USB_SERIAL = "24111412110686"
EXPECTED_USB_MODEL_SUBSTR = "Ultra Line"
MIN_USB_SIZE_GIB = 50

ALLOWED_PAYLOAD_REL_PATHS: tuple[str, ...] = (
    "live/filesystem.squashfs",
    "live/initrd.img",
    "live/vmlinuz",
    "setuphelfer/rescue/evidence.json",
    "setuphelfer/rescue/version.json",
    "setuphelfer/rescue/boot-branding.txt",
)

FORBIDDEN_SHELL_PATTERNS: tuple[str, ...] = (
    "wipefs",
    "sgdisk",
    "mkfs",
    " parted ",
    " dd ",
    "gdisk --zap",
)

EFI_PARTTYPE_MARKERS: tuple[str, ...] = (
    "EFI System",
    "ef00",
    "c12a7328-f81f-11d2-ba4b-00a0c93ec93b",
)


def _now_iso() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


def script_has_forbidden_destructive_commands(script_text: str) -> list[str]:
    executable: list[str] = []
    for raw in script_text.splitlines():
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        executable.append(f" {raw.lower()} ")
    lowered = "".join(executable)
    return [pat.strip() for pat in FORBIDDEN_SHELL_PATTERNS if pat in lowered]


def validate_payload_update_target_probe(
    *,
    target_device: str,
    partition_device: str,
    transport: str | None,
    size: str | None,
    model: str | None,
    serial: str | None,
    fstype: str | None,
    label: str | None,
    parttypename: str | None,
    gpt_partname: str | None,
    mountpoints: Sequence[str] | None,
) -> dict[str, Any]:
    """Pure safety evaluation from lsblk/blkid probes (unit-testable)."""
    blockers: list[str] = []
    dev = target_device.strip()
    part = partition_device.strip()

    if dev != "/dev/sdb":
        blockers.append("UNEXPECTED_TARGET_DEVICE")
    if part != "/dev/sdb1":
        blockers.append("UNEXPECTED_PARTITION_DEVICE")
    if (transport or "").lower() != "usb":
        blockers.append("NOT_USB_TRANSPORT")
    if (fstype or "").lower() not in ("vfat", "msdos"):
        blockers.append("NOT_VFAT_PARTITION")
    if (label or "").upper() != FAT_VOLUME_LABEL:
        blockers.append("FAT_LABEL_MISMATCH")
    pt = (parttypename or "").lower()
    gpt = (gpt_partname or "").upper()
    if not any(m.lower() in pt for m in EFI_PARTTYPE_MARKERS) and gpt != GPT_PARTITION_NAME:
        blockers.append("NOT_EFI_SYSTEM_PARTITION")
    if gpt and gpt != GPT_PARTITION_NAME:
        blockers.append("GPT_PARTNAME_MISMATCH")
    if serial and serial != EXPECTED_USB_SERIAL:
        blockers.append("SERIAL_MISMATCH")
    if model and EXPECTED_USB_MODEL_SUBSTR.lower() not in model.lower():
        blockers.append("MODEL_MISMATCH")
    if size:
        m = re.match(r"^(\d+(?:\.\d+)?)\s*G", str(size).strip(), re.I)
        if m and float(m.group(1)) < MIN_USB_SIZE_GIB:
            blockers.append("DEVICE_TOO_SMALL")
    if mountpoints:
        blockers.append("PARTITION_MOUNTED")

    blockers = sorted(set(blockers))
    return {
        "target_device": dev,
        "target_partition": part,
        "blocked": bool(blockers),
        "blockers": blockers,
        "write_allowed": not blockers,
        "partition_rewritten": False,
        "filesystem_reformatted": False,
        "secrets_exposed": False,
    }


def build_payload_update_plan(
    *,
    target_device: str,
    new_squashfs: Path,
    confirm_phrase: str | None,
    confirm_update: bool,
    execute_update: bool,
    safety: Mapping[str, Any],
    optional_paths: Sequence[str] | None = None,
) -> dict[str, Any]:
    part = partition_path_for_target(target_device.strip(), 1)
    sq = new_squashfs.resolve()
    paths = ["live/filesystem.squashfs"]
    for rel in optional_paths or ():
        if rel in ALLOWED_PAYLOAD_REL_PATHS and rel not in paths:
            paths.append(rel)

    blockers = list(safety.get("blockers") or [])
    if confirm_update and confirm_phrase != CONFIRM_PHRASE_PAYLOAD_UPDATE:
        blockers.append("CONFIRM_PHRASE_MISMATCH")
    if execute_update and not confirm_update:
        blockers.append("OPERATOR_CONFIRM_UPDATE_MISSING")
    if not sq.is_file():
        blockers.append("NEW_SQUASHFS_MISSING")

    blockers = sorted(set(blockers))
    return {
        "schema_version": 1,
        "operation": "fat32_esp_live_payload_update",
        "mode": "dry_run" if not execute_update else "execute",
        "target_device": target_device.strip(),
        "target_partition": part,
        "new_squashfs": str(sq),
        "new_squashfs_sha256": sha256_file(sq) if sq.is_file() else None,
        "payload_paths": paths,
        "atomic_squashfs": ".sqtmp/filesystem.squashfs.new → live/filesystem.squashfs",
        "safety": safety,
        "blocked": bool(blockers),
        "blockers": blockers,
        "payload_update_executed": False,
        "partition_rewritten": False,
        "filesystem_reformatted": False,
        "secrets_exposed": False,
    }


def build_updated_stick_evidence(
    *,
    medium_evidence: Mapping[str, Any],
    new_squashfs: Path,
    project_version: str,
) -> dict[str, Any]:
    """Refresh setuphelfer/rescue/evidence.json after squashfs swap."""
    out = dict(medium_evidence)
    files = list(out.get("files") or [])
    new_sha = sha256_file(new_squashfs)
    new_size = new_squashfs.stat().st_size
    replaced = False
    for entry in files:
        if entry.get("staging_path") == "live/filesystem.squashfs":
            entry["sha256"] = new_sha
            entry["size_bytes"] = new_size
            replaced = True
    if not replaced:
        files.append(
            {
                "iso_path": "/live/filesystem.squashfs",
                "staging_path": "live/filesystem.squashfs",
                "size_bytes": new_size,
                "sha256": new_sha,
            }
        )
    out["files"] = files
    out["payload_updated_at"] = _now_iso()
    out["writer_mode"] = "fat32_esp"
    out["project_version"] = project_version
    return out


def build_payload_update_result(
    *,
    target_device: str,
    old_squashfs_sha256: str | None,
    new_squashfs_sha256: str | None,
    started_at: str,
    completed_at: str | None,
    payload_update_executed: bool,
    payload_update_status: str,
    verify_status: str,
    evidence_dir: str | None = None,
    failed_step: str | None = None,
) -> dict[str, Any]:
    part = partition_path_for_target(target_device.strip(), 1)
    return {
        "schema_version": 1,
        "operation": "fat32_esp_live_payload_update",
        "target_device": target_device.strip(),
        "target_partition": part,
        "write_mode": "payload_only",
        "partition_rewritten": False,
        "filesystem_reformatted": False,
        "old_squashfs_sha256": old_squashfs_sha256,
        "new_squashfs_sha256": new_squashfs_sha256,
        "started_at": started_at,
        "completed_at": completed_at,
        "payload_update_executed": payload_update_executed,
        "payload_update_status": payload_update_status,
        "failed_step": failed_step,
        "verify_status": verify_status,
        "rs001_status": "yellow",
        "rs001_reason": "payload updated; hardware retest pending",
        "evidence_dir": evidence_dir,
        "secrets_exposed": False,
    }


def squashfs_contains_live_medium_fix(squashfs_path: Path) -> dict[str, Any]:
    """Check squashfs listing for live-medium-check fix (read-only)."""
    import subprocess

    proc = subprocess.run(
        ["unsquashfs", "-ll", str(squashfs_path)],
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )
    blob = (proc.stdout or "") + (proc.stderr or "")
    has_py = "setuphelfer-rescue-live-medium-check.py" in blob
    has_delegate = "setuphelfer-rescue-live-medium-check.py" in blob or (
        "exec python3" in blob and "media-check" in blob
    )
    return {
        "squashfs_path": str(squashfs_path),
        "contains_setuphelfer_rescue_live_medium_check_py": has_py,
        "contains_live_medium_fix": has_py,
        "unsquashfs_ok": proc.returncode == 0,
        "secrets_exposed": False,
    }
