from __future__ import annotations

import unittest
from pathlib import Path

from deploy.runner_next_phase_gate import evaluate_runner_next_phase_gate

from deploy.routes_source_aggregate import read_deploy_routes_aggregate

_REPO_ROOT = Path(__file__).resolve().parents[2]


class DeployRunnerNextPhaseGateV1Tests(unittest.TestCase):
    def test_without_runtime_results_manual_runtime_allowed(self) -> None:
        gate = evaluate_runner_next_phase_gate(
            acceptance={"acceptance_status": "hold", "operator_decision_required": True, "residual_risks": ["x"]},
            runtime_validation={"validation_status": "blocked"},
            runbook_export={"export_status": "ok"},
            consolidation={"consolidation_status": "ok", "runtime_open_items": [{}]},
        )
        self.assertEqual(gate["gate_status"], "manual_runtime_allowed")
        self.assertIn("NEXT_PHASE_MANUAL_RUNTIME_TESTS", gate["allowed_next_phases"])

    def test_production_release_always_blocked(self) -> None:
        gate = evaluate_runner_next_phase_gate()
        self.assertIn("NEXT_PHASE_BLOCKED_PRODUCTION_RELEASE", gate["blocked_next_phases"])

    def test_automated_deploy_always_blocked(self) -> None:
        gate = evaluate_runner_next_phase_gate()
        self.assertIn("NEXT_PHASE_BLOCKED_AUTOMATED_DEPLOY", gate["blocked_next_phases"])

    def test_unattended_write_always_blocked(self) -> None:
        gate = evaluate_runner_next_phase_gate()
        self.assertIn("NEXT_PHASE_BLOCKED_UNATTENDED_WRITE", gate["blocked_next_phases"])

    def test_skip_runtime_tests_always_blocked(self) -> None:
        gate = evaluate_runner_next_phase_gate()
        self.assertIn("NEXT_PHASE_BLOCKED_SKIP_RUNTIME_TESTS", gate["blocked_next_phases"])

    def test_root_backend_blocked(self) -> None:
        gate = evaluate_runner_next_phase_gate()
        self.assertIn("NEXT_PHASE_BLOCKED_ROOT_BACKEND", gate["blocked_next_phases"])

    def test_privileged_daemon_blocked(self) -> None:
        gate = evaluate_runner_next_phase_gate()
        self.assertIn("NEXT_PHASE_BLOCKED_PRIVILEGED_DAEMON", gate["blocked_next_phases"])

    def test_repeat_required_from_aggregator(self) -> None:
        gate = evaluate_runner_next_phase_gate(
            acceptance={"acceptance_status": "repeat_required", "operator_decision_required": True, "residual_risks": ["x"]},
            runtime_validation={"validation_status": "ok"},
            runbook_export={"export_status": "ok"},
            consolidation={"consolidation_status": "ok", "runtime_open_items": [{}]},
        )
        self.assertEqual(gate["gate_status"], "repeat_required")

    def test_blocked_from_aggregator(self) -> None:
        gate = evaluate_runner_next_phase_gate(
            acceptance={"acceptance_status": "blocked", "operator_decision_required": True, "residual_risks": ["x"]},
            runtime_validation={"validation_status": "ok"},
            runbook_export={"export_status": "ok"},
            consolidation={"consolidation_status": "ok", "runtime_open_items": [{}]},
        )
        self.assertEqual(gate["gate_status"], "blocked")

    def test_lab_candidate_no_production_release(self) -> None:
        gate = evaluate_runner_next_phase_gate(
            acceptance={"acceptance_status": "lab_ready_candidate", "operator_decision_required": True, "residual_risks": ["x"]},
            runtime_validation={"validation_status": "ok"},
            runbook_export={"export_status": "ok"},
            consolidation={"consolidation_status": "ok", "runtime_open_items": [{}]},
        )
        self.assertNotIn("NEXT_PHASE_PRODUCTION_RELEASE", gate["allowed_next_phases"])

    def test_operator_requirements_complete(self) -> None:
        gate = evaluate_runner_next_phase_gate()
        req_codes = {x["code"] for x in gate["operator_requirements"]}
        for k in [
            "manual_operator_required",
            "local_control_required",
            "physical_test_media_required",
            "full_backup_required",
            "single_test_media_required",
            "stop_conditions_acknowledged",
            "automatic_execution_allowed",
        ]:
            self.assertIn(k, req_codes)

    def test_no_execute_apply_install_write_delete_release_route(self) -> None:
        routes = read_deploy_routes_aggregate()
        self.assertIn("/runner/next-phase/gate", routes)
        for forbidden in [
            "/runner/next-phase/gate/execute",
            "/runner/next-phase/gate/apply",
            "/runner/next-phase/gate/install",
            "/runner/next-phase/gate/write",
            "/runner/next-phase/gate/delete",
            "/runner/next-phase/gate/release",
        ]:
            self.assertNotIn(forbidden, routes)

    def test_no_forbidden_systemcalls(self) -> None:
        src = (_REPO_ROOT / "backend/deploy/runner_next_phase_gate.py").read_text(encoding="utf-8").lower()
        for token in ["subprocess", "os.system", "chmod(", "chown(", "systemctl", " dd ", "mkfs", "mount ", "umount"]:
            self.assertNotIn(token, src)


if __name__ == "__main__":
    unittest.main()
