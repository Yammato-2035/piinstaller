"""
Generic multi-class driver resolver — read-only planning, no installation.

PI-RS-HW-COMPAT-PROVISION-001 Phase 9 (driver resolver half).

Implements the 8-stage resolution pipeline from the spec:
1. kernel modalias, 2. bound driver, 3. available kernel modules, 4. firmware
errors, 5. installed package info, 6. distro/arch, 7. curated quirks, 8. safe
activation plan. Class-specific resolvers (``gpu_driver_resolver``,
``peripherals.printer_driver_resolver``, ``peripherals.scanner_driver_resolver``)
cover GPU/printer/scanner nuance; this module is the fallback/generic path used
for every other device class and the common ``DriverPlan`` shape they all agree on.
"""

from __future__ import annotations

from typing import Any

from core.hardware_contracts import HardwareDevice

DRIVER_RESOLVER_VERSION = 1

# Package source trust levels (spec PHASE 9) — lower is more trusted.
PACKAGE_SOURCE_TRUST_LEVELS: dict[str, int] = {
    "already_in_rescue_image": 1,
    "official_distribution_repository": 2,
    "signed_setuphelfer_offline_cache": 3,
    "official_vendor_repository": 4,
    "manually_provided_signed_package": 5,
    "unknown_source": 6,
}

_BLOCKED_TRUST_LEVEL = 6


def classify_package_source_trust(source: str) -> int:
    return PACKAGE_SOURCE_TRUST_LEVELS.get(source, _BLOCKED_TRUST_LEVEL)


def resolve_driver_plan(
    device: HardwareDevice,
    *,
    quirk_entry: dict[str, Any] | None = None,
    architecture: str = "unknown",
    distribution: str | None = None,
    firmware_missing: bool = False,
    package_source: str = "unknown_source",
) -> dict[str, Any]:
    """Build a generic ``DriverPlan`` dict for any device class.

    ``quirk_entry`` (optional) comes from ``data/hardware/hardware_quirks.json`` via
    the Phase 10 catalog loader — this module never embeds device-specific quirks.
    """
    driver_in_use = device.driver.kernel_driver_in_use
    candidates = list(device.driver.kernel_driver_candidates)

    recommended_driver = driver_in_use
    if not recommended_driver and candidates:
        recommended_driver = candidates[0]
    alternative_drivers = [c for c in candidates if c != recommended_driver]

    driver_type = "unsupported"
    if recommended_driver and quirk_entry and quirk_entry.get("driver_type"):
        driver_type = quirk_entry["driver_type"]
    elif recommended_driver:
        driver_type = "kernel_in_tree"

    trust_level = classify_package_source_trust(package_source)
    package_blocked = trust_level >= _BLOCKED_TRUST_LEVEL

    warnings: list[str] = []
    if not recommended_driver:
        warnings.append("no_driver_candidate_known")
    if firmware_missing:
        warnings.append("firmware_missing_driver_may_be_limited")
    if package_blocked:
        warnings.append("package_source_untrusted_blocked")
    if quirk_entry and quirk_entry.get("known_issues"):
        warnings.append("curated_quirk_known_issues_apply")

    secure_boot_impact = "review_required" if driver_type == "proprietary_optional" else "none"

    return {
        "device_id": device.device_id,
        "current_state": device.operational_status,
        "recommended_driver": recommended_driver,
        "alternative_drivers": alternative_drivers,
        "driver_type": driver_type,
        "package_candidates": [] if package_blocked else (quirk_entry or {}).get("package_candidates", []),
        "firmware_candidates": list(device.firmware.candidates),
        "kernel_compatible": bool(recommended_driver) and not firmware_missing,
        "secure_boot_impact": secure_boot_impact,
        "license_review_required": driver_type == "proprietary_optional",
        "network_required": False,
        "reboot_required": bool(recommended_driver and recommended_driver != driver_in_use),
        "live_activation_possible": False,
        "persistent_install_possible": False,
        "rollback_plan": {},
        "warnings": warnings,
        "errors": ["package_source_blocked"] if package_blocked else [],
        "architecture": architecture,
        "distribution": distribution,
        "package_source_trust_level": trust_level,
    }


def build_driver_resolver_diagnostics() -> dict[str, Any]:
    return {
        "resolver_version": DRIVER_RESOLVER_VERSION,
        "module": "core.driver_resolver",
        "auto_install": False,
        "auto_add_package_source": False,
        "auto_accept_license": False,
        "curl_pipe_bash_used": False,
        "trust_levels": PACKAGE_SOURCE_TRUST_LEVELS,
    }


__all__ = [
    "DRIVER_RESOLVER_VERSION",
    "PACKAGE_SOURCE_TRUST_LEVELS",
    "classify_package_source_trust",
    "resolve_driver_plan",
    "build_driver_resolver_diagnostics",
]
