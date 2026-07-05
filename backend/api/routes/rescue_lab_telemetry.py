"""
PI-RS-TEL-001/002 — dev/lab-only Rescue Stick lab telemetry API.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from core.install_profile import get_install_profile_state
from core.rescue_lab_telemetry_reachability import (
    build_reachability_summary,
    get_last_reachability_summary,
    reachability_gate_code,
)
from core.rescue_lab_telemetry_send_preview_gate import SendPreviewOptions, execute_send_preview
from core.rescue_lab_telemetry_offline_queue_preview import build_offline_queue_preview_summary
from core.rescue_lab_telemetry_status import build_rescue_lab_telemetry_dashboard_status

router = APIRouter(prefix="/api/rescue/telemetry/lab", tags=["rescue-lab-telemetry"])

_LAB_PROFILES = frozenset({"developer", "local_lab", "rescue_lab"})


def _lab_profile_allowed() -> bool:
    state = get_install_profile_state()
    return state.install_profile in _LAB_PROFILES


def _current_profile_name() -> str:
    return get_install_profile_state().install_profile


def _feature_disabled_response(*, endpoint: str) -> JSONResponse:
    return JSONResponse(
        status_code=403,
        content={
            "code": "RESCUE_LAB_TELEMETRY_BLOCKED",
            "result": None,
            "reachability": None,
            "warnings": [],
            "errors": [f"feature_disabled:{endpoint}_requires_lab_profile"],
        },
    )


@router.get("/status")
async def rescue_lab_telemetry_status() -> JSONResponse:
    if not _lab_profile_allowed():
        return _feature_disabled_response(endpoint="rescue_lab_telemetry_status")

    reach = get_last_reachability_summary()
    queue = build_offline_queue_preview_summary()
    dashboard = build_rescue_lab_telemetry_dashboard_status()
    dashboard.update(
        {
            "install_profile": _current_profile_name(),
            "lab_api_enabled": True,
            "network_gate": (reach or {}).get("network_state", "unknown"),
            "telemetry_reachability": (reach or {}).get("telemetry_reachability", "not_checked"),
            "last_reachability_checked_at": (reach or {}).get("checked_at"),
            "offline_queue_preview_count": queue.get("count", 0),
            "offline_queue_preview_latest_reason": queue.get("latest_reason"),
            "auto_replay_enabled": False,
        }
    )
    return JSONResponse(status_code=200, content=dashboard)


@router.get("/reachability")
async def rescue_lab_telemetry_reachability() -> JSONResponse:
    if not _lab_profile_allowed():
        return _feature_disabled_response(endpoint="rescue_lab_telemetry_reachability")

    summary = build_reachability_summary(profile_allowed=True)
    code = reachability_gate_code(summary)
    return JSONResponse(
        status_code=200,
        content={
            "code": code,
            "reachability": summary,
            "warnings": summary.get("warnings") or [],
            "errors": summary.get("errors") or [],
        },
    )


@router.post("/send-preview")
async def rescue_lab_telemetry_send_preview(
    body: dict[str, Any] | None = None,
) -> JSONResponse:
    if not _lab_profile_allowed():
        return _feature_disabled_response(endpoint="rescue_lab_telemetry_send_preview")

    req = body or {}
    options = SendPreviewOptions(
        allow_send_when_reachable=bool(req.get("allow_send_when_reachable", False)),
        create_offline_queue_preview_when_blocked=bool(
            req.get("create_offline_queue_preview_when_blocked", True)
        ),
    )
    result = execute_send_preview(profile_allowed=True, options=options)
    return JSONResponse(status_code=200, content=result)
