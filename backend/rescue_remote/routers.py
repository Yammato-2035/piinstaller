"""Rescue remote control API — local_lab phase 1, allowlisted runbooks only."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query

from rescue_remote.schemas import (
    AgentDisconnectRequest,
    AgentHeartbeatRequest,
    AgentRegisterRequest,
    JobCreateRequest,
    JobResultRequest,
)
from rescue_remote.service import (
    RescueRemoteError,
    allowlisted_runbook_ids,
    claim_job,
    create_job,
    disconnect_agent,
    get_agent,
    get_agent_logs,
    heartbeat_agent,
    list_agents,
    list_jobs,
    register_agent,
    rescue_remote_enabled,
    submit_job_result,
)

router = APIRouter(prefix="/api/rescue-remote", tags=["rescue-remote"])


def _disabled() -> HTTPException:
    return HTTPException(
        status_code=403,
        detail={"code": "RESCUE_REMOTE_DISABLED", "errors": ["rescue_remote_disabled"]},
    )


def _handle(exc: RescueRemoteError) -> HTTPException:
    return HTTPException(
        status_code=exc.http_status,
        detail={"code": exc.code, "errors": exc.errors},
    )


def _guard() -> None:
    if not rescue_remote_enabled():
        raise _disabled()
    for fragment in ("/shell", "/execute", "/arbitrary", "/ssh"):
        pass  # no such routes registered


@router.post("/register")
async def api_register(body: AgentRegisterRequest) -> dict[str, Any]:
    _guard()
    try:
        agent = register_agent(body.model_dump())
    except RescueRemoteError as exc:
        raise _handle(exc) from exc
    return {"code": "RESCUE_REMOTE_AGENT_REGISTERED", "agent": agent}


@router.post("/heartbeat")
async def api_heartbeat(body: AgentHeartbeatRequest) -> dict[str, Any]:
    _guard()
    try:
        agent = heartbeat_agent(body.model_dump())
    except RescueRemoteError as exc:
        raise _handle(exc) from exc
    return {"code": "RESCUE_REMOTE_HEARTBEAT_OK", "agent": agent}


@router.get("/agents")
async def api_list_agents() -> dict[str, Any]:
    _guard()
    agents = list_agents()
    return {"code": "RESCUE_REMOTE_AGENTS_OK", "agents": agents, "count": len(agents)}


@router.get("/agents/{agent_id}")
async def api_get_agent(agent_id: str) -> dict[str, Any]:
    _guard()
    try:
        agent = get_agent(agent_id)
    except RescueRemoteError as exc:
        raise _handle(exc) from exc
    return {"code": "RESCUE_REMOTE_AGENT_OK", "agent": agent}


@router.get("/jobs")
async def api_list_jobs(agent_id: str | None = Query(default=None)) -> dict[str, Any]:
    _guard()
    jobs = list_jobs(agent_id=agent_id)
    return {
        "code": "RESCUE_REMOTE_JOBS_OK",
        "jobs": jobs,
        "allowlisted_runbooks": allowlisted_runbook_ids(),
    }


@router.post("/jobs")
async def api_create_job(body: JobCreateRequest) -> dict[str, Any]:
    _guard()
    try:
        job = create_job(body.model_dump())
    except RescueRemoteError as exc:
        raise _handle(exc) from exc
    return {"code": "RESCUE_REMOTE_JOB_CREATED", "job": job}


@router.post("/jobs/{job_id}/claim")
async def api_claim_job(job_id: str, agent_id: str = Query(...)) -> dict[str, Any]:
    _guard()
    try:
        job = claim_job(job_id, agent_id)
    except RescueRemoteError as exc:
        raise _handle(exc) from exc
    return {"code": "RESCUE_REMOTE_JOB_CLAIMED", "job": job}


@router.post("/jobs/{job_id}/result")
async def api_job_result(job_id: str, body: JobResultRequest) -> dict[str, Any]:
    _guard()
    try:
        job = submit_job_result(job_id, body.model_dump())
    except RescueRemoteError as exc:
        raise _handle(exc) from exc
    return {"code": "RESCUE_REMOTE_JOB_RESULT_ACCEPTED", "job": job}


@router.get("/logs/{agent_id}")
async def api_agent_logs(agent_id: str) -> dict[str, Any]:
    _guard()
    try:
        get_agent(agent_id)
    except RescueRemoteError as exc:
        raise _handle(exc) from exc
    logs = get_agent_logs(agent_id)
    return {"code": "RESCUE_REMOTE_LOGS_OK", "logs": logs}


@router.post("/disconnect")
async def api_disconnect(body: AgentDisconnectRequest) -> dict[str, Any]:
    _guard()
    try:
        agent = disconnect_agent(body.model_dump())
    except RescueRemoteError as exc:
        raise _handle(exc) from exc
    return {"code": "RESCUE_REMOTE_AGENT_DISCONNECTED", "agent": agent}
