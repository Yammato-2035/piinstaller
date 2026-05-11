"""Tests für read-only Runner-Installationsplan."""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

_BACKEND = Path(__file__).resolve().parent.parent
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

from deploy.runner_install_plan import build_runner_install_plan


class TestDeployRunnerInstallPlanV1(unittest.TestCase):
    def test_plan_contains_runner_path(self):
        plan = build_runner_install_plan()
        self.assertIn("/opt/setuphelfer/backend/tools/deploy_write_runner.py", str((plan.get("runner_binary") or {}).get("target_path")))

    def test_plan_contains_job_directory(self):
        plan = build_runner_install_plan()
        self.assertIn("/var/lib/setuphelfer/deploy-jobs", str((plan.get("job_directory") or {}).get("target_path")))

    def test_sudoers_example_contains_env_reset(self):
        plan = build_runner_install_plan()
        flags = list((plan.get("sudoers_policy") or {}).get("required_flags") or [])
        self.assertIn("env_reset", flags)

    def test_wildcard_policy_blocked(self):
        plan = build_runner_install_plan(sudoers_contains_wildcard=True)
        self.assertEqual(plan["plan_status"], "blocked")
        self.assertIn("RUNNER_INSTALL_BLOCKED_WILDCARD_SUDOERS", plan["blocked_steps"])

    def test_root_backend_model_blocked(self):
        plan = build_runner_install_plan(backend_runs_as_root=True)
        self.assertEqual(plan["plan_status"], "blocked")
        self.assertIn("RUNNER_INSTALL_BLOCKED_ROOT_BACKEND", plan["blocked_steps"])

    def test_daemon_mode_blocked(self):
        plan = build_runner_install_plan(daemon_mode_requested=True)
        self.assertEqual(plan["plan_status"], "blocked")
        self.assertIn("RUNNER_INSTALL_BLOCKED_DAEMON_MODE", plan["blocked_steps"])

    def test_manual_steps_auto_allowed_false(self):
        plan = build_runner_install_plan()
        for step in plan["required_manual_steps"]:
            self.assertFalse(bool(step.get("auto_allowed")))

    def test_no_install_apply_execute_route_present(self):
        try:
            from fastapi import FastAPI
        except ImportError:
            self.skipTest("fastapi nicht installiert")
        import deploy.routes as routes_mod

        app = FastAPI()
        app.include_router(routes_mod.router)
        paths = {getattr(r, "path", "") for r in app.routes}
        self.assertIn("/api/deploy/runner/install/plan", paths)
        self.assertNotIn("/api/deploy/runner/install/apply", paths)
        self.assertNotIn("/api/deploy/runner/install/execute", paths)

    def test_no_forbidden_systemcalls(self):
        src = (_BACKEND / "deploy" / "runner_install_plan.py").read_text(encoding="utf-8").lower()
        forbidden_patterns = [
            r"chmod\(",
            r"chown\(",
            r"\bsudo\b",
            r"\bvisudo\b",
            r"\bsystemctl\b",
            r"subprocess\.",
            r"os\.system\(",
            r"shell\s*=\s*true",
            r"\bdd\b",
            r"\bmkfs\b",
            r"\bparted\b",
            r"\bfdisk\b",
            r"mount\(",
            r"umount\(",
        ]
        for pat in forbidden_patterns:
            self.assertIsNone(re.search(pat, src), msg=pat)

