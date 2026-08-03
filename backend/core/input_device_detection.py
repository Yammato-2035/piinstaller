"""
Input device (keyboard/mouse/touchpad/...) classification — read-only.

PI-RS-HW-COMPAT-PROVISION-001 Phase 7.

Strict privacy rule (spec requirement): this module only ever sees device metadata
produced by ``hardware_inventory.collect_input_devices`` (name, handlers, bus code,
vendor/product ID). It never reads ``/dev/input/event*`` and has no code path that
could observe key presses, pointer movement, or any input *event* data.
"""

from __future__ import annotations

from typing import Any

from core.hardware_contracts import HardwareDevice

INPUT_DEVICE_DETECTION_VERSION = 1

# linux/input.h BUS_* codes as they appear (zero-padded hex, no "0x") in
# /proc/bus/input/devices "I: Bus=" field.
_BUS_CODE_NAMES = {
    "0001": "pci",
    "0003": "usb",
    "0005": "bluetooth",
    "0006": "virtual",
    "0011": "i8042",
    "0018": "host",
    "001d": "cec",
    "001e": "intel_ishtp",
}


def classify_bus_code(subclass: str | None) -> str:
    code = (subclass or "").lower()
    return _BUS_CODE_NAMES.get(code, "unknown")


def classify_input_function(device: HardwareDevice) -> tuple[str, str]:
    """Return (function, confidence_hint). Ambiguous cases -> ("generic_input", "low")."""
    name = (device.product_name or "").lower()
    handlers = set(device.driver.kernel_modules_loaded)
    bus_type = classify_bus_code(device.subclass)

    if "kvm" in name and ("composite" in name or "switch" in name):
        return "kvm_composite", "medium"
    if "touchpad" in name or "trackpad" in name:
        return "touchpad", "high"
    if "trackpoint" in name or "trackball" in name:
        return "trackpoint", "high"
    if "touchscreen" in name or "touch screen" in name:
        return "touchscreen", "high"
    if "wacom" in name or ("tablet" in name and "graphics" in name):
        return "graphics_tablet", "medium"
    if any(h.startswith("js") for h in handlers) or "joystick" in name or "gamepad" in name or "controller" in name:
        return "gaming_hid", "medium"

    has_kbd_handler = any(h.startswith("kbd") for h in handlers)
    has_mouse_handler = any(h.startswith("mouse") for h in handlers)

    if has_kbd_handler:
        if bus_type == "i8042" or "at translated" in name:
            return "laptop_keyboard", "high"
        if bus_type == "bluetooth":
            return "bluetooth_keyboard", "medium"
        return "keyboard", "high"
    if has_mouse_handler:
        if bus_type == "bluetooth":
            return "bluetooth_mouse", "medium"
        return "mouse", "high"
    if not handlers:
        return "generic_input", "low"
    return "generic_input", "low"


def build_input_device_report(devices: list[HardwareDevice]) -> list[dict[str, Any]]:
    """Enrich raw input HardwareDevice rows with function classification.

    Bluetooth devices are only ever reported if the kernel already surfaced them via
    ``/proc/bus/input/devices`` (i.e. currently connected) — no separate BT scan is
    triggered here (spec: no active pairing / connection attempts).
    """
    report: list[dict[str, Any]] = []
    for device in devices:
        function, confidence_hint = classify_input_function(device)
        operational_status = "ready" if function not in ("generic_input",) and device.product_name else "unknown"
        if function == "generic_input":
            operational_status = "review_required" if device.product_name else "unknown"
        report.append(
            {
                "device_id": device.device_id,
                "product_name": device.product_name,
                "bus_type": classify_bus_code(device.subclass),
                "function": function,
                "confidence_hint": confidence_hint,
                "operational_status": operational_status,
                "vendor_id": device.vendor_id,
                "product_id": device.product_id,
            }
        )
    return report


def build_input_device_detection_diagnostics() -> dict[str, Any]:
    return {
        "detection_version": INPUT_DEVICE_DETECTION_VERSION,
        "module": "core.input_device_detection",
        "read_only": True,
        "writes_allowed": False,
        "captures_input_events": False,
        "captures_keystrokes": False,
        "captures_pointer_movement": False,
    }


__all__ = [
    "INPUT_DEVICE_DETECTION_VERSION",
    "classify_bus_code",
    "classify_input_function",
    "build_input_device_report",
    "build_input_device_detection_diagnostics",
]
