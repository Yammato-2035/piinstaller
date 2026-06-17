"""Rescue evidence read-only API handlers (RS-F2S)."""

from __future__ import annotations

from typing import Any

from core.rescue_evidence_store import evidence_store_status
from core.rescue_local_telemetry_queue import build_local_telemetry_queue_status, enqueue_local_telemetry_event
from core.telemetry_redaction_contract import redact_preview


async def get_evidence_status() -> dict[str, Any]:
    return {
        "evidence": evidence_store_status(),
        "telemetry_queue": build_local_telemetry_queue_status(),
    }


async def post_telemetry_redact_preview(body: dict[str, Any]) -> dict[str, Any]:
    payload = body.get("payload") if isinstance(body.get("payload"), dict) else body
    return redact_preview(payload if isinstance(payload, dict) else {})


async def post_evidence_write_event(body: dict[str, Any]) -> dict[str, Any]:
    event = body.get("event") if isinstance(body.get("event"), dict) else body
    return enqueue_local_telemetry_event(
        event if isinstance(event, dict) else {},
        stick_build_id=str(body.get("stick_build_id") or ""),
        rescue_session_id=str(body.get("rescue_session_id") or "") or None,
    )


