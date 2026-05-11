"""Tests fuer Failure Injection Hardware Testdesign."""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

_BACKEND = Path(__file__).resolve().parent.parent
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

from deploy.runner_failure_injection_hardware_test_plan import build_runner_failure_injection_hardware_test_plan


class TestDeployRunnerFailureInjectionHardwareTestPlanV1(unittest.TestCase):
    def test_gap_code_correct(self):
        out = build_runner_failure_injection_hardware_test_plan()
        self.assertEqual("RUNNER_GAP_FAILURE_INJECTION_HW_OPEN", out["gap_code"])

    def test_preconditions_contain_disposable_backup_testmode_hooks(self):
        out = build_runner_failure_injection_hardware_test_plan()
        codes = {str((x or {}).get("code") or "") for x in list(out["preconditions"])}
        self.assertIn("PRECONDITION_DISPOSABLE_MEDIA_AVAILABLE", codes)
        self.assertIn("PRECONDITION_FULL_BACKUP_AVAILABLE", codes)
        self.assertIn("PRECONDITION_FAILURE_INJECTION_HOOKS_AVAILABLE", codes)

    def test_test_steps_contain_happy_path_prereq(self):
        out = build_runner_failure_injection_hardware_test_plan()
        codes = {str((x or {}).get("code") or "") for x in list(out["test_steps"])}
        self.assertIn("FI_HW_STEP_CONFIRM_HAPPY_PATH_REFERENCE", codes)

    def test_failure_cases_contain_all_required(self):
        out = build_runner_failure_injection_hardware_test_plan()
        codes = {str((x or {}).get("code") or "") for x in list(out["failure_cases"])}
        required = {
            "FAIL_BEFORE_OPEN",
            "FAIL_AFTER_OPEN",
            "FAIL_AFTER_CHUNKS",
            "FAIL_DURING_FSYNC",
            "FAIL_VERIFY_MISMATCH",
            "FAIL_DEVICE_CHANGED",
            "SIMULATED_READONLY_FLIP",
            "SIMULATED_MOUNTED_FLIP",
            "VERIFY_SHORT_READ",
            "VERIFY_MISMATCH",
        }
        self.assertTrue(required.issubset(codes))

    def test_failure_cases_auto_allowed_false(self):
        out = build_runner_failure_injection_hardware_test_plan()
        for item in out["failure_cases"]:
            self.assertFalse(bool(item.get("auto_allowed")))

    def test_required_evidence_contains_bytes_verify_mismatchoffset_audit(self):
        out = build_runner_failure_injection_hardware_test_plan()
        ev = list(out["required_evidence"])
        self.assertIn("bytes_written", ev)
        self.assertIn("verify_result", ev)
        self.assertIn("mismatch_offset_if_present", ev)
        self.assertIn("audit_jsonl", ev)

    def test_risk_controls_contain_no_retry_and_individual_runs(self):
        out = build_runner_failure_injection_hardware_test_plan()
        controls = list(out["risk_controls"])
        self.assertIn("no_retry_after_failure", controls)
        self.assertIn("run_failure_cases_individually", controls)

    def test_stop_conditions_contain_audit_missing_lock_operator_unsure(self):
        out = build_runner_failure_injection_hardware_test_plan()
        stops = list(out["stop_conditions"])
        self.assertIn("audit_missing", stops)
        self.assertIn("lock_not_released", stops)
        self.assertIn("operator_unsure", stops)

    def test_rollback_steps_auto_allowed_false(self):
        out = build_runner_failure_injection_hardware_test_plan()
        for step in out["rollback_steps"]:
            self.assertFalse(bool(step.get("auto_allowed")))

    def test_no_execute_apply_install_write_route_present(self):
        try:
            from fastapi import FastAPI
        except ImportError:
            self.skipTest("fastapi nicht installiert")
        import deploy.routes as routes_mod

        app = FastAPI()
        app.include_router(routes_mod.router)
        paths = {getattr(r, "path", "") for r in app.routes}
        self.assertIn("/api/deploy/runner/failure-injection-hardware/test-plan", paths)
        self.assertNotIn("/api/deploy/runner/failure-injection-hardware/execute", paths)
        self.assertNotIn("/api/deploy/runner/failure-injection-hardware/apply", paths)
        self.assertNotIn("/api/deploy/runner/failure-injection-hardware/install", paths)
        self.assertNotIn("/api/deploy/runner/failure-injection-hardware/write", paths)

    def test_no_forbidden_systemcalls(self):
        src = (_BACKEND / "deploy" / "runner_failure_injection_hardware_test_plan.py").read_text(encoding="utf-8").lower()
        forbidden_patterns = [
            r"\bsudo\b",
            r"\bvisudo\b",
            r"subprocess\.",
            r"os\.system\(",
            r"chmod\(",
            r"chown\(",
            r"mkdir\(",
            r"\bsystemctl\b",
            r"\bdd\b",
            r"\bmkfs\b",
            r"mount\(",
        ]
        for pat in forbidden_patterns:
            self.assertIsNone(re.search(pat, src), msg=pat)

