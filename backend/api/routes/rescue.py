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

try:
    from api.routes.data_rescue import router as data_rescue_router
    from api.routes.linux_migration import router as linux_migration_router
    from api.routes.rescue_backup import router as rescue_backup_plan_router
    from api.routes.rescue_evidence import router as rescue_evidence_plan_router
    from api.routes.rescue_network import build_live_boot_status, router as rescue_network_router
    from api.routes.rescue_ui import router as rescue_ui_router
except ImportError:
    data_rescue_router = None
    linux_migration_router = None
    rescue_backup_plan_router = None
    rescue_evidence_plan_router = None
    rescue_network_router = None
    rescue_ui_router = None
    build_live_boot_status = None

router = APIRouter(prefix="/api/rescue", tags=["rescue"])


@router.get("/analyze", response_model=RescueAnalyzeResponse)
async def get_rescue_analyze() -> RescueAnalyzeResponse:
    return run_rescue_readonly_analysis()


@router.get("/boot-status")
async def get_rescue_boot_status() -> dict:
    if build_live_boot_status is None:
        from rescue.rescue_state import build_rescue_state_snapshot

        return {"boot_status": build_rescue_state_snapshot(ui_status="ready")["boot_status"]}
    return {"boot_status": build_live_boot_status()}


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


if data_rescue_router is not None:
    router.include_router(data_rescue_router)
if linux_migration_router is not None:
    router.include_router(linux_migration_router)
if rescue_backup_plan_router is not None:
    router.include_router(rescue_backup_plan_router)
if rescue_evidence_plan_router is not None:
    router.include_router(rescue_evidence_plan_router)
if rescue_network_router is not None:
    router.include_router(rescue_network_router)
if rescue_ui_router is not None:
    router.include_router(rescue_ui_router)
