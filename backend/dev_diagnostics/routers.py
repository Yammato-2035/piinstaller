"""Read-only /api/dev-diagnostics/* (local lab, no control actions)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import PlainTextResponse

from core.dev_diagnostic_export import (
    DevDiagnosticExportError,
    build_diagnostic_summary_text,
    build_fleet_session_diagnostic_export,
    build_markdown_diagnostic_report,
    build_qemu_smoke_diagnostic_export,
    collect_evidence_index,
    dev_diagnostics_enabled,
)
from core.fleet_session_state import FORBIDDEN_ROUTE_FRAGMENTS, assert_no_forbidden_routes

router = APIRouter(prefix="/api/dev-diagnostics", tags=["dev-diagnostics"])


def _disabled() -> HTTPException:
    return HTTPException(
        status_code=403,
        detail={"code": "DEV_DIAGNOSTIC_DISABLED", "errors": ["dev_diagnostics_disabled"]},
    )


def _handle_error(exc: DevDiagnosticExportError) -> HTTPException:
    status = 404 if exc.code == "DEV_DIAGNOSTIC_NOT_FOUND" else 400
    return HTTPException(status_code=status, detail={"code": exc.code, "errors": exc.errors})


def _resolve_redacted(
    redacted: bool,
    operator_confirm_unredacted_local_only: bool,
) -> tuple[bool, str | None]:
    if redacted:
        return True, None
    if not operator_confirm_unredacted_local_only:
        return True, "DEV_DIAGNOSTIC_BLOCKED_UNREDACTED_NOT_CONFIRMED"
    return False, None


@router.get("/fleet-sessions/{session_id}/export")
async def export_fleet_session_diagnostics(
    session_id: str,
    redacted: bool = Query(default=True),
    operator_confirm_unredacted_local_only: bool = Query(default=False),
) -> dict[str, Any]:
    assert_no_forbidden_routes(f"/fleet-sessions/{session_id}/export")
    if not dev_diagnostics_enabled():
        raise _disabled()
    use_redacted, block_code = _resolve_redacted(redacted, operator_confirm_unredacted_local_only)
    if block_code:
        return {
            "code": block_code,
            "redacted": True,
            "sharing_warning": "Internal development data. Do not publish.",
        }
    try:
        export = build_fleet_session_diagnostic_export(session_id, redacted=use_redacted)
    except DevDiagnosticExportError as exc:
        raise _handle_error(exc) from exc
    code = "DEV_DIAGNOSTIC_REDACTED" if export.get("redacted") else "DEV_DIAGNOSTIC_EXPORT_OK"
    return {
        "code": code,
        "export": export,
        "summary_text": build_diagnostic_summary_text(export),
    }


@router.get("/qemu-smokes/{run_id}/export")
async def export_qemu_smoke_diagnostics(
    run_id: str,
    redacted: bool = Query(default=True),
    operator_confirm_unredacted_local_only: bool = Query(default=False),
) -> dict[str, Any]:
    assert_no_forbidden_routes(f"/qemu-smokes/{run_id}/export")
    if not dev_diagnostics_enabled():
        raise _disabled()
    use_redacted, block_code = _resolve_redacted(redacted, operator_confirm_unredacted_local_only)
    if block_code:
        return {
            "code": block_code,
            "redacted": True,
            "sharing_warning": "Internal development data. Do not publish.",
        }
    try:
        export = build_qemu_smoke_diagnostic_export(run_id, redacted=use_redacted)
    except DevDiagnosticExportError as exc:
        raise _handle_error(exc) from exc
    code = "DEV_DIAGNOSTIC_REDACTED" if export.get("redacted") else "DEV_DIAGNOSTIC_EXPORT_OK"
    return {
        "code": code,
        "export": export,
        "summary_text": build_diagnostic_summary_text(export),
    }


@router.get("/qemu-smokes/{run_id}/markdown", response_class=PlainTextResponse)
async def export_qemu_smoke_markdown(
    run_id: str,
    redacted: bool = Query(default=True),
    operator_confirm_unredacted_local_only: bool = Query(default=False),
) -> PlainTextResponse:
    assert_no_forbidden_routes(f"/qemu-smokes/{run_id}/markdown")
    if not dev_diagnostics_enabled():
        raise _disabled()
    use_redacted, block_code = _resolve_redacted(redacted, operator_confirm_unredacted_local_only)
    if block_code:
        return PlainTextResponse(
            "# Blocked\n\nUnredacted export requires operator_confirm_unredacted_local_only=true.\n",
            status_code=400,
        )
    try:
        export = build_qemu_smoke_diagnostic_export(run_id, redacted=use_redacted)
    except DevDiagnosticExportError as exc:
        raise _handle_error(exc) from exc
    md = build_markdown_diagnostic_report(export)
    return PlainTextResponse(content=md, media_type="text/markdown; charset=utf-8")


@router.get("/qemu-smokes/{run_id}/evidence-index")
async def export_qemu_evidence_index(run_id: str) -> dict[str, Any]:
    assert_no_forbidden_routes(f"/qemu-smokes/{run_id}/evidence-index")
    if not dev_diagnostics_enabled():
        raise _disabled()
    session_id = f"fleet-{run_id}"
    index = collect_evidence_index(run_id, session_id)
    return {"code": "DEV_DIAGNOSTIC_EVIDENCE_INDEX_OK", "index": index}


@router.get("/latest")
async def export_latest_qemu_diagnostic(
    redacted: bool = Query(default=True),
    operator_confirm_unredacted_local_only: bool = Query(default=False),
) -> dict[str, Any]:
    assert_no_forbidden_routes("/latest")
    if not dev_diagnostics_enabled():
        raise _disabled()
    from core.fleet_session_state import list_fleet_sessions

    listed = list_fleet_sessions(limit=1, include_finished=True)
    sessions = listed.get("sessions") or []
    if not sessions:
        raise HTTPException(
            status_code=404,
            detail={"code": "DEV_DIAGNOSTIC_NOT_FOUND", "errors": ["no_sessions"]},
        )
    run_id = str(sessions[0].get("run_id") or "")
    if not run_id:
        raise HTTPException(
            status_code=404,
            detail={"code": "DEV_DIAGNOSTIC_NOT_FOUND", "errors": ["run_id_missing"]},
        )
    return await export_qemu_smoke_diagnostics(
        run_id,
        redacted=redacted,
        operator_confirm_unredacted_local_only=operator_confirm_unredacted_local_only,
    )
