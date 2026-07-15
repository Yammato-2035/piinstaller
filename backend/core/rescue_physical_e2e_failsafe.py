"""Heartbeat-protected lab auto-shutdown failsafe (001D6)."""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

from core.rescue_physical_e2e_auto_e2e_state import (
    heartbeat_age_sec,
    read_auto_e2e_state,
)

INACTIVITY_LIMIT_SEC = 300.0
ABSOLUTE_MAX_UPTIME_SEC = 3600.0
MSI_EVIDENCE_GRACE_SEC = 900.0
LEGACY_FAILSAFE_SEC = 420.0

RESCUE_STATE_DIR = Path(os.environ.get("SETUPHELFER_RESCUE_STATE_DIR", "/run/setuphelfer-rescue"))


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
    return (RESCUE_STATE_DIR / name).is_file()


def evaluate_lab_failsafe(*, heartbeat_max_age: float = 180.0) -> dict[str, Any]:
    uptime = _uptime_sec()
    hb_age = heartbeat_age_sec()
    state_age = _state_age_sec()
    state = read_auto_e2e_state() or {}
    phase = str(state.get("phase") or "")
    status = str(state.get("status") or "")

    msi_evidence_done = _marker("auto-msi-evidence.done")
    physical_e2e_done = _marker("auto-physical-e2e.done")
    heartbeat_fresh = hb_age is not None and hb_age <= heartbeat_max_age
    state_fresh = state_age is not None and state_age <= INACTIVITY_LIMIT_SEC

    reasons_skip: list[str] = []
    reasons_shutdown: list[str] = []

    if physical_e2e_done:
        reasons_skip.append("physical_e2e_complete")
    if heartbeat_fresh:
        reasons_skip.append("heartbeat_fresh")
    if state_fresh and phase:
        reasons_skip.append("state_recently_updated")
    if not msi_evidence_done and uptime < MSI_EVIDENCE_GRACE_SEC:
        reasons_skip.append("msi_evidence_grace_period")
    if uptime < ABSOLUTE_MAX_UPTIME_SEC and (heartbeat_fresh or state_fresh or not msi_evidence_done):
        pass
    elif uptime >= ABSOLUTE_MAX_UPTIME_SEC:
        reasons_shutdown.append("absolute_max_uptime_exceeded")

    if not msi_evidence_done and uptime >= MSI_EVIDENCE_GRACE_SEC and not heartbeat_fresh:
        if not state_fresh:
            reasons_shutdown.append("msi_evidence_timeout_no_heartbeat")

    if msi_evidence_done and not physical_e2e_done:
        if not heartbeat_fresh and not state_fresh and uptime > INACTIVITY_LIMIT_SEC + 150:
            reasons_shutdown.append("e2e_inactivity_no_heartbeat")

    allow_shutdown = bool(reasons_shutdown) and not (
        heartbeat_fresh or state_fresh or (not msi_evidence_done and uptime < MSI_EVIDENCE_GRACE_SEC)
    )

    return {
        "allow_shutdown": allow_shutdown,
        "uptime_sec": uptime,
        "heartbeat_age_sec": hb_age,
        "state_age_sec": state_age,
        "phase": phase,
        "status": status,
        "msi_evidence_done": msi_evidence_done,
        "physical_e2e_done": physical_e2e_done,
        "heartbeat_fresh": heartbeat_fresh,
        "state_fresh": state_fresh,
        "legacy_420_disabled": True,
        "inactivity_limit_sec": INACTIVITY_LIMIT_SEC,
        "absolute_max_sec": ABSOLUTE_MAX_UPTIME_SEC,
        "reasons_skip": reasons_skip,
        "reasons_shutdown": reasons_shutdown,
    }
