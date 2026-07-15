"""Per-component rescue heartbeats (001D7C) — TUI / discovery / MSI / finalizer."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

COMPONENTS = (
    "tui",
    "discovery",
    "msi_evidence",
    "boot_finalizer",
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def state_dir() -> Path:
    return Path(os.environ.get("SETUPHELFER_RESCUE_STATE_DIR", "/run/setuphelfer-rescue"))


def heartbeat_dir() -> Path:
    return state_dir() / "heartbeats"


def heartbeat_path(component: str) -> Path:
    return heartbeat_dir() / f"{component}.json"


def write_component_heartbeat(
    component: str,
    *,
    state: str = "running",
    pid: int | None = None,
) -> dict[str, Any]:
    if component not in COMPONENTS:
        raise ValueError(f"unknown_component:{component}")
    heartbeat_dir().mkdir(parents=True, exist_ok=True)
    payload = {
        "component": component,
        "last_heartbeat_at": _utc_now(),
        "state": state,
        "pid": pid if pid is not None else os.getpid(),
    }
    path = heartbeat_path(component)
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    tmp.replace(path)
    return payload


def read_component_heartbeat(component: str) -> dict[str, Any] | None:
    path = heartbeat_path(component)
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def component_heartbeat_age_sec(component: str) -> float | None:
    data = read_component_heartbeat(component)
    if not data:
        return None
    stamp = str(data.get("last_heartbeat_at") or "")
    if not stamp:
        return None
    try:
        dt = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
        return max(0.0, (datetime.now(timezone.utc) - dt).total_seconds())
    except ValueError:
        return None
