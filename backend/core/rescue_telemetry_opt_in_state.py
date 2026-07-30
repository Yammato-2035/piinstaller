"""
Rescue telemetry opt-in state — local persistence backing the settings toggle
and the send-gate check used by maybe_send_assessment_telemetry_early().
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.telemetry_client_contract import TelemetryOptInState

STATE_SCHEMA_VERSION = 1
_DEFAULT_STATE_PATH = Path("/run/setuphelfer-rescue/telemetry-opt-in.json")


def default_opt_in_state_path() -> Path:
  return _DEFAULT_STATE_PATH


def _utc_now() -> str:
  return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_telemetry_opt_in(path: Path | None = None) -> TelemetryOptInState:
  target = path or default_opt_in_state_path()
  if not target.is_file():
    return TelemetryOptInState.DISABLED
  try:
    data = json.loads(target.read_text(encoding="utf-8"))
  except (OSError, json.JSONDecodeError):
    return TelemetryOptInState.DISABLED
  raw = str((data or {}).get("opt_in_state") or "disabled")
  try:
    return TelemetryOptInState(raw)
  except ValueError:
    return TelemetryOptInState.DISABLED


def save_telemetry_opt_in(state: TelemetryOptInState, *, path: Path | None = None) -> dict[str, Any]:
  target = path or default_opt_in_state_path()
  body = {
    "schema_version": STATE_SCHEMA_VERSION,
    "opt_in_state": state.value,
    "updated_at": _utc_now(),
  }
  target.parent.mkdir(parents=True, exist_ok=True)
  target.write_text(json.dumps(body, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
  return body


def is_telemetry_opt_in_enabled(path: Path | None = None) -> bool:
  return load_telemetry_opt_in(path) == TelemetryOptInState.ENABLED
