"""
Read-only / preview-only OS provisioning API.

PI-RS-HW-COMPAT-PROVISION-001 Phase 14 (provisioning half). ``write_allowed`` is
always ``false`` in every response — no image write, no download is ever
triggered by this router.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Body, HTTPException

from provisioning.os_catalog import load_os_catalog
from provisioning.os_compatibility import evaluate_compatibility
from provisioning.os_image_verifier import build_verification_preview
from provisioning.os_install_plan import build_provisioning_plan

router = APIRouter(tags=["rescue-provisioning"])


def _get_entry(image_id: str) -> dict[str, Any]:
    for entry in load_os_catalog():
        if entry.get("image_id") == image_id:
            return entry
    raise HTTPException(status_code=404, detail="image_id_not_found_in_catalog")


@router.get("/api/rescue/provision/catalog")
async def get_provision_catalog() -> dict[str, Any]:
    return {"entries": load_os_catalog()}


@router.post("/api/rescue/provision/compatibility")
async def post_provision_compatibility(payload: dict[str, Any] = Body(...)) -> dict[str, Any]:
    entry = _get_entry(payload["image_id"])
    return evaluate_compatibility(
        catalog_entry=entry,
        target_architecture=payload.get("target_architecture", "unknown"),
        target_platform_id=payload.get("target_platform_id"),
        target_bytes=payload.get("target_bytes"),
    )


@router.post("/api/rescue/provision/plan")
async def post_provision_plan(payload: dict[str, Any] = Body(...)) -> dict[str, Any]:
    entry = _get_entry(payload["image_id"])
    return build_provisioning_plan(
        catalog_entry=entry,
        target_architecture=payload.get("target_architecture", "unknown"),
        target_platform_id=payload.get("target_platform_id"),
        target_bytes=payload.get("target_bytes"),
        target_device_descriptor=payload.get("target_device_descriptor"),
        local_file_sha256=payload.get("local_file_sha256"),
    )


@router.post("/api/rescue/provision/image-verification-preview")
async def post_provision_image_verification_preview(payload: dict[str, Any] = Body(...)) -> dict[str, Any]:
    entry = _get_entry(payload["image_id"])
    return build_verification_preview(catalog_entry=entry, local_file_sha256=payload.get("local_file_sha256"))


__all__ = ["router"]
