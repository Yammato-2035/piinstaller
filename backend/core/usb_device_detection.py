"""
USB device classification — read-only, USB class-code driven.

PI-RS-HW-COMPAT-PROVISION-001 Phase 6.

Multi-function ("composite") USB devices are modeled as multiple independent
``PeripheralCapability`` entries (spec requirement: detecting a printer interface
must never imply the scanner interface on the same device also works).

Sources: USB device/interface class codes from sysfs
(``/sys/bus/usb/devices/<dev>/bDeviceClass`` and per-interface
``<dev>:<cfg>.<if>/bInterfaceClass`` etc.). All sysfs access is injectable via
``sysfs_root`` or direct ``class_info`` dict, so tests never touch real USB.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from core.hardware_contracts import PeripheralCapability

USB_DEVICE_DETECTION_VERSION = 1

# USB-IF base class codes (hex, lowercase, no "0x" prefix) -> generic function label.
_USB_CLASS_TO_FUNCTION: dict[str, str] = {
    "01": "audio",
    "02": "serial_adapter",  # CDC control
    "03": "hid_generic",
    "06": "still_image",  # scanner/camera candidate, needs corroboration
    "07": "printer",
    "08": "storage",
    "09": "hub",
    "0a": "cdc_data",
    "0b": "smartcard",
    "0e": "video",  # webcam (UVC)
    "e0": "wireless_controller",  # Bluetooth adapters typically report this
    "ef": "composite",
    "ff": "vendor_specific",
}

# HID boot-interface protocol codes (bInterfaceSubClass=1 "boot interface").
_HID_BOOT_PROTOCOL_KEYBOARD = "1"
_HID_BOOT_PROTOCOL_MOUSE = "2"


def classify_interface(interface_class: str | None, interface_subclass: str | None, interface_protocol: str | None) -> str:
    """Map one USB interface's class/subclass/protocol to a function label."""
    cls = (interface_class or "").lower().removeprefix("0x")
    cls = cls or "00"
    base = _USB_CLASS_TO_FUNCTION.get(cls, "unknown")
    if base == "hid_generic" and (interface_subclass or "") in ("1", "01"):
        if (interface_protocol or "") in (_HID_BOOT_PROTOCOL_KEYBOARD, "01"):
            return "keyboard"
        if (interface_protocol or "") in (_HID_BOOT_PROTOCOL_MOUSE, "02"):
            return "mouse"
        return "hid_generic"
    return base


def collect_usb_class_info(*, sysfs_root: Path | None = None) -> dict[str, dict[str, Any]]:
    """Read ``bDeviceClass``/interface class files under ``/sys/bus/usb/devices``.

    Returns ``{usb_dev_name: {"device_class": "...", "interfaces": [...]}}``.
    Empty dict (not a crash) if sysfs is unavailable.
    """
    root = sysfs_root or Path("/")
    base = root / "sys" / "bus" / "usb" / "devices"
    out: dict[str, dict[str, Any]] = {}
    if not base.exists():
        return out
    try:
        for entry in sorted(base.iterdir()):
            if ":" in entry.name or entry.name.startswith("usb"):
                continue  # skip interface entries and root hubs here
            device_class_path = entry / "bDeviceClass"
            device_class = None
            if device_class_path.exists():
                try:
                    device_class = device_class_path.read_text(encoding="utf-8", errors="ignore").strip()
                except OSError:
                    pass
            interfaces: list[dict[str, str | None]] = []
            for iface_dir in sorted(base.glob(f"{entry.name}:*")):
                iface_class = _read_optional(iface_dir / "bInterfaceClass")
                iface_subclass = _read_optional(iface_dir / "bInterfaceSubClass")
                iface_protocol = _read_optional(iface_dir / "bInterfaceProtocol")
                interfaces.append(
                    {
                        "interface_class": iface_class,
                        "interface_subclass": iface_subclass,
                        "interface_protocol": iface_protocol,
                    }
                )
            out[entry.name] = {"device_class": device_class, "interfaces": interfaces}
    except OSError:
        pass
    return out


def _read_optional(path: Path) -> str | None:
    if not path.exists():
        return None
    try:
        return path.read_text(encoding="utf-8", errors="ignore").strip()
    except OSError:
        return None


def classify_usb_device(
    *, device_id: str, class_info: dict[str, Any] | None
) -> list[PeripheralCapability]:
    """Build one PeripheralCapability per distinct function found on the device.

    A device with no usable class info at all stays a single "unknown" capability —
    never guessed from vendor/product name alone (spec requirement).
    """
    if not class_info:
        return [PeripheralCapability(function="unknown", operational_status="unknown", detection_confidence=0.2)]

    device_class = (class_info.get("device_class") or "").lower().removeprefix("0x") or None
    interfaces = class_info.get("interfaces") or []

    functions_found: dict[str, dict[str, Any]] = {}

    if device_class and device_class != "00" and device_class != "ef":
        # Non-composite device: bDeviceClass itself carries the function.
        label = _USB_CLASS_TO_FUNCTION.get(device_class, "unknown")
        functions_found[label] = {"source": "device_class"}

    for iface in interfaces:
        label = classify_interface(
            iface.get("interface_class"), iface.get("interface_subclass"), iface.get("interface_protocol")
        )
        if label != "unknown":
            functions_found.setdefault(label, {"source": "interface_class"})

    if not functions_found:
        return [PeripheralCapability(function="unknown", operational_status="unknown", detection_confidence=0.2)]

    caps: list[PeripheralCapability] = []
    for function, details in functions_found.items():
        # "still_image" is a candidate signal for scanner/camera, not a confirmed
        # function — mark review_required rather than asserting "scanner works".
        status = "review_required" if function in ("still_image", "hid_generic", "vendor_specific") else "detected"
        confidence = 0.9 if details.get("source") == "device_class" else 0.7
        caps.append(
            PeripheralCapability(
                function=function,
                operational_status=status,
                detection_confidence=confidence,
                details={"device_id": device_id, "source": details.get("source")},
            )
        )
    return caps


def is_composite_device(class_info: dict[str, Any] | None) -> bool:
    if not class_info:
        return False
    device_class = (class_info.get("device_class") or "").lower().removeprefix("0x")
    interfaces = class_info.get("interfaces") or []
    distinct_interface_classes = {i.get("interface_class") for i in interfaces if i.get("interface_class")}
    return device_class == "ef" or len(distinct_interface_classes) > 1


def build_usb_device_detection_diagnostics() -> dict[str, Any]:
    return {
        "detection_version": USB_DEVICE_DETECTION_VERSION,
        "module": "core.usb_device_detection",
        "read_only": True,
        "writes_allowed": False,
        "known_class_codes": sorted(_USB_CLASS_TO_FUNCTION.keys()),
    }


__all__ = [
    "USB_DEVICE_DETECTION_VERSION",
    "classify_interface",
    "collect_usb_class_info",
    "classify_usb_device",
    "is_composite_device",
    "build_usb_device_detection_diagnostics",
]
