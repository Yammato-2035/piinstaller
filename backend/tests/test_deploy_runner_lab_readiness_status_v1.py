"""Tests fuer Lab Readiness Status Matrix Update."""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

_BACKEND = Path(__file__).resolve().parent.parent
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

from deploy.runner_lab_readiness_status import build_runner_lab_readiness_status


class TestDeployRunnerLabReadinessStatusV1(unittest.TestCase):
    def test_all_seven_gaps_present(self):
        out = build_runner_lab_readiness_status()
        gaps = {str((x or {}).get("gap_code") or "") for x in list(out["gap_statuses"])}
        self.assertEqual(7, len(gaps))

    def test_design_status_ready_when_evidence_present(self):
        out = build_runner_lab_readiness_status()
        for item in out["gap_statuses"]:
            self.assertEqual("ready", item["design_status"])

    def test_runtime_status_not_started_without_runtime_evidence(self):
        out = build_runner_lab_readiness_status()
        for item in out["gap_statuses"]:
            self.assertEqual("not_started", item["runtime_status"])

    def test_status_test_design_ready_when_design_complete_runtime_open(self):
        out = build_runner_lab_readiness_status()
        self.assertEqual("test_design_ready", out["lab_readiness_status"])

    def test_remaining_runtime_gaps_contains_all_seven(self):
        out = build_runner_lab_readiness_status()
        self.assertEqual(7, len(list(out["remaining_runtime_gaps"])))

    def test_required_runtime_executions_auto_allowed_false(self):
        out = build_runner_lab_readiness_status()
        for item in out["required_runtime_executions"]:
            self.assertFalse(bool(item.get("auto_allowed")))

    def test_required_runtime_executions_manual_operator_required_true(self):
        out = build_runner_lab_readiness_status()
        for item in out["required_runtime_executions"]:
            self.assertTrue(bool(item.get("manual_operator_required")))

    def test_no_lab_or_production_ready_output(self):
        out = build_runner_lab_readiness_status()
        self.assertNotEqual("lab_ready", out["lab_readiness_status"])
        self.assertNotEqual("production_ready", out["lab_readiness_status"])

    def test_no_execute_apply_install_write_delete_route_present(self):
        try:
            from fastapi import FastAPI
        except ImportError:
            self.skipTest("fastapi nicht installiert")
        import deploy.routes as routes_mod

        app = FastAPI()
        app.include_router(routes_mod.router)
        paths = {getattr(r, "path", "") for r in app.routes}
        self.assertIn("/api/deploy/runner/lab-readiness/status", paths)
        self.assertNotIn("/api/deploy/runner/lab-readiness/execute", paths)
        self.assertNotIn("/api/deploy/runner/lab-readiness/apply", paths)
        self.assertNotIn("/api/deploy/runner/lab-readiness/install", paths)
        self.assertNotIn("/api/deploy/runner/lab-readiness/write", paths)
        self.assertNotIn("/api/deploy/runner/lab-readiness/delete", paths)

    def test_no_forbidden_systemcalls(self):
        src = (_BACKEND / "deploy" / "runner_lab_readiness_status.py").read_text(encoding="utf-8").lower()
        forbidden_patterns = [
            r"\bsudo\b",
            r"\bvisudo\b",
            r"subprocess\.",
            r"os\.system\(",
            r"chmod\(",
            r"chown\(",
            r"mkdir\(",
            r"\brm\b",
            r"\bsystemctl\b",
            r"\bdd\b",
            r"\bmkfs\b",
            r"mount\(",
            r"umount\(",
        ]
        for pat in forbidden_patterns:
            self.assertIsNone(re.search(pat, src), msg=pat)

