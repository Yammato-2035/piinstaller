"""
Control Center readonly router — safe GET routes for Development Cockpit (Phase E.10).

Delegates to core facades/services only. No BACKUP_JOBS, no execute, no POST.
"""

from __future__ import annotations

from fastapi import APIRouter, Query

from core.dcc_status_facade import (
    build_dcc_control_center_summary_api,
    build_dcc_cursor_meta_prompt_api,
    build_dcc_project_overview_body,
    build_dcc_prompt_findings_api,
    build_dcc_roadmap_api_bundle,
)
from core.packaging_readiness_state import build_packaging_readiness_state
from core.update_check import build_update_status

router = APIRouter(tags=["control-center-readonly"])


@router.get("/api/dev-dashboard/control-center-summary")
async def dev_dashboard_control_center_summary():
    """Read-only: Control Center Übersicht (Runtime, Roadmap, Dev-Server, Doku, Diagnostik)."""
    from app import logger

    try:
        return build_dcc_control_center_summary_api()
    except Exception:
        logger.exception("dev_dashboard_control_center_summary failed")
        raise


@router.get("/api/dev-dashboard/roadmap")
async def dev_dashboard_roadmap(
    frontend_build_version: str | None = Query(default=None),
    frontend_runtime_source: str | None = Query(default=None),
):
    fe_ver = (frontend_build_version or "").strip() or None
    return build_dcc_roadmap_api_bundle(
        include_dashboard_context=True,
        running_jobs=[],
        package_activity=[],
        frontend_build_version=fe_ver,
        frontend_runtime_source=frontend_runtime_source,
    )


@router.get("/api/dev-dashboard/update/status")
async def dev_dashboard_update_status():
    from app import logger

    try:
        body = build_update_status()
        return {"code": "DEV_DASHBOARD_UPDATE_STATUS_OK", **body}
    except Exception:
        logger.exception("dev_dashboard_update_status failed")
        raise


@router.get("/api/dev-dashboard/packaging/readiness")
async def dev_dashboard_packaging_readiness():
    from app import logger

    try:
        body = build_packaging_readiness_state()
        return {"code": "DEV_DASHBOARD_PACKAGING_READINESS_OK", **body}
    except Exception:
        logger.exception("dev_dashboard_packaging_readiness failed")
        raise


@router.get("/api/dev-dashboard/project-overview")
async def dev_dashboard_project_overview():
    from app import logger

    try:
        body = build_dcc_project_overview_body()
        return {"code": "DEV_DASHBOARD_PROJECT_OVERVIEW_OK", **body}
    except Exception:
        logger.exception("dev_dashboard_project_overview failed")
        raise


@router.get("/api/dev-dashboard/prompt-findings")
async def dev_dashboard_prompt_findings(
    frontend_build_version: str | None = Query(default=None),
    frontend_runtime_source: str | None = Query(default=None),
):
    return build_dcc_prompt_findings_api(
        frontend_build_version=frontend_build_version,
        frontend_runtime_source=frontend_runtime_source,
    )


@router.get("/api/dev-dashboard/cursor-meta-prompt")
async def dev_dashboard_cursor_meta_prompt(
    frontend_build_version: str | None = Query(default=None),
    frontend_runtime_source: str | None = Query(default=None),
):
    return build_dcc_cursor_meta_prompt_api(
        frontend_build_version=frontend_build_version,
        frontend_runtime_source=frontend_runtime_source,
    )
