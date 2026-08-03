"""
Raspberry Pi boot-medium plan — read-only, no EEPROM writes.

PI-RS-HW-COMPAT-PROVISION-001 Phase 11 (boot plan half).

Boot-medium support differs materially between generations (spec requirement: no
blanket "Pi 3-5 supported" statement). Values below reflect publicly documented
Raspberry Pi Foundation bootloader capabilities per generation, not measurements on
a specific unit — every result therefore carries
``physical_validation_required = True`` until a physical boot test evidence entry
exists (Phase 18 matrix).
"""

from __future__ import annotations

from typing import Any

RASPBERRY_PI_BOOT_PLAN_VERSION = 1

# model_id -> {boot_medium: status}. Status values per spec:
# boot_supported | bootloader_update_recommended | bootloader_update_required
_BOOT_MEDIUM_SUPPORT: dict[str, dict[str, str]] = {
    "pi3": {"microsd": "boot_supported", "usb_mass_storage": "bootloader_update_required", "nvme": "unsupported"},
    "pi3b_plus": {"microsd": "boot_supported", "usb_mass_storage": "bootloader_update_required", "nvme": "unsupported"},
    "pi4": {"microsd": "boot_supported", "usb_mass_storage": "bootloader_update_recommended", "nvme": "unsupported"},
    "pi400": {"microsd": "boot_supported", "usb_mass_storage": "bootloader_update_recommended", "nvme": "unsupported"},
    "cm4": {"microsd": "boot_supported", "usb_mass_storage": "bootloader_update_recommended", "nvme": "unsupported"},
    "pi5": {"microsd": "boot_supported", "usb_mass_storage": "boot_supported", "nvme": "bootloader_update_recommended"},
    "cm5": {"microsd": "boot_supported", "usb_mass_storage": "boot_supported", "nvme": "bootloader_update_recommended"},
}


def get_boot_medium_support(model_id: str | None) -> dict[str, str]:
    if not model_id or model_id not in _BOOT_MEDIUM_SUPPORT:
        return {}
    return dict(_BOOT_MEDIUM_SUPPORT[model_id])


def parse_eeprom_version(vcgencmd_bootloader_output: str | None) -> str | None:
    """Parse ``vcgencmd bootloader_version`` first line (date) if available."""
    if not vcgencmd_bootloader_output:
        return None
    first_line = vcgencmd_bootloader_output.strip().splitlines()[0] if vcgencmd_bootloader_output.strip() else ""
    return first_line or None


def build_boot_plan(*, model_id: str | None, eeprom_version_raw: str | None = None) -> dict[str, Any]:
    """Build the per-medium boot plan for one Pi model. Never writes EEPROM."""
    support = get_boot_medium_support(model_id)
    eeprom_version = parse_eeprom_version(eeprom_version_raw)

    media: list[dict[str, Any]] = []
    for medium, status in support.items():
        media.append(
            {
                "boot_medium": medium,
                "status": status,
                "storage_supported": status != "unsupported",
                "physical_validation_required": True,
            }
        )

    return {
        "schema_version": "raspberry-pi-boot-plan.v1",
        "model_id": model_id,
        "eeprom_version_detected": eeprom_version,
        "eeprom_write_performed": False,
        "boot_media": media,
        "network_boot_status": "future_experimental",
    }


def build_raspberry_pi_boot_plan_diagnostics() -> dict[str, Any]:
    return {
        "plan_version": RASPBERRY_PI_BOOT_PLAN_VERSION,
        "module": "platforms.raspberry_pi_boot_plan",
        "read_only": True,
        "eeprom_write_performed": False,
        "known_models": sorted(_BOOT_MEDIUM_SUPPORT.keys()),
    }


__all__ = [
    "RASPBERRY_PI_BOOT_PLAN_VERSION",
    "get_boot_medium_support",
    "parse_eeprom_version",
    "build_boot_plan",
    "build_raspberry_pi_boot_plan_diagnostics",
]
