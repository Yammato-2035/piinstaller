"""PI-RS-HW-BASELINE-DIAG-I18N-002 Phase 2: hardware_baseline_contracts.py tests."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from core.hardware_baseline_contracts import (
    FORBIDDEN_BASELINE_CLAIMS,
    BaselineSeverity,
    BaselineStatus,
    BaselineSubsystem,
    ExtendedTestRecommendation,
    HardwareBaselineGate,
    HardwareBaselineResult,
    HardwareFinding,
    HardwareMetric,
    HardwareSubsystemResult,
    build_hardware_baseline_contracts_diagnostics,
    contains_forbidden_baseline_claim,
)


class TestEnums(unittest.TestCase):
    def test_baseline_subsystem_values(self) -> None:
        self.assertEqual({s.value for s in BaselineSubsystem}, {"memory", "cpu", "gpu", "hdd", "sata_ssd", "nvme"})

    def test_baseline_status_has_no_healthy_or_passed_value(self) -> None:
        values = {s.value for s in BaselineStatus}
        for forbidden in ("healthy", "ok", "passed", "verified", "fault_free"):
            self.assertNotIn(forbidden, values)

    def test_baseline_status_allowed_vocabulary(self) -> None:
        expected = {
            "no_immediate_issue_detected",
            "immediate_issue_detected",
            "degraded",
            "review_required",
            "extended_test_recommended",
            "extended_test_required",
            "test_unavailable",
            "not_tested",
        }
        self.assertEqual({s.value for s in BaselineStatus}, expected)

    def test_severity_values(self) -> None:
        self.assertEqual({s.value for s in BaselineSeverity}, {"green", "yellow", "red", "gray"})


class TestForbiddenClaims(unittest.TestCase):
    def test_contains_forbidden_claim_detects_variants(self) -> None:
        self.assertTrue(contains_forbidden_baseline_claim("RAM fully tested and clean"))
        self.assertTrue(contains_forbidden_baseline_claim("disk_without_defect confirmed"))
        self.assertTrue(contains_forbidden_baseline_claim("All Storage Healthy"))

    def test_allowed_text_not_flagged(self) -> None:
        self.assertFalse(contains_forbidden_baseline_claim("no_immediate_issue_detected"))
        self.assertFalse(contains_forbidden_baseline_claim("extended test recommended"))

    def test_forbidden_claims_set_not_empty(self) -> None:
        self.assertGreater(len(FORBIDDEN_BASELINE_CLAIMS), 5)


class TestDataclassShapes(unittest.TestCase):
    def test_hardware_metric_to_dict(self) -> None:
        m = HardwareMetric(name="mem_total_kb", value=16384000, unit="kB", source="/proc/meminfo")
        self.assertEqual(m.to_dict()["name"], "mem_total_kb")

    def test_hardware_finding_to_dict(self) -> None:
        f = HardwareFinding(code="memory.kernel_uncorrected_error", severity=BaselineSeverity.RED.value, message="x")
        d = f.to_dict()
        self.assertEqual(d["code"], "memory.kernel_uncorrected_error")
        self.assertEqual(d["severity"], "red")
        self.assertEqual(d["evidence"], [])

    def test_extended_test_recommendation_defaults(self) -> None:
        e = ExtendedTestRecommendation()
        self.assertFalse(e.recommended)
        self.assertFalse(e.required)
        self.assertTrue(e.operator_confirmation_required)

    def test_subsystem_result_to_dict_shape(self) -> None:
        r = HardwareSubsystemResult(
            subsystem="memory",
            status=BaselineStatus.NO_IMMEDIATE_ISSUE_DETECTED.value,
            severity=BaselineSeverity.GREEN.value,
            checks_run=("meminfo_inventory",),
            metrics=(HardwareMetric(name="mem_total_kb", value=1000),),
            findings=(HardwareFinding(code="x", severity="green"),),
        )
        d = r.to_dict()
        self.assertEqual(d["subsystem"], "memory")
        self.assertIn("mem_total_kb", d["metrics"])
        self.assertEqual(len(d["findings"]), 1)
        self.assertNotIn("device_id", d)

    def test_subsystem_result_includes_device_id_when_set(self) -> None:
        r = HardwareSubsystemResult(subsystem="hdd", device_id="/dev/sda")
        self.assertEqual(r.to_dict()["device_id"], "/dev/sda")

    def test_gate_to_dict_shape(self) -> None:
        g = HardwareBaselineGate(status="passed", backup_allowed=True, restore_allowed=True)
        d = g.to_dict()
        self.assertEqual(d["status"], "passed")
        self.assertTrue(d["restore_allowed"])

    def test_baseline_result_to_dict_shape(self) -> None:
        result = HardwareBaselineResult(run_id="r1", collected_at="2026-01-01T00:00:00Z")
        d = result.to_dict()
        self.assertEqual(d["run_id"], "r1")
        self.assertEqual(d["mode"], "quick")
        self.assertEqual(d["subsystems"], [])


class TestDiagnostics(unittest.TestCase):
    def test_diagnostics_is_read_only_and_lists_models(self) -> None:
        diag = build_hardware_baseline_contracts_diagnostics()
        self.assertTrue(diag["read_only"])
        self.assertFalse(diag["writes_allowed"])
        self.assertIn("HardwareBaselineGate", diag["models"])


if __name__ == "__main__":
    unittest.main()
