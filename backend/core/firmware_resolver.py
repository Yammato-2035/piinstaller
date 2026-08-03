"""
Firmware status resolver — read-only, cross-references dmesg firmware errors.

PI-RS-HW-COMPAT-PROVISION-001 Phase 9 (firmware resolver half).
"""

from __future__ import annotations

from typing import Any

from core.hardware_contracts import FirmwareStatus

FIRMWARE_RESOLVER_VERSION = 1


def evaluate_firmware_status(
    *, driver_name: str | None, missing_firmware_lines: list[str] | None = None
) -> tuple[FirmwareStatus, list[str]]:
    """Return (status, matched_lines). No driver name -> not_required is *not* assumed;
    stays unknown, since "no driver" could mean many things besides "no firmware needed".
    """
    lines = missing_firmware_lines or []
    if not driver_name:
        return FirmwareStatus.UNKNOWN, []
    matched = [line for line in lines if driver_name.lower() in line.lower()]
    if matched:
        return FirmwareStatus.MISSING, matched
    return FirmwareStatus.UNKNOWN, []


def build_firmware_report(
    *, devices_with_drivers: list[tuple[str, str | None]], missing_firmware_lines: list[str]
) -> list[dict[str, Any]]:
    """``devices_with_drivers``: list of (device_id, driver_name)."""
    out: list[dict[str, Any]] = []
    for device_id, driver_name in devices_with_drivers:
        status, matched = evaluate_firmware_status(driver_name=driver_name, missing_firmware_lines=missing_firmware_lines)
        out.append(
            {
                "device_id": device_id,
                "driver_name": driver_name,
                "firmware_status": status.value,
                "matched_dmesg_lines": matched,
            }
        )
    return out


def build_firmware_resolver_diagnostics() -> dict[str, Any]:
    return {
        "resolver_version": FIRMWARE_RESOLVER_VERSION,
        "module": "core.firmware_resolver",
        "read_only": True,
        "firmware_download_triggered": False,
    }


__all__ = [
    "FIRMWARE_RESOLVER_VERSION",
    "evaluate_firmware_status",
    "build_firmware_report",
    "build_firmware_resolver_diagnostics",
]
