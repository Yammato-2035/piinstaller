"""
Read-only storage discovery for rescue stick UI (MSI Windows / external HDD).
"""

from __future__ import annotations

import json
import subprocess
from typing import Any

from core.rescue_backup_target_policy import (
    BACKUP_LABELS,
    RESCUE_STICK_LABELS,
    classify_storage_role,
)

SOURCE_ROLES = frozenset(
    {
        "windows_system_disk",
        "linux_system_disk",
    }
)
SOURCE_FSTYPES = frozenset({"ntfs", "ext4", "btrfs", "xfs", "vfat", "exfat"})
TARGET_ROLES = frozenset({"external_backup_hdd", "backup_target"})
BLOCKED_DISK_ROLES = frozenset(
    {
        "rescue_usb_stick",
        "rescue_usb_target_candidate",
        "blocked",
        "linux_system_disk",
    }
)


def classify_storage_role_extended(device: dict[str, Any]) -> str:
    path = str(device.get("path") or device.get("device") or "")
    fstype = str(device.get("fstype") or "").lower()
    dev_type = str(device.get("type") or "").lower()
    if dev_type == "disk" and not fstype:
        role = classify_storage_role(device)
        if role != "unknown":
            return role
        if path.startswith("/dev/nvme") and "nvme1" not in path:
            return "windows_system_disk"
    role = classify_storage_role(device)
    if role != "unknown":
        return role
    if fstype == "ntfs" and dev_type in ("disk", "part"):
        return "windows_system_disk"
    if fstype in ("ext4", "btrfs", "xfs") and dev_type == "part":
        parent = str(device.get("parent_path") or "")
        if parent.startswith("/dev/nvme1"):
            return "linux_system_disk"
    return role


def _lsblk_tree() -> list[dict[str, Any]]:
    try:
        out = subprocess.check_output(
            ["lsblk", "-J", "-b", "-o", "NAME,PATH,TYPE,SIZE,FSTYPE,LABEL,MOUNTPOINTS,TRAN,RM,HOTPLUG,MODEL"],
            text=True,
        )
        data = json.loads(out)
        return data.get("blockdevices") or []
    except (subprocess.CalledProcessError, json.JSONDecodeError, FileNotFoundError):
        return []


def _blkid_type_map() -> dict[str, str]:
    mapping: dict[str, str] = {}
    try:
        out = subprocess.check_output(["blkid", "-o", "export"], text=True, stderr=subprocess.DEVNULL)
    except (subprocess.CalledProcessError, FileNotFoundError):
        return mapping
    current: str | None = None
    for line in out.splitlines():
        if line.startswith("DEVNAME="):
            current = line.split("=", 1)[1].strip()
        elif line.startswith("TYPE=") and current:
            mapping[current] = line.split("=", 1)[1].strip().lower()
            current = None
    return mapping


def _flatten(nodes: list[dict[str, Any]], parent: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    flat: list[dict[str, Any]] = []
    blkid = _blkid_type_map()
    for node in nodes:
        entry = dict(node)
        if parent:
            entry["parent_path"] = parent.get("path")
        mps = entry.get("mountpoints") or []
        entry["mountpoint"] = mps[0] if mps else None
        path = str(entry.get("path") or "")
        if not entry.get("fstype") and path in blkid:
            entry["fstype"] = blkid[path]
        if parent and not entry.get("tran"):
            parent_tran = str(parent.get("tran") or "")
            if parent_tran:
                entry["tran"] = parent_tran
        flat.append(entry)
        children = entry.get("children") or []
        if children:
            flat.extend(_flatten(children, entry))
    return flat


def _parse_size_bytes(raw: Any) -> int | None:
    if raw is None:
        return None
    if isinstance(raw, int):
        return raw
    text = str(raw).strip()
    if text.isdigit():
        return int(text)
    return None


def _rescue_stick_disk_paths(devices: list[dict[str, Any]]) -> set[str]:
    paths: set[str] = set()
    for dev in devices:
        label = str(dev.get("label") or "").upper()
        if any(x in label for x in ("SETUPHELFER", "SETUP_LOGS")):
            parent = str(dev.get("parent_path") or "").strip()
            if parent:
                paths.add(parent)
    return paths


def _is_rescue_stick_item(dev: dict[str, Any], role: str, rescue_disks: set[str]) -> bool:
    path = str(dev.get("path") or "")
    if path in rescue_disks:
        return True
    label = str(dev.get("label") or "").upper()
    if role in ("rescue_usb_stick", "rescue_usb_target_candidate"):
        return True
    return any(x in label for x in ("SETUPHELFER", "SETUP_LOGS"))


def _is_source_candidate(dev: dict[str, Any], role: str, rescue_disks: set[str]) -> bool:
    if _is_rescue_stick_item(dev, role, rescue_disks):
        return False
    dev_type = str(dev.get("type") or "").lower()
    fstype = str(dev.get("fstype") or "").lower()
    path = str(dev.get("path") or "")
    if role in SOURCE_ROLES:
        return True
    if fstype in SOURCE_FSTYPES and dev_type in ("disk", "part"):
        return True
    if dev_type == "disk" and path.startswith("/dev/nvme"):
        return role not in ("rescue_usb_stick", "blocked")
    if dev_type == "disk" and str(dev.get("tran") or "").lower() in ("usb", "mmc"):
        return True
    return False


def _is_target_candidate(dev: dict[str, Any], role: str, rescue_disks: set[str]) -> bool:
    dev_type = str(dev.get("type") or "").lower()
    if dev_type != "disk":
        return False
    path = str(dev.get("path") or "")
    if _is_rescue_stick_item(dev, role, rescue_disks):
        return False
    if path in ("/dev/nvme0n1", "/dev/nvme1n1", "/dev/sda"):
        return False
    if path.startswith("/dev/nvme0n1") or path.startswith("/dev/nvme1n1"):
        return False
    if role in TARGET_ROLES:
        return True
    label = str(dev.get("label") or "").upper()
    tran = str(dev.get("tran") or "").lower()
    rm = bool(dev.get("rm"))
    if label in {x.upper() for x in BACKUP_LABELS}:
        return True
    if tran in ("usb", "mmc", "sata") and label not in {x.upper() for x in RESCUE_STICK_LABELS}:
        if "SETUPHELFER" not in label and "SETUP_LOGS" not in label:
            return True
    if rm and tran in ("usb", "mmc", "sata"):
        return label not in {x.upper() for x in RESCUE_STICK_LABELS}
    # External sd* disks (USB/SATA bridges often report as sd without tran=usb)
    if path.startswith("/dev/sd") and path not in ("/dev/sda",):
        return True
    return False


def _target_role_for_item(role: str) -> str:
    if role in TARGET_ROLES or role == "external_backup_hdd":
        return "backup_target"
    return role


def _partition_kind(part: dict[str, Any]) -> str:
    fstype = str(part.get("fstype") or "").lower()
    label = str(part.get("label") or "").lower()
    if fstype == "vfat" or "efi" in label:
        return "efi"
    if fstype == "ntfs":
        if "recovery" in label or "winre" in label:
            return "recovery"
        return "windows"
    if fstype in ("ext4", "btrfs", "xfs"):
        return "linux"
    return "other"


def _windows_auto_select_score(tags: set[str]) -> int:
    score = 0
    if "efi" in tags:
        score += 30
    if "windows" in tags:
        score += 40
    if "recovery" in tags:
        score += 30
    return score


def build_system_source_candidates(classified: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Group EFI + Windows + Recovery partitions into one Windows-System backup candidate."""
    disks = [d for d in classified if str(d.get("type") or "") == "disk"]
    groups: list[dict[str, Any]] = []
    for disk in disks:
        role = str(disk.get("role") or "")
        if role not in ("windows_system_disk", "mixed_system_disk"):
            continue
        disk_path = str(disk.get("path") or "")
        if not disk_path:
            continue
        parts = [
            p
            for p in classified
            if str(p.get("parent_path") or "") == disk_path and str(p.get("type") or "") == "part"
        ]
        tags: set[str] = set()
        part_rows: list[dict[str, Any]] = []
        for part in parts:
            kind = _partition_kind(part)
            if kind in ("efi", "windows", "recovery"):
                tags.add(kind)
            part_rows.append(
                {
                    "path": part.get("path"),
                    "fstype": part.get("fstype"),
                    "label": part.get("label"),
                    "size_bytes": part.get("size_bytes"),
                    "kind": kind,
                }
            )
        if role == "windows_system_disk" or tags.intersection({"efi", "windows"}):
            score = _windows_auto_select_score(tags)
            groups.append(
                {
                    "path": disk_path,
                    "type": "system_group",
                    "group_kind": "windows_system",
                    "label": "Windows-System",
                    "role": "windows_system_disk",
                    "size": disk.get("size"),
                    "size_bytes": disk.get("size_bytes"),
                    "fstype": "multi",
                    "tran": disk.get("tran"),
                    "model": disk.get("model"),
                    "partitions": part_rows,
                    "tags": sorted(tags),
                    "auto_select_score": score,
                    "recommended": score >= 70,
                    "backup_capable": bool(tags.intersection({"windows", "efi"})),
                }
            )
    groups.sort(key=lambda g: (-int(g.get("auto_select_score") or 0), str(g.get("path") or "")))
    if groups:
        groups[0]["recommended"] = True
    return groups


def _finalize_source_candidates(
    classified: list[dict[str, Any]],
    raw_sources: list[dict[str, Any]],
    system_groups: list[dict[str, Any]],
    rescue_disks: set[str],
) -> list[dict[str, Any]]:
    if not system_groups:
        return raw_sources
    result = list(system_groups)
    absorbed_disks = {str(g.get("path") or "") for g in system_groups}
    absorbed_parts: set[str] = set()
    for group in system_groups:
        for part in group.get("partitions") or []:
            path = str(part.get("path") or "")
            if path:
                absorbed_parts.add(path)
    for item in raw_sources:
        path = str(item.get("path") or "")
        parent = str(item.get("parent_path") or "")
        role = str(item.get("role") or "")
        if path in absorbed_parts or parent in absorbed_disks:
            continue
        if _is_rescue_stick_item(item, role, rescue_disks):
            continue
        if str(item.get("type") or "") == "part" and role == "windows_system_disk":
            continue
        result.append(item)
    return result


def pick_auto_backup_source(discovery: dict[str, Any]) -> dict[str, Any] | None:
    """Return best default backup source from discovery payload."""
    systems = discovery.get("system_source_candidates") or []
    if isinstance(systems, list) and systems:
        if len(systems) == 1:
            return systems[0] if isinstance(systems[0], dict) else None
        ranked = sorted(
            (s for s in systems if isinstance(s, dict)),
            key=lambda s: (-int(s.get("auto_select_score") or 0), str(s.get("path") or "")),
        )
        return ranked[0] if ranked else None
    sources = discovery.get("source_candidates") or []
    for item in sources:
        if not isinstance(item, dict):
            continue
        if str(item.get("role") or "") == "windows_system_disk" and str(item.get("type") or "") in (
            "system_group",
            "disk",
        ):
            return item
    for item in sources:
        if isinstance(item, dict) and str(item.get("role") or "") == "windows_system_disk":
            return item
    return None


def discover_rescue_storage() -> dict[str, Any]:
    devices = _flatten(_lsblk_tree())
    rescue_disks = _rescue_stick_disk_paths(devices)
    classified: list[dict[str, Any]] = []
    sources: list[dict[str, Any]] = []
    targets: list[dict[str, Any]] = []
    blocked: list[str] = []

    seen_source_paths: set[str] = set()
    seen_target_paths: set[str] = set()

    for dev in devices:
        path = str(dev.get("path") or "")
        if not path:
            continue
        role = classify_storage_role_extended(
            {
                "path": path,
                "type": dev.get("type"),
                "fstype": dev.get("fstype"),
                "label": dev.get("label"),
                "tran": dev.get("tran"),
                "mountpoint": dev.get("mountpoint"),
                "mountpoints": dev.get("mountpoints"),
                "parent_path": dev.get("parent_path"),
            }
        )
        size_bytes = _parse_size_bytes(dev.get("size"))
        item = {
            "path": path,
            "type": dev.get("type"),
            "size": dev.get("size"),
            "size_bytes": size_bytes,
            "fstype": dev.get("fstype"),
            "label": dev.get("label"),
            "mountpoint": dev.get("mountpoint"),
            "parent_path": dev.get("parent_path"),
            "tran": dev.get("tran"),
            "rm": dev.get("rm"),
            "model": dev.get("model"),
            "role": role,
        }
        classified.append(item)

        if _is_source_candidate(dev, role, rescue_disks) and path not in seen_source_paths:
            sources.append(item)
            seen_source_paths.add(path)

        if _is_target_candidate(dev, role, rescue_disks) and path not in seen_target_paths:
            target_item = dict(item)
            target_item["role"] = _target_role_for_item(role)
            targets.append(target_item)
            seen_target_paths.add(path)
        elif role in BLOCKED_DISK_ROLES and str(dev.get("type") or "") == "disk":
            blocked.append(path)

    if not sources:
        for item in classified:
            fstype = str(item.get("fstype") or "").lower()
            if fstype == "ntfs" and item.get("type") in ("disk", "part"):
                path = str(item.get("path") or "")
                if path and path not in seen_source_paths:
                    sources.append(item)
                    seen_source_paths.add(path)

    if not targets:
        for item in classified:
            if str(item.get("type") or "") != "disk":
                continue
            path = str(item.get("path") or "")
            role = str(item.get("role") or "")
            if not path or path in seen_target_paths:
                continue
            if _is_target_candidate(
                {"path": path, "type": "disk", "label": item.get("label"), "tran": item.get("tran"), "rm": item.get("rm")},
                role,
                rescue_disks,
            ):
                target_item = dict(item)
                target_item["role"] = _target_role_for_item(role)
                targets.append(target_item)
                seen_target_paths.add(path)

    system_groups = build_system_source_candidates(classified)
    sources = _finalize_source_candidates(classified, sources, system_groups, rescue_disks)

    return {
        "schema_version": 2,
        "read_only": True,
        "devices": classified,
        "source_candidates": sources,
        "system_source_candidates": system_groups,
        "target_candidates": targets,
        "blocked_devices": sorted(set(blocked)),
        "cloud_target_available": True,
        "cloud_target_mode": "local_unlock_test",
    }
