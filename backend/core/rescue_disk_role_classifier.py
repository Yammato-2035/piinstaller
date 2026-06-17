"""
Canonical disk role classification for rescue stick (RS-P1).
"""

from __future__ import annotations

from typing import Any

from core.rescue_backup_target_policy import RESCUE_STICK_LABELS, classify_storage_role

CONTRACT_VERSION = 1

ROLE_RESCUE_STICK = "rescue_stick"
ROLE_SETUP_LOGS = "setup_logs_partition"
ROLE_WINDOWS_SYSTEM = "windows_system_disk"
ROLE_LINUX_SYSTEM = "linux_system_disk"
ROLE_EXTERNAL_BACKUP = "external_backup_target"
ROLE_CLOUD_PLAN_ONLY = "cloud_target_plan_only"
ROLE_UNKNOWN = "unknown"
ROLE_BLOCKED = "blocked"

TARGET_BLOCKED_ROLES = frozenset(
    {ROLE_RESCUE_STICK, ROLE_SETUP_LOGS, ROLE_LINUX_SYSTEM, ROLE_BLOCKED, ROLE_CLOUD_PLAN_ONLY}
)


def _map_legacy_role(legacy: str, device: dict[str, Any]) -> str:
    label = str(device.get("label") or "").upper()
    if label == "SETUP_LOGS":
        return ROLE_SETUP_LOGS
    mapping = {
        "rescue_usb_stick": ROLE_RESCUE_STICK,
        "rescue_usb_target_candidate": ROLE_RESCUE_STICK,
        "windows_system_disk": ROLE_WINDOWS_SYSTEM,
        "linux_system_disk": ROLE_LINUX_SYSTEM,
        "external_backup_hdd": ROLE_EXTERNAL_BACKUP,
        "blocked": ROLE_BLOCKED,
    }
    return mapping.get(legacy, ROLE_UNKNOWN)


def classify_disk_role(device: dict[str, Any]) -> str:
    legacy = classify_storage_role(device)
    return _map_legacy_role(legacy, device)


def classify_disk_roles(devices: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for dev in devices:
        role = classify_disk_role(dev)
        item = dict(dev)
        item["role"] = role
        item["target_allowed"] = role == ROLE_EXTERNAL_BACKUP
        item["source_candidate"] = role in (ROLE_WINDOWS_SYSTEM, ROLE_LINUX_SYSTEM)
        out.append(item)
    return out


def validate_source_target_pair(source: dict[str, Any], target: dict[str, Any]) -> dict[str, Any]:
    src_role = classify_disk_role(source)
    tgt_role = classify_disk_role(target)
    src_path = str(source.get("path") or "")
    tgt_path = str(target.get("path") or "")
    errors: list[dict[str, str]] = []
    if src_path and tgt_path and src_path == tgt_path:
        errors.append({"code": "source_equals_target", "message": "Quelle und Ziel dürfen nicht identisch sein."})
    if tgt_role in TARGET_BLOCKED_ROLES:
        errors.append({"code": f"target_role_{tgt_role}", "message": f"Zielrolle {tgt_role} nicht erlaubt."})
    if src_role == ROLE_UNKNOWN:
        errors.append({"code": "source_unknown", "message": "Quelle unbekannt — review_required."})
    return {
        "source_role": src_role,
        "target_role": tgt_role,
        "ok": not errors,
        "errors": errors,
        "review_required": src_role == ROLE_UNKNOWN or tgt_role == ROLE_UNKNOWN,
    }
