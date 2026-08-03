"""
OS installation *plan* builder — preview only, ``write_allowed`` is always False.

PI-RS-HW-COMPAT-PROVISION-001 Phase 13 (install plan half).

No ``dd``, no ``mkfs``, no ``parted``/``sfdisk``/``sgdisk``/``wipefs`` call exists
anywhere in this module or its callers within this phase.
"""

from __future__ import annotations

from typing import Any

from provisioning.os_compatibility import evaluate_compatibility
from provisioning.os_image_verifier import build_verification_preview

OS_INSTALL_PLAN_VERSION = 1


def build_provisioning_plan(
    *,
    catalog_entry: dict[str, Any],
    target_architecture: str,
    target_platform_id: str | None = None,
    target_bytes: int | None = None,
    target_device_descriptor: dict[str, Any] | None = None,
    local_file_sha256: str | None = None,
) -> dict[str, Any]:
    """Build the read-only provisioning plan preview (spec PHASE 13 JSON shape).
    ``write_allowed`` is hardcoded False and never influenced by any input here."""
    compatibility = evaluate_compatibility(
        catalog_entry=catalog_entry,
        target_architecture=target_architecture,
        target_platform_id=target_platform_id,
        target_bytes=target_bytes,
    )
    verification = build_verification_preview(catalog_entry=catalog_entry, local_file_sha256=local_file_sha256)

    required_next_gates = ["signed_image_with_real_checksum", "physical_hardware_validation"]
    if compatibility["compatibility_status"] != "compatible":
        plan_status = "blocked"
    elif verification["verification_status"] != "hash_match":
        plan_status = "review_required"
    else:
        plan_status = "ready_for_preview"
        required_next_gates = ["physical_hardware_validation"]

    return {
        "schema_version": "os-install-plan.v1",
        "plan_status": plan_status,
        "source_image": {
            "image_id": catalog_entry.get("image_id"),
            "display_name": catalog_entry.get("display_name"),
            "architecture": catalog_entry.get("architecture"),
        },
        "target_platform": {"platform_id": target_platform_id, "architecture": target_architecture},
        "target_device": target_device_descriptor or {},
        "required_bytes": catalog_entry.get("minimum_target_bytes"),
        "boot_mode": (catalog_entry.get("supported_boot_modes") or [None])[0],
        "partition_plan_preview": [],
        "compatibility": compatibility,
        "verification": verification,
        "driver_plan": {},
        "firmware_plan": {},
        "post_install_plan": {},
        "write_allowed": False,
        "required_next_gates": required_next_gates,
    }


def build_os_install_plan_diagnostics() -> dict[str, Any]:
    return {
        "plan_version": OS_INSTALL_PLAN_VERSION,
        "module": "provisioning.os_install_plan",
        "write_allowed": False,
        "dd_used": False,
        "mkfs_used": False,
        "parted_used": False,
        "sfdisk_used": False,
        "sgdisk_used": False,
        "wipefs_used": False,
    }


__all__ = [
    "OS_INSTALL_PLAN_VERSION",
    "build_provisioning_plan",
    "build_os_install_plan_diagnostics",
]
