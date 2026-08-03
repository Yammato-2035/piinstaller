"""Rescue peripheral discovery tests."""

from __future__ import annotations

import unittest

from core.rescue_peripheral_discovery import _classify_usb_line, build_peripheral_inventory


class ClassifyUsbLineTests(unittest.TestCase):
    def test_keyboard_keyword(self) -> None:
        self.assertEqual(_classify_usb_line("Logitech, Inc. Keyboard K120"), "keyboard")

    def test_mouse_keyword(self) -> None:
        self.assertEqual(_classify_usb_line("Logitech, Inc. Optical Mouse"), "mouse")

    def test_printer_keyword(self) -> None:
        self.assertEqual(_classify_usb_line("Canon, Inc. LaserJet Printer"), "printer")

    def test_webcam_keyword(self) -> None:
        self.assertEqual(_classify_usb_line("Chicony Electronics Integrated Camera"), "webcam")

    def test_unknown_falls_back_to_usb(self) -> None:
        self.assertEqual(_classify_usb_line("Some Unknown Device"), "usb")


class BuildPeripheralInventoryTests(unittest.TestCase):
    def test_never_crashes_and_has_expected_keys(self) -> None:
        result = build_peripheral_inventory()
        self.assertIn("usb", result)
        self.assertIn("input_devices", result)
        self.assertIn("audio", result)
        self.assertIn("missing_tools", result)


if __name__ == "__main__":
    unittest.main()
