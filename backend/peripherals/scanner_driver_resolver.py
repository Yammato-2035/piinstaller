"""
Scanner driver (SANE backend) resolver — read-only planning only.

PI-RS-HW-COMPAT-PROVISION-001 Phase 8 (scanner resolver half).
"""

from __future__ import annotations

from typing import Any

SCANNER_DRIVER_RESOLVER_VERSION = 1

_SOURCE_TO_DRIVER_TYPE = {
    "sane_backend": "userspace",
    "escl_airscan": "userspace",
    "usb_still_image": "unsupported",
    "unknown": "unsupported",
}


def resolve_scanner_driver_plan(scanner_report_entry: dict[str, Any]) -> dict[str, Any]:
    source = scanner_report_entry.get("source", "unknown")
    driver_type = _SOURCE_TO_DRIVER_TYPE.get(source, "unsupported")

    recommended_driver = None
    warnings: list[str] = []
    if source == "sane_backend":
        recommended_driver = "sane_generic_backend"
    elif source == "escl_airscan":
        recommended_driver = "sane_airscan"
    elif source == "usb_still_image":
        warnings.append("still_image_class_only_no_confirmed_sane_backend_review_required")
    else:
        warnings.append("scanner_source_unresolved_review_required")

    return {
        "device_id": scanner_report_entry.get("device_id"),
        "current_state": scanner_report_entry.get("operational_status", "unknown"),
        "recommended_driver": recommended_driver,
        "alternative_drivers": [],
        "driver_type": driver_type,
        "package_candidates": [],
        "firmware_candidates": [],
        "kernel_compatible": True,
        "secure_boot_impact": "none",
        "license_review_required": False,
        "network_required": source == "escl_airscan",
        "reboot_required": False,
        "live_activation_possible": False,
        "persistent_install_possible": False,
        "rollback_plan": {},
        "warnings": warnings,
        "errors": [],
        "scan_test_performed": False,
    }


def build_scanner_driver_resolver_diagnostics() -> dict[str, Any]:
    return {
        "resolver_version": SCANNER_DRIVER_RESOLVER_VERSION,
        "module": "peripherals.scanner_driver_resolver",
        "auto_install": False,
        "scan_triggered": False,
    }


__all__ = [
    "SCANNER_DRIVER_RESOLVER_VERSION",
    "resolve_scanner_driver_plan",
    "build_scanner_driver_resolver_diagnostics",
]
