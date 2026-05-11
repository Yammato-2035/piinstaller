from __future__ import annotations

import os
import secrets
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from modules.backup_engine import create_file_backup
from modules.backup_verify import verify_basic
from safety.write_guard import evaluate_write_target

# In-Memory-Planstore (pro Prozess); keine globale Dauerfreigabe
_PLAN_STORE: dict[str, dict[str, Any]] = {}

_ALLOWED_TARGET_REASON = "SAFETY_BACKUP_TARGET_OK"
_WARN_TARGET_REASON = "SAFETY_EMPTY_DISK"
_BLOCKED_TARGET_REASONS = {
    "SAFETY_SYSTEM_DISK",
    "SAFETY_LIVE_SYSTEM",
    "SAFETY_WINDOWS_DETECTED",
    "SAFETY_DUALBOOT",
    "SAFETY_UNKNOWN_DEVICE",
}


def _scan_local_homes() -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    home = Path("/home")
    try:
        if not home.is_dir():
            return out
        entries = sorted(home.iterdir(), key=lambda p: p.name.lower())
    except (PermissionError, OSError):
        return out
    for ent in entries:
        try:
            if not ent.is_dir():
                continue
            readable = os.access(ent, os.R_OK | os.X_OK)
        except (PermissionError, OSError):
            readable = False
        out.append(
            {
                "source_id": f"linux_home:{ent}",
                "path": str(ent),
                "kind": "linux_home",
                "code": "PREFLIGHT_SOURCE_FOUND" if readable else "PREFLIGHT_SOURCE_UNREADABLE",
                "requires_confirmation": False,
                "warnings": [],
            }
        )
    return out


def _source_entry(path: str, kind: str, *, readable: bool, warnings: list[str] | None = None) -> dict[str, Any]:
    return {
        "source_id": f"{kind}:{path}",
        "path": path,
        "kind": kind,
        "code": "PREFLIGHT_SOURCE_FOUND" if readable else "PREFLIGHT_SOURCE_UNREADABLE",
        "requires_confirmation": bool(warnings),
        "warnings": warnings or [],
    }


def list_candidate_sources(inspect_result: dict[str, Any]) -> list[dict[str, Any]]:
    """Ermittelt defensive Quellen aus vorhandenen Inspect-Daten + lokal lesbaren Linux-Pfaden."""
    out: list[dict[str, Any]] = []

    # Linux Basispfade
    etc = Path("/etc")
    try:
        etc_readable = etc.is_dir() and os.access(etc, os.R_OK | os.X_OK)
    except (PermissionError, OSError):
        etc_readable = False
    out.append(
        _source_entry(
            str(etc),
            "linux_etc",
            readable=etc_readable,
        )
    )
    out.extend(_scan_local_homes())

    storage = inspect_result.get("storage") if isinstance(inspect_result, dict) else {}
    storage = storage if isinstance(storage, dict) else {}
    classified = storage.get("devices_classified")
    classified_list = classified if isinstance(classified, list) else []

    filesystems = inspect_result.get("filesystems") if isinstance(inspect_result, dict) else {}
    filesystems = filesystems if isinstance(filesystems, dict) else {}
    detected = filesystems.get("detected")
    detected = detected if isinstance(detected, dict) else {}

    seen_paths: set[str] = {str(x.get("path")) for x in out if isinstance(x, dict)}

    def visit(node: dict[str, Any]) -> None:
        parts = node.get("partitions")
        if isinstance(parts, list):
            for p in parts:
                if isinstance(p, dict):
                    visit(p)
        if node.get("type") != "part":
            return

        mp = node.get("mountpoint")
        if not isinstance(mp, str) or not mp:
            return
        if mp in {"/", "/boot", "/boot/efi"}:
            return
        if mp in seen_paths:
            return

        dev = node.get("device")
        fs_meta = detected.get(dev) if isinstance(dev, str) else None
        fs_type = str((fs_meta or {}).get("type") or node.get("fstype") or "").strip().lower()
        try:
            readable = os.access(mp, os.R_OK | os.X_OK)
        except (PermissionError, OSError):
            readable = False

        if fs_type == "ntfs":
            out.append(
                _source_entry(
                    mp,
                    "windows_candidate",
                    readable=readable,
                    warnings=["source.warning.windows_candidate"],
                )
            )
            seen_paths.add(mp)
            users = Path(mp) / "Users"
            if str(users) not in seen_paths:
                try:
                    users_readable = users.is_dir() and os.access(users, os.R_OK | os.X_OK)
                except (PermissionError, OSError):
                    users_readable = False
                out.append(
                    _source_entry(
                        str(users),
                        "windows_profiles_candidate",
                        readable=users_readable,
                        warnings=["source.warning.windows_candidate"],
                    )
                )
                seen_paths.add(str(users))
            return

        category = str(node.get("category") or "unknown")
        if category == "backup_candidate":
            out.append(_source_entry(mp, "data_partition", readable=readable))
        else:
            out.append(
                _source_entry(
                    mp,
                    "unknown_partition_candidate",
                    readable=readable,
                    warnings=["source.warning.unknown_partition"],
                )
            )
        seen_paths.add(mp)

    for disk in classified_list:
        if isinstance(disk, dict):
            visit(disk)

    return out


def _resolve_target_mountpoint(target_device: str, inspect_result: dict[str, Any]) -> str | None:
    storage = inspect_result.get("storage") if isinstance(inspect_result, dict) else {}
    storage = storage if isinstance(storage, dict) else {}
    classified = storage.get("devices_classified")
    classified_list = classified if isinstance(classified, list) else []

    for disk in classified_list:
        if not isinstance(disk, dict):
            continue
        if disk.get("device") != target_device:
            continue

        stack = [disk]
        while stack:
            n = stack.pop()
            if not isinstance(n, dict):
                continue
            parts = n.get("partitions")
            if isinstance(parts, list):
                stack.extend(parts)
            if n.get("type") != "part":
                continue
            if str(n.get("category") or "") != "backup_candidate":
                continue
            mp = n.get("mountpoint")
            if isinstance(mp, str) and mp:
                return mp
    return None


def _build_exec_sources_for_plan(plan_sources: list[dict[str, Any]]) -> tuple[list[str], list[dict[str, Any]]]:
    usable: list[str] = []
    rejected: list[dict[str, Any]] = []
    for s in plan_sources:
        code = s.get("code")
        path = s.get("path")
        warnings = s.get("warnings") or []
        if code != "PREFLIGHT_SOURCE_FOUND":
            rejected.append({"source_id": s.get("source_id"), "code": "PREFLIGHT_SOURCE_UNREADABLE"})
            continue
        if warnings:
            rejected.append({"source_id": s.get("source_id"), "code": "PREFLIGHT_SOURCE_UNREADABLE"})
            continue
        if isinstance(path, str) and path:
            usable.append(path)
    return usable, rejected


def create_backup_preview(
    *,
    target_device: str,
    inspect_result: dict[str, Any],
    selected_source_ids: list[str] | None = None,
) -> dict[str, Any]:
    safety = evaluate_write_target(target_device, inspect_result)
    reason = str(safety.get("reason_code") or "")

    if reason in _BLOCKED_TARGET_REASONS:
        return {
            "code": "PREFLIGHT_TARGET_BLOCKED",
            "plan_id": None,
            "confirmation_token": None,
            "target_device": target_device,
            "target_reason": reason,
            "requires_confirmation": False,
            "sources": [],
        }

    sources_all = list_candidate_sources(inspect_result)
    if selected_source_ids:
        wanted = set(selected_source_ids)
        sources = [s for s in sources_all if str(s.get("source_id")) in wanted]
    else:
        sources = sources_all

    plan_id = secrets.token_hex(8)
    token = secrets.token_urlsafe(24)
    target_mount = _resolve_target_mountpoint(target_device, inspect_result)

    _PLAN_STORE[plan_id] = {
        "plan_id": plan_id,
        "token": token,
        "target_device": target_device,
        "target_reason": reason,
        "target_mountpoint": target_mount,
        "sources": sources,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    code = "PREFLIGHT_PLAN_CREATED"
    requires_confirm = reason == _WARN_TARGET_REASON
    if requires_confirm:
        code = "PREFLIGHT_TARGET_REQUIRES_CONFIRMATION"

    return {
        "code": code,
        "plan_id": plan_id,
        "confirmation_token": token,
        "target_device": target_device,
        "target_reason": reason,
        "target_mountpoint": target_mount,
        "requires_confirmation": requires_confirm,
        "sources": sources,
    }


def execute_backup_plan(
    *,
    plan_id: str,
    confirmation_token: str,
    inspect_result: dict[str, Any],
    allow_empty_target: bool = False,
) -> dict[str, Any]:
    plan = _PLAN_STORE.get(plan_id)
    if not plan:
        return {"code": "PREFLIGHT_TOKEN_INVALID", "plan_id": plan_id}
    if str(plan.get("token") or "") != str(confirmation_token or ""):
        return {"code": "PREFLIGHT_TOKEN_INVALID", "plan_id": plan_id}

    target_device = str(plan.get("target_device") or "")
    safety = evaluate_write_target(target_device, inspect_result)
    reason = str(safety.get("reason_code") or "")

    if reason in _BLOCKED_TARGET_REASONS:
        return {
            "code": "PREFLIGHT_TARGET_BLOCKED",
            "plan_id": plan_id,
            "target_reason": reason,
        }

    if reason == _WARN_TARGET_REASON and not allow_empty_target:
        return {
            "code": "PREFLIGHT_TARGET_REQUIRES_CONFIRMATION",
            "plan_id": plan_id,
            "target_reason": reason,
        }

    target_mount = plan.get("target_mountpoint")
    if not isinstance(target_mount, str) or not target_mount:
        return {
            "code": "PREFLIGHT_TARGET_BLOCKED",
            "plan_id": plan_id,
            "target_reason": "SAFETY_UNKNOWN_DEVICE",
        }

    source_paths, rejected = _build_exec_sources_for_plan(plan.get("sources") or [])
    if not source_paths:
        return {
            "code": "PREFLIGHT_BACKUP_FAILED",
            "plan_id": plan_id,
            "rejected_sources": rejected,
        }

    preflight_dir = Path(target_mount) / "setuphelfer-preflight"
    preflight_dir.mkdir(parents=True, exist_ok=True)
    archive = preflight_dir / f"preflight-{plan_id}.tar.gz"

    backup = create_file_backup(
        source_paths,
        archive_path=archive,
        allowed_source_prefixes=[Path(p) for p in source_paths],
        allowed_output_prefixes=[Path(target_mount)],
    )
    if not backup.ok or not backup.archive_path:
        return {
            "code": "PREFLIGHT_BACKUP_FAILED",
            "plan_id": plan_id,
            "backup_code": backup.message_key,
        }

    # Backup erstellt
    out: dict[str, Any] = {
        "code": "PREFLIGHT_BACKUP_STARTED",
        "plan_id": plan_id,
        "archive_path": backup.archive_path,
        "backup_code": backup.message_key,
    }

    ok_verify, verify_key, _detail = verify_basic(backup.archive_path)
    if ok_verify:
        out["code"] = "PREFLIGHT_BACKUP_VERIFIED"
        out["verify_code"] = verify_key
    else:
        out["code"] = "PREFLIGHT_BACKUP_VERIFY_FAILED"
        out["verify_code"] = verify_key
    return out
