from __future__ import annotations

import secrets
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from core.install_profile import get_install_profile_state
from rescue_agent.crypto_envelope import build_encrypted_envelope
from rescue_agent.discovery import discover_devserver
from rescue_agent.nftables_policy import build_nftables_policy_preview
from rescue_agent.registration import build_pairing_response
from rescue_agent.system_report import build_rescue_system_report

UTC = timezone.utc
router = APIRouter(prefix="/api/rescue-agent", tags=["rescue-agent"])
_SESSIONS: dict[str, dict[str, Any]] = {}


class RegisterBody(BaseModel):
    agent_kind: str = "rescue_stick"
    agent_version: str = "0.1.0-stub"
    boot_id: str = "boot-stub"
    public_key: str = "stub-public-key"
    capabilities: list[str] = Field(default_factory=lambda: ["system_report", "heartbeat"])
    operator_label: str | None = None


class HeartbeatBody(BaseModel):
    session_id: str
    agent_state: str = "alive"
    telemetry: dict[str, Any] = Field(default_factory=dict)


class SystemReportBody(BaseModel):
    session_id: str
    agent_id: str
    encrypted_envelope: dict[str, Any] | None = None
    test_mode_allow_unencrypted: bool = False


def _ensure_profile_allows_registration() -> None:
    state = get_install_profile_state()
    if state.install_profile in {"release", "production"}:
        raise HTTPException(status_code=403, detail={"code": "RESCUE_AGENT_REGISTRATION_DISABLED_IN_RELEASE"})


def _require_valid_session(session_id: str) -> dict[str, Any]:
    session = _SESSIONS.get(session_id)
    if not session:
        raise HTTPException(status_code=403, detail={"code": "RESCUE_AGENT_INVALID_SESSION"})
    return session


@router.post("/discovery/preview")
async def preview_discovery() -> dict[str, Any]:
    state = get_install_profile_state()
    result = discover_devserver(
        profile=state.install_profile,
        rescue_mode_enabled=state.install_profile in {"local_lab", "rescue_lab", "developer"},
        mdns_endpoint="http://setuphelfer-dev.local:8000",
    )
    nft = build_nftables_policy_preview(
        discovery_phase=True,
        validated_endpoint=result.get("discovery_status") == "found",
    )
    return {"code": "RESCUE_AGENT_DISCOVERY_PREVIEW_OK", "discovery": result, "nftables_preview": nft}


@router.post("/register")
async def rescue_agent_register(body: RegisterBody) -> dict[str, Any]:
    _ensure_profile_allows_registration()
    session_id = f"rescue-{secrets.token_hex(4)}"
    agent_id = f"ra-{secrets.token_hex(6)}"
    response = build_pairing_response(
        profile=get_install_profile_state().install_profile,
        rescue_pairing_enabled=True,
        session_id=session_id,
        server_public_key="server-public-key-stub",
    )
    _SESSIONS[session_id] = {
        "session_id": session_id,
        "agent_id": agent_id,
        "registration_status": response["registration_status"],
        "last_heartbeat_at": None,
        "agent_state": "booting",
        "report_received": False,
        "operator_label": body.operator_label or "",
    }
    return {"code": "RESCUE_AGENT_REGISTER_OK", "agent_id": agent_id, **response}


@router.post("/heartbeat")
async def rescue_agent_heartbeat(body: HeartbeatBody) -> dict[str, Any]:
    session = _require_valid_session(body.session_id)
    session["last_heartbeat_at"] = datetime.now(tz=UTC).replace(microsecond=0).isoformat()
    session["agent_state"] = body.agent_state
    session["telemetry"] = body.telemetry
    return {"code": "RESCUE_AGENT_HEARTBEAT_OK", "session": session}


@router.post("/system-report")
async def rescue_agent_system_report(body: SystemReportBody) -> dict[str, Any]:
    session = _require_valid_session(body.session_id)
    if not body.encrypted_envelope and not body.test_mode_allow_unencrypted:
        raise HTTPException(status_code=400, detail={"code": "RESCUE_AGENT_E2EE_REQUIRED"})
    if body.encrypted_envelope is None:
        report = build_rescue_system_report(
            agent_id=body.agent_id,
            session_id=body.session_id,
            discovery_result={"discovery_status": "not_found", "endpoint_hash": ""},
            e2ee_status="contract_stub",
        )
        envelope = build_encrypted_envelope(
            plaintext_report=report,
            session_id=body.session_id,
            agent_id=body.agent_id,
            sender_public_key="agent-public-key-stub",
            recipient_key_id="server-key-1",
            created_at=report["created_at"],
        )
    else:
        envelope = body.encrypted_envelope
    session["report_received"] = True
    session["last_report_encrypted"] = True
    return {"code": "RESCUE_AGENT_REPORT_ACCEPTED", "session_id": body.session_id, "envelope": envelope}


@router.get("/sessions")
async def rescue_agent_sessions() -> dict[str, Any]:
    return {"code": "RESCUE_AGENT_SESSIONS_OK", "sessions": list(_SESSIONS.values()), "count": len(_SESSIONS)}


@router.get("/sessions/{session_id}")
async def rescue_agent_session(session_id: str) -> dict[str, Any]:
    session = _require_valid_session(session_id)
    return {"code": "RESCUE_AGENT_SESSION_OK", "session": session}

