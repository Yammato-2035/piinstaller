"""HTTP routes for rescue stick telemetry ingest (separate from /api/dev-dashboard)."""

from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from core.rescue_telemetry_ingest import build_health_payload, process_telemetry_ingest

router = APIRouter(prefix="/api/rescue/telemetry", tags=["rescue-telemetry"])


def _header_map(request: Request) -> dict[str, str]:
    return {k: v for k, v in request.headers.items()}


@router.get("/health")
async def rescue_telemetry_health() -> dict[str, Any]:
    """Health for rescue telemetry ingest — not gated by dev-dashboard profile."""
    return build_health_payload()


@router.post("/v1/ingest")
async def rescue_telemetry_ingest_v1(request: Request) -> JSONResponse:
    """Accept Windows rescue inspect telemetry when RESCUE_TELEMETRY_INGEST_ENABLED=1."""
    raw = await request.body()
    try:
        payload = json.loads(raw.decode("utf-8") if raw else "{}")
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JSONResponse(
            status_code=422,
            content={"status": "error", "code": "TELEMETRY-SCHEMA-001", "message": "Invalid JSON body."},
        )
    if not isinstance(payload, dict):
        return JSONResponse(
            status_code=422,
            content={"status": "error", "code": "TELEMETRY-SCHEMA-001", "message": "Payload must be a JSON object."},
        )

    result = process_telemetry_ingest(payload, headers=_header_map(request), body_bytes=raw)
    return JSONResponse(status_code=int(result["http_status"]), content=result["body"])
