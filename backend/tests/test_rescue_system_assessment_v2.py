"""System assessment V2 tests."""

from __future__ import annotations

import unittest

from core.rescue_system_assessment_v2 import (
    ASSESSMENT_SCHEMA_VERSION,
    build_assessment_from_snapshot,
    build_system_assessment_v2,
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


if __name__ == "__main__":
    unittest.main()
