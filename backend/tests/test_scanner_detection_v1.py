"""PI-RS-HW-COMPAT-PROVISION-001 Phase 8: scanner_detection.py + scanner_driver_resolver.py."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from peripherals.scanner_detection import (
    build_scanner_detection_diagnostics,
    build_scanner_report,
    classify_scanner_source,
    parse_sane_find_scanner,
    parse_scanimage_l,
)
from peripherals.scanner_driver_resolver import build_scanner_driver_resolver_diagnostics, resolve_scanner_driver_plan

SCANIMAGE_L_SAMPLE = "device `pixma:04A91764_5F3D21' is a CANON Canon PIXMA MG3000 Series multi-function peripheral\n"
SANE_FIND_SAMPLE = "found USB scanner (vendor=0x04a9 [Canon], product=0x1764 [MG3000]) at libusb:001:004\n"


class TestParsing(unittest.TestCase):
    def test_scanimage_l_parses_backend_device(self) -> None:
        rows = parse_scanimage_l(SCANIMAGE_L_SAMPLE)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["backend_device"], "pixma:04A91764_5F3D21")

    def test_sane_find_scanner_parses_usb_line(self) -> None:
        rows = parse_sane_find_scanner(SANE_FIND_SAMPLE)
        self.assertEqual(len(rows), 1)


class TestSourceClassification(unittest.TestCase):
    def test_sane_backend_preferred_source(self) -> None:
        self.assertEqual(
            classify_scanner_source(has_sane_backend=True, has_escl=False, is_usb_still_image=True), "sane_backend"
        )

    def test_usb_still_image_only_is_review_required_source(self) -> None:
        source = classify_scanner_source(has_sane_backend=False, has_escl=False, is_usb_still_image=True)
        self.assertEqual(source, "usb_still_image")

    def test_no_evidence_is_unknown(self) -> None:
        source = classify_scanner_source(has_sane_backend=False, has_escl=False, is_usb_still_image=False)
        self.assertEqual(source, "unknown")


class TestReportAndIndependenceFromPrinter(unittest.TestCase):
    def test_pure_usb_scanner_needs_physical_test(self) -> None:
        report = build_scanner_report(device_id="usb:3-1", is_usb_still_image=True)
        self.assertEqual(report["source"], "usb_still_image")
        self.assertEqual(report["operational_status"], "review_required")
        self.assertTrue(report["requires_physical_scan_test"])

    def test_network_scanner_via_escl(self) -> None:
        report = build_scanner_report(device_id="net:scanner-1", has_escl=True, is_network_device=True)
        self.assertEqual(report["source"], "escl_airscan")
        self.assertEqual(report["operational_status"], "ready")
        self.assertTrue(report["is_network_device"])

    def test_mfp_scanner_function_independent_report(self) -> None:
        """A MFP's scanner function gets its own report entry, unaffected by printer status."""
        scanner_report = build_scanner_report(device_id="usb:2-1:scanner", is_usb_still_image=True)
        self.assertNotIn("printer", scanner_report)
        self.assertEqual(scanner_report["operational_status"], "review_required")


class TestDriverResolver(unittest.TestCase):
    def test_sane_backend_gets_generic_backend_recommendation(self) -> None:
        report = build_scanner_report(device_id="usb:3-1", has_sane_backend=True)
        plan = resolve_scanner_driver_plan(report)
        self.assertEqual(plan["recommended_driver"], "sane_generic_backend")
        self.assertFalse(plan["scan_test_performed"])

    def test_still_image_only_flags_review_required(self) -> None:
        report = build_scanner_report(device_id="usb:3-2", is_usb_still_image=True)
        plan = resolve_scanner_driver_plan(report)
        self.assertIn("still_image_class_only_no_confirmed_sane_backend_review_required", plan["warnings"])

    def test_diagnostics_never_triggers_scan(self) -> None:
        diag = build_scanner_detection_diagnostics()
        self.assertFalse(diag["scan_triggered"])
        rdiag = build_scanner_driver_resolver_diagnostics()
        self.assertFalse(rdiag["scan_triggered"])
        self.assertFalse(rdiag["auto_install"])


if __name__ == "__main__":
    unittest.main()
