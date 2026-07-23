"""In-process lab job store for ASUS_ROG_GABRIEL_LAB (PI-RS-ASUS-LAB-CONTROL-006).

Jobs are keyed by job_id and remain queryable after reboot planning via run_id.
Not a durable agent runtime — persistence across process restarts is best-effort
via optional JSON sidecar when LAB_JOB_STORE_PATH is set.
"""

from __future__ import annotations

import json
import os
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.rescue_lab_job_contract import JOB_STATES

_LOCK = threading.Lock()
_JOBS: dict[str, dict[str, Any]] = {}


def _store_path() -> Path | None:
    raw = (os.environ.get("SETUPHELFER_LAB_JOB_STORE_PATH") or "").strip()
    return Path(raw) if raw else None


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _persist_unlocked() -> None:
    path = _store_path()
    if path is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(_JOBS, indent=2) + "\n", encoding="utf-8")


def _load_unlocked() -> None:
    path = _store_path()
    if path is None or not path.is_file():
        return
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return
    if isinstance(data, dict):
        for job_id, job in data.items():
            if isinstance(job, dict) and job_id:
                _JOBS[str(job_id)] = job


def put_job(job: dict[str, Any]) -> dict[str, Any]:
    job_id = str(job.get("job_id") or "")
    if not job_id:
        raise ValueError("job_id_missing")
    with _LOCK:
        if not _JOBS and _store_path():
            _load_unlocked()
        stored = dict(job)
        stored.setdefault("state", "created")
        stored["updated_at"] = _utc_now()
        _JOBS[job_id] = stored
        _persist_unlocked()
        return dict(stored)


def get_job(job_id: str) -> dict[str, Any] | None:
    with _LOCK:
        if not _JOBS and _store_path():
            _load_unlocked()
        job = _JOBS.get(job_id)
        return dict(job) if job else None


def find_jobs_by_run_id(run_id: str) -> list[dict[str, Any]]:
    with _LOCK:
        if not _JOBS and _store_path():
            _load_unlocked()
        return [dict(j) for j in _JOBS.values() if str(j.get("run_id") or "") == run_id]


def transition_job(job_id: str, new_state: str, *, note: str | None = None) -> dict[str, Any]:
    if new_state not in JOB_STATES:
        raise ValueError("invalid_job_state")
    with _LOCK:
        if not _JOBS and _store_path():
            _load_unlocked()
        job = _JOBS.get(job_id)
        if job is None:
            raise KeyError("job_not_found")
        job = dict(job)
        prev = str(job.get("state") or "")
        if prev in {"success", "failed", "blocked", "cancelled"} and new_state != prev:
            raise ValueError("job_terminal")
        job["state"] = new_state
        job["updated_at"] = _utc_now()
        if note:
            history = list(job.get("state_history") or [])
            history.append({"from": prev, "to": new_state, "at": job["updated_at"], "note": note})
            job["state_history"] = history
        _JOBS[job_id] = job
        _persist_unlocked()
        return dict(job)


def cancel_job(job_id: str, *, reason: str = "operator_cancel") -> dict[str, Any]:
    return transition_job(job_id, "cancelled", note=reason)


def mark_waiting_for_reboot(job_id: str) -> dict[str, Any]:
    return transition_job(job_id, "waiting_for_reboot", note="reboot_pending")


def mark_reconnected(job_id: str) -> dict[str, Any]:
    return transition_job(job_id, "reconnected", note="agent_reconnected")
