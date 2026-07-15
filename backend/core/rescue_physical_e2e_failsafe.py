"""Heartbeat-protected lab auto-shutdown failsafe (001D6/001D7C)."""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

from core.rescue_component_heartbeat import component_heartbeat_age_sec
from core.rescue_discovery_observability import read_runtime_json
from core.rescue_physical_e2e_auto_e2e_state import (
    heartbeat_age_sec,
    read_auto_e2e_state,
)
from core.rescue_run_mode import resolve_run_mode

INACTIVITY_LIMIT_SEC = 300.0
ABSOLUTE_MAX_UPTIME_SEC = 3600.0
MSI_EVIDENCE_GRACE_SEC = 900.0
LEGACY_FAILSAFE_SEC = 420.0
OBSERVABILITY_TIMEOUT_SEC = 1200.0
COMPONENT_HB_MAX_AGE = 180.0


def _rescue_state_dir() -> Path:
    return Path(os.environ.get("SETUPHELFER_RESCUE_STATE_DIR", "/run/setuphelfer-rescue"))


def _uptime_sec() -> float:
    try:
        return float(Path("/proc/uptime").read_text(encoding="utf-8").split()[0])
    except (OSError, ValueError, IndexError):
        return 0.0


def _state_age_sec() -> float | None:
    state = read_auto_e2e_state()
    if not state:
        return None
    updated = str(state.get("updated_at") or "")
    if not updated:
        return None
    try:
        from datetime import datetime, timezone

        dt = datetime.fromisoformat(updated.replace("Z", "+00:00"))
        return (datetime.now(timezone.utc) - dt).total_seconds()
    except ValueError:
        return None


def _marker(name: str) -> bool:
    return (_rescue_state_dir() / name).is_file()


def _any_component_heartbeat_fresh(*, max_age: float = COMPONENT_HB_MAX_AGE) -> bool:
    for component in ("tui", "discovery", "msi_evidence", "boot_finalizer"):
        age = component_heartbeat_age_sec(component)
        if age is not None and age <= max_age:
            return True
    return False


def evaluate_lab_failsafe(*, heartbeat_max_age: float = 180.0) -> dict[str, Any]:
    uptime = _uptime_sec()
    hb_age = heartbeat_age_sec()
    state_age = _state_age_sec()
    state = read_auto_e2e_state() or {}
    phase = str(state.get("phase") or "")
    status = str(state.get("status") or "")

    msi_evidence_done = _marker("auto-msi-evidence.done")
    physical_e2e_done = _marker("auto-physical-e2e.done")
    discovery_done = _marker("auto-discovery.done")
    finalizer = read_runtime_json("boot-finalizer.json") or {}
    finalizer_ready = bool(finalizer.get("terminal") and finalizer.get("shutdown_safe"))

    mode = resolve_run_mode()
    discovery_mode = bool(mode.get("ok") and mode.get("run_mode") == "auto_discovery_only")

    heartbeat_fresh = hb_age is not None and hb_age <= heartbeat_max_age
    component_hb_fresh = _any_component_heartbeat_fresh(max_age=heartbeat_max_age)
    state_fresh = state_age is not None and state_age <= INACTIVITY_LIMIT_SEC

    reasons_skip: list[str] = []
    reasons_shutdown: list[str] = []

    if physical_e2e_done:
        reasons_skip.append("physical_e2e_complete")
    if discovery_done and finalizer_ready:
        reasons_skip.append("discovery_complete_with_finalizer")
    if heartbeat_fresh or component_hb_fresh:
        reasons_skip.append("heartbeat_fresh")
    if state_fresh and phase:
        reasons_skip.append("state_recently_updated")
    if not msi_evidence_done and uptime < MSI_EVIDENCE_GRACE_SEC:
        reasons_skip.append("msi_evidence_grace_period")

    # 001D7C: never failsafe-shutdown discovery before boot-finalizer,
    # unless observability itself timed out.
    if discovery_mode and not finalizer_ready:
        if uptime < OBSERVABILITY_TIMEOUT_SEC:
            reasons_skip.append("waiting_boot_finalizer")
        else:
            reasons_shutdown.append("failsafe_observability_timeout")

    if uptime >= ABSOLUTE_MAX_UPTIME_SEC:
        reasons_shutdown.append("absolute_max_uptime_exceeded")

    if not msi_evidence_done and uptime >= MSI_EVIDENCE_GRACE_SEC and not heartbeat_fresh and not component_hb_fresh:
        if not state_fresh:
            reasons_shutdown.append("msi_evidence_timeout_no_heartbeat")

    if msi_evidence_done and not physical_e2e_done and not discovery_mode:
        if not heartbeat_fresh and not component_hb_fresh and not state_fresh and uptime > INACTIVITY_LIMIT_SEC + 150:
            reasons_shutdown.append("e2e_inactivity_no_heartbeat")

    if discovery_mode and finalizer_ready and not component_hb_fresh and not state_fresh:
        if uptime > INACTIVITY_LIMIT_SEC + 150:
            reasons_shutdown.append("discovery_complete_inactivity")

    allow_shutdown = bool(reasons_shutdown) and not (
        (heartbeat_fresh or component_hb_fresh or state_fresh or (not msi_evidence_done and uptime < MSI_EVIDENCE_GRACE_SEC))
        and "failsafe_observability_timeout" not in reasons_shutdown
        and "absolute_max_uptime_exceeded" not in reasons_shutdown
    )

    # Absolute max / observability timeout can override skips (except fresh work signals for absolute max only via note).
    if "failsafe_observability_timeout" in reasons_shutdown and not finalizer_ready:
        allow_shutdown = True
    if "absolute_max_uptime_exceeded" in reasons_shutdown:
        allow_shutdown = True

    # Still require best-effort finalizer before poweroff when possible.
    requires_finalizer_first = discovery_mode and not finalizer_ready and "failsafe_observability_timeout" not in reasons_shutdown
    if requires_finalizer_first:
        allow_shutdown = False

    return {
        "allow_shutdown": allow_shutdown,
        "uptime_sec": uptime,
        "heartbeat_age_sec": hb_age,
        "state_age_sec": state_age,
        "phase": phase,
        "status": status,
        "msi_evidence_done": msi_evidence_done,
        "physical_e2e_done": physical_e2e_done,
        "discovery_done": discovery_done,
        "discovery_mode": discovery_mode,
        "boot_finalizer_ready": finalizer_ready,
        "boot_finalizer_status": finalizer.get("status"),
        "component_heartbeat_fresh": component_hb_fresh,
        "heartbeat_fresh": heartbeat_fresh,
        "state_fresh": state_fresh,
        "legacy_420_disabled": True,
        "inactivity_limit_sec": INACTIVITY_LIMIT_SEC,
        "absolute_max_sec": ABSOLUTE_MAX_UPTIME_SEC,
        "observability_timeout_sec": OBSERVABILITY_TIMEOUT_SEC,
        "reasons_skip": reasons_skip,
        "reasons_shutdown": reasons_shutdown,
        "shutdown_classification": (
            "failsafe_observability_timeout"
            if "failsafe_observability_timeout" in reasons_shutdown
            else ("auto_shutdown_failsafe_timeout" if allow_shutdown else "deferred")
        ),
    }
