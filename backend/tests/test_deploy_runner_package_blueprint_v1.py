"""Tests fuer Runner Package Blueprint (read-only)."""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

_BACKEND = Path(__file__).resolve().parent.parent
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

from deploy.runner_package_blueprint import build_runner_package_blueprint


class TestDeployRunnerPackageBlueprintV1(unittest.TestCase):
    def test_blueprint_contains_package_model(self):
        bp = build_runner_package_blueprint()
        self.assertIn("package_type", bp["package_model"])

    def test_file_manifest_contains_runner(self):
        bp = build_runner_package_blueprint()
        files = [str(x.get("path") or "") for x in bp["file_manifest"]]
        self.assertIn("/opt/setuphelfer/backend/tools/deploy_write_runner.py", files)

    def test_directory_manifest_contains_deploy_jobs(self):
        bp = build_runner_package_blueprint()
        dirs = [str(x.get("path") or "") for x in bp["directory_manifest"]]
        self.assertIn("/var/lib/setuphelfer/deploy-jobs/", dirs)

    def test_permission_manifest_blocks_world_writable(self):
        bp = build_runner_package_blueprint()
        codes = [str(x.get("code") or "") for x in bp["permission_manifest"]]
        self.assertIn("RUNNER_FILE_NOT_WORLD_WRITABLE", codes)
        self.assertIn("RUNNER_JOBDIR_NOT_WORLD_WRITABLE", codes)

    def test_sudoers_manifest_auto_install_false(self):
        bp = build_runner_package_blueprint()
        self.assertFalse(bool((bp["sudoers_manifest"] or {}).get("install_automatically")))

    def test_sudoers_manifest_blocks_unsafe_patterns(self):
        bp = build_runner_package_blueprint()
        pats = list((bp["sudoers_manifest"] or {}).get("unsafe_patterns_blocked") or [])
        self.assertIn("ALL=(ALL) ALL", pats)
        self.assertIn("generic_python3_invocation", pats)

    def test_rollback_manifest_auto_allowed_false(self):
        bp = build_runner_package_blueprint()
        for step in bp["rollback_manifest"]:
            self.assertFalse(bool(step.get("auto_allowed")))

    def test_validation_plan_auto_allowed_false(self):
        bp = build_runner_package_blueprint()
        for step in bp["validation_plan"]:
            self.assertFalse(bool(step.get("auto_allowed")))

    def test_no_build_install_apply_execute_route_present(self):
        try:
            from fastapi import FastAPI
        except ImportError:
            self.skipTest("fastapi nicht installiert")
        import deploy.routes as routes_mod

        app = FastAPI()
        app.include_router(routes_mod.router)
        paths = {getattr(r, "path", "") for r in app.routes}
        self.assertIn("/api/deploy/runner/package/blueprint", paths)
        self.assertNotIn("/api/deploy/runner/package/build", paths)
        self.assertNotIn("/api/deploy/runner/package/install", paths)
        self.assertNotIn("/api/deploy/runner/package/apply", paths)
        self.assertNotIn("/api/deploy/runner/package/execute", paths)

    def test_no_forbidden_systemcalls(self):
        src = (_BACKEND / "deploy" / "runner_package_blueprint.py").read_text(encoding="utf-8").lower()
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
            r"\bdd\b",
            r"\bmkfs\b",
            r"mount\(",
            r"umount\(",
        ]
        for pat in forbidden_patterns:
            self.assertIsNone(re.search(pat, src), msg=pat)

