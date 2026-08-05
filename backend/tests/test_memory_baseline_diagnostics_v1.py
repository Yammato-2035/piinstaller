"""PI-RS-HW-BASELINE-DIAG-I18N-002 Phase 3: memory_baseline_diagnostics.py tests.

Fixture groups per spec PHASE 18: normal, very low available, EDAC corrected
error, EDAC uncorrected error, MCE, OOM history, quick-probe success,
quick-probe failed, quick-probe skipped (low available).
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from core.hardware_baseline_contracts import BaselineSeverity, BaselineStatus
from core.memory_baseline_diagnostics import (
    build_memory_baseline_diagnostics,
    build_memory_baseline_result,
    check_memory_plausibility,
    collect_memory_inventory,
    detect_ecc_support,
    parse_dmi_memory_devices,
    parse_meminfo,
    run_quick_memory_probe,
    scan_kernel_memory_errors,
)

_MEMINFO_NORMAL = """MemTotal:       16384000 kB
MemFree:         9000000 kB
MemAvailable:    12000000 kB
SwapTotal:        2000000 kB
SwapFree:         2000000 kB
HugePages_Total:        0
HugePages_Free:         0
"""

_MEMINFO_LOW_AVAILABLE = _MEMINFO_NORMAL.replace("MemAvailable:    12000000 kB", "MemAvailable:       100000 kB")

_DMIDECODE_TWO_MODULES = """Memory Device
\tArray Handle: 0x0012
\tSize: 8192 MB
\tType: DDR4
\tSpeed: 3200 MT/s
\tManufacturer: Kingston
\tLocator: DIMM0
\tError Correction Type: None

Memory Device
\tArray Handle: 0x0012
\tSize: 8192 MB
\tType: DDR4
\tSpeed: 3200 MT/s
\tManufacturer: Kingston
\tLocator: DIMM1
"""

_DMIDECODE_ECC = _DMIDECODE_TWO_MODULES.replace("Error Correction Type: None", "Error Correction Type: Single-bit ECC")

_DMIDECODE_EMPTY_SLOT = """Memory Device
\tSize: No Module Installed
\tLocator: DIMM2
"""

_DMESG_CLEAN = "[    0.0] Linux version 6.1\n"
_DMESG_EDAC_CORRECTED = "[  100.0] EDAC MC0: 1 CE memory read correctable error on unknown memory\n"
_DMESG_EDAC_UNCORRECTED = "[  100.0] EDAC MC0: 1 UE memory read uncorrectable error on unknown memory\n"
_DMESG_MCE = "[  100.0] mce: [Hardware Error]: Machine check events logged\n"
_DMESG_OOM = "[  100.0] Out of memory: Killed process 1234 (python3)\n"

_AVAILABLE_TOOLING_RUNNER = None


class TestParseMeminfo(unittest.TestCase):
    def test_parses_all_expected_fields(self) -> None:
        parsed = parse_meminfo(_MEMINFO_NORMAL)
        self.assertEqual(parsed["mem_total_kb"], 16384000)
        self.assertEqual(parsed["mem_available_kb"], 12000000)
        self.assertEqual(parsed["swap_total_kb"], 2000000)

    def test_empty_text_yields_all_none(self) -> None:
        parsed = parse_meminfo("")
        self.assertIsNone(parsed["mem_total_kb"])


class TestParseDmiMemoryDevices(unittest.TestCase):
    def test_parses_two_modules(self) -> None:
        modules = parse_dmi_memory_devices(_DMIDECODE_TWO_MODULES)
        self.assertEqual(len(modules), 2)
        self.assertEqual(modules[0]["manufacturer"], "Kingston")

    def test_skips_empty_slots(self) -> None:
        modules = parse_dmi_memory_devices(_DMIDECODE_EMPTY_SLOT)
        self.assertEqual(modules, [])

    def test_empty_text_yields_empty_list(self) -> None:
        self.assertEqual(parse_dmi_memory_devices(""), [])


class TestDetectEccSupport(unittest.TestCase):
    def test_ecc_detected_true(self) -> None:
        self.assertTrue(detect_ecc_support(_DMIDECODE_ECC))

    def test_ecc_detected_false_when_none(self) -> None:
        self.assertFalse(detect_ecc_support(_DMIDECODE_TWO_MODULES))

    def test_ecc_unknown_when_no_dmi_data(self) -> None:
        self.assertIsNone(detect_ecc_support(""))


class TestCollectMemoryInventory(unittest.TestCase):
    def test_normal_inventory(self) -> None:
        inv = collect_memory_inventory(meminfo_text=_MEMINFO_NORMAL, dmidecode_text=_DMIDECODE_TWO_MODULES)
        self.assertEqual(inv["mem_total_kb"], 16384000)
        self.assertEqual(len(inv["ram_modules"]), 2)
        self.assertFalse(inv["ecc_supported"])

    def test_dmidecode_missing_marks_unavailable(self) -> None:
        inv = collect_memory_inventory(meminfo_text=_MEMINFO_NORMAL, runner=lambda *a, **k: (_ for _ in ()).throw(FileNotFoundError()))
        self.assertFalse(inv["dmidecode_available"])
        self.assertEqual(inv["ram_modules"], [])


class TestScanKernelMemoryErrors(unittest.TestCase):
    def test_clean_log_has_zero_counts(self) -> None:
        scan = scan_kernel_memory_errors(_DMESG_CLEAN)
        self.assertEqual(scan["edac_corrected_count"], 0)
        self.assertEqual(scan["edac_uncorrected_count"], 0)
        self.assertEqual(scan["mce_count"], 0)
        self.assertEqual(scan["oom_count"], 0)

    def test_edac_corrected_detected(self) -> None:
        self.assertEqual(scan_kernel_memory_errors(_DMESG_EDAC_CORRECTED)["edac_corrected_count"], 1)

    def test_edac_uncorrected_detected(self) -> None:
        self.assertEqual(scan_kernel_memory_errors(_DMESG_EDAC_UNCORRECTED)["edac_uncorrected_count"], 1)

    def test_mce_detected(self) -> None:
        self.assertGreaterEqual(scan_kernel_memory_errors(_DMESG_MCE)["mce_count"], 1)

    def test_oom_detected(self) -> None:
        self.assertEqual(scan_kernel_memory_errors(_DMESG_OOM)["oom_count"], 1)

    def test_missing_dmesg_tool_reported_not_crashed(self) -> None:
        scan = scan_kernel_memory_errors(None, runner=lambda *a, **k: (_ for _ in ()).throw(FileNotFoundError()))
        self.assertIn("dmesg", scan["missing_tools"])


class TestCheckMemoryPlausibility(unittest.TestCase):
    def test_no_findings_for_matching_capacity(self) -> None:
        inv = collect_memory_inventory(meminfo_text=_MEMINFO_NORMAL, dmidecode_text=_DMIDECODE_TWO_MODULES)
        findings = check_memory_plausibility(inv)
        codes = [f.code for f in findings]
        self.assertNotIn("memory.capacity_mismatch", codes)

    def test_capacity_mismatch_detected(self) -> None:
        low_total_meminfo = _MEMINFO_NORMAL.replace("MemTotal:       16384000 kB", "MemTotal:        4000000 kB")
        inv = collect_memory_inventory(meminfo_text=low_total_meminfo, dmidecode_text=_DMIDECODE_TWO_MODULES)
        findings = check_memory_plausibility(inv)
        codes = [f.code for f in findings]
        self.assertIn("memory.capacity_mismatch", codes)

    def test_extremely_low_available_detected(self) -> None:
        inv = collect_memory_inventory(meminfo_text=_MEMINFO_LOW_AVAILABLE, dmidecode_text="")
        findings = check_memory_plausibility(inv)
        codes = [f.code for f in findings]
        self.assertIn("memory.extremely_low_available", codes)


class TestRunQuickMemoryProbe(unittest.TestCase):
    def test_success_path(self) -> None:
        result = run_quick_memory_probe(12_000_000)
        self.assertEqual(result["status"], "success")
        self.assertGreater(result["tested_bytes"], 0)
        self.assertLessEqual(result["tested_bytes"], 128 * 1024 * 1024)

    def test_skipped_when_low_available(self) -> None:
        result = run_quick_memory_probe(100_000)
        self.assertEqual(result["status"], "skipped_low_available")
        self.assertEqual(result["tested_bytes"], 0)

    def test_skipped_when_none(self) -> None:
        result = run_quick_memory_probe(None)
        self.assertEqual(result["status"], "skipped_low_available")

    def test_forced_failure(self) -> None:
        result = run_quick_memory_probe(12_000_000, force_result="failed")
        self.assertEqual(result["status"], "failed")

    def test_forced_timeout(self) -> None:
        result = run_quick_memory_probe(12_000_000, force_result="timeout")
        self.assertEqual(result["status"], "timeout")

    def test_probe_never_exceeds_two_percent_of_available(self) -> None:
        result = run_quick_memory_probe(1_000_000)  # 1e6 kB available
        self.assertLessEqual(result["tested_bytes"], int(1_000_000 * 0.02) * 1024 + 1024)


class TestBuildMemoryBaselineResult(unittest.TestCase):
    def test_normal_yields_no_immediate_issue(self) -> None:
        result = build_memory_baseline_result(
            meminfo_text=_MEMINFO_NORMAL,
            dmidecode_text=_DMIDECODE_TWO_MODULES,
            dmesg_text=_DMESG_CLEAN,
        )
        self.assertEqual(result.status, BaselineStatus.NO_IMMEDIATE_ISSUE_DETECTED.value)
        self.assertEqual(result.severity, BaselineSeverity.GREEN.value)

    def test_low_available_yields_review_required(self) -> None:
        result = build_memory_baseline_result(
            meminfo_text=_MEMINFO_LOW_AVAILABLE,
            dmidecode_text="",
            dmesg_text=_DMESG_CLEAN,
        )
        self.assertEqual(result.status, BaselineStatus.REVIEW_REQUIRED.value)

    def test_edac_corrected_yields_yellow_finding(self) -> None:
        result = build_memory_baseline_result(
            meminfo_text=_MEMINFO_NORMAL, dmidecode_text=_DMIDECODE_TWO_MODULES, dmesg_text=_DMESG_EDAC_CORRECTED
        )
        codes = [f.code for f in result.findings]
        self.assertIn("memory.kernel_corrected_error", codes)
        self.assertEqual(result.status, BaselineStatus.REVIEW_REQUIRED.value)

    def test_edac_uncorrected_yields_red_and_extended_test_required(self) -> None:
        result = build_memory_baseline_result(
            meminfo_text=_MEMINFO_NORMAL, dmidecode_text=_DMIDECODE_TWO_MODULES, dmesg_text=_DMESG_EDAC_UNCORRECTED
        )
        self.assertEqual(result.status, BaselineStatus.IMMEDIATE_ISSUE_DETECTED.value)
        self.assertEqual(result.severity, BaselineSeverity.RED.value)
        self.assertTrue(result.extended_test.required)
        codes = [f.code for f in result.findings]
        self.assertIn("memory.kernel_uncorrected_error", codes)
        self.assertIn("memory.extended_memtest_required", codes)

    def test_mce_yields_red(self) -> None:
        result = build_memory_baseline_result(meminfo_text=_MEMINFO_NORMAL, dmidecode_text="", dmesg_text=_DMESG_MCE)
        self.assertEqual(result.status, BaselineStatus.IMMEDIATE_ISSUE_DETECTED.value)

    def test_oom_history_detected_yields_yellow(self) -> None:
        result = build_memory_baseline_result(meminfo_text=_MEMINFO_NORMAL, dmidecode_text="", dmesg_text=_DMESG_OOM)
        codes = [f.code for f in result.findings]
        self.assertIn("memory.oom_history_detected", codes)

    def test_quick_probe_success_recorded_in_metrics(self) -> None:
        result = build_memory_baseline_result(meminfo_text=_MEMINFO_NORMAL, dmidecode_text="", dmesg_text=_DMESG_CLEAN)
        names = {m.name: m.value for m in result.metrics}
        self.assertEqual(names["quick_probe_status"], "success")

    def test_quick_probe_failed_yields_red(self) -> None:
        result = build_memory_baseline_result(
            meminfo_text=_MEMINFO_NORMAL, dmidecode_text="", dmesg_text=_DMESG_CLEAN, force_probe_result="failed"
        )
        codes = [f.code for f in result.findings]
        self.assertIn("memory.quick_probe_failed", codes)
        self.assertEqual(result.status, BaselineStatus.IMMEDIATE_ISSUE_DETECTED.value)

    def test_quick_probe_skipped_when_low_available(self) -> None:
        result = build_memory_baseline_result(meminfo_text=_MEMINFO_LOW_AVAILABLE, dmidecode_text="", dmesg_text=_DMESG_CLEAN)
        codes = [f.code for f in result.findings]
        self.assertIn("memory.quick_probe_skipped_low_available", codes)

    def test_skip_quick_probe_flag_skips_check(self) -> None:
        result = build_memory_baseline_result(
            meminfo_text=_MEMINFO_NORMAL, dmidecode_text="", dmesg_text=_DMESG_CLEAN, skip_quick_probe=True
        )
        self.assertIn("quick_memory_probe", result.checks_skipped)

    def test_dmidecode_missing_is_checks_skipped_not_error(self) -> None:
        result = build_memory_baseline_result(
            meminfo_text=_MEMINFO_NORMAL,
            dmesg_text=_DMESG_CLEAN,
            runner=lambda *a, **k: (_ for _ in ()).throw(FileNotFoundError()),
        )
        self.assertIn("dmidecode", result.checks_skipped)

    def test_never_claims_passed_full_memtest(self) -> None:
        result = build_memory_baseline_result(meminfo_text=_MEMINFO_NORMAL, dmidecode_text="", dmesg_text=_DMESG_CLEAN)
        blob = str(result.to_dict()).lower()
        self.assertNotIn("passed_full_memtest", blob)
        self.assertNotIn("ram_fully_verified", blob)


class TestDiagnostics(unittest.TestCase):
    def test_diagnostics_never_installs_tools(self) -> None:
        diag = build_memory_baseline_diagnostics()
        self.assertFalse(diag["installs_tools"])
        self.assertTrue(diag["read_only"])


if __name__ == "__main__":
    unittest.main()
