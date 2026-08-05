"""PI-RS-HW-BASELINE-DIAG-I18N-002 Phase 7: hdd_baseline_diagnostics.py tests.

Fixture groups per spec PHASE 18: clean SMART, pending sectors, offline
uncorrectable, reallocated sectors, CRC errors, high temperature, SMART
FAILED, missing smartctl, repeated I/O errors.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from core.hardware_baseline_contracts import BaselineSeverity, BaselineStatus
from core.hdd_baseline_diagnostics import (
    build_hdd_baseline_diagnostics,
    build_hdd_baseline_result,
    parse_smartctl_attributes,
    parse_smartctl_overall_health,
)

_HEALTH_PASSED = "SMART overall-health self-assessment test result: PASSED\n"
_HEALTH_FAILED = "SMART overall-health self-assessment test result: FAILED!\n"


def _attr_table(overrides: dict[int, int] | None = None) -> str:
    values = {5: 0, 194: 35, 197: 0, 198: 0, 199: 0}
    if overrides:
        values.update(overrides)
    lines = [
        "ID# ATTRIBUTE_NAME          FLAG     VALUE WORST THRESH TYPE      UPDATED  WHEN_FAILED RAW_VALUE",
        f"  5 Reallocated_Sector_Ct   0x0033   100   100   010    Pre-fail  Always       -       {values[5]}",
        f"194 Temperature_Celsius     0x0022   100   100   000    Old_age   Always       -       {values[194]}",
        f"197 Current_Pending_Sector  0x0012   100   100   000    Old_age   Always       -       {values[197]}",
        f"198 Offline_Uncorrectable   0x0010   100   100   000    Old_age   Offline      -       {values[198]}",
        f"199 UDMA_CRC_Error_Count    0x003e   200   200   000    Old_age   Always       -       {values[199]}",
    ]
    return "\n".join(lines) + "\n"


class TestParseSmartctlOverallHealth(unittest.TestCase):
    def test_passed(self) -> None:
        self.assertEqual(parse_smartctl_overall_health(_HEALTH_PASSED), "PASSED")

    def test_failed(self) -> None:
        self.assertEqual(parse_smartctl_overall_health(_HEALTH_FAILED), "FAILED")

    def test_absent_yields_none(self) -> None:
        self.assertIsNone(parse_smartctl_overall_health("no relevant line here"))


class TestParseSmartctlAttributes(unittest.TestCase):
    def test_parses_all_known_attributes(self) -> None:
        attrs = parse_smartctl_attributes(_attr_table())
        self.assertEqual(attrs[5]["raw_value"], 0)
        self.assertEqual(attrs[194]["raw_value"], 35)
        self.assertEqual(attrs[197]["name"], "Current_Pending_Sector")

    def test_empty_text_yields_empty_dict(self) -> None:
        self.assertEqual(parse_smartctl_attributes(""), {})


class TestBuildHddBaselineResult(unittest.TestCase):
    def test_clean_smart_yields_no_immediate_issue(self) -> None:
        result = build_hdd_baseline_result(
            device_id="sda", smart_health_raw=_HEALTH_PASSED, smart_attributes_raw=_attr_table(), dmesg_text=""
        )
        self.assertEqual(result.status, BaselineStatus.NO_IMMEDIATE_ISSUE_DETECTED.value)
        self.assertEqual(result.device_id, "sda")

    def test_pending_sectors_yields_red(self) -> None:
        result = build_hdd_baseline_result(
            device_id="sda", smart_health_raw=_HEALTH_PASSED, smart_attributes_raw=_attr_table({197: 5}), dmesg_text=""
        )
        self.assertEqual(result.status, BaselineStatus.IMMEDIATE_ISSUE_DETECTED.value)
        codes = [f.code for f in result.findings]
        self.assertIn("hdd.pending_sectors_detected", codes)

    def test_offline_uncorrectable_yields_red(self) -> None:
        result = build_hdd_baseline_result(
            device_id="sda", smart_health_raw=_HEALTH_PASSED, smart_attributes_raw=_attr_table({198: 3}), dmesg_text=""
        )
        codes = [f.code for f in result.findings]
        self.assertIn("hdd.offline_uncorrectable_detected", codes)
        self.assertEqual(result.status, BaselineStatus.IMMEDIATE_ISSUE_DETECTED.value)

    def test_reallocated_sectors_yields_yellow(self) -> None:
        result = build_hdd_baseline_result(
            device_id="sda", smart_health_raw=_HEALTH_PASSED, smart_attributes_raw=_attr_table({5: 2}), dmesg_text=""
        )
        codes = [f.code for f in result.findings]
        self.assertIn("hdd.reallocated_sectors_detected", codes)
        self.assertEqual(result.status, BaselineStatus.REVIEW_REQUIRED.value)

    def test_crc_errors_yields_yellow(self) -> None:
        result = build_hdd_baseline_result(
            device_id="sda", smart_health_raw=_HEALTH_PASSED, smart_attributes_raw=_attr_table({199: 4}), dmesg_text=""
        )
        codes = [f.code for f in result.findings]
        self.assertIn("hdd.crc_error_detected", codes)

    def test_high_temperature_yields_yellow(self) -> None:
        result = build_hdd_baseline_result(
            device_id="sda", smart_health_raw=_HEALTH_PASSED, smart_attributes_raw=_attr_table({194: 60}), dmesg_text=""
        )
        codes = [f.code for f in result.findings]
        self.assertIn("hdd.high_temperature", codes)

    def test_smart_failed_yields_red(self) -> None:
        result = build_hdd_baseline_result(
            device_id="sda", smart_health_raw=_HEALTH_FAILED, smart_attributes_raw=_attr_table(), dmesg_text=""
        )
        self.assertEqual(result.status, BaselineStatus.IMMEDIATE_ISSUE_DETECTED.value)
        codes = [f.code for f in result.findings]
        self.assertIn("hdd.smart_overall_failed", codes)
        self.assertTrue(result.extended_test.required)

    def test_missing_smartctl_yields_test_unavailable(self) -> None:
        result = build_hdd_baseline_result(
            device_id="sda",
            smartctl_available=True,
            dmesg_text="",
            runner=lambda *a, **k: (_ for _ in ()).throw(FileNotFoundError()),
        )
        self.assertEqual(result.status, BaselineStatus.TEST_UNAVAILABLE.value)
        self.assertIn("smartctl", result.checks_skipped)

    def test_repeated_io_errors_yields_red(self) -> None:
        dmesg = "\n".join([f"[ {i}.0] blk_update_request: I/O error, dev sda, sector {i}" for i in range(5)])
        result = build_hdd_baseline_result(
            device_id="sda", smart_health_raw=_HEALTH_PASSED, smart_attributes_raw=_attr_table(), dmesg_text=dmesg
        )
        self.assertEqual(result.status, BaselineStatus.IMMEDIATE_ISSUE_DETECTED.value)
        codes = [f.code for f in result.findings]
        self.assertIn("hdd.repeated_io_errors", codes)

    def test_live_fetch_via_runner_when_no_raw_text_given(self) -> None:
        calls: list[list[str]] = []

        class R:
            def __init__(self, stdout: str) -> None:
                self.stdout = stdout

        def fake_runner(argv, **kwargs):
            calls.append(argv)
            if "-H" in argv:
                return R(_HEALTH_PASSED)
            return R(_attr_table())

        result = build_hdd_baseline_result(device_id="sda", smartctl_available=True, dmesg_text="", runner=fake_runner)
        self.assertEqual(result.status, BaselineStatus.NO_IMMEDIATE_ISSUE_DETECTED.value)
        self.assertTrue(any("-H" in c for c in calls))
        self.assertTrue(any("-A" in c for c in calls))

    def test_never_claims_disk_without_defect(self) -> None:
        result = build_hdd_baseline_result(
            device_id="sda", smart_health_raw=_HEALTH_PASSED, smart_attributes_raw=_attr_table(), dmesg_text=""
        )
        blob = str(result.to_dict()).lower()
        self.assertNotIn("disk_without_defect", blob)


class TestDiagnostics(unittest.TestCase):
    def test_never_starts_self_test(self) -> None:
        self.assertFalse(build_hdd_baseline_diagnostics()["starts_smart_self_test"])


if __name__ == "__main__":
    unittest.main()
