"""PI-OPT-DEPLOY-TAURI-001: runtime-opt profile, plan, and RUNTIME_API gate."""

from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock

from core.deploy_build_profiles import (
    build_deploy_plan,
    normalize_deploy_profile,
    tauri_required_for_profile,
)
from core.dev_dashboard_cockpit import build_runtime_gate


REPO = Path(__file__).resolve().parents[2]


class DeployProfileTests(unittest.TestCase):
    def test_normalize_unknown_blocked(self) -> None:
        with self.assertRaises(ValueError):
            normalize_deploy_profile("build-all")

    def test_runtime_opt_skips_tauri(self) -> None:
        plan = build_deploy_plan(repo_root=REPO, profile="runtime-opt")
        self.assertEqual(plan["profile"], "runtime-opt")
        self.assertFalse(plan["components"]["tauri"]["required"])
        self.assertEqual(plan["components"]["tauri"]["action"], "skip")
        self.assertTrue(plan["components"]["web_frontend"]["required"])
        self.assertTrue(plan["components"]["backend"]["required"])
        self.assertFalse(plan["components"]["rescue_payload"]["required"])

    def test_with_tauri_on_runtime_opt(self) -> None:
        self.assertTrue(tauri_required_for_profile("runtime-opt", with_tauri=True))
        plan = build_deploy_plan(repo_root=REPO, profile="runtime-opt", with_tauri=True)
        self.assertTrue(plan["components"]["tauri"]["required"])

    def test_desktop_release_requires_tauri(self) -> None:
        plan = build_deploy_plan(repo_root=REPO, profile="desktop-release")
        self.assertTrue(plan["components"]["tauri"]["required"])

    def test_plan_contains_commit_and_versions(self) -> None:
        plan = build_deploy_plan(repo_root=REPO, profile="runtime-opt")
        self.assertTrue(plan.get("source_commit"))
        self.assertTrue(plan.get("application_version"))
        self.assertIn("rescue_payload_version", plan)


class RuntimeApiGateTests(unittest.TestCase):
    def test_gray_with_manifest_commit_not_outdated(self) -> None:
        gate = build_runtime_gate(
            consistency={"backend_workspace_match": None, "status": "green", "warnings": []},
            deploy_drift={
                "status": "gray",
                "manifest_match": True,
                "suggested_actions": ["none"],
                "manifest_git_commit": "abc123",
            },
            runtime={
                "backend_project_version": "1.9.20.1",
                "backend_runtime_path": "/opt/setuphelfer/backend",
                "deploy_source_commit": "abc123",
            },
            workspace={
                "workspace_version": "1.9.20.1",
                "workspace_context_unavailable": True,
                "deploy_source_commit": "abc123",
            },
            install_profile="release",
            app_edition="release",
        )
        self.assertTrue(gate["passed"])
        self.assertNotIn("blocked_runtime_outdated", gate["blockers"])
        self.assertNotIn("deploy_drift_unknown", gate["blockers"])

    def test_version_mismatch_still_blocks(self) -> None:
        gate = build_runtime_gate(
            consistency={"backend_workspace_match": False, "status": "yellow", "warnings": ["backend_runtime_outdated"]},
            deploy_drift={"status": "green", "manifest_match": True, "suggested_actions": ["none"]},
            runtime={
                "backend_project_version": "1.9.20.0",
                "backend_runtime_path": "/opt/setuphelfer/backend",
            },
            workspace={"workspace_version": "1.9.20.1", "workspace_context_unavailable": False},
            install_profile="release",
            app_edition="release",
        )
        self.assertFalse(gate["passed"])
        self.assertIn("blocked_runtime_outdated", gate["blockers"])


class VersionDomainTests(unittest.TestCase):
    def test_app_and_payload_may_differ(self) -> None:
        plan = build_deploy_plan(repo_root=REPO, profile="runtime-opt")
        app = plan["application_version"]
        payload = plan["rescue_payload_version"]
        self.assertTrue(app)
        self.assertTrue(payload)
        # Domains are separate fields; inequality is allowed.
        self.assertIn("application_version", plan)
        self.assertIn("rescue_payload_version", plan)


if __name__ == "__main__":
    unittest.main()
