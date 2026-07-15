"""Boot completion validator when discovery should have started but did not (001D7B)."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.rescue_discovery_run_control import (
    consume_discovery_run_control,
    load_discovery_run_control,
)
from core.rescue_physical_e2e_evidence_import import find_setup_logs_mount
from core.rescue_session_state import (
    init_session_state,
    mark_terminal,
    session_evidence_dir,
)

FAILED_STATUS = "failed_discovery_service_not_started"


def _state_dir() -> Path:
    return Path(os.environ.get("SETUPHELFER_RESCUE_STATE_DIR", "/run/setuphelfer-rescue"))


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _discovery_started_markers() -> bool:
    state_dir = _state_dir()
    if (state_dir / "auto-discovery.done").is_file():
        return True
    if (state_dir / "auto-discovery.started").is_file():
        return True
    from core.rescue_session_state import session_state_path

    session = session_state_path()
    if session.is_file():
        try:
            data = json.loads(session.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            data = {}
        if data.get("run_mode") == "auto_discovery_only" or str(data.get("source") or "").startswith(
            "physical"
        ):
            # Session exists — discovery (or its start path) ran.
            if data.get("session_id"):
                return True
    return False


def evaluate_discovery_boot_completion(
    *,
    setup_logs_base: Path | None = None,
) -> dict[str, Any]:
    base = setup_logs_base or find_setup_logs_mount()
    if base is None:
        return {"action": "none", "reason": "setup_logs_missing"}

    control = load_discovery_run_control(base)
    if not control:
        return {"action": "none", "reason": "no_discovery_run_control"}
    if control.get("consumed"):
        return {"action": "none", "reason": "already_consumed"}
    if not control.get("enabled"):
        return {"action": "none", "reason": "disabled"}
    if control.get("run_mode") != "auto_discovery_only":
        return {"action": "none", "reason": "run_mode_not_discovery"}

    if _discovery_started_markers():
        return {"action": "none", "reason": "discovery_started"}

    # Failure path: control still enabled, discovery never started.
    from core.rescue_payload_version import rescue_payload_version

    state = init_session_state(payload_version=rescue_payload_version(), source="physical_msi")
    state = mark_terminal(result="failed", evidence_complete=True, shutdown_safe=True)
    session_dir = session_evidence_dir(base, str(state["session_id"]))
    session_dir.mkdir(parents=True, exist_ok=True)
    failure = {
        "schema": "setuphelfer.rescue.discovery-boot-completion.v1",
        "status": FAILED_STATUS,
        "session_id": state.get("session_id"),
        "boot_id": state.get("boot_id"),
        "recorded_at": _utc_now(),
        "reason": "discovery_service_not_started_with_enabled_run_control",
    }
    path = session_dir / "16-discovery-summary.json"
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(failure, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    tmp.replace(path)

    consume_discovery_run_control(
        base,
        consumed_by_session_id=str(state.get("session_id") or ""),
        terminal_status=FAILED_STATUS,
    )
    try:
        state_dir = _state_dir()
        state_dir.mkdir(parents=True, exist_ok=True)
        (state_dir / "auto-discovery.done").write_text(FAILED_STATUS + "\n", encoding="utf-8")
    except OSError:
        pass
    return {
        "action": "failed_and_consumed",
        "status": FAILED_STATUS,
        "session_id": state.get("session_id"),
        "session_dir": str(session_dir),
    }
