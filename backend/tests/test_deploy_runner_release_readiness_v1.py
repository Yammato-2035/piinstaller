"""Tests fuer Runner Release Readiness Matrix."""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

_BACKEND = Path(__file__).resolve().parent.parent
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

from deploy.runner_release_readiness import build_runner_release_readiness_matrix


class TestDeployRunnerReleaseReadinessV1(unittest.TestCase):
    def test_all_required_components_present(self):
        out = build_runner_release_readiness_matrix()
        ids = {str((x or {}).get("component_id") or "") for x in list(out.get("components") or [])}
        required = {
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
        }
        self.assertTrue(required.issubset(ids))

    def test_known_hardware_e2e_gaps_block(self):
        out = build_runner_release_readiness_matrix()
        self.assertEqual(out["readiness_status"], "blocked")
        self.assertIn("RUNNER_GAP_REAL_WRITE_HARDWARE_E2E_OPEN", out["blocking_gaps"])

    def test_no_production_ready_status_possible(self):
        out = build_runner_release_readiness_matrix(blocking_gaps=[], non_blocking_gaps=[])
        self.assertNotEqual(out["readiness_status"], "production_ready")
        self.assertEqual(out["readiness_status"], "ready_for_lab")

    def test_blocking_gaps_force_blocked(self):
        out = build_runner_release_readiness_matrix(blocking_gaps=["RUNNER_GAP_X"], non_blocking_gaps=[])
        self.assertEqual(out["readiness_status"], "blocked")

    def test_non_blocking_gaps_max_review_required(self):
        out = build_runner_release_readiness_matrix(blocking_gaps=[], non_blocking_gaps=["RUNNER_GAP_UI_POLISHING_OPEN"])
        self.assertEqual(out["readiness_status"], "review_required")

    def test_evidence_files_pass_through(self):
        out = build_runner_release_readiness_matrix(
            blocking_gaps=[],
            non_blocking_gaps=[],
            required_evidence=["docs/evidence/DEPLOY_RUNNER_RELEASE_READINESS_MATRIX.md"],
        )
        self.assertIn("docs/evidence/DEPLOY_RUNNER_RELEASE_READINESS_MATRIX.md", out["required_evidence"])

    def test_test_suites_pass_through(self):
        comps = [
            {
                "component_id": "RUNNER_COMPONENT_RUNNER_HANDOFF",
                "status": "tested",
                "risk_level": "medium",
                "release_gate": "review",
                "test_suites": ["backend.tests.test_deploy_runner_handoff_v1"],
            }
        ]
        out = build_runner_release_readiness_matrix(components=comps)
        handoff = next((x for x in out["components"] if x.get("component_id") == "RUNNER_COMPONENT_RUNNER_HANDOFF"), {})
        self.assertIn("backend.tests.test_deploy_runner_handoff_v1", list(handoff.get("test_suites") or []))

    def test_no_release_apply_execute_route_present(self):
        try:
            from fastapi import FastAPI
        except ImportError:
            self.skipTest("fastapi nicht installiert")
        import deploy.routes as routes_mod

        app = FastAPI()
        app.include_router(routes_mod.router)
        paths = {getattr(r, "path", "") for r in app.routes}
        self.assertIn("/api/deploy/runner/release/readiness", paths)
        self.assertNotIn("/api/deploy/runner/release/apply", paths)
        self.assertNotIn("/api/deploy/runner/release/execute", paths)

    def test_no_forbidden_systemcalls(self):
        src = (_BACKEND / "deploy" / "runner_release_readiness.py").read_text(encoding="utf-8").lower()
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

