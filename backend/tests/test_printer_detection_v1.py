"""PI-RS-HW-COMPAT-PROVISION-001 Phase 8: printer_detection.py + printer_driver_resolver.py.

Fixture groups per spec PHASE 17: inkjet, monochrome laser, color laser,
multifunction (printer+scanner), matrix printer via USB-parallel adapter.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from peripherals.printer_detection import (
    build_printer_detection_diagnostics,
    build_printer_report,
    classify_color_capability,
    classify_device_kind,
    classify_printer_technology,
    parse_lpstat_v,
)
from peripherals.printer_driver_resolver import build_printer_driver_resolver_diagnostics, resolve_printer_driver_plan

PPD_MONO_LASER = "*ModelName: \"LaserJet Pro M15w\"\n*Technology: laser\n*ColorDevice: False\n"
PPD_COLOR_LASER = "*ModelName: \"Color LaserJet Pro M255dw\"\n*Technology: laser\n*ColorDevice: True\n"

LPSTAT_SAMPLE = "device for HP_LaserJet: usb://HP/LaserJet%20Pro%20M15w\ndevice for Network_Printer: ipp://192.0.2.5/ipp/print\n"


class TestClassificationDefaultsToUnknown(unittest.TestCase):
    def test_no_evidence_stays_unknown_review_required(self) -> None:
        tech, status = classify_printer_technology()
        self.assertEqual(tech, "unknown")
        self.assertEqual(status, "review_required")
        color, cstatus = classify_color_capability()
        self.assertEqual(color, "unknown")
        self.assertEqual(cstatus, "review_required")

    def test_model_name_alone_is_not_evidence(self) -> None:
        """Spec: technology/color must not be guessed from a free-text model name."""
        tech, status = classify_printer_technology(ppd_text="*ModelName: \"Epson Stylus Color 900\"\n")
        self.assertEqual(tech, "unknown")
        self.assertEqual(status, "review_required")


class TestConfirmedClassification(unittest.TestCase):
    def test_monochrome_laser_confirmed_via_ppd(self) -> None:
        tech, tstatus = classify_printer_technology(ppd_text=PPD_MONO_LASER)
        color, cstatus = classify_color_capability(ppd_text=PPD_MONO_LASER)
        self.assertEqual(tech, "laser")
        self.assertEqual(tstatus, "confirmed")
        self.assertEqual(color, "monochrome")
        self.assertEqual(cstatus, "confirmed")

    def test_color_laser_confirmed_via_ppd(self) -> None:
        tech, _ = classify_printer_technology(ppd_text=PPD_COLOR_LASER)
        color, _ = classify_color_capability(ppd_text=PPD_COLOR_LASER)
        self.assertEqual(tech, "laser")
        self.assertEqual(color, "color")

    def test_inkjet_confirmed_via_ipp_output_supported(self) -> None:
        tech, status = classify_printer_technology(ipp_output_supported="photo, inkjet")
        self.assertEqual(tech, "inkjet")
        self.assertEqual(status, "confirmed")

    def test_matrix_via_ppd_dot_matrix_alias(self) -> None:
        tech, status = classify_printer_technology(ppd_text="*ModelName: \"Epson LX-350\"\n*Technology: dot matrix\n")
        self.assertEqual(tech, "matrix")
        self.assertEqual(status, "confirmed")


class TestDeviceKindAndMultifunction(unittest.TestCase):
    def test_multifunction_when_both_functions_present(self) -> None:
        self.assertEqual(classify_device_kind(has_printer_function=True, has_scanner_function=True), "multifunction")

    def test_printer_only(self) -> None:
        self.assertEqual(classify_device_kind(has_printer_function=True, has_scanner_function=False), "printer")

    def test_report_flags_mfp_needs_physical_test(self) -> None:
        report = build_printer_report(
            device_id="usb:2-1", has_printer_function=True, has_scanner_function=True, ppd_text=PPD_COLOR_LASER
        )
        self.assertEqual(report["device_kind"], "multifunction")
        self.assertTrue(report["requires_physical_print_test"])
        self.assertEqual(report["classification_status"], "confirmed")


class TestLpstatParsing(unittest.TestCase):
    def test_parses_queue_and_uri(self) -> None:
        rows = parse_lpstat_v(LPSTAT_SAMPLE)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]["queue_name"], "HP_LaserJet")


class TestDriverOrderAndResolver(unittest.TestCase):
    def test_driverless_ipp_preferred_when_supported(self) -> None:
        report = build_printer_report(
            device_id="usb:2-1", has_printer_function=True, driverless_ipp_supported=True, ppd_text=PPD_MONO_LASER
        )
        self.assertEqual(report["driver_order"][0], "driverless_ipp")
        plan = resolve_printer_driver_plan(report)
        self.assertEqual(plan["recommended_driver"], "driverless_ipp")
        self.assertFalse(plan["test_print_performed"])

    def test_review_required_when_unconfirmed(self) -> None:
        report = build_printer_report(device_id="usb:2-2", has_printer_function=True)
        plan = resolve_printer_driver_plan(report)
        self.assertIn("technology_or_color_capability_unconfirmed_review_required", plan["warnings"])

    def test_diagnostics_never_triggers_test_print(self) -> None:
        diag = build_printer_detection_diagnostics()
        self.assertFalse(diag["test_print_triggered"])
        self.assertFalse(diag["cups_queue_modified"])
        rdiag = build_printer_driver_resolver_diagnostics()
        self.assertFalse(rdiag["auto_install"])
        self.assertFalse(rdiag["test_print_triggered"])


if __name__ == "__main__":
    unittest.main()
