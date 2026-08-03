"""
Raspberry Pi 3-5 model detection — read-only, device-tree compatible string based.

PI-RS-HW-COMPAT-PROVISION-001 Phase 11 (detection half).

Relationship to existing code: ``modules.raspberry_pi_config._detect_pi_model`` reads
only ``/proc/device-tree/model`` and coarsely buckets pi1..pi5 for the *live Pi
configuration* feature. This module additionally reads
``/proc/device-tree/compatible`` (a NUL-separated list of standard, stable Linux
device-tree compatible strings) to distinguish 3B vs. 3B+, 4B vs. 400 vs. CM4, and
5 vs. CM5 — required for Phase 12/13 boot- and OS-planning, which needs the exact
board, not just the generation.

Board detection never overwrites or calls into the live-config module (independent,
read-only paths — see audit doc).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

RASPBERRY_PI_DETECTION_VERSION = 1

# Standard Raspberry Pi Linux device-tree "compatible" identifiers (stable, public
# kernel/firmware ABI — not proprietary or guessed). Small, closed enumeration by
# design (spec forbids "thousands of hardcoded devices"; there are ~7 boards here).
_PI_COMPATIBLE_MODEL_MAP: dict[str, tuple[str, str, str]] = {
    # compatible_string: (model_id, model_name, soc)
    "raspberrypi,3-model-b": ("pi3", "Raspberry Pi 3 Model B", "bcm2837"),
    "raspberrypi,3-model-b-plus": ("pi3b_plus", "Raspberry Pi 3 Model B+", "bcm2837"),
    "raspberrypi,4-model-b": ("pi4", "Raspberry Pi 4 Model B", "bcm2711"),
    "raspberrypi,400": ("pi400", "Raspberry Pi 400", "bcm2711"),
    "raspberrypi,4-compute-module": ("cm4", "Compute Module 4", "bcm2711"),
    "raspberrypi,5-model-b": ("pi5", "Raspberry Pi 5 Model B", "bcm2712"),
    "raspberrypi,5-compute-module": ("cm5", "Compute Module 5", "bcm2712"),
}

_PI_MODEL_GENERATION: dict[str, int] = {
    "pi3": 3,
    "pi3b_plus": 3,
    "pi4": 4,
    "pi400": 4,
    "cm4": 4,
    "pi5": 5,
    "cm5": 5,
}


def parse_device_tree_compatible(raw: str | bytes | None) -> list[str]:
    """Split the NUL-separated device-tree ``compatible`` property into strings."""
    if raw is None:
        return []
    if isinstance(raw, bytes):
        text = raw.decode("utf-8", errors="ignore")
    else:
        text = raw
    return [part for part in text.split("\x00") if part]


def detect_raspberry_pi_model(
    *,
    compatible_raw: str | bytes | None = None,
    model_string: str | None = None,
    sysfs_root: Path | None = None,
) -> dict[str, Any]:
    """Detect exact Pi board from device-tree compatible strings (preferred) or the
    ``model`` string (fallback, coarser). Returns is_raspberry_pi=False with
    model_id=None for any non-Pi or unrecognized board — never guessed."""
    compat_text = compatible_raw
    if compat_text is None:
        root = sysfs_root or Path("/")
        for rel in ("proc/device-tree/compatible", "sys/firmware/devicetree/base/compatible"):
            p = root / rel
            if p.exists():
                try:
                    compat_text = p.read_bytes()
                    break
                except OSError:
                    continue

    compatibles = parse_device_tree_compatible(compat_text)
    for compat in compatibles:
        if compat in _PI_COMPATIBLE_MODEL_MAP:
            model_id, model_name, soc = _PI_COMPATIBLE_MODEL_MAP[compat]
            return {
                "is_raspberry_pi": True,
                "model_id": model_id,
                "model_name": model_name,
                "soc": soc,
                "generation": _PI_MODEL_GENERATION[model_id],
                "detection_source": "device_tree_compatible",
                "detection_confidence": 0.95,
            }

    # Fallback: coarse model string match (cannot distinguish 3 vs 3B+, 4 vs 400/CM4).
    model_lower = (model_string or "").lower()
    if "raspberry pi" in model_lower:
        return {
            "is_raspberry_pi": True,
            "model_id": None,
            "model_name": model_string,
            "soc": None,
            "generation": None,
            "detection_source": "model_string_only",
            "detection_confidence": 0.4,
        }

    return {
        "is_raspberry_pi": False,
        "model_id": None,
        "model_name": None,
        "soc": None,
        "generation": None,
        "detection_source": "none",
        "detection_confidence": 0.0,
    }


def known_raspberry_pi_models() -> list[str]:
    return sorted(_PI_MODEL_GENERATION.keys())


def build_raspberry_pi_detection_diagnostics() -> dict[str, Any]:
    return {
        "detection_version": RASPBERRY_PI_DETECTION_VERSION,
        "module": "platforms.raspberry_pi_detection",
        "read_only": True,
        "eeprom_write": False,
        "known_models": known_raspberry_pi_models(),
    }


__all__ = [
    "RASPBERRY_PI_DETECTION_VERSION",
    "parse_device_tree_compatible",
    "detect_raspberry_pi_model",
    "known_raspberry_pi_models",
    "build_raspberry_pi_detection_diagnostics",
]
