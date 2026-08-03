"""PI-RS-HW-COMPAT-PROVISION-001 Phase 7: input_device_detection.py tests."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from core.hardware_contracts import Bus, HardwareDevice, HardwareDriverState
from core.hardware_inventory import collect_input_devices
from core.input_device_detection import (
    build_input_device_detection_diagnostics,
    build_input_device_report,
    classify_bus_code,
)

USB_KEYBOARD_MOUSE_TOUCHPAD_SAMPLE = """I: Bus=0003 Vendor=046d Product=c31c Version=0111
N: Name="Logitech USB Keyboard"
S: Sysfs=/devices/usb1/1-2/input0
H: Handlers=sysrq kbd event3

I: Bus=0003 Vendor=046d Product=c077 Version=0111
N: Name="Logitech USB Optical Mouse"
S: Sysfs=/devices/usb1/1-3/input1
H: Handlers=mouse0 event4

I: Bus=0011 Vendor=0002 Product=0007 Version=ab83
N: Name="AT Translated Set 2 keyboard"
S: Sysfs=/devices/platform/i8042/serio0/input/input2
H: Handlers=sysrq kbd event0

I: Bus=0018 Vendor=0000 Product=0000 Version=0000
N: Name="SynPS/2 Synaptics TouchPad"
S: Sysfs=/devices/platform/i8042/serio1/input/input5
H: Handlers=mouse1 event5
"""


def _device(name: str, subclass: str, handlers: tuple[str, ...], vendor="1234", product="5678") -> HardwareDevice:
    return HardwareDevice(
        device_id=f"input:{name}",
        device_class="input",
        subclass=subclass,
        bus=Bus.INPUT,
        vendor_id=vendor,
        product_id=product,
        product_name=name,
        driver=HardwareDriverState(kernel_modules_loaded=handlers),
    )


class TestBusClassification(unittest.TestCase):
    def test_known_bus_codes(self) -> None:
        self.assertEqual(classify_bus_code("0003"), "usb")
        self.assertEqual(classify_bus_code("0011"), "i8042")
        self.assertEqual(classify_bus_code("0005"), "bluetooth")

    def test_unknown_bus_code_stays_unknown(self) -> None:
        self.assertEqual(classify_bus_code("abcd"), "unknown")
        self.assertEqual(classify_bus_code(None), "unknown")


class TestInputFunctionClassification(unittest.TestCase):
    def test_usb_keyboard(self) -> None:
        dev = _device("Logitech USB Keyboard", "0003", ("kbd", "event3"))
        report = build_input_device_report([dev])
        self.assertEqual(report[0]["function"], "keyboard")
        self.assertEqual(report[0]["operational_status"], "ready")

    def test_usb_mouse(self) -> None:
        dev = _device("Logitech USB Optical Mouse", "0003", ("mouse0", "event4"))
        report = build_input_device_report([dev])
        self.assertEqual(report[0]["function"], "mouse")

    def test_laptop_keyboard_via_i8042_bus(self) -> None:
        dev = _device("AT Translated Set 2 keyboard", "0011", ("kbd", "event0"))
        report = build_input_device_report([dev])
        self.assertEqual(report[0]["function"], "laptop_keyboard")

    def test_touchpad_via_name(self) -> None:
        dev = _device("SynPS/2 Synaptics TouchPad", "0018", ("mouse1", "event5"))
        report = build_input_device_report([dev])
        self.assertEqual(report[0]["function"], "touchpad")

    def test_ambiguous_device_is_review_required_not_guessed(self) -> None:
        dev = _device("Some Unknown Composite Device", "0006", ())
        report = build_input_device_report([dev])
        self.assertEqual(report[0]["function"], "generic_input")
        self.assertEqual(report[0]["operational_status"], "review_required")


class TestIntegrationWithHardwareInventoryCollector(unittest.TestCase):
    def test_full_pipeline_from_raw_proc_text(self) -> None:
        devices, missing = collect_input_devices(raw_text=USB_KEYBOARD_MOUSE_TOUCHPAD_SAMPLE)
        self.assertEqual(missing, [])
        self.assertEqual(len(devices), 4)
        report = build_input_device_report(devices)
        functions = [r["function"] for r in report]
        self.assertIn("keyboard", functions)
        self.assertIn("mouse", functions)
        self.assertIn("laptop_keyboard", functions)
        self.assertIn("touchpad", functions)


class TestPrivacyDiagnostics(unittest.TestCase):
    def test_no_input_event_capture_flags(self) -> None:
        diag = build_input_device_detection_diagnostics()
        self.assertFalse(diag["captures_input_events"])
        self.assertFalse(diag["captures_keystrokes"])
        self.assertFalse(diag["captures_pointer_movement"])


if __name__ == "__main__":
    unittest.main()
