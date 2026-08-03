"""
GPU driver resolver — turns a gpu_detection report entry into a safe DriverPlan.

PI-RS-HW-COMPAT-PROVISION-001 Phase 5 (resolver half).

No automatic installation, no MOK/Secure-Boot key changes, no blacklist edits.
Proprietary NVIDIA is always presented as an explicitly optional, review-required
candidate — never the default recommendation.
"""

from __future__ import annotations

from typing import Any

GPU_DRIVER_RESOLVER_VERSION = 1

_OPEN_SOURCE_DRIVERS = {"i915", "xe", "amdgpu", "nouveau"}


def resolve_gpu_driver_plan(gpu_report_entry: dict[str, Any]) -> dict[str, Any]:
    """Build a DriverPlan-shaped dict for one GPU report entry (spec PHASE 9 shape,
    scoped to GPU here; the generic multi-class version lives in driver_resolver.py)."""
    vendor = gpu_report_entry.get("vendor", "unknown")
    driver_in_use = gpu_report_entry.get("driver_in_use")
    candidates = list(gpu_report_entry.get("driver_candidates") or [])
    gpu_status = gpu_report_entry.get("gpu_status", "unknown")

    recommended_driver = driver_in_use
    alternative_drivers = [c for c in candidates if c != driver_in_use]

    if not recommended_driver and candidates:
        # Open-source in-tree candidate first; proprietary NVIDIA stays an alternative.
        open_source = [c for c in candidates if c in _OPEN_SOURCE_DRIVERS]
        recommended_driver = open_source[0] if open_source else candidates[0]
        alternative_drivers = [c for c in candidates if c != recommended_driver]

    driver_type = "unsupported"
    if recommended_driver in _OPEN_SOURCE_DRIVERS:
        driver_type = "kernel_in_tree"
    elif recommended_driver == "nvidia":
        driver_type = "proprietary_optional"
    elif recommended_driver:
        driver_type = "kernel_in_tree"

    secure_boot_impact = "review_required" if driver_type == "proprietary_optional" else "none"
    license_review_required = driver_type == "proprietary_optional"

    warnings: list[str] = []
    if gpu_status == "disabled_by_cmdline":
        warnings.append("gpu_disabled_by_kernel_cmdline_parameter")
    if vendor == "nvidia" and driver_in_use == "nouveau" and "nvidia" in candidates:
        warnings.append("proprietary_driver_available_as_optional_review_required")
    if vendor == "unknown":
        warnings.append("gpu_vendor_unresolved_review_required")

    return {
        "device_id": gpu_report_entry.get("device_id"),
        "current_state": gpu_status,
        "recommended_driver": recommended_driver,
        "alternative_drivers": alternative_drivers,
        "driver_type": driver_type,
        "package_candidates": [],
        "firmware_candidates": [],
        "kernel_compatible": gpu_status not in ("driver_missing", "unknown"),
        "secure_boot_impact": secure_boot_impact,
        "license_review_required": license_review_required,
        "network_required": False,
        "reboot_required": bool(recommended_driver and recommended_driver != driver_in_use),
        "live_activation_possible": False,
        "persistent_install_possible": False,
        "rollback_plan": {},
        "warnings": warnings,
        "errors": [],
    }


def build_gpu_driver_resolver_diagnostics() -> dict[str, Any]:
    return {
        "resolver_version": GPU_DRIVER_RESOLVER_VERSION,
        "module": "core.gpu_driver_resolver",
        "auto_install": False,
        "mok_key_management": False,
        "blacklist_modified": False,
    }


__all__ = [
    "GPU_DRIVER_RESOLVER_VERSION",
    "resolve_gpu_driver_plan",
    "build_gpu_driver_resolver_diagnostics",
]
