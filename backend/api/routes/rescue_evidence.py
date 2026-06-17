"""Rescue evidence / telemetry plan-only routes (RS-F2S)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Body

from api.handlers import rescue_evidence_handlers as evidence_handlers

router = APIRouter(tags=["rescue-evidence"])


@router.get("/evidence/status")
async def rescue_evidence_status_route():
    return await evidence_handlers.get_evidence_status()


@router.post("/telemetry/redact-preview")
async def rescue_telemetry_redact_preview_route(body: dict[str, Any] = Body(...)):
    return await evidence_handlers.post_telemetry_redact_preview(body)


@router.post("/evidence/write-event")
async def rescue_evidence_write_event_route(body: dict[str, Any] = Body(...)):
    return await evidence_handlers.post_evidence_write_event(body)
