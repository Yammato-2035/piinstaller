"""PI-RS-HW-BASELINE-DIAG-I18N-002 Phase 18: baseline telemetry/privacy checks.

Verifies that baseline results (and derived JSON) never embed raw serial
numbers, MAC addresses or IP addresses, and that the additive gate never
claims to bypass safety_facade.
"""

from __future__ import annotations

import json
import re
import sys
import unittest
from pathlib import Path

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from core.hardware_baseline_contracts import (
    BaselineSeverity,
    BaselineStatus,
    HardwareBaselineGate,
    HardwareBaselineResult,
    HardwareFinding,
    HardwareMetric,
    HardwareSubsystemResult,
)
from rescue.hardware_baseline_gate import (
    build_hardware_baseline_gate,
    build_hardware_baseline_gate_diagnostics,
    evaluate_operation_against_baseline_gate,
)

_SERIAL_LIKE = re.compile(r"\b(?=[A-Z0-9]*[A-Z])(?=[A-Z0-9]*[0-9])[A-Z0-9]{10,32}\b")
_MAC_LIKE = re.compile(r"\b([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}\b")
_IPV4_LIKE = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")


def _result(subsystem: str, status: str, *, device_id: str | None = None) -> HardwareSubsystemResult:
    severity = {
        BaselineStatus.NO_IMMEDIATE_ISSUE_DETECTED.value: BaselineSeverity.GREEN.value,
        BaselineStatus.REVIEW_REQUIRED.value: BaselineSeverity.YELLOW.value,
        BaselineStatus.IMMEDIATE_ISSUE_DETECTED.value: BaselineSeverity.RED.value,
        BaselineStatus.NOT_TESTED.value: BaselineSeverity.GRAY.value,
    }.get(status, BaselineSeverity.GRAY.value)
    return HardwareSubsystemResult(
        subsystem=subsystem,
        status=status,
        severity=severity,
        device_id=device_id,
        metrics=(HardwareMetric(name="example_metric", value=1),),
        findings=(HardwareFinding(code=f"{subsystem}.example", severity=severity, message="example"),),
    )


class TestBaselineResultHasNoSensitiveIdentifiers(unittest.TestCase):
    def test_to_dict_contains_no_serial_mac_or_ip(self) -> None:
        gate = HardwareBaselineGate(
            status="passed",
            memory_status=BaselineStatus.NO_IMMEDIATE_ISSUE_DETECTED.value,
            cpu_status=BaselineStatus.NO_IMMEDIATE_ISSUE_DETECTED.value,
            gpu_status=BaselineStatus.NO_IMMEDIATE_ISSUE_DETECTED.value,
            storage_status=BaselineStatus.NO_IMMEDIATE_ISSUE_DETECTED.value,
            backup_allowed=True,
            restore_allowed=True,
            os_installation_allowed=True,
            gui_mode_allowed=True,
        )
        result = HardwareBaselineResult(
            run_id="run-privacy-check",
            collected_at="2026-08-06T00:00:00+00:00",
            mode="quick",
            subsystems=(
                _result("memory", BaselineStatus.NO_IMMEDIATE_ISSUE_DETECTED.value),
                _result("cpu", BaselineStatus.NO_IMMEDIATE_ISSUE_DETECTED.value),
                _result("gpu", BaselineStatus.NO_IMMEDIATE_ISSUE_DETECTED.value),
                _result("nvme", BaselineStatus.NO_IMMEDIATE_ISSUE_DETECTED.value, device_id="nvme0n1"),
            ),
            gate=gate,
        )
        blob = json.dumps(result.to_dict(), ensure_ascii=False)
        self.assertIsNone(_SERIAL_LIKE.search(blob))
        self.assertIsNone(_MAC_LIKE.search(blob))
        self.assertIsNone(_IPV4_LIKE.search(blob))
        self.assertNotIn("serial", blob.lower())

    def test_findings_must_not_embed_raw_serial_numbers(self) -> None:
        finding = HardwareFinding(
            code="nvme.critical_warning",
            severity=BaselineSeverity.RED.value,
            message="Critical Warning bitmask is non-zero.",
            evidence=("smart-log:critical_warning=0x4",),
        )
        blob = json.dumps(finding.to_dict())
        self.assertIsNone(_SERIAL_LIKE.search(blob))
        self.assertNotIn("S3Z1NX0M123456", blob)


class TestGateNeverBypassesSafetyFacade(unittest.TestCase):
    def test_diagnostics_declare_additive_only(self) -> None:
        diag = build_hardware_baseline_gate_diagnostics()
        self.assertTrue(diag["additive_only"])
        self.assertFalse(diag["bypasses_safety_facade"])

    def test_operation_evaluation_never_sets_bypass_flag(self) -> None:
        gate = build_hardware_baseline_gate(
            memory=_result("memory", BaselineStatus.NO_IMMEDIATE_ISSUE_DETECTED.value),
            cpu=_result("cpu", BaselineStatus.NO_IMMEDIATE_ISSUE_DETECTED.value),
            gpu=_result("gpu", BaselineStatus.NO_IMMEDIATE_ISSUE_DETECTED.value),
            storage=[],
        )
        for op in ("backup", "restore", "os_installation", "gui_mode"):
            decision = evaluate_operation_against_baseline_gate(gate, op)
            self.assertFalse(decision["bypasses_safety_facade"])


class TestForbiddenBaselineClaimsAbsent(unittest.TestCase):
    def test_green_result_never_claims_fault_free(self) -> None:
        result = HardwareBaselineResult(
            run_id="r1",
            collected_at="2026-08-06T00:00:00+00:00",
            subsystems=(_result("memory", BaselineStatus.NO_IMMEDIATE_ISSUE_DETECTED.value),),
        )
        blob = json.dumps(result.to_dict()).lower()
        for forbidden in ("fault_free", "fully_verified", "fully_stable", "disk_without_defect", "healthy"):
            self.assertNotIn(forbidden, blob)


if __name__ == "__main__":
    unittest.main()
