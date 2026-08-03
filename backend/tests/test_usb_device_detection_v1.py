"""PI-RS-HW-COMPAT-PROVISION-001 Phase 6: usb_device_detection.py tests.

Fixture groups per spec PHASE 17: USB keyboard, USB mouse, USB hub, USB mass
storage, multifunction device (printer+scanner), unknown USB device.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from core.usb_device_detection import (
    build_usb_device_detection_diagnostics,
    classify_usb_device,
    is_composite_device,
)


class TestSingleFunctionDevices(unittest.TestCase):
    def test_usb_keyboard_via_hid_boot_protocol(self) -> None:
        class_info = {
            "device_class": "00",
            "interfaces": [{"interface_class": "03", "interface_subclass": "1", "interface_protocol": "1"}],
        }
        caps = classify_usb_device(device_id="usb:1-2", class_info=class_info)
        self.assertEqual(len(caps), 1)
        self.assertEqual(caps[0].function, "keyboard")
        self.assertEqual(caps[0].operational_status, "detected")

    def test_usb_mouse_via_hid_boot_protocol(self) -> None:
        class_info = {
            "device_class": "00",
            "interfaces": [{"interface_class": "03", "interface_subclass": "1", "interface_protocol": "2"}],
        }
        caps = classify_usb_device(device_id="usb:1-3", class_info=class_info)
        self.assertEqual(caps[0].function, "mouse")

    def test_usb_hub(self) -> None:
        class_info = {"device_class": "09", "interfaces": []}
        caps = classify_usb_device(device_id="usb:1-0", class_info=class_info)
        self.assertEqual(caps[0].function, "hub")

    def test_usb_mass_storage(self) -> None:
        class_info = {"device_class": "08", "interfaces": [{"interface_class": "08", "interface_subclass": "6", "interface_protocol": "50"}]}
        caps = classify_usb_device(device_id="usb:1-4", class_info=class_info)
        self.assertEqual(caps[0].function, "storage")
        self.assertEqual(caps[0].operational_status, "detected")

    def test_unknown_usb_device_stays_unknown(self) -> None:
        caps = classify_usb_device(device_id="usb:1-9", class_info=None)
        self.assertEqual(len(caps), 1)
        self.assertEqual(caps[0].function, "unknown")
        self.assertEqual(caps[0].operational_status, "unknown")


class TestCompositeMultifunctionDevices(unittest.TestCase):
    def test_printer_scanner_mfp_has_independent_functions(self) -> None:
        class_info = {
            "device_class": "ef",  # composite
            "interfaces": [
                {"interface_class": "07", "interface_subclass": "1", "interface_protocol": "2"},  # printer
                {"interface_class": "06", "interface_subclass": None, "interface_protocol": None},  # still image (scanner candidate)
            ],
        }
        caps = classify_usb_device(device_id="usb:2-1", class_info=class_info)
        functions = {c.function for c in caps}
        self.assertIn("printer", functions)
        self.assertIn("still_image", functions)
        printer_cap = next(c for c in caps if c.function == "printer")
        scanner_cap = next(c for c in caps if c.function == "still_image")
        # Independence: printer confirmed does not imply scanner confirmed.
        self.assertEqual(printer_cap.operational_status, "detected")
        self.assertEqual(scanner_cap.operational_status, "review_required")
        self.assertTrue(is_composite_device(class_info))

    def test_single_function_device_is_not_composite(self) -> None:
        class_info = {"device_class": "08", "interfaces": [{"interface_class": "08", "interface_subclass": "6", "interface_protocol": "50"}]}
        self.assertFalse(is_composite_device(class_info))


class TestDiagnostics(unittest.TestCase):
    def test_diagnostics_read_only(self) -> None:
        diag = build_usb_device_detection_diagnostics()
        self.assertTrue(diag["read_only"])
        self.assertFalse(diag["writes_allowed"])


if __name__ == "__main__":
    unittest.main()
