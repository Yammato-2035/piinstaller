"""
Rescue-Read-only-Analyse API.

GET /api/rescue/analyze — strukturierter Befund ohne Schreibzugriff auf Zielmedien.
POST /api/rescue/restore-dryrun — Restore-Simulation ohne produktives Ziel.
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends

from core.auth import SessionContext, get_optional_session
from models.diagnosis import (
    RescueAnalyzeResponse,
    RescueRestoreRequest,
    RescueRestoreResponse,
    RestoreDryRunRequest,
    RestoreDryRunResponse,
)
from modules.rescue_readonly_analyze import run_rescue_readonly_analysis
from modules.rescue_restore_dryrun import run_restore_dryrun_pipeline
from modules.rescue_restore_gate import load_dry_run_grant
from modules.rescue_restore_execute import RESTORE_LOG_PATH, run_rescue_restore

router = APIRouter(prefix="/api/rescue", tags=["rescue"])


@router.get("/analyze", response_model=RescueAnalyzeResponse)
async def get_rescue_analyze() -> RescueAnalyzeResponse:
    return run_rescue_readonly_analysis()


@router.post("/restore-dryrun", response_model=RestoreDryRunResponse)
async def post_rescue_restore_dryrun(
    body: RestoreDryRunRequest,
    session: Optional[SessionContext] = Depends(get_optional_session),
) -> RestoreDryRunResponse:
    auth_sid = session.session_id if session else None
    return run_restore_dryrun_pipeline(body, auth_session_id=auth_sid)


@router.post("/restore", response_model=RescueRestoreResponse)
async def post_rescue_restore(
    body: RescueRestoreRequest,
    session: Optional[SessionContext] = Depends(get_optional_session),
) -> RescueRestoreResponse:
    grant = load_dry_run_grant(body.dry_run_token)
    if (
        session is not None
        and grant
        and grant.get("session_source") == "remote_db"
        and str(grant.get("session_id") or "") != str(session.session_id)
    ):
        return RescueRestoreResponse(
            status="error",
            result="RESTORE_BLOCKED",
            warnings=[],
            log_path=str(RESTORE_LOG_PATH),
            bootable=False,
            codes=["rescue.restore.session_invalid", "rescue.hardstop.session_invalid"],
        )
    return run_rescue_restore(body)
