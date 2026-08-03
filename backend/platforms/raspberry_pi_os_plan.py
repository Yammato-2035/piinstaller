"""
Raspberry Pi OS candidate matrix — board x architecture x OS x boot medium.

PI-RS-HW-COMPAT-PROVISION-001 Phase 11 (OS plan half).

Every combination starts at ``test_status = "planned"``; nothing here becomes
"physically_verified" without a corresponding Phase 18 physical test matrix entry.
This module only prepares the *candidate list* — actual signed image references
live in the generic ``backend/provisioning`` catalog (Phase 13), which this module
does not duplicate.
"""

from __future__ import annotations

from typing import Any

RASPBERRY_PI_OS_PLAN_VERSION = 1

_OS_CANDIDATES: list[dict[str, Any]] = [
    {"os_id": "raspberry_pi_os", "display_name": "Raspberry Pi OS", "min_ram_gb": 1, "future_or_optional": False},
    {"os_id": "debian_arm64", "display_name": "Debian ARM64", "min_ram_gb": 1, "future_or_optional": False},
    {"os_id": "ubuntu_server_arm64", "display_name": "Ubuntu Server ARM64", "min_ram_gb": 1, "future_or_optional": False},
    {"os_id": "ubuntu_desktop_arm64", "display_name": "Ubuntu Desktop ARM64", "min_ram_gb": 4, "future_or_optional": True},
]

_TEST_STATUS_VALUES = frozenset(
    {"planned", "detected", "driver_plan_created", "physically_verified", "limited", "blocked", "unavailable"}
)


def build_os_candidate_matrix(*, model_id: str | None, ram_variants_gb: list[float]) -> list[dict[str, Any]]:
    """One row per (OS candidate). ``ram_sufficient`` checks against the smallest
    known RAM variant for the board, since operators may have any variant."""
    if not model_id:
        return []
    smallest_ram = min(ram_variants_gb) if ram_variants_gb else 0

    rows: list[dict[str, Any]] = []
    for candidate in _OS_CANDIDATES:
        ram_sufficient = smallest_ram >= candidate["min_ram_gb"] if smallest_ram else None
        support_status = "future" if candidate["future_or_optional"] else "experimental"
        if ram_sufficient is False:
            support_status = "blocked"
        rows.append(
            {
                "os_id": candidate["os_id"],
                "display_name": candidate["display_name"],
                "model_id": model_id,
                "architecture": "aarch64",
                "min_ram_gb": candidate["min_ram_gb"],
                "ram_sufficient_for_smallest_known_variant": ram_sufficient,
                "support_status": support_status,
                "test_status": "planned",
            }
        )
    return rows


def build_raspberry_pi_os_plan_diagnostics() -> dict[str, Any]:
    return {
        "plan_version": RASPBERRY_PI_OS_PLAN_VERSION,
        "module": "platforms.raspberry_pi_os_plan",
        "install_triggered": False,
        "valid_test_status_values": sorted(_TEST_STATUS_VALUES),
    }


__all__ = [
    "RASPBERRY_PI_OS_PLAN_VERSION",
    "build_os_candidate_matrix",
    "build_raspberry_pi_os_plan_diagnostics",
]
