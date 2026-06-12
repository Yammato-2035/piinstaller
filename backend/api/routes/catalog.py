"""
Static catalog routes (Phase E.3).

Read-only metadata — no system calls.
"""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(tags=["catalog"])


@router.get("/api/apps")
async def get_apps():
    """Liste der verfügbaren Apps (App Store Katalog)."""
    from app import APPS_CATALOG

    return {"apps": APPS_CATALOG}
