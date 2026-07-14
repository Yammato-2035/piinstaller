"""Storage safety classification for physical E2E backup and restore."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from core.rescue_disk_role_classifier import (
    ROLE_EXTERNAL_BACKUP,
    ROLE_RESCUE_STICK,
    ROLE_SETUP_LOGS,
    ROLE_WINDOWS_SYSTEM,
    ROLE_LINUX_SYSTEM,
    classify_disk_role,
    validate_source_target_pair,
)

BLOCKED_RESTORE_PATH_PREFIXES = (
    "/",
    "/boot",
    "/boot/efi",
    "/efi",
    "/windows",
    "/mnt/setuphelfer",
    "/run/live",
)

BLOCKED_RESTORE_LABELS = frozenset({"SETUPHELFER", "SETUP_LOGS", "SETUPHELFER_LOGS"})


def _path_blocked_for_restore(path: str) -> str | None:
    normalized = path.rstrip("/") or "/"
    if normalized == "/":
        return "root_partition"
    for prefix in BLOCKED_RESTORE_PATH_PREFIXES:
        if prefix != "/" and (normalized == prefix or normalized.startswith(prefix + "/")):
            return f"blocked_prefix:{prefix}"
    return None


def classify_storage_entry(device: dict[str, Any]) -> dict[str, Any]:
    role = classify_disk_role(device)
    path = str(device.get("path") or device.get("mountpoint") or "")
    label = str(device.get("label") or "").upper()
    return {
        "source_role": role,
        "backup_target_role": role,
        "restore_target_role": role,
        "is_internal_system_disk": role in (ROLE_WINDOWS_SYSTEM, ROLE_LINUX_SYSTEM),
        "is_boot_partition": path in {"/boot", "/boot/efi"} or "boot" in path.lower(),
        "is_efi_partition": "efi" in path.lower(),
        "is_setuphelfer_partition": label == "SETUPHELFER",
        "is_setup_logs_partition": label in {"SETUP_LOGS", "SETUPHELFER_LOGS"},
        "is_mounted": bool(device.get("mounted") or path.startswith("/")),
        "filesystem": str(device.get("filesystem") or device.get("fstype") or ""),
        "size_bytes": int(device.get("size_bytes") or device.get("size") or 0),
        "free_bytes": int(device.get("free_bytes") or device.get("avail") or 0),
        "path": path,
        "label": label,
        "role": role,
    }


def directory_is_empty(path: Path) -> bool:
    if not path.exists():
        return True
    if not path.is_dir():
        return False
    try:
        next(path.iterdir())
        return False
    except StopIteration:
        return True


def validate_restore_target(
    restore_path: Path,
    *,
    source_path: Path,
    backup_path: Path,
    min_free_bytes: int = 512 * 1024 * 1024,
    device: dict[str, Any] | None = None,
) -> dict[str, Any]:
    errors: list[dict[str, str]] = []
    restore_str = str(restore_path)
    source_str = str(source_path)

    if restore_str == source_str:
        errors.append({"code": "source_equals_restore", "message": "Restoreziel darf nicht die Quelle sein."})
    if str(backup_path) == restore_str:
        errors.append({"code": "backup_equals_restore", "message": "Restoreziel darf nicht das Backupziel sein."})

    blocked = _path_blocked_for_restore(restore_str)
    if blocked:
        errors.append({"code": "unsafe_restore_target", "message": f"STOP — unsafe_restore_target ({blocked})"})

    if device:
        classification = classify_storage_entry(device)
        if classification["is_setuphelfer_partition"] or classification["is_setup_logs_partition"]:
            errors.append({"code": "setup_partition", "message": "SETUPHELFER/SETUP_LOGS nicht erlaubt."})
        if classification["is_internal_system_disk"]:
            errors.append({"code": "system_disk", "message": "Systempartition nicht erlaubt."})
        if classification["restore_target_role"] not in (ROLE_EXTERNAL_BACKUP,):
            errors.append(
                {
                    "code": "unknown_or_blocked_role",
                    "message": f"Restore-Rolle {classification['restore_target_role']} nicht erlaubt.",
                }
            )
        if classification["free_bytes"] and classification["free_bytes"] < min_free_bytes:
            errors.append({"code": "target_too_small", "message": "Ziel hat zu wenig freien Speicher."})

    if restore_path.exists() and not directory_is_empty(restore_path):
        errors.append({"code": "target_not_empty", "message": "Restoreziel ist nicht leer."})

    return {"ok": not errors, "errors": errors, "restore_target_empty": directory_is_empty(restore_path)}


def validate_backup_target_pair(source_device: dict[str, Any], target_device: dict[str, Any]) -> dict[str, Any]:
    pair = validate_source_target_pair(source_device, target_device)
    if pair.get("target_role") != ROLE_EXTERNAL_BACKUP:
        pair.setdefault("errors", []).append(
            {"code": "backup_target_not_external", "message": "Backupziel muss externes Testmedium sein."}
        )
        pair["ok"] = False
    return pair


def validate_paths_for_e2e(
    *,
    source_dir: Path,
    backup_dir: Path,
    restore_dir: Path,
    source_device: dict[str, Any] | None = None,
    backup_device: dict[str, Any] | None = None,
    restore_device: dict[str, Any] | None = None,
) -> dict[str, Any]:
    errors: list[dict[str, str]] = []
    if not source_dir.is_dir():
        errors.append({"code": "source_missing", "message": "Testdatenquelle fehlt."})
    if source_dir.resolve() == restore_dir.resolve():
        errors.append({"code": "source_equals_restore", "message": "Quelle und Restoreziel identisch."})

    restore_check = validate_restore_target(
        restore_dir,
        source_path=source_dir,
        backup_path=backup_dir,
        device=restore_device,
    )
    errors.extend(restore_check.get("errors") or [])

    if backup_device and source_device:
        backup_pair = validate_backup_target_pair(source_device, backup_device)
        if not backup_pair.get("ok"):
            errors.extend(backup_pair.get("errors") or [])

    return {
        "ok": not errors,
        "errors": errors,
        "source_role": classify_storage_entry(source_device or {}).get("role") if source_device else "test_data",
        "backup_target_role": classify_storage_entry(backup_device or {}).get("role") if backup_device else "external",
        "restore_target_role": classify_storage_entry(restore_device or {}).get("role") if restore_device else "external",
    }
