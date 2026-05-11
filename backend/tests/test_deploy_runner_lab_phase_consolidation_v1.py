from __future__ import annotations

import unittest
from pathlib import Path

from deploy.runner_lab_phase_consolidation import build_runner_lab_phase_consolidation

_REPO_ROOT = Path(__file__).resolve().parents[2]


class DeployRunnerLabPhaseConsolidationV1Tests(unittest.TestCase):
    def test_all_required_components_present(self) -> None:
        out = build_runner_lab_phase_consolidation(include_artifact_existence=False)
        ids = {c["component_id"] for c in out["components"]}
        for required in [
            "RUNNER_COMPONENT_REAL_WRITE_GUARD",
            "RUNNER_COMPONENT_HARDWARE_GATE",
            "RUNNER_COMPONENT_REAL_WRITE_PROTOTYPE",
            "RUNNER_COMPONENT_FAILURE_INJECTION",
            "RUNNER_COMPONENT_RUNNER_CONTRACT",
            "RUNNER_COMPONENT_RUNNER_RUNTIME_VALIDATION",
            "RUNNER_COMPONENT_RUNNER_LIFECYCLE",
            "RUNNER_COMPONENT_RUNNER_HANDOFF",
            "RUNNER_COMPONENT_PERMISSION_BOUNDARY",
            "RUNNER_COMPONENT_SANDBOX",
            "RUNNER_COMPONENT_ROOTLESS_E2E",
            "RUNNER_COMPONENT_INSTALL_PLAN",
            "RUNNER_COMPONENT_INSTALL_VALIDATOR",
            "RUNNER_COMPONENT_PACKAGE_BLUEPRINT",
            "RUNNER_COMPONENT_INSTALL_CONSISTENCY",
            "RUNNER_COMPONENT_RELEASE_READINESS",
            "RUNNER_COMPONENT_LAB_READINESS_UNBLOCK_PLAN",
            "RUNNER_COMPONENT_SEVEN_RUNTIME_TEST_DESIGNS",
            "RUNNER_COMPONENT_LAB_READINESS_STATUS",
            "RUNNER_COMPONENT_RUNTIME_RUNBOOK_BUNDLE",
            "RUNNER_COMPONENT_RUNTIME_RUNBOOK_EXPORT",
            "RUNNER_COMPONENT_RUNTIME_RESULT_VALIDATOR",
            "RUNNER_COMPONENT_LAB_ACCEPTANCE_AGGREGATOR",
            "RUNNER_COMPONENT_LAB_ACCEPTANCE_REPORT_EXPORT",
        ]:
            self.assertIn(required, ids)

    def test_artifact_index_contains_required_domains(self) -> None:
        out = build_runner_lab_phase_consolidation(include_artifact_existence=False)
        types = {a["artifact_type"] for a in out["artifact_index"]}
        for t in ["backend_module", "test", "deploy_doc", "kb", "evidence", "runbook_export", "template", "report"]:
            self.assertIn(t, types)

    def test_runtime_open_items_contains_all_7(self) -> None:
        out = build_runner_lab_phase_consolidation(include_artifact_existence=False)
        self.assertEqual(len(out["runtime_open_items"]), 7)

    def test_runtime_open_items_auto_allowed_false(self) -> None:
        out = build_runner_lab_phase_consolidation(include_artifact_existence=False)
        self.assertTrue(all(x["auto_allowed"] is False for x in out["runtime_open_items"]))

    def test_runtime_open_items_blocks_production_true(self) -> None:
        out = build_runner_lab_phase_consolidation(include_artifact_existence=False)
        self.assertTrue(all(x["blocks_production"] is True for x in out["runtime_open_items"]))

    def test_validated_items_contains_expected(self) -> None:
        out = build_runner_lab_phase_consolidation(include_artifact_existence=False)
        for key in ["ROOTLESS_E2E", "READ_ONLY_EXPORT_VALIDATOR_AGGREGATOR_PATHS", "RUNTIME_RUNBOOK_EXPORT", "LAB_ACCEPTANCE_REPORT_EXPORT"]:
            self.assertIn(key, out["validated_items"])

    def test_planned_only_contains_all_7_runtime_tests(self) -> None:
        out = build_runner_lab_phase_consolidation(include_artifact_existence=False)
        for code in [
            "RUNBOOK_SUDOERS_RUNTIME_DRYRUN",
            "RUNBOOK_PRIVILEGED_RUNNER_VALIDATION_DRYRUN",
            "RUNBOOK_REAL_WRITE_HARDWARE_E2E",
            "RUNBOOK_FAILURE_INJECTION_HARDWARE_E2E",
            "RUNBOOK_DEVICE_REENUMERATION",
            "RUNBOOK_HOTPLUG_UNMOUNT_RACE",
            "RUNBOOK_ROLLBACK_RUNTIME",
        ]:
            self.assertIn(code, out["planned_only_items"])

    def test_risk_summary_contains_not_production_and_privileged_open(self) -> None:
        out = build_runner_lab_phase_consolidation(include_artifact_existence=False)
        self.assertIn("NOT_PRODUCTION_READY", out["risk_summary"])
        self.assertIn("PRIVILEGED_RUNNER_NOT_REAL_VALIDATED", out["risk_summary"])

    def test_release_statement_flags(self) -> None:
        out = build_runner_lab_phase_consolidation(include_artifact_existence=False)
        rs = out["release_statement"]
        self.assertFalse(rs["production_ready"])
        self.assertFalse(rs["automatic_release_allowed"])

    def test_no_production_ready_true_output(self) -> None:
        out = build_runner_lab_phase_consolidation(include_artifact_existence=False)
        self.assertNotEqual(out["release_statement"]["production_ready"], True)

    def test_no_execute_apply_install_write_delete_release_route(self) -> None:
        routes = (_REPO_ROOT / "backend/deploy/routes.py").read_text(encoding="utf-8")
        self.assertIn("/runner/lab-phase/consolidation", routes)
        for forbidden in ["/runner/lab-phase/consolidation/execute", "/runner/lab-phase/consolidation/apply", "/runner/lab-phase/consolidation/install", "/runner/lab-phase/consolidation/write", "/runner/lab-phase/consolidation/delete", "/runner/lab-phase/consolidation/release"]:
            self.assertNotIn(forbidden, routes)

    def test_no_forbidden_systemcalls(self) -> None:
        src = (_REPO_ROOT / "backend/deploy/runner_lab_phase_consolidation.py").read_text(encoding="utf-8").lower()
        for token in ["subprocess", "os.system", "chmod(", "chown(", "systemctl", " dd ", "mkfs", "mount ", "umount"]:
            self.assertNotIn(token, src)


if __name__ == "__main__":
    unittest.main()
