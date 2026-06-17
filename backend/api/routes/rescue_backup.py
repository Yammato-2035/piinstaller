"""
Rescue backup / restore-preview plan-only routes (RS-F2S).

No execute, wipe, linux-install, or credential endpoints.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Body

from api.handlers import rescue_backup_handlers as backup_handlers
from api.handlers import rescue_restore_preview_handlers as restore_handlers

router = APIRouter(tags=["rescue-backup"])


@router.get("/capabilities")
async def rescue_capabilities_route():
    return await backup_handlers.get_rescue_capabilities()


@router.get("/storage/discovery")
async def rescue_storage_discovery_route():
    return await backup_handlers.get_storage_discovery()


@router.get("/cloud-target/status")
async def rescue_cloud_target_status_route():
    return await backup_handlers.get_cloud_target_local_status()


@router.post("/cloud-target/local-config")
async def rescue_cloud_target_local_config_route(body: dict[str, Any] = Body(...)):
    return await backup_handlers.post_cloud_target_local(body)


@router.post("/backup/preflight")
async def rescue_backup_preflight_route(body: dict[str, Any] = Body(...)):
    return await backup_handlers.post_backup_preflight(body)


@router.get("/system/summary")
async def rescue_system_summary_route():
    return await backup_handlers.get_system_summary()


@router.post("/backup/plan")
async def rescue_backup_plan_route(body: dict[str, Any] = Body(...)):
    return await backup_handlers.post_backup_plan(body)


@router.post("/backup/full-plan")
async def rescue_full_backup_plan_route(body: dict[str, Any] = Body(...)):
    return await backup_handlers.post_full_backup_plan(body)


@router.post("/restore/preview-preflight")
async def rescue_restore_preview_preflight_route(body: dict[str, Any] = Body(...)):
    return await restore_handlers.post_restore_preview_preflight(body)
