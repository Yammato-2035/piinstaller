"""Controlled rescue telemetry task pull — allowlist only, no remote shell."""

from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ALLOWED_TASK_TYPES = frozenset(
    {
        "collect_logs",
        "run_media_check",
        "run_network_check",
        "resend_telemetry",
        "show_operator_message",
        "request_operator_confirmation",
        "prepare_windows_inspect_readonly_preflight",
    }
)

FORBIDDEN_TASK_KEYS = frozenset({"shell", "command", "exec", "script", "eval", "bash"})


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def tasks_storage_root() -> Path:
    raw = os.environ.get("RESCUE_TELEMETRY_TASKS_STORAGE_ROOT", "").strip()
    if raw:
        return Path(raw)
    return _repo_root() / "docs/evidence/runtime-results/rescue/telemetry-tasks"


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _parse_iso(value: str) -> datetime | None:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None


def validate_task_manifest(task: dict[str, Any]) -> tuple[bool, str | None]:
    if not isinstance(task, dict):
        return False, "invalid_task_object"
    task_type = task.get("task_type")
    if task_type not in ALLOWED_TASK_TYPES:
        return False, "unknown_task_type"
    for key in task:
        if key.lower() in FORBIDDEN_TASK_KEYS:
            return False, "forbidden_task_key"
    if not task.get("task_id"):
        return False, "missing_task_id"
    expires_at = task.get("expires_at")
    if expires_at:
        exp = _parse_iso(str(expires_at))
        if exp is None:
            return False, "invalid_expires_at"
        if exp < _utc_now():
            return False, "task_expired"
    return True, None


def get_next_task(*, boot_id: str) -> dict[str, Any] | None:
    queue = tasks_storage_root() / "pending"
    if not queue.is_dir():
        return None
    for path in sorted(queue.glob("*.json")):
        try:
            task = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if str(task.get("boot_id") or "*") not in {boot_id, "*", ""}:
            continue
        ok, _reason = validate_task_manifest(task)
        if ok:
            return task
    return None


def store_task_result(payload: dict[str, Any]) -> dict[str, Any]:
    task_id = str(payload.get("task_id") or "")
    if not task_id:
        return {"stored": False, "error": "missing_task_id"}
    root = tasks_storage_root() / "results"
    root.mkdir(parents=True, exist_ok=True)
    record = {
        "received_at": _utc_now().isoformat(),
        "boot_id": payload.get("boot_id"),
        "task_id": task_id,
        "task_type": payload.get("task_type"),
        "result_status": payload.get("result_status"),
        "result_payload": payload.get("result_payload") or {},
        "dry_run": bool(payload.get("dry_run", True)),
        "secrets_exposed": False,
    }
    path = root / f"{task_id}.json"
    path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    pending = tasks_storage_root() / "pending"
    for candidate in pending.glob("*.json"):
        try:
            task = json.loads(candidate.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if str(task.get("task_id")) == task_id:
            candidate.unlink(missing_ok=True)
    return {"stored": True, "task_id": task_id, "path": str(path)}


def build_compact_task_pull_status() -> dict[str, Any]:
    root = tasks_storage_root()
    results = sorted((root / "results").glob("*.json")) if (root / "results").is_dir() else []
    last_task_id = None
    last_result = None
    if results:
        try:
            last = json.loads(results[-1].read_text(encoding="utf-8"))
            last_task_id = last.get("task_id")
            last_result = last.get("result_status")
        except (OSError, json.JSONDecodeError):
            pass
    enabled = os.environ.get("RESCUE_TELEMETRY_TASK_PULL_ENABLED", "1").strip().lower() in {
        "1",
        "true",
        "yes",
    }
    return {
        "controlled_task_pull_available": enabled,
        "last_task_id": last_task_id,
        "last_task_result": last_result,
        "task_pull_allowed_paths_only": True,
        "allowed_task_types": sorted(ALLOWED_TASK_TYPES),
        "secrets_exposed": False,
    }


def enqueue_dev_task(task_type: str, *, boot_id: str = "*", dry_run: bool = True, params: dict | None = None) -> dict[str, Any]:
    """Development helper — queue allowlisted task for stick pull."""
    if task_type not in ALLOWED_TASK_TYPES:
        raise ValueError(f"unknown task_type: {task_type}")
    task_id = f"rtask-{uuid.uuid4().hex[:12]}"
    exp = (_utc_now() + __import__("datetime").timedelta(hours=1)).isoformat().replace("+00:00", "Z")
    task = {
        "task_id": task_id,
        "task_type": task_type,
        "boot_id": boot_id,
        "expires_at": exp,
        "min_rescue_version": "1.7.5.0",
        "dry_run": dry_run,
        "params": params or {},
        "payload_hash": None,
    }
    pending = tasks_storage_root() / "pending"
    pending.mkdir(parents=True, exist_ok=True)
    path = pending / f"{task_id}.json"
    path.write_text(json.dumps(task, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return task
