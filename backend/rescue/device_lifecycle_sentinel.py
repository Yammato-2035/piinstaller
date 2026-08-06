"""
Device lifecycle sentinel — orchestrates hardware state + boot stage coupling.

PI-RS-ASUS-EMERGENCY-LINUX-TELEMETRY-003 Phase 4.
"""

from __future__ import annotations

from typing import Any, Mapping

from rescue.hardware_state_sentinel import HardwareDeviceState, transition_device


def apply_lifecycle_step(
    device: HardwareDeviceState,
    step: str,
    *,
    context: Mapping[str, Any],
) -> dict[str, Any]:
    """Apply one lifecycle step and return the structured event."""
    return transition_device(
        device,
        step,
        run_id=str(context.get("run_id") or ""),
        boot_id=str(context.get("boot_id") or ""),
        boot_attempt=int(context.get("boot_attempt") or 0),
        boot_profile=str(context.get("boot_profile") or ""),
        boot_stage=str(context.get("boot_stage") or ""),
        driver_expected=context.get("driver_expected"),  # type: ignore[arg-type]
        driver_actual=context.get("driver_actual"),  # type: ignore[arg-type]
        module_state=context.get("module_state"),  # type: ignore[arg-type]
        firmware_state=context.get("firmware_state"),  # type: ignore[arg-type]
        operational_state=context.get("operational_state"),  # type: ignore[arg-type]
        issue_code=str(context.get("issue_code") or ""),
        technical_summary=str(context.get("technical_summary") or ""),
        evidence_refs=list(context.get("evidence_refs") or []),
    )


def summarize_devices(devices: Mapping[str, HardwareDeviceState]) -> dict[str, Any]:
    missing_drivers = []
    missing_firmware = []
    degraded = []
    blocked = []
    for dev in devices.values():
        if dev.state in {"driver_missing", "driver_unknown", "driver_bind_failed", "module_load_failed"}:
            missing_drivers.append(
                {
                    "device_id": dev.device_id,
                    "device_class": dev.device_class,
                    "driver_expected": dev.driver_expected,
                    "state": dev.state,
                }
            )
        if dev.state in {"firmware_missing", "firmware_load_failed"}:
            missing_firmware.append(
                {
                    "device_id": dev.device_id,
                    "device_class": dev.device_class,
                    "state": dev.state,
                }
            )
        if dev.state == "degraded":
            degraded.append(dev.device_id)
        if dev.state == "blocked":
            blocked.append(dev.device_id)
    return {
        "device_count": len(devices),
        "missing_drivers": missing_drivers,
        "missing_firmware": missing_firmware,
        "degraded_devices": degraded,
        "blocked_devices": blocked,
    }
