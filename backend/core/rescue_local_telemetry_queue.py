"""
Rescue stick local telemetry queue — offline-first, redacted before persist.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from core.rescue_persistence import Runner
from core.rescue_telemetry_spool import build_telemetry_spool_summary, write_telemetry_event
from core.telemetry_redaction_contract import redact_telemetry_payload

QUEUE_VERSION = 2

RESCUE_EVENT_TYPES = frozenset(
    {
        "rescue_boot_started",
        "rescue_boot_completed",
        "system_detection_completed",
        "wifi_diagnostics_completed",
        "backup_plan_requested",
        "backup_plan_ready",
        "backup_plan_blocked",
        "backup_preflight_ready",
        "backup_preflight_blocked",
        "backup_execute_not_allowed_in_this_phase",
        "evidence_persisted",
        "evidence_persistence_failed",
    }
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def enqueue_local_telemetry_event(
    event: dict[str, Any],
    *,
    runner: Runner = None,
    stick_build_id: str | None = None,
    rescue_session_id: str | None = None,
) -> dict[str, Any]:
    body = dict(event)
    etype = str(body.get("event_type") or body.get("phase") or "unknown")
    if etype not in RESCUE_EVENT_TYPES and body.get("phase"):
        etype = str(body["phase"])
    body.setdefault("event_type", etype)
    body.setdefault("rescue_session_id", rescue_session_id or uuid.uuid4().hex[:16])
    body.setdefault("stick_build_id", stick_build_id or "unknown")
    body.setdefault("queued_at", _utc_now())
    body.setdefault("network_upload_attempted", False)
    redacted = redact_telemetry_payload(body)
    return write_telemetry_event(redacted, runner=runner)


def build_local_telemetry_queue_status(*, runner: Runner = None) -> dict[str, Any]:
    summary = build_telemetry_spool_summary(runner=runner)
    return {
        "schema_version": 1,
        "queue_version": QUEUE_VERSION,
        "offline_first": True,
        "cloud_dependency": False,
        "network_upload_attempted": False,
        "spool": summary,
    }
