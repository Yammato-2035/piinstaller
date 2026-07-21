"""
Read-only Dev-Dashboard index routes (Phase E.4, extended E.8).

Delegates to core.dev_dashboard* / core.dcc_status_facade — no new file scanners, no shell commands.
"""

from __future__ import annotations

from fastapi import APIRouter, Query, Request
from fastapi.responses import JSONResponse

router = APIRouter(tags=["dev-dashboard-readonly"])


@router.get("/api/dev-dashboard/rescue-bvr-status")
async def dev_dashboard_rescue_bvr_status(request: Request):
    """Read-only: Rescue Stick BVR/GUI/i18n/drift status for PI-RS-BVR-GUI-DCC-001."""
    from pathlib import Path

    from core.rescue_bvr_dcc_status import build_rescue_bvr_dcc_status
    from core.version_commit_drift import build_version_drift_matrix

    repo = Path(__file__).resolve().parents[3]
    workspace_commit = ""
    workspace_branch = ""
    origin_main = ""
    try:
        import subprocess

        workspace_commit = (
            subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()
        )
        workspace_branch = (
            subprocess.check_output(
                ["git", "branch", "--show-current"], cwd=repo, text=True
            ).strip()
        )
        origin_main = (
            subprocess.check_output(
                ["git", "rev-parse", "origin/main"], cwd=repo, text=True
            ).strip()
        )
    except Exception:
        pass

    payload_meta = {}
    project_version = ""
    try:
        import json

        payload_meta = json.loads(
            (repo / "config/rescue_payload_version.json").read_text(encoding="utf-8")
        )
        project_version = str(
            json.loads((repo / "config/version.json").read_text(encoding="utf-8")).get(
                "project_version"
            )
            or ""
        )
    except Exception:
        pass

    drift = build_version_drift_matrix(
        workspace_version=project_version,
        workspace_commit=workspace_commit,
        runtime_version="",
        runtime_commit="",
        api_version=project_version,
        frontend_version=project_version,
        payload_version=str(payload_meta.get("rescue_payload_version") or ""),
        payload_commit=workspace_commit,
        payload_sha256="",
        usb_payload_version="",
        usb_payload_sha256="",
        origin_main_commit=origin_main,
        feature_commit=workspace_commit,
    )
    status = build_rescue_bvr_dcc_status(
        repo_root=repo,
        workspace_branch=workspace_branch,
        workspace_commit=workspace_commit,
        origin_main_commit=origin_main,
        payload_version=str(payload_meta.get("rescue_payload_version") or ""),
        payload_build_commit=workspace_commit,
        version_drift_status=str(drift.get("overall_status") or "unknown"),
        deploy_drift_status="unknown",
    )
    status["version_drift_matrix"] = drift
    return status


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


@router.get("/api/dev-dashboard/status")
async def dev_dashboard_status(
    request: Request,
    frontend_build_version: str | None = Query(
        default=None,
        description="Optional: Frontend-Build-Version (__APP_VERSION__), fuer Runtime-vs-Workspace-Konsistenz.",
    ),
    frontend_runtime_source: str | None = Query(
        default=None,
        description="Optional: dev | build | unknown — steuert frontend_version_matches_backend.",
    ),
):
    """Read-only: Development Cockpit Gesamtstatus (kein Backup/Restore)."""
    from app import logger
    from core.dcc_status_facade import build_dcc_dashboard_status_api

    headers = {k: v for k, v in request.headers.items()}
    try:
        return await build_dcc_dashboard_status_api(
            request_headers=headers,
            frontend_build_version=frontend_build_version,
            frontend_runtime_source=frontend_runtime_source,
        )
    except Exception:
        logger.exception("dev_dashboard_status failed")
        raise


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


@router.get("/api/dev-dashboard/products")
async def dev_dashboard_products(
    request: Request,
    visibility: str | None = Query(default=None),
    category: str | None = Query(default=None),
    product_id: str | None = Query(default=None),
):
    """Read-only: product registry from docs/dev-dashboard/products (no secrets)."""
    from core.dev_dashboard_status_service import build_dcc_profile_block_response
    from core.product_registry_contract import build_products_api_response

    headers = {k: v for k, v in request.headers.items()}
    blocked = build_dcc_profile_block_response(
        request_headers=headers,
        path="/api/dev-dashboard/products",
    )
    if blocked:
        return JSONResponse(status_code=404, content=blocked)
    return build_products_api_response(
        visibility=visibility,
        category=category,
        product_id=product_id,
    )
