"""System assessment V2 tests."""

from __future__ import annotations

import unittest

from core.rescue_system_assessment_v2 import (
    ASSESSMENT_SCHEMA_VERSION,
    build_assessment_from_snapshot,
    build_system_assessment_v2,
    derive_driver_hints,
    derive_issue_codes,
)


class RescueSystemAssessmentV2Tests(unittest.TestCase):
    def test_build_from_snapshot_no_crash(self) -> None:
        snap = {
            "system": {"missing_tools": ["dmidecode"]},
            "storage": {"smart_summary": [{"device": "sda", "health_passed": False}]},
            "pcie_aer": {"fatal_count": 0, "pci_noaer_cmdline": True},
            "firmware": {"dmesg_missing_firmware_redacted": ["firmware missing"]},
        }
        result = build_assessment_from_snapshot(snap)
        self.assertEqual(result["assessment"]["schema_version"], ASSESSMENT_SCHEMA_VERSION)
        self.assertIn("missing_tool", result["issue_codes"])

    def test_live_build_produces_json(self) -> None:
        result = build_system_assessment_v2(rescue_version="1.9.17.0")
        self.assertIn("assessment", result)
        self.assertIn("redaction_report", result)

    def test_missing_tool_issue_code(self) -> None:
        codes = derive_issue_codes({"storage": {"missing_tools": ["smartctl"]}})
        self.assertIn("missing_tool", codes)

    def test_bios_info_unavailable_issue_code(self) -> None:
        codes = derive_issue_codes({"mainboard": {"bios_version": None, "missing_tools": []}})
        self.assertIn("bios_info_unavailable", codes)

    def test_cpu_info_partial_issue_code(self) -> None:
        codes = derive_issue_codes({"cpu_ram": {"cpu_vendor": None, "missing_tools": []}})
        self.assertIn("cpu_info_partial", codes)

    def test_gpu_driver_missing_issue_code(self) -> None:
        codes = derive_issue_codes({"gpu": {"vendor_driver_gaps": ["nvidia"], "missing_tools": []}})
        self.assertIn("gpu_driver_missing", codes)

    def test_live_build_includes_mainboard_and_cpu_vendor_display(self) -> None:
        result = build_system_assessment_v2(rescue_version="1.9.17.0")
        assessment = result["assessment"]
        self.assertIn("mainboard", assessment)
        self.assertIn("board_vendor", assessment["mainboard"])
        self.assertIn("bios_version", assessment["mainboard"])
        self.assertIn("cpu_vendor_display", assessment["cpu_ram"])
        self.assertIn("integrated_graphics_present", assessment["gpu"])
        self.assertIn("vendor_driver_gaps", assessment["gpu"])
        self.assertIn("peripherals", assessment)
        self.assertIn("driver_hints", result)

    def test_driver_hints_from_gpu_vendor_gap(self) -> None:
        hints = derive_driver_hints({"gpu": {"vendor_driver_gaps": ["nvidia"]}})
        self.assertEqual(len(hints), 1)
        self.assertEqual(hints[0]["vendor"], "NVIDIA")
        self.assertEqual(hints[0]["context"], "gpu")

    def test_driver_hints_from_peripheral_printer(self) -> None:
        snapshot = {
            "peripherals": {
                "usb": {"devices": [{"description": "Canon LaserJet Printer", "kind": "printer"}]}
            }
        }
        hints = derive_driver_hints(snapshot)
        self.assertEqual(len(hints), 1)
        self.assertEqual(hints[0]["vendor"], "Canon")
        self.assertEqual(hints[0]["context"], "printer")

    def test_driver_hints_dedupe(self) -> None:
        snapshot = {"gpu": {"vendor_driver_gaps": ["nvidia", "nvidia"]}}
        hints = derive_driver_hints(snapshot)
        self.assertEqual(len(hints), 1)

    def test_driver_hints_empty_when_no_match(self) -> None:
        self.assertEqual(derive_driver_hints({}), [])


if __name__ == "__main__":
    unittest.main()
