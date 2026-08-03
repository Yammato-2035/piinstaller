"""
Raspberry Pi compatibility summary — combines detection + boot plan per board.

PI-RS-HW-COMPAT-PROVISION-001 Phase 11 (compatibility half).

Deliberately refuses to answer "is Pi 3-5 supported" as one boolean — every
compatibility statement is scoped to (board × architecture) and carries its own
boot-medium plan (spec requirement, see PHASE 11 "keine gemeinsame pauschale
Aussage").
"""

from __future__ import annotations

from typing import Any

from platforms.raspberry_pi_boot_plan import build_boot_plan

RASPBERRY_PI_COMPATIBILITY_VERSION = 1

_MODEL_RAM_VARIANTS_GB: dict[str, list[float]] = {
    "pi3": [1],
    "pi3b_plus": [1],
    "pi4": [1, 2, 4, 8],
    "pi400": [4],
    "cm4": [1, 2, 4, 8],
    "pi5": [2, 4, 8],
    "cm5": [2, 4, 8],
}

# Known, generation-level limitations (not device-specific quirks — those live in
# data/hardware/hardware_quirks.json). Kept intentionally short and factual.
_MODEL_KNOWN_LIMITATIONS: dict[str, list[str]] = {
    "pi3": ["no_native_pcie", "usb_boot_requires_otp_program", "max_ram_1gb"],
    "pi3b_plus": ["no_native_pcie", "usb_boot_requires_otp_program", "max_ram_1gb"],
    "pi4": ["no_native_pcie", "early_bootloader_lacks_usb_boot"],
    "pi400": ["no_native_pcie", "early_bootloader_lacks_usb_boot", "integrated_keyboard_only_variant"],
    "cm4": ["no_native_pcie_on_lite_carrier_variants"],
    "pi5": ["pcie_nvme_requires_hat_and_adapter"],
    "cm5": ["pcie_nvme_requires_carrier_board_support"],
}


def build_compatibility_summary(*, model_id: str | None, eeprom_version_raw: str | None = None) -> dict[str, Any]:
    """One compatibility entry, scoped to exactly one board. ``model_id=None`` returns
    an explicit ``unsupported``/insufficient-detection result, never a guess."""
    if not model_id:
        return {
            "schema_version": "raspberry-pi-compatibility.v1",
            "model_id": None,
            "architecture": "aarch64",
            "compatibility_status": "unknown",
            "reason": "model_not_identified_via_device_tree_compatible",
        }

    boot_plan = build_boot_plan(model_id=model_id, eeprom_version_raw=eeprom_version_raw)
    ram_variants = _MODEL_RAM_VARIANTS_GB.get(model_id, [])
    limitations = _MODEL_KNOWN_LIMITATIONS.get(model_id, [])

    return {
        "schema_version": "raspberry-pi-compatibility.v1",
        "model_id": model_id,
        "architecture": "aarch64",
        "ram_variants_gb": ram_variants,
        "known_limitations": limitations,
        "boot_plan": boot_plan,
        "compatibility_status": "board_identified_boot_plan_available",
        "physical_validation_required": True,
    }


def build_raspberry_pi_compatibility_diagnostics() -> dict[str, Any]:
    return {
        "compatibility_version": RASPBERRY_PI_COMPATIBILITY_VERSION,
        "module": "platforms.raspberry_pi_compatibility",
        "blanket_pi_3_to_5_claim_allowed": False,
        "known_models": sorted(_MODEL_RAM_VARIANTS_GB.keys()),
    }


__all__ = [
    "RASPBERRY_PI_COMPATIBILITY_VERSION",
    "build_compatibility_summary",
    "build_raspberry_pi_compatibility_diagnostics",
]
