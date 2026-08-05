"""PI-RS-HW-BASELINE-DIAG-I18N-002 Phase 8: sata_ssd_baseline_diagnostics.py tests.

Fixture groups per spec PHASE 18: normal, wear warnings, low reserved
space, uncorrectable errors, CRC errors, unknown vendor attributes,
missing smartctl.
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from core.hardware_baseline_contracts import BaselineStatus
from core.sata_ssd_baseline_diagnostics import (
    build_sata_ssd_baseline_diagnostics,
    build_sata_ssd_baseline_result,
    detect_trim_support,
)

_HEALTH_PASSED = "SMART overall-health self-assessment test result: PASSED\n"


def _attr_table(overrides: dict[int, dict[str, int]] | None = None) -> str:
    values = {
        177: {"value": 90, "raw": 10},
        232: {"value": 90, "raw": 0},
        187: {"value": 100, "raw": 0},
        199: {"value": 200, "raw": 0},
        174: {"value": 100, "raw": 0},
    }
    if overrides:
        for k, v in overrides.items():
            values[k].update(v)
    lines = [
        "ID# ATTRIBUTE_NAME              FLAG     VALUE WORST THRESH TYPE      UPDATED  WHEN_FAILED RAW_VALUE",
        f"177 Wear_Leveling_Count        0x0033   {values[177]['value']}   100   000    Pre-fail  Always       -       {values[177]['raw']}",
        f"232 Available_Reservd_Space    0x0033   {values[232]['value']}   100   010    Pre-fail  Always       -       {values[232]['raw']}",
        f"187 Reported_Uncorrect         0x0032   {values[187]['value']}   100   000    Old_age   Always       -       {values[187]['raw']}",
        f"199 UDMA_CRC_Error_Count       0x003e   {values[199]['value']}   200   000    Old_age   Always       -       {values[199]['raw']}",
        f"174 Unexpect_Power_Loss_Ct     0x0032   {values[174]['value']}   100   000    Old_age   Always       -       {values[174]['raw']}",
    ]
    return "\n".join(lines) + "\n"


class TestDetectTrimSupport(unittest.TestCase):
    def test_supported(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "sys" / "block" / "sdb" / "queue"
            path.mkdir(parents=True)
            (path / "discard_granularity").write_text("512")
            self.assertTrue(detect_trim_support("sdb", sysfs_root=root))

    def test_missing_entry_yields_none(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            self.assertIsNone(detect_trim_support("sdb", sysfs_root=Path(tmp)))


class TestBuildSataSsdBaselineResult(unittest.TestCase):
    def test_normal_yields_no_immediate_issue(self) -> None:
        result = build_sata_ssd_baseline_result(
            device_id="sdb", smart_health_raw=_HEALTH_PASSED, smart_attributes_raw=_attr_table(), dmesg_text=""
        )
        self.assertEqual(result.status, BaselineStatus.NO_IMMEDIATE_ISSUE_DETECTED.value)

    def test_wear_warning_yields_yellow(self) -> None:
        result = build_sata_ssd_baseline_result(
            device_id="sdb",
            smart_health_raw=_HEALTH_PASSED,
            smart_attributes_raw=_attr_table({177: {"value": 5}}),
            dmesg_text="",
        )
        codes = [f.code for f in result.findings]
        self.assertIn("sata_ssd.wear_warning", codes)
        self.assertEqual(result.status, BaselineStatus.REVIEW_REQUIRED.value)

    def test_low_reserved_space_yields_red(self) -> None:
        result = build_sata_ssd_baseline_result(
            device_id="sdb",
            smart_health_raw=_HEALTH_PASSED,
            smart_attributes_raw=_attr_table({232: {"value": 5}}),
            dmesg_text="",
        )
        codes = [f.code for f in result.findings]
        self.assertIn("sata_ssd.low_reserved_space", codes)
        self.assertEqual(result.status, BaselineStatus.IMMEDIATE_ISSUE_DETECTED.value)

    def test_uncorrectable_errors_yield_red(self) -> None:
        result = build_sata_ssd_baseline_result(
            device_id="sdb",
            smart_health_raw=_HEALTH_PASSED,
            smart_attributes_raw=_attr_table({187: {"raw": 3}}),
            dmesg_text="",
        )
        codes = [f.code for f in result.findings]
        self.assertIn("sata_ssd.uncorrectable_errors_detected", codes)

    def test_crc_errors_yield_yellow(self) -> None:
        result = build_sata_ssd_baseline_result(
            device_id="sdb",
            smart_health_raw=_HEALTH_PASSED,
            smart_attributes_raw=_attr_table({199: {"raw": 7}}),
            dmesg_text="",
        )
        codes = [f.code for f in result.findings]
        self.assertIn("sata_ssd.crc_error_detected", codes)

    def test_unknown_vendor_attributes_do_not_crash(self) -> None:
        text = "ID# ATTRIBUTE_NAME FLAG VALUE WORST THRESH TYPE UPDATED WHEN_FAILED RAW_VALUE\n241 Total_LBAs_Written 0x0032 100 100 000 Old_age Always - 123456\n"
        result = build_sata_ssd_baseline_result(device_id="sdb", smart_health_raw=_HEALTH_PASSED, smart_attributes_raw=text, dmesg_text="")
        self.assertEqual(result.status, BaselineStatus.NO_IMMEDIATE_ISSUE_DETECTED.value)

    def test_missing_smartctl_yields_test_unavailable(self) -> None:
        result = build_sata_ssd_baseline_result(
            device_id="sdb",
            smartctl_available=True,
            dmesg_text="",
            runner=lambda *a, **k: (_ for _ in ()).throw(FileNotFoundError()),
        )
        self.assertEqual(result.status, BaselineStatus.TEST_UNAVAILABLE.value)

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

        result = build_sata_ssd_baseline_result(device_id="sdb", smartctl_available=True, dmesg_text="", runner=fake_runner)
        self.assertEqual(result.status, BaselineStatus.NO_IMMEDIATE_ISSUE_DETECTED.value)
        self.assertTrue(any("-H" in c for c in calls))
        self.assertTrue(any("-A" in c for c in calls))


class TestDiagnostics(unittest.TestCase):
    def test_never_starts_self_test(self) -> None:
        self.assertFalse(build_sata_ssd_baseline_diagnostics()["starts_smart_self_test"])


if __name__ == "__main__":
    unittest.main()
