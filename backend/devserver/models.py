"""Hilfsfunktionen und stabile Dict-Modelle für den Development Server."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

UTC = timezone.utc


def utc_now_iso() -> str:
    return datetime.now(tz=UTC).replace(microsecond=0).isoformat()


def new_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:16]}"


def empty_hardware_inventory() -> dict[str, Any]:
    return {
        "cpu": {},
        "memory": {},
        "board": {},
        "gpu": {},
        "firmware_mode": "",
        "secure_boot": None,
        "machine_type": "",
        "virtualization_hint": "",
    }


def empty_storage_topology() -> dict[str, Any]:
    return {
        "block_devices": [],
        "partitions": [],
        "filesystems": [],
        "mountpoints": [],
        "removable": [],
        "transport": {},
        "size_bytes": 0,
        "smart_status": {},
        "serial_hash": None,
    }


def empty_boot_profile() -> dict[str, Any]:
    return {
        "firmware_mode": "",
        "efi_present": None,
        "secure_boot": None,
        "detected_bootloaders": [],
        "windows_boot_manager_present": None,
        "grub_present": None,
        "systemd_boot_present": None,
        "os_candidates": [],
    }


def default_dev_node(
    *,
    node_id: str,
    display_name: str = "",
    node_kind: str = "unknown",
    lab_mode: str = "local_lab",
) -> dict[str, Any]:
    return {
        "node_id": node_id,
        "display_name": display_name or node_id,
        "node_kind": node_kind,
        "lab_mode": lab_mode,
        "last_seen_at": utc_now_iso(),
        "status": "online",
        "current_action": None,
        "tags": [],
        "notes": "",
        "ssh": {
            "enabled": False,
            "host": "",
            "port": 22,
            "username": "",
            "auth_ref": "",
            "last_check_status": "not_configured",
            "last_check_error": "",
        },
    }


def default_dev_report(
    *,
    report_id: str,
    node_id: str,
    report_type: str = "manual",
    lab_mode: str = "local_lab",
    payload: dict[str, Any] | None = None,
    redaction_status: str = "raw_lab",
) -> dict[str, Any]:
    return {
        "report_id": report_id,
        "node_id": node_id,
        "created_at": utc_now_iso(),
        "report_type": report_type,
        "lab_mode": lab_mode,
        "setuphelfer_version": "",
        "rescue_build_id": "",
        "payload": payload or {},
        "redaction_status": redaction_status,
        "evidence_paths": [],
        "warnings": [],
        "errors": [],
    }


def default_dev_action(
    *,
    action_id: str,
    node_id: str,
    action_type: str,
    command_profile: str = "",
    commands: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "action_id": action_id,
        "node_id": node_id,
        "requested_at": utc_now_iso(),
        "started_at": None,
        "finished_at": None,
        "requested_by": "developer_dashboard",
        "action_type": action_type,
        "mode": "read_only",
        "status": "queued",
        "command_profile": command_profile,
        "commands": commands or [],
        "stdout_excerpt": "",
        "stderr_excerpt": "",
        "exit_code": None,
        "warnings": [],
        "errors": [],
    }


def merge_node_update(existing: dict[str, Any], incoming: dict[str, Any]) -> dict[str, Any]:
    out = dict(existing)
    for key in ("display_name", "node_kind", "lab_mode", "tags", "notes", "status"):
        if key in incoming and incoming[key] is not None:
            out[key] = incoming[key]
    if "ssh" in incoming and isinstance(incoming["ssh"], dict):
        ssh = dict(out.get("ssh") or {})
        ssh.update({k: v for k, v in incoming["ssh"].items() if v is not None})
        out["ssh"] = ssh
    out["last_seen_at"] = utc_now_iso()
    return out
