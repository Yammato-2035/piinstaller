"""PI-RS-HW-BASELINE-DIAG-I18N-002 Phase 4: cpu_baseline_diagnostics.py tests.

Fixture groups per spec PHASE 18: normal, machine check, thermal warning,
throttling, quick-probe checksum failure, timeout, missing temperature
source, ARM/Raspberry-Pi CPU. All thermal-dependent tests pin
``sysfs_root`` to a nonexistent path so results are deterministic
regardless of the real host's thermal state.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from core.hardware_baseline_contracts import BaselineSeverity, BaselineStatus
from core.cpu_baseline_diagnostics import (
    build_cpu_baseline_diagnostics,
    build_cpu_baseline_result,
    detect_thermal_throttling,
    read_thermal_zone_temperatures,
    run_quick_cpu_probe,
    scan_kernel_cpu_errors,
)

_NONEXISTENT_SYSFS = Path("/nonexistent-cpu-baseline-thermal")

_LSCPU_X86 = """Architecture:        x86_64
Vendor ID:           GenuineIntel
Model name:          Intel(R) Core(TM) i7-8700K
CPU family:          6
Model:                158
Core(s) per socket:  6
Socket(s):           1
Thread(s) per core:  2
Flags:               vmx aes avx2
"""

_LSCPU_ARM = """Architecture:        aarch64
Vendor ID:           ARM
Model name:          Cortex-A72
Core(s) per socket:  4
Socket(s):           1
Thread(s) per core:  1
"""

_CPUINFO_WITH_MICROCODE = "processor\t: 0\nvendor_id\t: GenuineIntel\nmicrocode\t: 0xea\n\n"

_DMESG_CLEAN = "[    0.0] Linux version 6.1\n"
_DMESG_MCE = "[  100.0] mce: [Hardware Error]: Machine check events logged\n"
_DMESG_THROTTLE = "[  100.0] CPU0: Core temperature above threshold, cpu clock throttled\n"


class TestScanKernelCpuErrors(unittest.TestCase):
    def test_clean_log(self) -> None:
        scan = scan_kernel_cpu_errors(_DMESG_CLEAN)
        self.assertEqual(scan["machine_check_count"], 0)

    def test_machine_check_detected(self) -> None:
        scan = scan_kernel_cpu_errors(_DMESG_MCE)
        self.assertGreaterEqual(scan["machine_check_count"], 1)

    def test_missing_dmesg_reported(self) -> None:
        scan = scan_kernel_cpu_errors(None, runner=lambda *a, **k: (_ for _ in ()).throw(FileNotFoundError()))
        self.assertIn("dmesg", scan["missing_tools"])


class TestReadThermalZoneTemperatures(unittest.TestCase):
    def test_nonexistent_sysfs_yields_empty(self) -> None:
        self.assertEqual(read_thermal_zone_temperatures(sysfs_root=_NONEXISTENT_SYSFS), [])


class TestDetectThermalThrottling(unittest.TestCase):
    def test_detects_throttle_message(self) -> None:
        self.assertTrue(detect_thermal_throttling(_DMESG_THROTTLE))

    def test_no_throttle_in_clean_log(self) -> None:
        self.assertFalse(detect_thermal_throttling(_DMESG_CLEAN))

    def test_none_text_is_false(self) -> None:
        self.assertFalse(detect_thermal_throttling(None))


class TestRunQuickCpuProbe(unittest.TestCase):
    def test_success(self) -> None:
        result = run_quick_cpu_probe(max_temp_c=40.0)
        self.assertEqual(result["status"], "success")

    def test_skipped_when_already_hot(self) -> None:
        result = run_quick_cpu_probe(max_temp_c=95.0)
        self.assertEqual(result["status"], "skipped_high_temperature")

    def test_forced_checksum_mismatch(self) -> None:
        result = run_quick_cpu_probe(max_temp_c=40.0, force_result="checksum_mismatch")
        self.assertEqual(result["status"], "checksum_mismatch")

    def test_forced_timeout(self) -> None:
        result = run_quick_cpu_probe(max_temp_c=40.0, force_result="timeout")
        self.assertEqual(result["status"], "timeout")

    def test_none_temperature_does_not_skip(self) -> None:
        result = run_quick_cpu_probe(max_temp_c=None)
        self.assertEqual(result["status"], "success")


class TestBuildCpuBaselineResult(unittest.TestCase):
    def test_normal_x86_yields_no_immediate_issue(self) -> None:
        result = build_cpu_baseline_result(
            lscpu_raw=_LSCPU_X86,
            cpuinfo_raw=_CPUINFO_WITH_MICROCODE,
            uname_machine_raw="x86_64",
            dmesg_text=_DMESG_CLEAN,
            sysfs_root=_NONEXISTENT_SYSFS,
        )
        self.assertEqual(result.status, BaselineStatus.NO_IMMEDIATE_ISSUE_DETECTED.value)
        self.assertEqual(result.severity, BaselineSeverity.GREEN.value)

    def test_arm_raspberry_pi_cpu_no_microcode_finding(self) -> None:
        result = build_cpu_baseline_result(
            lscpu_raw=_LSCPU_ARM,
            cpuinfo_raw="",
            uname_machine_raw="aarch64",
            device_tree_compatible="raspberrypi,4-model-b",
            dmesg_text=_DMESG_CLEAN,
            sysfs_root=_NONEXISTENT_SYSFS,
        )
        codes = [f.code for f in result.findings]
        self.assertNotIn("cpu.microcode_review_required", codes)

    def test_machine_check_yields_red_and_extended_test_recommended(self) -> None:
        result = build_cpu_baseline_result(
            lscpu_raw=_LSCPU_X86,
            cpuinfo_raw=_CPUINFO_WITH_MICROCODE,
            uname_machine_raw="x86_64",
            dmesg_text=_DMESG_MCE,
            sysfs_root=_NONEXISTENT_SYSFS,
        )
        self.assertEqual(result.status, BaselineStatus.IMMEDIATE_ISSUE_DETECTED.value)
        codes = [f.code for f in result.findings]
        self.assertIn("cpu.machine_check_detected", codes)
        self.assertTrue(result.extended_test.recommended)

    def test_throttling_yields_yellow(self) -> None:
        result = build_cpu_baseline_result(
            lscpu_raw=_LSCPU_X86,
            cpuinfo_raw=_CPUINFO_WITH_MICROCODE,
            uname_machine_raw="x86_64",
            dmesg_text=_DMESG_THROTTLE,
            sysfs_root=_NONEXISTENT_SYSFS,
        )
        self.assertEqual(result.status, BaselineStatus.REVIEW_REQUIRED.value)
        codes = [f.code for f in result.findings]
        self.assertIn("cpu.throttling_detected", codes)

    def test_quick_probe_failure_yields_red(self) -> None:
        result = build_cpu_baseline_result(
            lscpu_raw=_LSCPU_X86,
            cpuinfo_raw=_CPUINFO_WITH_MICROCODE,
            uname_machine_raw="x86_64",
            dmesg_text=_DMESG_CLEAN,
            sysfs_root=Path("/nonexistent-cpu-baseline-thermal"),
            force_probe_result="checksum_mismatch",
        )
        self.assertEqual(result.status, BaselineStatus.IMMEDIATE_ISSUE_DETECTED.value)
        codes = [f.code for f in result.findings]
        self.assertIn("cpu.quick_probe_failed", codes)

    def test_quick_probe_timeout_yields_yellow_not_red(self) -> None:
        result = build_cpu_baseline_result(
            lscpu_raw=_LSCPU_X86,
            cpuinfo_raw=_CPUINFO_WITH_MICROCODE,
            uname_machine_raw="x86_64",
            dmesg_text=_DMESG_CLEAN,
            sysfs_root=Path("/nonexistent-cpu-baseline-thermal"),
            force_probe_result="timeout",
        )
        self.assertEqual(result.status, BaselineStatus.REVIEW_REQUIRED.value)
        codes = [f.code for f in result.findings]
        self.assertIn("cpu.quick_probe_timeout", codes)

    def test_missing_temperature_source_is_checks_skipped(self) -> None:
        result = build_cpu_baseline_result(
            lscpu_raw=_LSCPU_X86,
            cpuinfo_raw=_CPUINFO_WITH_MICROCODE,
            uname_machine_raw="x86_64",
            dmesg_text=_DMESG_CLEAN,
            sysfs_root=_NONEXISTENT_SYSFS,
        )
        self.assertIn("thermal_zones", result.checks_skipped)

    def test_missing_microcode_field_flagged_on_x86(self) -> None:
        result = build_cpu_baseline_result(
            lscpu_raw=_LSCPU_X86,
            cpuinfo_raw="",
            uname_machine_raw="x86_64",
            dmesg_text=_DMESG_CLEAN,
            sysfs_root=_NONEXISTENT_SYSFS,
        )
        codes = [f.code for f in result.findings]
        self.assertIn("cpu.microcode_review_required", codes)

    def test_skip_quick_probe_flag(self) -> None:
        result = build_cpu_baseline_result(
            lscpu_raw=_LSCPU_X86,
            cpuinfo_raw=_CPUINFO_WITH_MICROCODE,
            uname_machine_raw="x86_64",
            dmesg_text=_DMESG_CLEAN,
            sysfs_root=_NONEXISTENT_SYSFS,
            skip_quick_probe=True,
        )
        self.assertIn("quick_cpu_probe", result.checks_skipped)

    def test_never_claims_cpu_fully_stable(self) -> None:
        result = build_cpu_baseline_result(
            lscpu_raw=_LSCPU_X86,
            cpuinfo_raw=_CPUINFO_WITH_MICROCODE,
            uname_machine_raw="x86_64",
            dmesg_text=_DMESG_CLEAN,
            sysfs_root=_NONEXISTENT_SYSFS,
        )
        blob = str(result.to_dict()).lower()
        self.assertNotIn("cpu_fully_stable", blob)
        self.assertNotIn("cpu_fully_verified", blob)


class TestDiagnostics(unittest.TestCase):
    def test_diagnostics_never_updates_microcode_or_bios(self) -> None:
        diag = build_cpu_baseline_diagnostics()
        self.assertFalse(diag["triggers_microcode_update"])
        self.assertFalse(diag["triggers_bios_update"])


if __name__ == "__main__":
    unittest.main()
