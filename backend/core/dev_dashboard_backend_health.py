"""
Read-only loader for external developer backend health evidence (JSON on disk).

No shell, no health probes from the API process — only file reads.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core import dev_dashboard as dev_dashboard_core

DEFAULT_STALE_AFTER_SECONDS = 180
_HISTORY_TAIL_MAX = 20


def _candidate_paths(repo_root: Path) -> list[Path]:
    paths: list[Path] = [
        repo_root / "docs" / "evidence" / "dev-dashboard" / "backend_health_latest.json",
    ]
    opt = Path("/opt/setuphelfer")
    if opt != repo_root:
        paths.append(
            opt / "docs" / "evidence" / "dev-dashboard" / "backend_health_latest.json"
        )
    return paths


def _read_json_file(path: Path) -> dict[str, Any] | None:
    try:
        if not path.is_file():
            return None
        raw = path.read_text(encoding="utf-8", errors="replace")
        data = json.loads(raw)
        return data if isinstance(data, dict) else None
    except (OSError, json.JSONDecodeError):
        return None


def _parse_generated_at(value: str | None) -> datetime | None:
    if not value or not isinstance(value, str):
        return None
    text = value.strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(text)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except ValueError:
        return None


def _load_history_tail(history_path: Path, *, limit: int = _HISTORY_TAIL_MAX) -> list[dict[str, Any]]:
    if not history_path.is_file() or limit <= 0:
        return []
    lines = history_path.read_text(encoding="utf-8", errors="replace").splitlines()
    tail: list[dict[str, Any]] = []
    for line in lines[-limit:]:
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
            if isinstance(row, dict):
                tail.append(row)
        except json.JSONDecodeError:
            continue
    return tail


def load_backend_health_snapshot(
    *,
    stale_after_seconds: int = DEFAULT_STALE_AFTER_SECONDS,
    history_limit: int = _HISTORY_TAIL_MAX,
) -> dict[str, Any]:
    repo = dev_dashboard_core._repo_root()
    source_path: Path | None = None
    current: dict[str, Any] | None = None
    for candidate in _candidate_paths(repo):
        loaded = _read_json_file(candidate)
        if loaded is not None:
            current = loaded
            source_path = candidate
            break

    now = datetime.now(timezone.utc)
    if current is None:
        return {
            "status": "unknown",
            "stale": True,
            "stale_after_seconds": stale_after_seconds,
            "generated_at": None,
            "source_path": None,
            "current_health": None,
            "history_tail": [],
            "message": "backend_health_latest.json not found; run scripts/dev-dashboard/check-backend-health.sh",
        }

    gen_dt = _parse_generated_at(current.get("generated_at"))
    age_sec: float | None = None
    stale = True
    if gen_dt is not None:
        age_sec = (now - gen_dt).total_seconds()
        stale = age_sec > float(stale_after_seconds)

    overall = str(current.get("overall_status") or "unknown")
    if stale:
        status = "warning" if overall in ("ok", "warning") else "blocked"
    elif overall == "ok":
        status = "ok"
    elif overall == "warning":
        status = "warning"
    else:
        status = "blocked"

    history_path = (source_path.parent / "backend_health_history.jsonl") if source_path else None
    history_tail: list[dict[str, Any]] = []
    if history_path is not None:
        history_tail = _load_history_tail(history_path, limit=min(history_limit, _HISTORY_TAIL_MAX))

    return {
        "status": status,
        "stale": stale,
        "stale_after_seconds": stale_after_seconds,
        "generated_at": current.get("generated_at"),
        "age_seconds": round(age_sec, 1) if age_sec is not None else None,
        "source_path": str(source_path) if source_path else None,
        "current_health": current,
        "history_tail": history_tail,
    }
