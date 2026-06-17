"""
Rescue OS/filesystem detection — read-only heuristics (RS-P1).
"""

from __future__ import annotations

from typing import Any

CONTRACT_VERSION = 1

LINUX_FSTYPES = frozenset({"ext4", "ext3", "ext2", "btrfs", "xfs"})
WINDOWS_FSTYPES = frozenset({"ntfs", "exfat", "vfat"})


def classify_detected_os(device: dict[str, Any]) -> dict[str, Any]:
    fstype = str(device.get("fstype") or "").lower()
    path = str(device.get("path") or "")
    label = str(device.get("label") or "").upper()
    parttypename = str(device.get("parttypename") or device.get("partlabel") or "").lower()

    os_family = "unknown"
    backup_modes: list[str] = []
    review_required = False

    if fstype in WINDOWS_FSTYPES or "microsoft" in parttypename or "basic data" in parttypename:
        os_family = "windows"
        backup_modes = ["raw_image"]
        if fstype == "ntfs":
            backup_modes.append("file_backup_later")
    elif fstype in LINUX_FSTYPES:
        os_family = "linux"
        backup_modes = ["linux_full_root_tar", "raw_image_later"]
    elif device.get("type") == "disk" and not fstype:
        if path.startswith("/dev/nvme0"):
            os_family = "windows"
            backup_modes = ["raw_image"]
            review_required = True
        elif path.startswith("/dev/nvme1"):
            os_family = "linux"
            backup_modes = ["linux_full_root_tar"]
            review_required = True

    encryption = detect_encryption_indicators(device)
    if encryption.get("bitlocker_status") in ("detected", "detected_key_missing"):
        review_required = True
    if encryption.get("luks_detected"):
        review_required = True

    return {
        "contract_version": CONTRACT_VERSION,
        "device": path,
        "os_family": os_family,
        "fstype": fstype or None,
        "label": label or None,
        "backup_modes": backup_modes,
        "encryption": encryption,
        "review_required": review_required,
    }


def detect_encryption_indicators(device: dict[str, Any]) -> dict[str, Any]:
    fstype = str(device.get("fstype") or "").lower()
    flags = str(device.get("flags") or device.get("partflags") or "").lower()
    bitlocker = "not_detected"
    if fstype == "bitlocker" or "bitlocker" in flags or device.get("bitlocker") is True:
        bitlocker = "detected_key_missing" if not device.get("bitlocker_key_available") else "detected_key_available"
    luks = fstype == "crypto_luks" or "luks" in flags or bool(device.get("luks"))
    return {
        "bitlocker_status": bitlocker,
        "luks_detected": luks,
        "file_backup_allowed": bitlocker == "not_detected" and not luks,
        "raw_image_allowed": True,
    }
