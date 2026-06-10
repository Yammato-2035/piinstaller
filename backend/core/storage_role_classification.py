"""
Wiederverwendbare Storage-Rollen-Klassifikation (Partitionshelfer + Rescue).

Nur lesende Heuristiken auf Scan-/lsblk-Daten — keine Gerätenamen-Shortcuts,
keine Schreibaktionen, keine Fake-Freigaben.
"""

from __future__ import annotations

from typing import Any, Literal

StorageRole = Literal[
    "linux_system_disk",
    "windows_system_disk",
    "mixed_system_disk",
    "backup_target",
    "backup_source",
    "rescue_stick",
    "external_data_disk",
    "internal_data_disk",
    "unknown_disk",
]

Confidence = Literal["high", "medium", "low"]
RiskLevel = Literal["green", "yellow", "red"]

_NTFS_LARGE_BYTES = 50 * 1024 * 1024 * 1024
_EFI_MAX_BYTES = 600 * 1024 * 1024

_ROLE_LABELS: dict[StorageRole, tuple[str, str]] = {
    "linux_system_disk": ("Linux-Systemlaufwerk", "Linux system disk"),
    "windows_system_disk": ("Windows-Systemlaufwerk", "Windows system disk"),
    "mixed_system_disk": ("Gemischtes Systemlaufwerk", "Mixed system disk"),
    "backup_target": ("Backup-Ziel", "Backup target"),
    "backup_source": ("Backup-Quelle", "Backup source"),
    "rescue_stick": ("Rettungsstick", "Rescue stick"),
    "external_data_disk": ("Externer Datenträger", "External data disk"),
    "internal_data_disk": ("Interner Datenträger", "Internal data disk"),
    "unknown_disk": ("Unbekannter Datenträger", "Unknown disk"),
}


def _flatten_partitions(parts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for p in parts:
        if not isinstance(p, dict):
            continue
        out.append(p)
        children = p.get("children") or []
        if isinstance(children, list):
            out.extend(_flatten_partitions(children))
    return out


def _norm_dev(name: str | None) -> str:
    if not name:
        return ""
    n = str(name).strip()
    if not n:
        return ""
    return n if n.startswith("/dev/") else f"/dev/{n}"


def _part_field(part: dict[str, Any], key: str) -> str:
    val = part.get(key)
    return str(val).strip().lower() if val else ""


def _is_efi_partition(part: dict[str, Any]) -> bool:
    pt = _part_field(part, "parttypename")
    fst = _part_field(part, "fstype")
    label = _part_field(part, "label")
    size = int(part.get("size_bytes") or 0)
    if "efi system" in pt or pt.endswith(" efi") or " esp" in pt:
        return True
    if fst in ("vfat", "fat32", "fat") and size <= _EFI_MAX_BYTES:
        return True
    if "efi" in label and fst in ("vfat", "fat32", "fat", ""):
        return True
    mp = _part_field(part, "mountpoint")
    return mp in ("/boot/efi", "/efi")


def _is_ntfs_partition(part: dict[str, Any]) -> bool:
    return _part_field(part, "fstype") == "ntfs"


def _is_linux_fs_partition(part: dict[str, Any]) -> bool:
    return _part_field(part, "fstype") in ("ext4", "ext3", "btrfs", "xfs")


def _is_microsoft_basic_data(part: dict[str, Any]) -> bool:
    pt = _part_field(part, "parttypename")
    return "microsoft basic data" in pt or "basic data" in pt


def _is_windows_recovery(part: dict[str, Any]) -> bool:
    pt = _part_field(part, "parttypename")
    label = _part_field(part, "label")
    return "recovery" in pt or "windows recovery" in pt or "recovery" in label


def _is_bitlocker_hint(part: dict[str, Any]) -> bool:
    pt = _part_field(part, "parttypename")
    fst = _part_field(part, "fstype")
    return "bitlocker" in pt or fst == "bitlocker"


def _is_linux_gpt_type(part: dict[str, Any]) -> bool:
    pt = _part_field(part, "parttypename")
    return "linux filesystem" in pt or "linux root" in pt or "linux swap" in pt


def _infer_transport(disk: dict[str, Any]) -> str:
    tran = str(disk.get("tran") or "").strip().lower()
    if tran:
        return tran
    name = str(disk.get("name") or "").lower()
    if name.startswith("nvme"):
        return "nvme"
    if name.startswith("mmcblk"):
        return "mmc"
    if name.startswith("sd"):
        return "sata"
    return "unknown"


def _is_removable(disk: dict[str, Any]) -> bool:
    rm = disk.get("removable")
    if rm is True or rm == 1 or str(rm).strip() == "1":
        return True
    return _infer_transport(disk) == "usb"


def _disk_haystack(disk: dict[str, Any]) -> str:
    return " ".join(
        str(disk.get(k) or "")
        for k in ("display_name", "model", "vendor", "name", "label")
    ).lower()


def _has_setuphelfer_rescue_markers(disk: dict[str, Any], parts: list[dict[str, Any]]) -> bool:
    hay = _disk_haystack(disk)
    if any(tok in hay for tok in ("setuphelfer", "setuphelfer_rescue", "rettungsstick")):
        return True
    for p in parts:
        label = _part_field(p, "label")
        if "setuphelfer" in label or "rescue" in label:
            return True
    return False


def _has_rescue_structure(parts: list[dict[str, Any]]) -> bool:
    has_efi = any(_is_efi_partition(p) for p in parts)
    has_iso = any(_part_field(p, "fstype") in ("iso9660", "udf") for p in parts)
    has_squash_hint = any("squash" in _part_field(p, "label") for p in parts)
    return has_efi and (has_iso or has_squash_hint)


def _collect_filesystem_hints(parts: list[dict[str, Any]]) -> list[str]:
    hints: list[str] = []
    for p in parts:
        fst = _part_field(p, "fstype")
        if fst and fst not in hints:
            hints.append(fst)
    return hints


def _risk_for_role(role: StorageRole, confidence: Confidence) -> RiskLevel:
    if role in ("linux_system_disk", "windows_system_disk", "mixed_system_disk", "rescue_stick", "backup_source"):
        return "red"
    if role == "backup_target":
        return "green" if confidence == "high" else "yellow"
    if role == "unknown_disk" or confidence == "low":
        return "yellow"
    return "yellow"


def classify_disk_storage_role(
    disk: dict[str, Any],
    *,
    live_root_device: str | None = None,
    backup_source_device: str | None = None,
) -> dict[str, Any]:
    """
    Klassifiziert einen Scan-Datenträger.

    ``disk`` entspricht ``_disk_to_dict`` aus der Partitions-API.
    """
    device = _norm_dev(disk.get("name"))
    parts = _flatten_partitions(disk.get("partitions") or [])
    evidence: list[str] = []

    has_live_root = any(_part_field(p, "mountpoint") == "/" for p in parts)
    has_linux_boot = any(
        _part_field(p, "mountpoint") in ("/boot", "/boot/efi", "/efi")
        or p.get("is_system_critical")
        for p in parts
    )
    has_efi = any(_is_efi_partition(p) for p in parts)
    has_ntfs = any(_is_ntfs_partition(p) for p in parts)
    has_linux_fs = any(_is_linux_fs_partition(p) for p in parts)
    has_ms_data = any(_is_microsoft_basic_data(p) for p in parts)
    has_recovery = any(_is_windows_recovery(p) for p in parts)
    has_bitlocker = any(_is_bitlocker_hint(p) for p in parts)
    has_linux_gpt = any(_is_linux_gpt_type(p) for p in parts)
    large_ntfs = any(
        _is_ntfs_partition(p) and int(p.get("size_bytes") or 0) >= _NTFS_LARGE_BYTES for p in parts
    )

    if has_efi:
        evidence.append("efi_partition_detected")
    if has_ntfs:
        evidence.append("ntfs_partition_detected")
    if has_ms_data:
        evidence.append("microsoft_basic_data_partition_detected")
    if has_recovery:
        evidence.append("windows_recovery_partition_detected")
    if large_ntfs:
        evidence.append("large_ntfs_partition_detected")
    if has_bitlocker:
        evidence.append("bitlocker_partition_detected")
    if has_linux_fs:
        evidence.append("linux_filesystem_detected")
    if has_linux_gpt:
        evidence.append("linux_gpt_type_detected")
    if has_live_root:
        evidence.append("live_root_mount_detected")
    if has_linux_boot:
        evidence.append("linux_boot_partition_detected")

    removable = _is_removable(disk)
    transport = _infer_transport(disk)
    if transport == "usb" or removable:
        evidence.append("removable_or_usb_transport")

    role: StorageRole = "unknown_disk"
    confidence: Confidence = "low"

    backup_src = _norm_dev(backup_source_device)
    if backup_src and device and (device == backup_src or device == backup_src):
        role = "backup_source"
        confidence = "high"
        evidence.append("matches_backup_source_device")
    elif _has_setuphelfer_rescue_markers(disk, parts) or _has_rescue_structure(parts):
        role = "rescue_stick"
        confidence = "high" if _has_setuphelfer_rescue_markers(disk, parts) else "medium"
        evidence.append("rescue_stick_markers_detected")
    elif has_live_root or (has_linux_boot and has_linux_fs and has_efi):
        role = "linux_system_disk"
        confidence = "high" if has_live_root else "medium"
    elif has_efi and has_ntfs and (has_ms_data or has_recovery or large_ntfs or has_bitlocker):
        role = "windows_system_disk"
        confidence = "high" if (has_ms_data or has_recovery) else "medium"
    elif has_efi and has_ntfs:
        role = "windows_system_disk"
        confidence = "medium"
        evidence.append("efi_plus_ntfs_without_strong_windows_markers")
    elif has_efi and has_linux_fs and has_ntfs:
        role = "mixed_system_disk"
        confidence = "medium"
        evidence.append("efi_linux_and_ntfs_coexist")
    elif has_ntfs and not has_efi:
        role = "external_data_disk" if removable else "internal_data_disk"
        confidence = "medium"
        evidence.append("ntfs_without_efi")
    elif has_linux_fs and not has_live_root:
        if has_efi or has_linux_gpt:
            role = "linux_system_disk"
            confidence = "medium"
            evidence.append("offline_linux_system_candidate")
        else:
            role = "external_data_disk" if removable else "internal_data_disk"
            confidence = "low"
    elif removable:
        mounted_external = any(
            (_part_field(p, "mountpoint") or "").startswith(("/media/", "/run/media/", "/mnt/"))
            for p in parts
        )
        if mounted_external and not has_live_root:
            role = "backup_target"
            confidence = "medium"
            evidence.append("external_mount_detected")
        else:
            role = "external_data_disk"
            confidence = "low"
    else:
        role = "internal_data_disk" if parts else "unknown_disk"
        confidence = "low" if role == "unknown_disk" else "medium"

    if live_root_device and device == _norm_dev(live_root_device):
        role = "linux_system_disk"
        confidence = "high"
        evidence.append("matches_live_root_device")

    label_de, label_en = _ROLE_LABELS[role]
    risk = _risk_for_role(role, confidence)
    write_allowed = False

    fs_hints = _collect_filesystem_hints(parts)
    return {
        "device": device,
        "role": role,
        "confidence": confidence,
        "evidence": evidence,
        "write_allowed": write_allowed,
        "risk_level": risk,
        "ui_label_de": label_de,
        "ui_label_en": label_en,
        "transport": transport,
        "removable": removable,
        "filesystem_hints": fs_hints,
        "classification_source": "storage_role_classification_v1",
    }


def classify_scan_disks(
    disks: list[dict[str, Any]],
    *,
    live_root_device: str | None = None,
    backup_source_device: str | None = None,
) -> list[dict[str, Any]]:
    live = live_root_device
    if not live:
        for disk in disks:
            for p in _flatten_partitions(disk.get("partitions") or []):
                if _part_field(p, "mountpoint") == "/":
                    live = _norm_dev(disk.get("name"))
                    break
            if live:
                break
    return [
        classify_disk_storage_role(
            d,
            live_root_device=live,
            backup_source_device=backup_source_device,
        )
        for d in disks
    ]


def _disk_of_dev(device: str) -> str:
    dev = _norm_dev(device)
    if not dev:
        return ""
    base = dev.split("/")[-1]
    if base.startswith("nvme") and "p" in base:
        return _norm_dev(base.rsplit("p", 1)[0])
    disk = base.rstrip("0123456789")
    return _norm_dev(disk) if disk else dev


def find_classification_for_target(
    disks: list[dict[str, Any]],
    target_device: str,
    *,
    backup_source_device: str | None = None,
) -> dict[str, Any] | None:
    target = _norm_dev(target_device)
    if not target:
        return None
    parent = _disk_of_dev(target)
    for disk in disks:
        dev = _norm_dev(disk.get("name"))
        if dev == target or dev == parent:
            role = classify_disk_storage_role(
                disk,
                backup_source_device=backup_source_device,
            )
            return {**role, **classification_to_hardstop_flags(role)}
    return None


def classification_to_hardstop_flags(classification: dict[str, Any]) -> dict[str, Any]:
    """Mappt Klassifikation auf Felder für partition_hardstop / facade."""
    role = str(classification.get("role") or "")
    flags: dict[str, Any] = {
        "storage_role": role,
        "confidence": classification.get("confidence"),
        "evidence": classification.get("evidence") or [],
        "risk_level": classification.get("risk_level"),
        "write_allowed": False,
    }
    if role in ("linux_system_disk", "mixed_system_disk"):
        flags["system_disk"] = True
        flags["is_system_disk"] = True
        flags["target_classification"] = "linux_system_disk"
    if role == "windows_system_disk":
        flags["system_disk"] = True
        flags["is_system_disk"] = True
        flags["is_foreign_os_disk"] = True
        flags["target_classification"] = "windows_system_disk"
    if role == "rescue_stick":
        flags["rescue_stick"] = True
        flags["target_classification"] = "rescue_stick"
    if role == "backup_target":
        flags["backup_target_candidate"] = True
    if role == "backup_source":
        flags["backup_source"] = True
    if role == "unknown_disk" or classification.get("confidence") == "low":
        flags["identity_unknown"] = role == "unknown_disk"
        flags["role_uncertain"] = classification.get("confidence") == "low"
    return flags
