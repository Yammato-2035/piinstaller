"""
Rescue backup / restore routes (plan + gated execute).

Wipe / linux-install remain unavailable. System-disk restore requires one-shot control.
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


@router.post("/backup/execute")
async def rescue_backup_execute_route(body: dict[str, Any] = Body(...)):
    return await backup_handlers.post_windows_backup_execute(body)


@router.post("/backup/verify")
async def rescue_backup_verify_route(body: dict[str, Any] = Body(...)):
    return await backup_handlers.post_windows_backup_verify(body)


@router.post("/restore/preview-preflight")
async def rescue_restore_preview_preflight_route(body: dict[str, Any] = Body(...)):
    return await restore_handlers.post_restore_preview_preflight(body)


@router.post("/restore/system-disk/preview")
async def rescue_system_disk_restore_preview_route(body: dict[str, Any] = Body(...)):
    return await backup_handlers.post_system_disk_restore_preview(body)


@router.post("/restore/system-disk/execute")
async def rescue_system_disk_restore_execute_route(body: dict[str, Any] = Body(...)):
    return await backup_handlers.post_system_disk_restore_execute(body)
