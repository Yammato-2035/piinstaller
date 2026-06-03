"""
Read-only loader for external developer backend health evidence (JSON on disk).

No shell, no health probes from the API process — only file reads.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core import dev_dashboard as dev_dashboard_core

DEFAULT_STALE_AFTER_SECONDS = 180
_HISTORY_TAIL_MAX = 20
_OPT_INSTALL_ROOT = Path("/opt/setuphelfer")


def _dedupe_paths(paths: list[Path]) -> list[Path]:
    seen: set[str] = set()
    out: list[Path] = []
    for p in paths:
        key = str(p.resolve()) if p.exists() or p.parent.exists() else str(p)
        if key in seen:
            continue
        seen.add(key)
        out.append(p)
    return out


def build_health_evidence_search_paths() -> list[Path]:
    """Ordered candidates for backend_health_latest.json (first match wins)."""
    latest_name = "backend_health_latest.json"
    paths: list[Path] = []

    env_dir = (os.environ.get("SETUPHELFER_HEALTH_EVIDENCE_DIR") or "").strip()
    if env_dir:
        paths.append(Path(env_dir) / latest_name)

    # Runtime under /opt: prefer /opt evidence before workspace checkout.
    backend_core = Path(__file__).resolve()
    if str(_OPT_INSTALL_ROOT) in str(backend_core):
        paths.append(
            _OPT_INSTALL_ROOT / "docs" / "evidence" / "dev-dashboard" / latest_name
        )

    repo = dev_dashboard_core._repo_root()
    paths.append(repo / "docs" / "evidence" / "dev-dashboard" / latest_name)

    if str(repo) != str(_OPT_INSTALL_ROOT):
        paths.append(
            _OPT_INSTALL_ROOT / "docs" / "evidence" / "dev-dashboard" / latest_name
        )

    ws = (os.environ.get("SETUPHELFER_DEV_WORKSPACE_ROOT") or "").strip()
    if ws:
        paths.append(Path(ws) / "docs" / "evidence" / "dev-dashboard" / latest_name)

    return _dedupe_paths(paths)


def _probe_evidence_file(path: Path) -> tuple[str, dict[str, Any] | None]:
    if not path.is_file():
        return "missing", None
    try:
        raw = path.read_text(encoding="utf-8", errors="replace")
        data = json.loads(raw)
        if isinstance(data, dict):
            return "ok", data
        return "invalid_json", None
    except PermissionError:
        return "permission_denied", None
    except (OSError, json.JSONDecodeError):
        return "read_error", None


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
    try:
        lines = history_path.read_text(encoding="utf-8", errors="replace").splitlines()
    except (OSError, PermissionError):
        return []
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
    searched: list[dict[str, str]] = []
    source_path: Path | None = None
    current: dict[str, Any] | None = None
    permission_denied_paths: list[str] = []

    for candidate in build_health_evidence_search_paths():
        state, loaded = _probe_evidence_file(candidate)
        searched.append({"path": str(candidate), "state": state})
        if state == "permission_denied":
            permission_denied_paths.append(str(candidate))
            continue
        if state == "ok" and loaded is not None:
            current = loaded
            source_path = candidate
            break

    now = datetime.now(timezone.utc)
    if current is None:
        msg = "backend_health_latest.json not found; run scripts/dev-dashboard/check-backend-health.sh"
        if permission_denied_paths:
            msg = (
                "backend_health_latest.json not readable (permission denied); "
                "re-run healthcheck or chmod 664 the evidence file"
            )
        return {
            "status": "unknown",
            "stale": True,
            "stale_after_seconds": stale_after_seconds,
            "generated_at": None,
            "source_path": None,
            "searched_paths": searched,
            "current_health": None,
            "history_tail": [],
            "message": msg,
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
        "searched_paths": searched,
        "current_health": current,
        "history_tail": history_tail,
    }
