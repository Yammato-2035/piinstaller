"""PI-RS-HW-BASELINE-DIAG-I18N-002 Phase 9: nvme_baseline_diagnostics.py tests.

Fixture groups per spec PHASE 18: normal, critical warning, low spare,
high percentage used, media errors, high temperature, unsafe shutdowns,
repeated controller resets, missing nvme-cli, incomplete data (USB-NVMe
bridge).
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from core.hardware_baseline_contracts import BaselineStatus
from core.nvme_baseline_diagnostics import (
    build_nvme_baseline_diagnostics,
    build_nvme_baseline_result,
    nvme_controller_name,
    parse_nvme_id_ctrl,
    parse_nvme_smart_log,
)

_ID_CTRL = "vid     : 0x144d\nfr      : 3B2QEXM7\nnn      : 1\n"


def _smart_log(overrides: dict[str, str] | None = None) -> str:
    fields = {
        "Critical Warning": "0x00",
        "Temperature": "35 C",
        "Available Spare": "100%",
        "Available Spare Threshold": "10%",
        "Percentage Used": "5%",
        "Unsafe Shutdowns": "3",
        "Media and Data Integrity Errors": "0",
    }
    if overrides:
        fields.update(overrides)
    return "\n".join(f"{k}:{'':20}{v}" for k, v in fields.items()) + "\n"


class TestNvmeControllerName(unittest.TestCase):
    def test_strips_namespace_suffix(self) -> None:
        self.assertEqual(nvme_controller_name("nvme0n1"), "nvme0")

    def test_handles_dev_prefix(self) -> None:
        self.assertEqual(nvme_controller_name("/dev/nvme1n1"), "nvme1")


class TestParseNvmeSmartLog(unittest.TestCase):
    def test_parses_normal_log(self) -> None:
        parsed = parse_nvme_smart_log(_smart_log())
        self.assertEqual(parsed["critical_warning"], 0)
        self.assertEqual(parsed["temperature_c"], 35)
        self.assertEqual(parsed["available_spare_pct"], 100)

    def test_empty_text_yields_all_none(self) -> None:
        parsed = parse_nvme_smart_log("")
        self.assertTrue(all(v is None for v in parsed.values()))


class TestParseNvmeIdCtrl(unittest.TestCase):
    def test_parses_firmware_and_namespace_count(self) -> None:
        parsed = parse_nvme_id_ctrl(_ID_CTRL)
        self.assertEqual(parsed["firmware_version"], "3B2QEXM7")
        self.assertEqual(parsed["namespace_count"], 1)


class TestBuildNvmeBaselineResult(unittest.TestCase):
    def test_normal_yields_no_immediate_issue(self) -> None:
        result = build_nvme_baseline_result(device_id="nvme0n1", smart_log_raw=_smart_log(), id_ctrl_raw=_ID_CTRL, dmesg_text="")
        self.assertEqual(result.status, BaselineStatus.NO_IMMEDIATE_ISSUE_DETECTED.value)

    def test_critical_warning_yields_red(self) -> None:
        result = build_nvme_baseline_result(device_id="nvme0n1", smart_log_raw=_smart_log({"Critical Warning": "0x04"}), id_ctrl_raw=_ID_CTRL, dmesg_text="")
        codes = [f.code for f in result.findings]
        self.assertIn("nvme.critical_warning", codes)
        self.assertEqual(result.status, BaselineStatus.IMMEDIATE_ISSUE_DETECTED.value)

    def test_low_spare_yields_red(self) -> None:
        result = build_nvme_baseline_result(
            device_id="nvme0n1", smart_log_raw=_smart_log({"Available Spare": "5%"}), id_ctrl_raw=_ID_CTRL, dmesg_text=""
        )
        codes = [f.code for f in result.findings]
        self.assertIn("nvme.low_available_spare", codes)

    def test_high_percentage_used_critical_yields_red(self) -> None:
        result = build_nvme_baseline_result(
            device_id="nvme0n1", smart_log_raw=_smart_log({"Percentage Used": "100%"}), id_ctrl_raw=_ID_CTRL, dmesg_text=""
        )
        codes = [f.code for f in result.findings]
        self.assertIn("nvme.high_percentage_used", codes)
        self.assertEqual(result.status, BaselineStatus.IMMEDIATE_ISSUE_DETECTED.value)

    def test_media_errors_detected_yields_red(self) -> None:
        result = build_nvme_baseline_result(
            device_id="nvme0n1", smart_log_raw=_smart_log({"Media and Data Integrity Errors": "2"}), id_ctrl_raw=_ID_CTRL, dmesg_text=""
        )
        codes = [f.code for f in result.findings]
        self.assertIn("nvme.media_errors_detected", codes)

    def test_high_temperature_yields_yellow(self) -> None:
        result = build_nvme_baseline_result(
            device_id="nvme0n1", smart_log_raw=_smart_log({"Temperature": "75 C"}), id_ctrl_raw=_ID_CTRL, dmesg_text=""
        )
        codes = [f.code for f in result.findings]
        self.assertIn("nvme.high_temperature", codes)
        self.assertEqual(result.status, BaselineStatus.REVIEW_REQUIRED.value)

    def test_unsafe_shutdowns_yields_yellow(self) -> None:
        result = build_nvme_baseline_result(
            device_id="nvme0n1", smart_log_raw=_smart_log({"Unsafe Shutdowns": "25"}), id_ctrl_raw=_ID_CTRL, dmesg_text=""
        )
        codes = [f.code for f in result.findings]
        self.assertIn("nvme.unsafe_shutdowns_detected", codes)

    def test_repeated_controller_resets_red(self) -> None:
        dmesg = "\n".join([f"[ {i}.0] nvme0: I/O {i} QID 0 timeout, reset controller" for i in range(3)])
        result = build_nvme_baseline_result(device_id="nvme0n1", smart_log_raw=_smart_log(), id_ctrl_raw=_ID_CTRL, dmesg_text=dmesg)
        codes = [f.code for f in result.findings]
        self.assertIn("nvme.repeated_controller_resets", codes)
        self.assertEqual(result.status, BaselineStatus.IMMEDIATE_ISSUE_DETECTED.value)

    def test_missing_nvme_cli_yields_test_unavailable(self) -> None:
        result = build_nvme_baseline_result(
            device_id="nvme0n1",
            nvme_cli_available=True,
            dmesg_text="",
            runner=lambda *a, **k: (_ for _ in ()).throw(FileNotFoundError()),
        )
        self.assertEqual(result.status, BaselineStatus.TEST_UNAVAILABLE.value)
        self.assertIn("nvme-cli", result.checks_skipped)

    def test_usb_nvme_bridge_incomplete_data_yellow(self) -> None:
        result = build_nvme_baseline_result(device_id="nvme0n1", smart_log_raw="", id_ctrl_raw="", dmesg_text="")
        codes = [f.code for f in result.findings]
        self.assertIn("nvme.incomplete_smart_log", codes)
        self.assertEqual(result.status, BaselineStatus.TEST_UNAVAILABLE.value)

    def test_live_fetch_via_runner_when_no_raw_text_given(self) -> None:
        calls: list[list[str]] = []

        class R:
            def __init__(self, stdout: str) -> None:
                self.stdout = stdout

        def fake_runner(argv, **kwargs):
            calls.append(argv)
            if "smart-log" in argv:
                return R(_smart_log())
            return R(_ID_CTRL)

        result = build_nvme_baseline_result(device_id="nvme0n1", nvme_cli_available=True, dmesg_text="", runner=fake_runner)
        self.assertEqual(result.status, BaselineStatus.NO_IMMEDIATE_ISSUE_DETECTED.value)
        self.assertTrue(any("smart-log" in c for c in calls))
        self.assertTrue(any("id-ctrl" in c for c in calls))


class TestDiagnostics(unittest.TestCase):
    def test_never_triggers_firmware_update(self) -> None:
        diag = build_nvme_baseline_diagnostics()
        self.assertFalse(diag["triggers_firmware_update"])
        self.assertFalse(diag["starts_smart_self_test"])


if __name__ == "__main__":
    unittest.main()
