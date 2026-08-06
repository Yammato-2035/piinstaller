"""PI-RS-HW-BASELINE-DIAG-I18N-002 Phase 11: hardware_baseline_gate.py tests."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from core.hardware_baseline_contracts import BaselineSeverity, BaselineStatus, HardwareSubsystemResult
from rescue.hardware_baseline_gate import (
    build_hardware_baseline_gate,
    build_hardware_baseline_gate_diagnostics,
    evaluate_operation_against_baseline_gate,
)


def _result(subsystem: str, status: str, *, device_id: str | None = None) -> HardwareSubsystemResult:
    severity = {
        BaselineStatus.NO_IMMEDIATE_ISSUE_DETECTED.value: BaselineSeverity.GREEN.value,
        BaselineStatus.REVIEW_REQUIRED.value: BaselineSeverity.YELLOW.value,
        BaselineStatus.IMMEDIATE_ISSUE_DETECTED.value: BaselineSeverity.RED.value,
        BaselineStatus.NOT_TESTED.value: BaselineSeverity.GRAY.value,
    }.get(status, BaselineSeverity.GRAY.value)
    return HardwareSubsystemResult(subsystem=subsystem, status=status, severity=severity, device_id=device_id)


_GREEN_MEM = _result("memory", BaselineStatus.NO_IMMEDIATE_ISSUE_DETECTED.value)
_GREEN_CPU = _result("cpu", BaselineStatus.NO_IMMEDIATE_ISSUE_DETECTED.value)
_GREEN_GPU = _result("gpu", BaselineStatus.NO_IMMEDIATE_ISSUE_DETECTED.value)
_RED_MEM = _result("memory", BaselineStatus.IMMEDIATE_ISSUE_DETECTED.value)
_RED_CPU = _result("cpu", BaselineStatus.IMMEDIATE_ISSUE_DETECTED.value)
_RED_GPU = _result("gpu", BaselineStatus.IMMEDIATE_ISSUE_DETECTED.value)
_YELLOW_GPU = _result("gpu", BaselineStatus.REVIEW_REQUIRED.value)
_NOT_TESTED_MEM = _result("memory", BaselineStatus.NOT_TESTED.value)


class TestBuildHardwareBaselineGate(unittest.TestCase):
    def test_all_green_passes(self) -> None:
        gate = build_hardware_baseline_gate(memory=_GREEN_MEM, cpu=_GREEN_CPU, gpu=_GREEN_GPU, storage=[])
        self.assertEqual(gate.status, "passed")
        self.assertTrue(gate.restore_allowed)
        self.assertTrue(gate.os_installation_allowed)
        self.assertTrue(gate.gui_mode_allowed)

    def test_red_memory_blocks_restore_and_install(self) -> None:
        gate = build_hardware_baseline_gate(memory=_RED_MEM, cpu=_GREEN_CPU, gpu=_GREEN_GPU, storage=[])
        self.assertEqual(gate.status, "blocked")
        self.assertFalse(gate.restore_allowed)
        self.assertFalse(gate.os_installation_allowed)
        self.assertTrue(gate.backup_allowed)  # backup from a failing source must still be possible

    def test_red_cpu_blocks_restore(self) -> None:
        gate = build_hardware_baseline_gate(memory=_GREEN_MEM, cpu=_RED_CPU, gpu=_GREEN_GPU, storage=[])
        self.assertFalse(gate.restore_allowed)

    def test_red_gpu_blocks_gui_but_not_restore(self) -> None:
        gate = build_hardware_baseline_gate(memory=_GREEN_MEM, cpu=_GREEN_CPU, gpu=_RED_GPU, storage=[])
        self.assertFalse(gate.gui_mode_allowed)
        self.assertTrue(gate.restore_allowed)

    def test_yellow_gpu_warns_for_gui_but_still_allowed(self) -> None:
        gate = build_hardware_baseline_gate(memory=_GREEN_MEM, cpu=_GREEN_CPU, gpu=_YELLOW_GPU, storage=[])
        self.assertTrue(gate.gui_mode_allowed)
        self.assertEqual(gate.status, "review_required")

    def test_not_tested_yields_incomplete(self) -> None:
        gate = build_hardware_baseline_gate(memory=_NOT_TESTED_MEM, cpu=_GREEN_CPU, gpu=_GREEN_GPU, storage=[])
        self.assertEqual(gate.status, "incomplete")
        self.assertFalse(gate.restore_allowed)

    def test_empty_subsystems_storage_not_tested(self) -> None:
        gate = build_hardware_baseline_gate(memory=_GREEN_MEM, cpu=_GREEN_CPU, gpu=_GREEN_GPU, storage=[])
        self.assertEqual(gate.storage_status, BaselineStatus.NOT_TESTED.value)

    def test_storage_status_aggregation_worst_wins(self) -> None:
        disk1 = _result("hdd", BaselineStatus.NO_IMMEDIATE_ISSUE_DETECTED.value, device_id="sda")
        disk2 = _result("nvme", BaselineStatus.IMMEDIATE_ISSUE_DETECTED.value, device_id="nvme0n1")
        gate = build_hardware_baseline_gate(memory=_GREEN_MEM, cpu=_GREEN_CPU, gpu=_GREEN_GPU, storage=[disk1, disk2])
        self.assertEqual(gate.storage_status, BaselineStatus.IMMEDIATE_ISSUE_DETECTED.value)
        self.assertEqual(gate.status, "blocked")

    def test_required_extended_tests_surfaced_in_next_actions(self) -> None:
        gate = build_hardware_baseline_gate(memory=_RED_MEM, cpu=_GREEN_CPU, gpu=_GREEN_GPU, storage=[])
        self.assertTrue(len(gate.required_next_actions) > 0)


class TestEvaluateOperationAgainstBaselineGate(unittest.TestCase):
    def test_backup_allowed_even_with_red_source_disk(self) -> None:
        gate = build_hardware_baseline_gate(memory=_RED_MEM, cpu=_GREEN_CPU, gpu=_GREEN_GPU, storage=[])
        result = evaluate_operation_against_baseline_gate(
            gate, "backup", source_disk_status=BaselineStatus.IMMEDIATE_ISSUE_DETECTED.value, target_disk_status=BaselineStatus.NO_IMMEDIATE_ISSUE_DETECTED.value
        )
        self.assertTrue(result["allowed"])
        self.assertFalse(result["bypasses_safety_facade"])

    def test_backup_blocked_when_target_disk_red(self) -> None:
        gate = build_hardware_baseline_gate(memory=_GREEN_MEM, cpu=_GREEN_CPU, gpu=_GREEN_GPU, storage=[])
        result = evaluate_operation_against_baseline_gate(gate, "backup", target_disk_status=BaselineStatus.IMMEDIATE_ISSUE_DETECTED.value)
        self.assertFalse(result["allowed"])

    def test_restore_blocked_when_gate_blocked(self) -> None:
        gate = build_hardware_baseline_gate(memory=_RED_MEM, cpu=_GREEN_CPU, gpu=_GREEN_GPU, storage=[])
        result = evaluate_operation_against_baseline_gate(gate, "restore")
        self.assertFalse(result["allowed"])

    def test_restore_blocked_when_target_disk_red_even_if_gate_passed(self) -> None:
        gate = build_hardware_baseline_gate(memory=_GREEN_MEM, cpu=_GREEN_CPU, gpu=_GREEN_GPU, storage=[])
        result = evaluate_operation_against_baseline_gate(gate, "restore", target_disk_status=BaselineStatus.IMMEDIATE_ISSUE_DETECTED.value)
        self.assertFalse(result["allowed"])

    def test_os_installation_allowed_when_gate_passed_and_target_green(self) -> None:
        gate = build_hardware_baseline_gate(memory=_GREEN_MEM, cpu=_GREEN_CPU, gpu=_GREEN_GPU, storage=[])
        result = evaluate_operation_against_baseline_gate(gate, "os_installation", target_disk_status=BaselineStatus.NO_IMMEDIATE_ISSUE_DETECTED.value)
        self.assertTrue(result["allowed"])

    def test_gui_mode_blocked_when_gpu_red(self) -> None:
        gate = build_hardware_baseline_gate(memory=_GREEN_MEM, cpu=_GREEN_CPU, gpu=_RED_GPU, storage=[])
        result = evaluate_operation_against_baseline_gate(gate, "gui_mode")
        self.assertFalse(result["allowed"])

    def test_unknown_operation_rejected(self) -> None:
        gate = build_hardware_baseline_gate(memory=_GREEN_MEM, cpu=_GREEN_CPU, gpu=_GREEN_GPU, storage=[])
        result = evaluate_operation_against_baseline_gate(gate, "reformat_everything")
        self.assertFalse(result["allowed"])

    def test_never_bypasses_safety_facade_flag(self) -> None:
        gate = build_hardware_baseline_gate(memory=_GREEN_MEM, cpu=_GREEN_CPU, gpu=_GREEN_GPU, storage=[])
        for op in ("backup", "restore", "os_installation", "gui_mode"):
            result = evaluate_operation_against_baseline_gate(gate, op)
            self.assertFalse(result["bypasses_safety_facade"])


class TestDiagnostics(unittest.TestCase):
    def test_additive_only_and_no_bypass(self) -> None:
        diag = build_hardware_baseline_gate_diagnostics()
        self.assertTrue(diag["additive_only"])
        self.assertFalse(diag["bypasses_safety_facade"])


if __name__ == "__main__":
    unittest.main()
