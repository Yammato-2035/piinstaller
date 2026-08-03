"""
Printer driver resolver — turns a printer_detection report entry into a safe plan.

PI-RS-HW-COMPAT-PROVISION-001 Phase 8 (printer resolver half).

Driver order (spec PHASE 8, strict): driverless IPP > distribution driver > free
generic driver > curated vendor package > proprietary (explicitly optional) >
unsupported/review_required. No step here installs anything.
"""

from __future__ import annotations

from typing import Any

PRINTER_DRIVER_RESOLVER_VERSION = 1


def resolve_printer_driver_plan(printer_report_entry: dict[str, Any]) -> dict[str, Any]:
    driver_order = printer_report_entry.get("driver_order") or []
    classification_status = printer_report_entry.get("classification_status", "review_required")

    recommended = driver_order[0] if driver_order else None
    alternatives = driver_order[1:] if len(driver_order) > 1 else []

    warnings: list[str] = []
    if classification_status == "review_required":
        warnings.append("technology_or_color_capability_unconfirmed_review_required")
    if recommended == "proprietary_optional":
        warnings.append("only_proprietary_candidate_review_required")

    driver_type = "unsupported"
    if recommended == "driverless_ipp":
        driver_type = "userspace"
    elif recommended in ("distribution_driver", "generic_free_driver"):
        driver_type = "userspace"
    elif recommended == "curated_vendor_package":
        driver_type = "userspace"
    elif recommended == "proprietary_optional":
        driver_type = "proprietary_optional"

    return {
        "device_id": printer_report_entry.get("device_id"),
        "current_state": classification_status,
        "recommended_driver": recommended,
        "alternative_drivers": alternatives,
        "driver_type": driver_type,
        "package_candidates": [],
        "firmware_candidates": [],
        "kernel_compatible": True,
        "secure_boot_impact": "none",
        "license_review_required": recommended == "proprietary_optional",
        "network_required": recommended == "driverless_ipp",
        "reboot_required": False,
        "live_activation_possible": False,
        "persistent_install_possible": False,
        "rollback_plan": {},
        "warnings": warnings,
        "errors": [],
        "test_print_performed": False,
    }


def build_printer_driver_resolver_diagnostics() -> dict[str, Any]:
    return {
        "resolver_version": PRINTER_DRIVER_RESOLVER_VERSION,
        "module": "peripherals.printer_driver_resolver",
        "auto_install": False,
        "test_print_triggered": False,
    }


__all__ = [
    "PRINTER_DRIVER_RESOLVER_VERSION",
    "resolve_printer_driver_plan",
    "build_printer_driver_resolver_diagnostics",
]
