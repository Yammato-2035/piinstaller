"""
DCC (Development Control Center) status fields for
PI-RS-HW-COMPAT-PROVISION-001.

Additive extension only — this module does not modify
``core.dev_dashboard_roadmap`` or ``core.dcc_status_facade``'s existing
functions; it is wired in via a new, separate function
(``dcc_status_facade.build_dcc_hardware_provisioning_section``).

Status values follow the existing roadmap vocabulary
(``core.dev_dashboard_roadmap._status_from_flags``): ``partial_green`` (module +
tests present), ``yellow`` (partially present), ``not_started`` (nothing found).
No status here is ever ``all_hardware_supported``/``production_ready`` or similar
forbidden absolute claim (spec PHASE 22) — this only reports code/evidence
presence, never real-world verification.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

_REPO_ROOT_MARKERS = ("backend", "frontend", "docs")


def _default_repo_root() -> Path:
    here = Path(__file__).resolve()
    for parent in here.parents:
        if all((parent / marker).exists() for marker in _REPO_ROOT_MARKERS):
            return parent
    return here.parents[2]


def _status_from_presence(*, all_present: list[bool], any_present: list[bool]) -> str:
    if all(all_present) and all_present:
        return "partial_green"
    if any(any_present):
        return "yellow"
    return "not_started"


def _exists(repo_root: Path, *relative_paths: str) -> list[bool]:
    return [(repo_root / p).is_file() or (repo_root / p).is_dir() for p in relative_paths]


def build_hardware_dcc_status_fields(*, repo_root: Path | None = None) -> dict[str, Any]:
    root = repo_root or _default_repo_root()

    hardware_detection = _exists(
        root,
        "backend/core/hardware_contracts.py",
        "backend/core/hardware_inventory.py",
        "backend/core/cpu_platform_detection.py",
        "backend/core/gpu_detection.py",
        "backend/core/usb_device_detection.py",
        "backend/tests/test_hardware_contracts_v1.py",
        "backend/tests/test_hardware_inventory_v1.py",
    )
    driver_resolution = _exists(
        root,
        "backend/core/driver_resolver.py",
        "backend/core/driver_activation_plan.py",
        "backend/tests/test_driver_resolver_v1.py",
    )
    firmware_coverage = _exists(
        root,
        "backend/core/firmware_resolver.py",
        "backend/tests/test_firmware_resolver_v1.py",
    )
    printer_scanner_detection = _exists(
        root,
        "backend/peripherals/printer_detection.py",
        "backend/peripherals/scanner_detection.py",
        "backend/tests/test_printer_detection_v1.py",
        "backend/tests/test_scanner_detection_v1.py",
    )
    raspberry_pi_coverage = _exists(
        root,
        "backend/platforms/raspberry_pi_detection.py",
        "backend/platforms/raspberry_pi_boot_plan.py",
        "backend/platforms/raspberry_pi_compatibility.py",
        "backend/platforms/raspberry_pi_os_plan.py",
        "backend/tests/test_raspberry_pi_detection_v1.py",
    )
    carrier_feasibility = _exists(
        root,
        "backend/rescue/carrier_layout.py",
        "backend/rescue/carrier_capacity_planner.py",
        "backend/rescue/carrier_content_catalog.py",
        "backend/tests/test_rescue_carrier_capacity_v1.py",
    )
    provisioning_catalog = _exists(
        root,
        "backend/provisioning/os_catalog.py",
        "backend/provisioning/os_install_plan.py",
        "data/provisioning/os_catalog.json",
        "backend/tests/test_provisioning_os_catalog_v1.py",
    )
    physical_matrix = _exists(
        root,
        "docs/evidence/rescue/hardware-compat-001/PHYSICAL_HARDWARE_TEST_MATRIX.md",
        "docs/evidence/rescue/hardware-compat-001/physical_hardware_test_matrix.json",
    )

    return {
        "hardware_detection_status": _status_from_presence(all_present=hardware_detection, any_present=hardware_detection),
        "driver_resolution_status": _status_from_presence(all_present=driver_resolution, any_present=driver_resolution),
        "firmware_coverage_status": _status_from_presence(all_present=firmware_coverage, any_present=firmware_coverage),
        "printer_scanner_detection_status": _status_from_presence(
            all_present=printer_scanner_detection, any_present=printer_scanner_detection
        ),
        "raspberry_pi_coverage_status": _status_from_presence(all_present=raspberry_pi_coverage, any_present=raspberry_pi_coverage),
        "carrier_feasibility_status": _status_from_presence(all_present=carrier_feasibility, any_present=carrier_feasibility),
        "provisioning_catalog_status": _status_from_presence(all_present=provisioning_catalog, any_present=provisioning_catalog),
        "physical_matrix_status": _status_from_presence(all_present=physical_matrix, any_present=physical_matrix),
        "note": "Diese Statuswerte melden Code-/Evidence-Praesenz, keine physische Verifikation (siehe PI-RS-HW-COMPAT-PROVISION-001 Phase 22).",
    }


def build_hardware_dcc_status_diagnostics() -> dict[str, Any]:
    return {
        "module": "core.hardware_dcc_status",
        "additive_only": True,
        "modifies_existing_dcc_functions": False,
    }


__all__ = [
    "build_hardware_dcc_status_fields",
    "build_hardware_dcc_status_diagnostics",
]
