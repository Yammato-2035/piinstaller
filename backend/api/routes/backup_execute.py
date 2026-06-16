"""
Backup execute router — POST handlers without full backup create/restore (Phase B.4).

Job cancel, evidence collect, profiles list/preview.
"""

from __future__ import annotations

from fastapi import APIRouter, Request

from core import backup_execute_handlers as handlers

router = APIRouter(tags=["backup-execute"])


@router.post("/api/backup/jobs/{job_id}/cancel")
async def backup_job_cancel_route(job_id: str):
    return await handlers.backup_job_cancel(job_id)


@router.post("/api/backup/jobs/{job_id}/evidence")
async def backup_job_evidence_collect_route(job_id: str):
    return await handlers.backup_job_evidence_collect(job_id)


@router.post("/api/backup/profiles")
async def backup_profiles_list_post_route():
    return await handlers.backup_profiles_list_post()


@router.post("/api/backup/profile-preview")
async def backup_profile_preview_route(request: Request):
    return await handlers.backup_profile_preview(request)

@router.post("/api/backup/settings")
async def backup_set_settings_route(request: Request):
    return await handlers.backup_set_settings(request)

@router.post("/api/backup/schedule/run-now")
async def backup_run_now_route(request: Request):
    return await handlers.backup_run_now(request)

@router.post("/api/backup/cloud/test")
async def backup_cloud_test_route(request: Request):
    return await handlers.backup_cloud_test(request)

@router.post("/api/backup/cloud/delete")
async def backup_cloud_delete_route(request: Request):
    return await handlers.backup_cloud_delete(request)

@router.post("/api/backup/cloud/verify")
async def backup_cloud_verify_route(request: Request):
    return await handlers.backup_cloud_verify(request)
