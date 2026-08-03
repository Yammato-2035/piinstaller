"""
Read-only Raspberry Pi platform detection/compatibility API.

PI-RS-HW-COMPAT-PROVISION-001 Phase 14 (platform half). Read-only device-tree
inspection only; no EEPROM write, no bootloader update.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter

from platforms.raspberry_pi_boot_plan import build_boot_plan
from platforms.raspberry_pi_compatibility import build_compatibility_summary
from platforms.raspberry_pi_detection import detect_raspberry_pi_model

router = APIRouter(tags=["rescue-platform"])

_DEVICE_TREE_MODEL = Path("/proc/device-tree/model")
_DEVICE_TREE_COMPATIBLE = Path("/proc/device-tree/compatible")


def _read_optional(path: Path) -> str | None:
    try:
        if path.exists():
            return path.read_bytes().decode("utf-8", errors="ignore")
    except OSError:
        return None
    return None


def _detect_local_pi() -> dict[str, Any]:
    compatible_raw = _read_optional(_DEVICE_TREE_COMPATIBLE) or ""
    model_string = _read_optional(_DEVICE_TREE_MODEL)
    return detect_raspberry_pi_model(compatible_raw=compatible_raw, model_string=model_string)


@router.get("/api/rescue/platform/raspberry-pi")
async def get_platform_raspberry_pi() -> dict[str, Any]:
    detection = _detect_local_pi()
    model_id = detection.get("model_id")
    return {
        "detection": detection,
        "boot_plan": build_boot_plan(model_id=model_id),
        "compatibility_summary": build_compatibility_summary(model_id=model_id),
    }


@router.get("/api/rescue/platform/raspberry-pi/os-compatibility")
async def get_platform_raspberry_pi_os_compatibility() -> dict[str, Any]:
    from platforms.raspberry_pi_os_plan import build_os_candidate_matrix

    detection = _detect_local_pi()
    model_id = detection.get("model_id")
    # RAM variants are declared per known board release, never guessed from a single
    # /proc/meminfo read on the current host (which is only one specific unit).
    known_ram_variants_gb = {
        "pi3": [1],
        "pi3b_plus": [1],
        "pi4": [1, 2, 4, 8],
        "pi400": [2, 4],
        "cm4": [1, 2, 4, 8],
        "pi5": [2, 4, 8],
        "cm5": [2, 4, 8],
    }
    ram_variants = known_ram_variants_gb.get(model_id, [])
    return {
        "detection": detection,
        "os_candidates": build_os_candidate_matrix(model_id=model_id, ram_variants_gb=ram_variants),
    }


__all__ = ["router"]
