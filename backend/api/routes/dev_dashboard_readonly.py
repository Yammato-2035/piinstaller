"""
Read-only Dev-Dashboard index routes (Phase E.4, extended E.8).

Delegates to core.dev_dashboard* / core.dcc_status_facade — no new file scanners, no shell commands.
"""

from __future__ import annotations

from fastapi import APIRouter, Query, Request
from fastapi.responses import JSONResponse

router = APIRouter(tags=["dev-dashboard-readonly"])


@router.get("/api/dev-dashboard/modules")
async def dev_dashboard_modules():
    from core import dev_dashboard as dev_dashboard_core

    return dev_dashboard_core.build_modules_list()


@router.get("/api/dev-dashboard/modules/{module_id}")
async def dev_dashboard_module_detail(module_id: str):
    from core import dev_dashboard as dev_dashboard_core

    return dev_dashboard_core.build_module_detail(module_id)


@router.get("/api/dev-dashboard/evidence-index")
async def dev_dashboard_evidence_index():
    from core.dcc_status_facade import build_dcc_evidence_index_api

    return build_dcc_evidence_index_api()


@router.get("/api/dev-dashboard/manual-command-runs")
async def dev_dashboard_manual_command_runs(
    limit: int = Query(default=5, ge=1, le=50),
):
    """Read-only: strukturierte manuelle Kommandoläufe aus Evidence-JSON (keine Shell-Ausführung)."""
    from core.dev_dashboard_manual_command_runs import build_manual_command_runs_index

    return build_manual_command_runs_index(max_runs=limit)


@router.get("/api/dev-dashboard/recent-evidence")
async def dev_dashboard_recent_evidence(
    limit: int = Query(default=5, ge=1, le=50),
    category: str | None = Query(default=None),
    status: str | None = Query(default=None),
    search: str | None = Query(default=None),
    time_range: str | None = Query(default="all"),
):
    """Read-only: neueste Repo-Evidence-Berichte und Testläufe (kein Shell, kein Execute)."""
    from core.dev_dashboard_recent_evidence import build_recent_evidence_feed

    return build_recent_evidence_feed(
        limit=limit,
        category=category,
        status=status,
        search=search,
        time_range=time_range,
    )


@router.get("/api/dev-dashboard/backend-health")
async def dev_dashboard_backend_health(
    request: Request,
    history_limit: int = Query(default=20, ge=0, le=20),
    stale_after_seconds: int = Query(default=180, ge=30, le=3600),
):
    """Read-only: externer Developer-Healthcheck aus Evidence-JSON (kein Probe aus dem Backend)."""
    from core.dcc_status_facade import build_dcc_backend_health_api
    from core.dev_dashboard_status_service import build_dcc_profile_block_response

    headers = {k: v for k, v in request.headers.items()}
    blocked = build_dcc_profile_block_response(
        request_headers=headers,
        path="/api/dev-dashboard/backend-health",
    )
    if blocked:
        return JSONResponse(status_code=404, content=blocked)
    return build_dcc_backend_health_api(
        stale_after_seconds=stale_after_seconds,
        history_limit=history_limit,
    )


@router.get("/api/dev-dashboard/notifications/status")
async def dev_dashboard_notifications_status():
    from app import logger
    from core.dcc_status_facade import build_dcc_notifications_status_api

    try:
        return build_dcc_notifications_status_api()
    except Exception:
        logger.exception("dev_dashboard_notifications_status failed")
        raise


@router.get("/api/dev-dashboard/notifications/events")
async def dev_dashboard_notifications_events(limit: int = 50):
    from app import logger
    from core.dcc_status_facade import build_dcc_notifications_events_api

    try:
        return build_dcc_notifications_events_api(limit=limit)
    except Exception:
        logger.exception("dev_dashboard_notifications_events failed")
        raise
