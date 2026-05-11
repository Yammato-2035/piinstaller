"""Tests fuer Runner Lab Readiness Unblock Plan."""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

_BACKEND = Path(__file__).resolve().parent.parent
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

from deploy.runner_lab_readiness_plan import build_runner_lab_readiness_unblock_plan


class TestDeployRunnerLabReadinessPlanV1(unittest.TestCase):
    def test_all_blocking_gaps_present(self):
        out = build_runner_lab_readiness_unblock_plan()
        codes = {str((x or {}).get("gap_code") or "") for x in list(out.get("gap_plan") or [])}
        required = {
            "RUNNER_GAP_REAL_WRITE_HARDWARE_E2E_OPEN",
            "RUNNER_GAP_PRIVILEGED_RUNNER_VALIDATION_OPEN",
            "RUNNER_GAP_SUDOERS_RUNTIME_OPEN",
            "RUNNER_GAP_FAILURE_INJECTION_HW_OPEN",
            "RUNNER_GAP_ROLLBACK_RUNTIME_OPEN",
            "RUNNER_GAP_DEVICE_REENUMERATION_OPEN",
            "RUNNER_GAP_HOTPLUG_RACE_OPEN",
        }
        self.assertTrue(required.issubset(codes))

    def test_execution_order_correct(self):
        out = build_runner_lab_readiness_unblock_plan()
        steps = list(out.get("execution_order") or [])
        self.assertEqual(7, len(steps))
        self.assertEqual("LAB_STEP_SUDOERS_RUNTIME_DRYRUN", steps[0]["code"])
        self.assertEqual("LAB_STEP_ROLLBACK_RUNTIME_TEST", steps[-1]["code"])

    def test_all_steps_auto_allowed_false(self):
        out = build_runner_lab_readiness_unblock_plan()
        for step in out["execution_order"]:
            self.assertFalse(bool(step.get("auto_allowed")))

    def test_all_steps_manual_operator_required_true(self):
        out = build_runner_lab_readiness_unblock_plan()
        for step in out["execution_order"]:
            self.assertTrue(bool(step.get("manual_operator_required")))

    def test_required_equipment_contains_test_media(self):
        out = build_runner_lab_readiness_unblock_plan()
        self.assertIn("disposable_usb_or_sd_test_media", list(out.get("required_equipment") or []))

    def test_required_evidence_contains_lsblk_findmnt_sha_audit(self):
        out = build_runner_lab_readiness_unblock_plan()
        evidence = list(out.get("required_evidence") or [])
        self.assertIn("lsblk_before_after_each_test", evidence)
        self.assertIn("findmnt_before_after_each_test", evidence)
        self.assertIn("verify_sha256", evidence)
        self.assertIn("runner_audit_jsonl", evidence)

    def test_risk_controls_contain_no_remote_without_local_control(self):
        out = build_runner_lab_readiness_unblock_plan()
        self.assertIn("no_remote_test_without_local_control", list(out.get("risk_controls") or []))

    def test_stop_conditions_contain_operator_unsure(self):
        out = build_runner_lab_readiness_unblock_plan()
        self.assertIn("operator_unsure", list(out.get("stop_conditions") or []))

    def test_no_execute_apply_write_route_present(self):
        try:
            from fastapi import FastAPI
        except ImportError:
            self.skipTest("fastapi nicht installiert")
        import deploy.routes as routes_mod

        app = FastAPI()
        app.include_router(routes_mod.router)
        paths = {getattr(r, "path", "") for r in app.routes}
        self.assertIn("/api/deploy/runner/lab-readiness/unblock-plan", paths)
        self.assertNotIn("/api/deploy/runner/lab-readiness/execute", paths)
        self.assertNotIn("/api/deploy/runner/lab-readiness/apply", paths)
        self.assertNotIn("/api/deploy/runner/lab-readiness/write", paths)

    def test_no_forbidden_systemcalls(self):
        src = (_BACKEND / "deploy" / "runner_lab_readiness_plan.py").read_text(encoding="utf-8").lower()
        forbidden_patterns = [
            r"\bsudo\b",
            r"\bvisudo\b",
            r"chmod\(",
            r"chown\(",
            r"mkdir\(",
            r"\bsystemctl\b",
            r"os\.system\(",
            r"subprocess\.",
            r"shell\s*=\s*true",
        ]
        for pat in forbidden_patterns:
            self.assertIsNone(re.search(pat, src), msg=pat)

