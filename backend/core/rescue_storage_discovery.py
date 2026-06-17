"""
Read-only storage discovery for rescue stick UI (MSI Windows / external HDD).
"""

from __future__ import annotations

import json
import subprocess
from typing import Any

from core.rescue_backup_target_policy import classify_storage_role


def classify_storage_role_extended(device: dict[str, Any]) -> str:
    path = str(device.get("path") or device.get("device") or "")
    fstype = str(device.get("fstype") or "").lower()
    if device.get("type") == "disk" and fstype == "":
        # Heuristic: NVMe with NTFS children often Windows system disk
        role = classify_storage_role(device)
        if role != "unknown":
            return role
        if path.startswith("/dev/nvme") and "nvme1" not in path:
            return "windows_system_disk"
    return classify_storage_role(device)


def _lsblk_tree() -> list[dict[str, Any]]:
    try:
        out = subprocess.check_output(
            ["lsblk", "-J", "-o", "NAME,PATH,TYPE,SIZE,FSTYPE,LABEL,MOUNTPOINTS,TRAN,RM,HOTPLUG,MODEL"],
            text=True,
        )
        data = json.loads(out)
        return data.get("blockdevices") or []
    except (subprocess.CalledProcessError, json.JSONDecodeError, FileNotFoundError):
        return []


def _flatten(nodes: list[dict[str, Any]], parent: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    flat: list[dict[str, Any]] = []
    for node in nodes:
        entry = dict(node)
        if parent:
            entry["parent_path"] = parent.get("path")
        mps = entry.get("mountpoints") or []
        entry["mountpoint"] = mps[0] if mps else None
        flat.append(entry)
        children = entry.get("children") or []
        if children:
            flat.extend(_flatten(children, entry))
    return flat


def discover_rescue_storage() -> dict[str, Any]:
    devices = _flatten(_lsblk_tree())
    classified: list[dict[str, Any]] = []
    sources: list[dict[str, Any]] = []
    targets: list[dict[str, Any]] = []
    blocked: list[str] = []

    for dev in devices:
        path = str(dev.get("path") or "")
        role = classify_storage_role_extended(
            {
                "path": path,
                "type": dev.get("type"),
                "fstype": dev.get("fstype"),
                "label": dev.get("label"),
                "tran": dev.get("tran"),
                "mountpoint": dev.get("mountpoint"),
                "mountpoints": dev.get("mountpoints"),
            }
        )
        item = {
            "path": path,
            "type": dev.get("type"),
            "size": dev.get("size"),
            "fstype": dev.get("fstype"),
            "label": dev.get("label"),
            "mountpoint": dev.get("mountpoint"),
            "tran": dev.get("tran"),
            "rm": dev.get("rm"),
            "role": role,
        }
        classified.append(item)
        if role in ("windows_system_disk",) or (
            dev.get("fstype") == "ntfs" and dev.get("type") == "disk"
        ):
            sources.append(item)
        elif role == "external_backup_hdd":
            targets.append(item)
        elif role in ("linux_system_disk", "rescue_usb_stick", "rescue_usb_target_candidate", "blocked"):
            if dev.get("type") == "disk":
                blocked.append(path)

    if not sources:
        for item in classified:
            if item.get("fstype") == "ntfs" and item.get("type") in ("disk", "part"):
                sources.append(item)

    return {
        "schema_version": 1,
        "read_only": True,
        "devices": classified,
        "source_candidates": sources,
        "target_candidates": targets,
        "blocked_devices": sorted(set(blocked)),
        "cloud_target_available": True,
        "cloud_target_mode": "local_unlock_test",
    }
