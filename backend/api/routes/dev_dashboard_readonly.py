"""
Read-only Dev-Dashboard index routes (Phase E.4).

Delegates to core.dev_dashboard* — no new file scanners, no shell commands.
"""

from __future__ import annotations

from fastapi import APIRouter, Query

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
    from core import dev_dashboard as dev_dashboard_core

    return dev_dashboard_core.build_evidence_index()


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
