from __future__ import annotations

import unittest
from pathlib import Path

from deploy.runner_manual_runtime_precheck import build_runner_manual_runtime_precheck

_REPO_ROOT = Path(__file__).resolve().parents[2]


class DeployRunnerManualRuntimePrecheckV1Tests(unittest.TestCase):
    def _operator_ok(self) -> dict[str, bool]:
        return {
            "full_backup_confirmed": True,
            "local_control_confirmed": True,
            "single_test_media_confirmed": True,
            "productive_media_removed_confirmed": True,
            "stop_conditions_acknowledged": True,
            "no_remote_without_local_control_confirmed": True,
            "no_auto_retry_confirmed": True,
            "operator_understands_data_loss": True,
        }

    def test_unknown_runbook_blocked(self) -> None:
        out = build_runner_manual_runtime_precheck(selected_runbook="UNKNOWN")
        self.assertEqual(out["precheck_status"], "blocked")
        self.assertIn("MANUAL_RUNTIME_PRECHECK_BLOCKED_UNKNOWN_RUNBOOK", out["blocked_reasons"])

    def test_valid_dry_run_without_test_media_possible(self) -> None:
        out = build_runner_manual_runtime_precheck(
            selected_runbook="RUNBOOK_SUDOERS_RUNTIME_DRYRUN",
            next_phase_gate={"allowed_next_phases": ["NEXT_PHASE_MANUAL_RUNTIME_TESTS"]},
            operator_confirmations=self._operator_ok(),
            runtime_context={},
        )
        self.assertIn(out["precheck_status"], {"ready_for_manual_runtime", "review_required"})
        self.assertTrue(any(x["code"] == "MEDIA_NOT_APPLICABLE_DRYRUN" for x in out["test_media_checks"]))

    def test_write_runbook_without_hardware_gate_blocked(self) -> None:
        out = build_runner_manual_runtime_precheck(
            selected_runbook="RUNBOOK_REAL_WRITE_HARDWARE_E2E",
            next_phase_gate={"allowed_next_phases": ["NEXT_PHASE_MANUAL_RUNTIME_TESTS"]},
            operator_confirmations=self._operator_ok(),
            real_write_guard_report={"guard_status": "READY"},
            runtime_context={"physical_label_present": True, "target_device_declared": True, "snapshot_fingerprint_present": True},
        )
        self.assertEqual(out["precheck_status"], "blocked")
        self.assertIn("MEDIA_HARDWARE_GATE_REPORT_PROVIDED", out["blocked_reasons"])

    def test_hardware_gate_not_test_ready_blocked(self) -> None:
        out = build_runner_manual_runtime_precheck(
            selected_runbook="RUNBOOK_REAL_WRITE_HARDWARE_E2E",
            next_phase_gate={"allowed_next_phases": ["NEXT_PHASE_MANUAL_RUNTIME_TESTS"]},
            operator_confirmations=self._operator_ok(),
            hardware_gate_report={"gate_status": "review_required"},
            real_write_guard_report={"guard_status": "READY"},
            runtime_context={"physical_label_present": True, "target_device_declared": True, "snapshot_fingerprint_present": True},
        )
        self.assertEqual(out["precheck_status"], "blocked")
        self.assertIn("MEDIA_HARDWARE_GATE_TEST_READY", out["blocked_reasons"])

    def test_real_write_guard_missing_blocked(self) -> None:
        out = build_runner_manual_runtime_precheck(
            selected_runbook="RUNBOOK_REAL_WRITE_HARDWARE_E2E",
            next_phase_gate={"allowed_next_phases": ["NEXT_PHASE_MANUAL_RUNTIME_TESTS"]},
            operator_confirmations=self._operator_ok(),
            hardware_gate_report={"gate_status": "test_ready"},
            runtime_context={"physical_label_present": True, "target_device_declared": True, "snapshot_fingerprint_present": True},
        )
        self.assertEqual(out["precheck_status"], "blocked")
        self.assertIn("MEDIA_REAL_WRITE_GUARD_READY", out["blocked_reasons"])

    def test_operator_without_backup_review_or_blocked(self) -> None:
        conf = self._operator_ok()
        conf["full_backup_confirmed"] = False
        out = build_runner_manual_runtime_precheck(
            selected_runbook="RUNBOOK_SUDOERS_RUNTIME_DRYRUN",
            next_phase_gate={"allowed_next_phases": ["NEXT_PHASE_MANUAL_RUNTIME_TESTS"]},
            operator_confirmations=conf,
        )
        self.assertIn(out["precheck_status"], {"review_required", "blocked"})

    def test_multiple_candidate_media_blocks(self) -> None:
        out = build_runner_manual_runtime_precheck(
            selected_runbook="RUNBOOK_REAL_WRITE_HARDWARE_E2E",
            next_phase_gate={"allowed_next_phases": ["NEXT_PHASE_MANUAL_RUNTIME_TESTS"]},
            operator_confirmations=self._operator_ok(),
            hardware_gate_report={"gate_status": "test_ready"},
            real_write_guard_report={"guard_status": "READY"},
            runtime_context={
                "physical_label_present": True,
                "target_device_declared": True,
                "snapshot_fingerprint_present": True,
                "multiple_candidate_media": True,
            },
        )
        self.assertEqual(out["precheck_status"], "blocked")
        self.assertIn("MEDIA_NO_MULTIPLE_CANDIDATE_MEDIA", out["blocked_reasons"])

    def test_evidence_plan_contains_runtime_results_path(self) -> None:
        out = build_runner_manual_runtime_precheck(
            selected_runbook="RUNBOOK_SUDOERS_RUNTIME_DRYRUN",
            next_phase_gate={"allowed_next_phases": ["NEXT_PHASE_MANUAL_RUNTIME_TESTS"]},
            operator_confirmations=self._operator_ok(),
        )
        entry = next(x for x in out["evidence_plan"] if x["code"] == "EVIDENCE_RESULT_FILE_PATH")
        self.assertIn("docs/evidence/runtime-results/", entry["value"])

    def test_stop_conditions_complete(self) -> None:
        out = build_runner_manual_runtime_precheck(
            selected_runbook="RUNBOOK_SUDOERS_RUNTIME_DRYRUN",
            next_phase_gate={"allowed_next_phases": ["NEXT_PHASE_MANUAL_RUNTIME_TESTS"]},
            operator_confirmations=self._operator_ok(),
        )
        for code in [
            "operator_unsure",
            "unknown_target_media",
            "multiple_removable_media",
            "systemdisk_as_target",
            "hardware_gate_not_ready",
            "guard_not_ready",
            "unexpected_mount_change",
            "unexpected_device_change",
            "verify_mismatch",
            "audit_missing",
            "non_json_stdout",
            "blocked_env_variable",
        ]:
            self.assertIn(code, out["stop_conditions"])

    def test_auto_allowed_false_everywhere(self) -> None:
        out = build_runner_manual_runtime_precheck(
            selected_runbook="RUNBOOK_SUDOERS_RUNTIME_DRYRUN",
            next_phase_gate={"allowed_next_phases": ["NEXT_PHASE_MANUAL_RUNTIME_TESTS"]},
            operator_confirmations=self._operator_ok(),
        )
        for item in out["environment_checks"] + out["operator_checks"] + out["test_media_checks"]:
            self.assertFalse(item["auto_allowed"])
        for item in out["evidence_plan"]:
            self.assertFalse(item["auto_allowed"])

    def test_no_execute_apply_install_write_delete_release_route(self) -> None:
        routes = (_REPO_ROOT / "backend/deploy/routes.py").read_text(encoding="utf-8")
        self.assertIn("/runner/manual-runtime/precheck", routes)
        for forbidden in [
            "/runner/manual-runtime/precheck/execute",
            "/runner/manual-runtime/precheck/apply",
            "/runner/manual-runtime/precheck/install",
            "/runner/manual-runtime/precheck/write",
            "/runner/manual-runtime/precheck/delete",
            "/runner/manual-runtime/precheck/release",
        ]:
            self.assertNotIn(forbidden, routes)

    def test_no_forbidden_systemcalls(self) -> None:
        src = (_REPO_ROOT / "backend/deploy/runner_manual_runtime_precheck.py").read_text(encoding="utf-8").lower()
        for token in ["subprocess", "os.system", "chmod(", "chown(", "systemctl", " dd ", "mkfs", "mount ", "umount"]:
            self.assertNotIn(token, src)


if __name__ == "__main__":
    unittest.main()
