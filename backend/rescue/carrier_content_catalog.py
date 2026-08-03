"""
64-GB carrier content catalog — declares what *could* live on the rescue carrier.

PI-RS-HW-COMPAT-PROVISION-001 Phase 12 (content catalog half).

Sizes here are **planning estimates**, not measurements of a specific build —
every value is explicitly labeled ``estimated_bytes`` and carries a short
rationale. This module never partitions or writes anything.
"""

from __future__ import annotations

from typing import Any

CARRIER_CONTENT_CATALOG_VERSION = 1

_GB = 1024**3
_MB = 1024**2

# Planning-time estimates only (see module docstring). Based on current rescue ISO
# evidence (docs/evidence/pi_rs_gui_bvr_phase, docs/evidence/rescue-stick) order of
# magnitude, rounded conservatively upward — not a measured build manifest.
CARRIER_CONTENT_COMPONENTS: list[dict[str, Any]] = [
    {
        "component_id": "rescue_runtime",
        "display_name": "Setuphelfer Rescue Runtime (squashfs + kernel + initramfs)",
        "estimated_bytes": 2 * _GB,
        "required": True,
        "rationale": "current x86_64 rescue ISO order of magnitude, rounded up for headroom",
    },
    {
        "component_id": "x86_64_boot_assets",
        "display_name": "x86_64 boot path (GRUB, EFI, MBR fallback)",
        "estimated_bytes": 256 * _MB,
        "required": True,
        "rationale": "existing FAT32 ESP layout order of magnitude",
    },
    {
        "component_id": "arm_pi_boot_assets",
        "display_name": "ARM/Raspberry Pi boot assets (optional, only if validated)",
        "estimated_bytes": 512 * _MB,
        "required": False,
        "rationale": "placeholder until a validated universal or split boot path exists (Phase 12 decision)",
    },
    {
        "component_id": "hardware_catalog",
        "display_name": "Curated hardware compatibility catalog + quirks",
        "estimated_bytes": 16 * _MB,
        "required": True,
        "rationale": "JSON catalog, small by design (Phase 10 — not exhaustive)",
    },
    {
        "component_id": "driver_firmware_offline_packages",
        "display_name": "Driver/firmware offline package cache",
        "estimated_bytes": 4 * _GB,
        "required": False,
        "rationale": "planning placeholder; real package set defined in PI-RS-HW-ACTIVATE-002",
    },
    {
        "component_id": "os_image_cache",
        "display_name": "Cached target OS images (Phase 13 catalog)",
        "estimated_bytes": 8 * _GB,
        "required": False,
        "rationale": "placeholder for 1-2 cached net-install-sized images; full images do not fit many at once",
    },
    {
        "component_id": "evidence_and_logs",
        "display_name": "Evidence / diagnostic export area",
        "estimated_bytes": 1 * _GB,
        "required": True,
        "rationale": "existing evidence run sizes observed under docs/evidence/runtime-results",
    },
    {
        "component_id": "update_and_signature_metadata",
        "display_name": "Update + signature metadata",
        "estimated_bytes": 32 * _MB,
        "required": True,
        "rationale": "small manifest/signature files",
    },
]


def get_required_components() -> list[dict[str, Any]]:
    return [c for c in CARRIER_CONTENT_COMPONENTS if c["required"]]


def get_optional_components() -> list[dict[str, Any]]:
    return [c for c in CARRIER_CONTENT_COMPONENTS if not c["required"]]


def build_carrier_content_catalog_diagnostics() -> dict[str, Any]:
    return {
        "catalog_version": CARRIER_CONTENT_CATALOG_VERSION,
        "module": "rescue.carrier_content_catalog",
        "component_count": len(CARRIER_CONTENT_COMPONENTS),
        "required_component_count": len(get_required_components()),
        "sizes_are_estimates_not_measurements": True,
        "partitioning_performed": False,
    }


__all__ = [
    "CARRIER_CONTENT_CATALOG_VERSION",
    "CARRIER_CONTENT_COMPONENTS",
    "get_required_components",
    "get_optional_components",
    "build_carrier_content_catalog_diagnostics",
]
