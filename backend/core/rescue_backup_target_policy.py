"""
Rescue backup target policy — external HDD vs rescue stick vs internal disks.
"""

from __future__ import annotations

from typing import Any

from core.msi_windows_image_backup import (
    F2_ALLOWED_SOURCE,
    F2_BLOCKED_TARGET_DEVICES,
    compute_required_bytes,
    is_blockdevice_output_path,
    run_f2_preflight,
    validate_target_mount_path,
)

POLICY_VERSION = 1

RESCUE_STICK_LABELS = frozenset({"SETUPHELFER", "SETUP_LOGS", "SETUPHELFER-EVIDENCE"})
BACKUP_LABELS = frozenset({"Backup", "BACKUP"})


def classify_storage_role(device: dict[str, Any]) -> str:
    path = str(device.get("path") or device.get("device") or "")
    label = str(device.get("label") or "").upper()
    tran = str(device.get("tran") or "").lower()
    mount = str(device.get("mountpoint") or device.get("mountpoints") or "")
    if path in ("/dev/nvme0n1", "/dev/nvme0n1p1"):
        return "windows_system_disk"
    if path.startswith("/dev/nvme1n1"):
        return "linux_system_disk"
    if label in {x.upper() for x in RESCUE_STICK_LABELS} or "SETUPHELFER" in label:
        return "rescue_usb_stick"
    if label in {x.upper() for x in BACKUP_LABELS}:
        return "external_backup_hdd"
    if tran == "usb" and path.startswith("/dev/sd"):
        if any(x in mount for x in ("/media/", "/run/media/")):
            return "external_backup_hdd"
        return "rescue_usb_target_candidate"
    if path in F2_BLOCKED_TARGET_DEVICES:
        return "blocked"
    return "unknown"


def rescue_backup_preflight(
    *,
    source_device: str,
    source_size_bytes: int,
    target_mount: str,
    target_device: str,
    free_bytes: int,
    fstype: str,
    operator_confirmation_1: str | None = None,
    operator_confirmation_2: str | None = None,
) -> dict[str, Any]:
    pf = run_f2_preflight(
        source_device=source_device,
        source_size_bytes=source_size_bytes,
        target_mount=target_mount,
        target_device=target_device,
        free_bytes=free_bytes,
        fstype=fstype,
        operator_confirmation_1=operator_confirmation_1,
        operator_confirmation_2=operator_confirmation_2,
    )
    mount_ok, mount_errors = validate_target_mount_path(target_mount)
    return {
        "policy_version": POLICY_VERSION,
        "allowed_source": F2_ALLOWED_SOURCE,
        "blocked_targets": sorted(F2_BLOCKED_TARGET_DEVICES),
        "required_bytes": compute_required_bytes(source_size_bytes),
        "target_is_blockdevice": is_blockdevice_output_path(target_mount),
        "mount_path_valid": mount_ok,
        "mount_errors": mount_errors,
        "execute_allowed_on_development_laptop": False,
        "execute_allowed_only_when_booted_from_rescue": True,
        "requires_operator_confirmation": True,
        "requires_external_target": True,
        "preflight": pf.to_dict(),
    }


def rescue_capabilities_matrix() -> dict[str, Any]:
    return {
        "policy_version": POLICY_VERSION,
        "backup_execute": {
            "development_laptop": False,
            "rescue_stick_boot": True,
            "requires_operator_confirmation": True,
        },
        "restore_execute": {
            "development_laptop": False,
            "rescue_stick_boot": False,
            "deferred_until": "RS-F2B after verify",
        },
        "wipe": False,
        "linux_install": False,
        "ntfs_mount_write": False,
        "bitlocker_unlock": False,
        "cloud_dependency": False,
    }
