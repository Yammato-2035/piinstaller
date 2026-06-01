"""Read-only Fleet-Session-API + host-local state writes (no control actions)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query

from core.fleet_session_state import (
    FleetSessionError,
    assert_fleet_write_allowed,
    assert_no_forbidden_routes,
    build_fleet_session_summary,
    create_fleet_session,
    detect_stale_sessions,
    finish_fleet_session,
    fleet_sessions_enabled,
    get_fleet_session,
    heartbeat_fleet_session,
    list_fleet_sessions,
    update_fleet_session,
)
from fleet.schemas import FleetSessionFinishBody, FleetSessionPatchBody, FleetSessionWriteBody

router = APIRouter(prefix="/api/fleet", tags=["fleet-sessions"])


def _fleet_disabled_response() -> dict[str, Any]:
    return {
        "code": "FLEET_SESSION_DISABLED",
        "enabled": False,
        "sessions": [],
        "count": 0,
    }


def _handle_error(exc: FleetSessionError) -> HTTPException:
    status = 404 if exc.code == "FLEET_SESSION_NOT_FOUND" else 400
    return HTTPException(
        status_code=status,
        detail={"code": exc.code, "errors": exc.errors},
    )


@router.get("/sessions")
async def fleet_list_sessions(
    limit: int = Query(default=50, ge=1, le=200),
    include_finished: bool = Query(default=True),
) -> dict[str, Any]:
    assert_no_forbidden_routes("/sessions")
    if not fleet_sessions_enabled():
        return _fleet_disabled_response() | {"code": "FLEET_SESSION_LIST_OK"}
    detect_stale_sessions()
    return list_fleet_sessions(limit=limit, include_finished=include_finished)


@router.get("/sessions/summary")
async def fleet_sessions_summary() -> dict[str, Any]:
    assert_no_forbidden_routes("/sessions/summary")
    if not fleet_sessions_enabled():
        return _fleet_disabled_response() | build_fleet_session_summary()
    detect_stale_sessions()
    return build_fleet_session_summary()


@router.get("/sessions/{session_id}")
async def fleet_get_session(session_id: str) -> dict[str, Any]:
    assert_no_forbidden_routes(f"/sessions/{session_id}")
    if not fleet_sessions_enabled():
        raise HTTPException(status_code=403, detail={"code": "FLEET_SESSION_DISABLED"})
    try:
        return get_fleet_session(session_id)
    except FleetSessionError as exc:
        raise _handle_error(exc) from exc


@router.post("/sessions")
async def fleet_create_session(body: FleetSessionWriteBody) -> dict[str, Any]:
    assert_no_forbidden_routes("/sessions")
    try:
        assert_fleet_write_allowed()
        return create_fleet_session(body.model_dump(exclude_none=True))
    except FleetSessionError as exc:
        raise _handle_error(exc) from exc


@router.post("/sessions/{session_id}/heartbeat")
async def fleet_session_heartbeat(session_id: str, body: FleetSessionPatchBody | None = None) -> dict[str, Any]:
    assert_no_forbidden_routes(f"/sessions/{session_id}/heartbeat")
    try:
        assert_fleet_write_allowed()
        patch = body.model_dump(exclude_none=True) if body else None
        return heartbeat_fleet_session(session_id, patch)
    except FleetSessionError as exc:
        raise _handle_error(exc) from exc


@router.post("/sessions/{session_id}/finish")
async def fleet_session_finish(session_id: str, body: FleetSessionFinishBody) -> dict[str, Any]:
    assert_no_forbidden_routes(f"/sessions/{session_id}/finish")
    try:
        assert_fleet_write_allowed()
        patch = body.model_dump(exclude_none=True)
        exit_code = patch.pop("qemu_exit_code", None)
        if exit_code is not None:
            patch.setdefault("qemu", {})["exit_code"] = exit_code
        return finish_fleet_session(session_id, body.status, patch)
    except FleetSessionError as exc:
        raise _handle_error(exc) from exc
