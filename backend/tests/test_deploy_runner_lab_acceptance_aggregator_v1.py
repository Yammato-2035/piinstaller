from __future__ import annotations

import unittest
from pathlib import Path

from deploy.runner_lab_acceptance_aggregator import build_runner_lab_acceptance_summary


def _required_runbooks() -> list[str]:
    return [
        "RUNBOOK_SUDOERS_RUNTIME_DRYRUN",
        "RUNBOOK_PRIVILEGED_RUNNER_VALIDATION_DRYRUN",
        "RUNBOOK_REAL_WRITE_HARDWARE_E2E",
        "RUNBOOK_FAILURE_INJECTION_HARDWARE_E2E",
        "RUNBOOK_DEVICE_REENUMERATION",
        "RUNBOOK_HOTPLUG_UNMOUNT_RACE",
        "RUNBOOK_ROLLBACK_RUNTIME",
    ]


def _result_entry(runbook_id: str, pass_fail: str = "pass", findings: list[str] | None = None) -> dict:
    return {
        "ok": True,
        "result": {"runbook_id": runbook_id, "pass_fail": pass_fail, "rollback_status": "ok"},
        "blocking_findings": list(findings or []),
        "warnings": [],
        "errors": [],
    }


def _validated_bundle(status: str = "ok", entries: list[dict] | None = None, findings: list[str] | None = None, decision: str = "blocked") -> dict:
    items = list(entries or [])
    return {
        "validation_status": status,
        "result_files": [f"docs/evidence/runtime-results/{idx}.json" for idx, _ in enumerate(items)],
        "runbook_results": items,
        "blocking_findings": list(findings or []),
        "acceptance_check": {"accepted_decision": decision},
        "warnings": [],
        "errors": [],
    }


class DeployRunnerLabAcceptanceAggregatorV1Tests(unittest.TestCase):
    def test_7_pass_validator_ok_candidate(self) -> None:
        entries = [_result_entry(rb, "pass") for rb in _required_runbooks()]
        out = build_runner_lab_acceptance_summary(validated_runtime_results=_validated_bundle(status="ok", entries=entries))
        self.assertEqual(out["acceptance_status"], "lab_ready_candidate")

    def test_validator_blocked_means_blocked(self) -> None:
        entries = [_result_entry(rb, "pass") for rb in _required_runbooks()]
        out = build_runner_lab_acceptance_summary(
            validated_runtime_results=_validated_bundle(status="blocked", entries=entries, findings=["RESULT_JSON_INVALID"])
        )
        self.assertEqual(out["acceptance_status"], "blocked")

    def test_one_runbook_failed_blocked(self) -> None:
        entries = [_result_entry(rb, "pass") for rb in _required_runbooks()]
        entries[2] = _result_entry(_required_runbooks()[2], "fail")
        out = build_runner_lab_acceptance_summary(validated_runtime_results=_validated_bundle(status="ok", entries=entries))
        self.assertEqual(out["acceptance_status"], "blocked")

    def test_one_runbook_missing_repeat_or_blocked(self) -> None:
        entries = [_result_entry(rb, "pass") for rb in _required_runbooks()[:-1]]
        out = build_runner_lab_acceptance_summary(validated_runtime_results=_validated_bundle(status="ok", entries=entries))
        self.assertIn(out["acceptance_status"], {"repeat_required", "blocked"})

    def test_evidence_partial_repeat_required(self) -> None:
        entries = [_result_entry(rb, "pass") for rb in _required_runbooks()]
        entries[0] = _result_entry(_required_runbooks()[0], "pass", findings=["RESULT_EVIDENCE_MISSING"])
        out = build_runner_lab_acceptance_summary(validated_runtime_results=_validated_bundle(status="ok", entries=entries))
        self.assertEqual(out["acceptance_status"], "repeat_required")

    def test_rollback_incomplete_blocked(self) -> None:
        entries = [_result_entry(rb, "pass") for rb in _required_runbooks()]
        entries[-1] = _result_entry(_required_runbooks()[-1], "pass", findings=["RESULT_ROLLBACK_INCOMPLETE"])
        out = build_runner_lab_acceptance_summary(validated_runtime_results=_validated_bundle(status="ok", entries=entries))
        self.assertEqual(out["acceptance_status"], "blocked")

    def test_verify_mismatch_blocked(self) -> None:
        entries = [_result_entry(rb, "pass") for rb in _required_runbooks()]
        entries[2] = _result_entry(_required_runbooks()[2], "pass", findings=["RESULT_VERIFY_MISMATCH"])
        out = build_runner_lab_acceptance_summary(validated_runtime_results=_validated_bundle(status="ok", entries=entries))
        self.assertEqual(out["acceptance_status"], "blocked")

    def test_internal_drive_touched_blocked(self) -> None:
        entries = [_result_entry(rb, "pass") for rb in _required_runbooks()]
        entries[2] = _result_entry(_required_runbooks()[2], "pass", findings=["RESULT_INTERNAL_DRIVE_TOUCHED"])
        out = build_runner_lab_acceptance_summary(validated_runtime_results=_validated_bundle(status="ok", entries=entries))
        self.assertEqual(out["acceptance_status"], "blocked")

    def test_untracked_mount_change_blocked(self) -> None:
        entries = [_result_entry(rb, "pass") for rb in _required_runbooks()]
        entries[2] = _result_entry(_required_runbooks()[2], "pass", findings=["RESULT_UNTRACKED_MOUNT_CHANGE"])
        out = build_runner_lab_acceptance_summary(validated_runtime_results=_validated_bundle(status="ok", entries=entries))
        self.assertEqual(out["acceptance_status"], "blocked")

    def test_residual_risks_visible_on_candidate(self) -> None:
        entries = [_result_entry(rb, "pass") for rb in _required_runbooks()]
        out = build_runner_lab_acceptance_summary(validated_runtime_results=_validated_bundle(status="ok", entries=entries))
        self.assertGreaterEqual(len(out["residual_risks"]), 5)

    def test_operator_decision_always_required(self) -> None:
        out = build_runner_lab_acceptance_summary(validated_runtime_results=_validated_bundle(status="blocked", entries=[]))
        self.assertTrue(out["operator_decision_required"])

    def test_no_production_ready_possible(self) -> None:
        entries = [_result_entry(rb, "pass") for rb in _required_runbooks()]
        out = build_runner_lab_acceptance_summary(validated_runtime_results=_validated_bundle(status="ok", entries=entries))
        self.assertNotEqual(out["acceptance_status"], "production_ready")

    def test_no_execute_apply_install_write_delete_route_present(self) -> None:
        routes = Path(__file__).resolve().parents[1] / "deploy" / "routes.py"
        text = routes.read_text(encoding="utf-8")
        self.assertIn("/runner/lab-readiness/acceptance", text)
        self.assertNotIn("/runner/lab-readiness/acceptance/execute", text)
        self.assertNotIn("/runner/lab-readiness/acceptance/apply", text)
        self.assertNotIn("/runner/lab-readiness/acceptance/install", text)
        self.assertNotIn("/runner/lab-readiness/acceptance/write", text)
        self.assertNotIn("/runner/lab-readiness/acceptance/delete", text)

    def test_no_forbidden_systemcalls(self) -> None:
        src = (Path(__file__).resolve().parents[1] / "deploy" / "runner_lab_acceptance_aggregator.py").read_text(encoding="utf-8").lower()
        for token in ["subprocess", "os.system", "chmod(", "chown(", "systemctl", " dd ", "mkfs", "mount ", "umount"]:
            self.assertNotIn(token, src)


if __name__ == "__main__":
    unittest.main()
