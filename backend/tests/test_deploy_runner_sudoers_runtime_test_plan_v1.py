"""Tests fuer Sudoers Runtime Dry-run Testdesign."""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

_BACKEND = Path(__file__).resolve().parent.parent
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

from deploy.runner_sudoers_runtime_test_plan import build_runner_sudoers_runtime_test_plan


class TestDeployRunnerSudoersRuntimeTestPlanV1(unittest.TestCase):
    def test_gap_code_correct(self):
        out = build_runner_sudoers_runtime_test_plan()
        self.assertEqual("RUNNER_GAP_SUDOERS_RUNTIME_OPEN", out["gap_code"])

    def test_preconditions_present(self):
        out = build_runner_sudoers_runtime_test_plan()
        self.assertTrue(bool(out["preconditions"]))

    def test_test_steps_contain_manual_visudo_step(self):
        out = build_runner_sudoers_runtime_test_plan()
        codes = {str((x or {}).get("code") or "") for x in list(out["test_steps"])}
        self.assertIn("SUDOERS_TEST_STEP_MANUAL_VISUDO_CHECK", codes)

    def test_dry_run_step_present(self):
        out = build_runner_sudoers_runtime_test_plan()
        codes = {str((x or {}).get("code") or "") for x in list(out["test_steps"])}
        self.assertIn("SUDOERS_TEST_STEP_MANUAL_DRYRUN_CALL", codes)

    def test_negative_tests_cover_pythonpath_ld_preload_wildcard(self):
        out = build_runner_sudoers_runtime_test_plan()
        codes = {str((x or {}).get("code") or "") for x in list(out["negative_tests"])}
        self.assertIn("SUDOERS_NEGATIVE_ENV_KEEP_PYTHONPATH", codes)
        self.assertIn("SUDOERS_NEGATIVE_ENV_KEEP_LD_PRELOAD", codes)
        self.assertIn("SUDOERS_NEGATIVE_WILDCARD_JOB_PATH", codes)

    def test_required_evidence_contains_stdout_json_audit_no_device_write(self):
        out = build_runner_sudoers_runtime_test_plan()
        ev = list(out["required_evidence"])
        self.assertIn("dry_run_runner_stdout_json", ev)
        self.assertIn("runner_audit_jsonl", ev)
        self.assertIn("proof_no_device_write", ev)

    def test_risk_controls_contain_no_persistent_sudoers(self):
        out = build_runner_sudoers_runtime_test_plan()
        self.assertIn("no_change_to_production_sudoers", list(out["risk_controls"]))

    def test_stop_conditions_contain_stdout_not_json(self):
        out = build_runner_sudoers_runtime_test_plan()
        self.assertIn("stdout_not_json", list(out["stop_conditions"]))

    def test_rollback_steps_auto_allowed_false(self):
        out = build_runner_sudoers_runtime_test_plan()
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
        self.assertIn("/api/deploy/runner/sudoers/runtime-test-plan", paths)
        self.assertNotIn("/api/deploy/runner/sudoers/execute", paths)
        self.assertNotIn("/api/deploy/runner/sudoers/apply", paths)
        self.assertNotIn("/api/deploy/runner/sudoers/install", paths)

    def test_no_forbidden_systemcalls(self):
        src = (_BACKEND / "deploy" / "runner_sudoers_runtime_test_plan.py").read_text(encoding="utf-8").lower()
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

