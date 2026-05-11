"""Tests fuer Privileged Runner Validation Dry-run Testdesign."""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

_BACKEND = Path(__file__).resolve().parent.parent
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

from deploy.runner_privileged_validation_test_plan import build_runner_privileged_validation_test_plan


class TestDeployRunnerPrivilegedValidationTestPlanV1(unittest.TestCase):
    def test_gap_code_correct(self):
        out = build_runner_privileged_validation_test_plan()
        self.assertEqual("RUNNER_GAP_PRIVILEGED_RUNNER_VALIDATION_OPEN", out["gap_code"])

    def test_preconditions_present(self):
        out = build_runner_privileged_validation_test_plan()
        self.assertTrue(bool(out["preconditions"]))

    def test_test_steps_contain_privileged_dry_run(self):
        out = build_runner_privileged_validation_test_plan()
        codes = {str((x or {}).get("code") or "") for x in list(out["test_steps"])}
        self.assertIn("PRIV_VALID_STEP_MANUAL_PRIVILEGED_DRYRUN_START", codes)

    def test_effective_uid_gid_evidence_present(self):
        out = build_runner_privileged_validation_test_plan()
        self.assertIn("effective_uid_gid_in_runner_context", list(out["required_evidence"]))

    def test_negative_tests_cover_key_cases(self):
        out = build_runner_privileged_validation_test_plan()
        codes = {str((x or {}).get("code") or "") for x in list(out["negative_tests"])}
        self.assertIn("PRIV_VALID_NEGATIVE_NO_DRY_RUN_FLAG", codes)
        self.assertIn("PRIV_VALID_NEGATIVE_JOB_HASH_MISMATCH", codes)
        self.assertIn("PRIV_VALID_NEGATIVE_SYMLINK_JOBFILE", codes)
        self.assertIn("PRIV_VALID_NEGATIVE_ENV_LD_PRELOAD", codes)
        self.assertIn("PRIV_VALID_NEGATIVE_ENV_PYTHONPATH", codes)

    def test_risk_controls_contain_local_control_and_no_parallel(self):
        out = build_runner_privileged_validation_test_plan()
        controls = list(out["risk_controls"])
        self.assertIn("no_test_without_local_control", controls)
        self.assertIn("no_parallel_runners", controls)

    def test_stop_conditions_contain_device_open_stdout_json_operator_unsure(self):
        out = build_runner_privileged_validation_test_plan()
        stops = list(out["stop_conditions"])
        self.assertIn("device_open_detected", stops)
        self.assertIn("stdout_not_json", stops)
        self.assertIn("operator_unsure", stops)

    def test_rollback_steps_auto_allowed_false(self):
        out = build_runner_privileged_validation_test_plan()
        for step in out["rollback_steps"]:
            self.assertFalse(bool(step.get("auto_allowed")))

    def test_no_execute_apply_install_route_present(self):
        try:
            from fastapi import FastAPI
        except ImportError:
            self.skipTest("fastapi nicht installiert")
        import deploy.routes as routes_mod

        app = FastAPI()
        app.include_router(routes_mod.router)
        paths = {getattr(r, "path", "") for r in app.routes}
        self.assertIn("/api/deploy/runner/privileged-validation/test-plan", paths)
        self.assertNotIn("/api/deploy/runner/privileged-validation/execute", paths)
        self.assertNotIn("/api/deploy/runner/privileged-validation/apply", paths)
        self.assertNotIn("/api/deploy/runner/privileged-validation/install", paths)

    def test_no_forbidden_systemcalls(self):
        src = (_BACKEND / "deploy" / "runner_privileged_validation_test_plan.py").read_text(encoding="utf-8").lower()
        forbidden_patterns = [
            r"\bsudo\b",
            r"\bvisudo\b",
            r"subprocess\.",
            r"os\.system\(",
            r"chmod\(",
            r"chown\(",
            r"mkdir\(",
            r"\bsystemctl\b",
            r"shell\s*=\s*true",
        ]
        for pat in forbidden_patterns:
            self.assertIsNone(re.search(pat, src), msg=pat)

