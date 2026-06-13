"""
Backup readonly router — safe GET inventory/status routes (Phase B.2).

No create, restore, clone, USB mount/prepare, or verify POST handlers.
"""

from __future__ import annotations

from fastapi import APIRouter, Query, Request

from core import backup_readonly_handlers as handlers

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
