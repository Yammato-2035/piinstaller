"""
PI-RS-TEL-001 — dev/lab-only Rescue Stick lab telemetry send preview API.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from core.install_profile import get_install_profile_state
from core.rescue_lab_telemetry_config import load_rescue_lab_telemetry_config
from core.rescue_lab_telemetry_client import send_rescue_lab_telemetry
from core.rescue_lab_telemetry_model import build_synthetic_rescue_lab_payload
from core.rescue_lab_telemetry_status import build_rescue_lab_telemetry_dashboard_status

router = APIRouter(prefix="/api/rescue/telemetry/lab", tags=["rescue-lab-telemetry"])

_LAB_PROFILES = frozenset({"developer", "local_lab", "rescue_lab"})


def _lab_profile_allowed() -> bool:
    state = get_install_profile_state()
    return state.install_profile in _LAB_PROFILES


def _feature_disabled_response() -> JSONResponse:
    return JSONResponse(
        status_code=403,
        content={
            "code": "RESCUE_LAB_TELEMETRY_BLOCKED",
            "result": None,
            "warnings": [],
            "errors": ["feature_disabled:rescue_lab_telemetry_send_preview_requires_lab_profile"],
        },
    )


def _map_result_code(status: str) -> str:
    if status == "accepted_rescue_lab_telemetry":
        return "RESCUE_LAB_TELEMETRY_ACCEPTED"
    if status.startswith("blocked"):
        return "RESCUE_LAB_TELEMETRY_BLOCKED"
    if status in {"rejected_auth", "rejected_product_source_or_environment", "replay_nonce"}:
        return "RESCUE_LAB_TELEMETRY_REJECTED"
    return "RESCUE_LAB_TELEMETRY_UNAVAILABLE"


@router.get("/status")
async def rescue_lab_telemetry_status() -> dict[str, Any]:
    if not _lab_profile_allowed():
        return {"feature_enabled": False, "production_ready": False, "reason": "feature_disabled"}
    return {"feature_enabled": True, **build_rescue_lab_telemetry_dashboard_status()}


@router.post("/send-preview")
async def rescue_lab_telemetry_send_preview() -> JSONResponse:
    if not _lab_profile_allowed():
        return _feature_disabled_response()

    payload_obj = build_synthetic_rescue_lab_payload()
    payload = payload_obj.to_dict()
    config = load_rescue_lab_telemetry_config()
    result = send_rescue_lab_telemetry(config, payload)
    code = _map_result_code(result.status)
    http_status = 200 if code != "RESCUE_LAB_TELEMETRY_BLOCKED" else 200
    if result.status == "blocked_missing_secret":
        http_status = 200
    return JSONResponse(
        status_code=http_status,
        content={
            "code": code,
            "result": {
                "client_id": result.client_id,
                "product": result.product,
                "source": result.source,
                "environment": result.environment,
                "payload_kind": result.payload_kind,
                "http_status": result.http_status,
                "server_status": result.server_status,
                "nonce_status": result.nonce_status,
                "sent_at": result.sent_at,
                "production_ready": False,
            },
            "warnings": result.warnings,
            "errors": result.errors,
        },
    )
