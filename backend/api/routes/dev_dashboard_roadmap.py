"""
Read-only Dev-Dashboard roadmap registry routes (Phase E.5).

Delegates to core.dev_dashboard_roadmap — no DCC dashboard aggregation, no new parsers.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from core.dev_dashboard_roadmap import load_roadmap_registry_bundle

router = APIRouter(tags=["dev-dashboard-roadmap"])


def _roadmap_readonly_base(bundle: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": bundle.get("status"),
        "read_only": True,
        "execution_allowed": False,
        "warnings": bundle.get("warnings") or [],
    }


@router.get("/api/dev-dashboard/roadmap/areas")
async def dev_dashboard_roadmap_areas():
    bundle = load_roadmap_registry_bundle()
    return {**_roadmap_readonly_base(bundle), "areas": bundle.get("areas") or []}


@router.get("/api/dev-dashboard/roadmap/milestones")
async def dev_dashboard_roadmap_milestones():
    bundle = load_roadmap_registry_bundle()
    return {**_roadmap_readonly_base(bundle), "milestones": bundle.get("milestones") or []}


@router.get("/api/dev-dashboard/roadmap/blockers")
async def dev_dashboard_roadmap_blockers():
    bundle = load_roadmap_registry_bundle()
    return {**_roadmap_readonly_base(bundle), "blockers": bundle.get("blockers") or []}


@router.get("/api/dev-dashboard/roadmap/decisions")
async def dev_dashboard_roadmap_decisions():
    bundle = load_roadmap_registry_bundle()
    return {**_roadmap_readonly_base(bundle), "decisions": bundle.get("decisions") or []}


@router.get("/api/dev-dashboard/roadmap/next-prompt")
async def dev_dashboard_roadmap_next_prompt():
    bundle = load_roadmap_registry_bundle()
    return {
        **_roadmap_readonly_base(bundle),
        "prompt": bundle.get("recommended_prompt"),
    }
