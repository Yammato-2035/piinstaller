"""
Backup readonly router — safe GET inventory/status routes (Phase B.2).

No create, restore, or verify POST handlers. Clone disk-info (GET/POST) is read-only.
"""

from __future__ import annotations

from fastapi import APIRouter, Query, Request

from core import backup_readonly_handlers as handlers
from core.backup_target_check_handler import backup_target_check

router = APIRouter(tags=["backup-readonly"])


@router.get("/api/backup/status")
async def backup_status():
    return await handlers.backup_status()


@router.get("/api/backup/settings")
async def backup_get_settings():
    return await handlers.backup_get_settings()


@router.get("/api/backup/jobs")
async def backup_jobs_list():
    return await handlers.backup_jobs_list()


@router.get("/api/backup/jobs/{job_id}")
async def backup_job_status(job_id: str):
    return await handlers.backup_job_status(job_id)


@router.get("/api/backup/jobs/{job_id}/evidence")
async def backup_job_evidence_get(job_id: str):
    return await handlers.backup_job_evidence_get(job_id)


@router.get("/api/backup/cloud/list")
async def backup_cloud_list(rule_id: str = ""):
    return await handlers.backup_cloud_list(rule_id)


@router.get("/api/backup/cloud/quota")
async def backup_cloud_quota():
    return await handlers.backup_cloud_quota()


@router.get("/api/backup/targets")
async def backup_targets():
    return await handlers.backup_targets()


@router.get("/api/backup/external-targets")
async def backup_external_targets_list():
    return await handlers.backup_external_targets_list()


@router.get("/api/backup/profiles")
async def backup_profiles_list_get():
    return await handlers.backup_profiles_list_get()


@router.get("/api/backup/usb/info")
async def backup_usb_info(mountpoint: str = "", device: str = ""):
    return await handlers.backup_usb_info(mountpoint, device)


@router.get("/api/backup/list")
async def list_backups(backup_dir: str = "/mnt/setuphelfer/backups"):
    return await handlers.list_backups(backup_dir)


@router.get("/api/backup/target-check")
async def backup_target_check_route(
    backup_dir: str,
    create: int = 0,
    auto_prepare: int = 0,
    label: str = "br001",
):
    return await backup_target_check(
        backup_dir,
        create=create,
        auto_prepare=auto_prepare,
        label=label,
    )


@router.api_route("/api/backup/clone/disk-info", methods=["GET", "POST"])
async def clone_disk_info_route(request: Request, refresh: int = 0):
    return await handlers.clone_disk_info(request, refresh=refresh)
