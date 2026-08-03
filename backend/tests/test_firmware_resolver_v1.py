"""PI-RS-HW-COMPAT-PROVISION-001 Phase 9: firmware_resolver.py tests."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from core.firmware_resolver import build_firmware_report, build_firmware_resolver_diagnostics, evaluate_firmware_status
from core.hardware_contracts import FirmwareStatus

DMESG_LINES = [
    "usb 1-2: firmware: failed to load radeon/R600_rlc.bin (-2)",
    "Bluetooth: hci0: Direct firmware load failed with error -2",
]


class TestEvaluateFirmwareStatus(unittest.TestCase):
    def test_missing_firmware_matched_by_driver_name(self) -> None:
        status, matched = evaluate_firmware_status(driver_name="radeon", missing_firmware_lines=DMESG_LINES)
        self.assertEqual(status, FirmwareStatus.MISSING)
        self.assertEqual(len(matched), 1)

    def test_no_driver_name_stays_unknown_not_not_required(self) -> None:
        status, matched = evaluate_firmware_status(driver_name=None, missing_firmware_lines=DMESG_LINES)
        self.assertEqual(status, FirmwareStatus.UNKNOWN)
        self.assertEqual(matched, [])

    def test_driver_with_no_matching_error_stays_unknown(self) -> None:
        status, matched = evaluate_firmware_status(driver_name="e1000e", missing_firmware_lines=DMESG_LINES)
        self.assertEqual(status, FirmwareStatus.UNKNOWN)
        self.assertEqual(matched, [])


class TestBuildFirmwareReport(unittest.TestCase):
    def test_report_covers_each_device(self) -> None:
        report = build_firmware_report(
            devices_with_drivers=[("pci:01:00.0", "radeon"), ("net:eth0", "e1000e")],
            missing_firmware_lines=DMESG_LINES,
        )
        self.assertEqual(len(report), 2)
        radeon_entry = next(r for r in report if r["driver_name"] == "radeon")
        self.assertEqual(radeon_entry["firmware_status"], "missing")

    def test_diagnostics_never_downloads(self) -> None:
        diag = build_firmware_resolver_diagnostics()
        self.assertFalse(diag["firmware_download_triggered"])


if __name__ == "__main__":
    unittest.main()
