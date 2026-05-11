"""Tests fuer Runner Install Consistency Audit."""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

_BACKEND = Path(__file__).resolve().parent.parent
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

from deploy.runner_install_consistency import validate_runner_install_consistency
from deploy.runner_install_plan import build_runner_install_plan
from deploy.runner_install_validator import validate_runner_installation_dryrun
from deploy.runner_package_blueprint import build_runner_package_blueprint


def _base_triplet() -> tuple[dict, dict, dict]:
    plan = build_runner_install_plan()
    blueprint = build_runner_package_blueprint()
    validation = validate_runner_installation_dryrun(
        install_plan=plan,
        sudoers_snippet_text="Defaults env_reset\nsetuphelfer ALL=(root) NOPASSWD: /usr/bin/python3 /opt/setuphelfer/backend/tools/deploy_write_runner.py --job /var/lib/setuphelfer/deploy-jobs/runner-job-001.json --dry-run",
        environment={"PATH": "/usr/bin:/bin"},
    )
    return plan, validation, blueprint


class TestDeployRunnerInstallConsistencyV1(unittest.TestCase):
    def test_consistent_plans_ok(self):
        plan, validation, blueprint = _base_triplet()
        out = validate_runner_install_consistency(install_plan=plan, install_validation=validation, package_blueprint=blueprint)
        self.assertEqual(out["consistency_status"], "ok")

    def test_runner_path_mismatch_blocked_or_review(self):
        plan, validation, blueprint = _base_triplet()
        blueprint["package_model"]["target_paths"][0] = "/opt/setuphelfer/backend/tools/other_runner.py"
        validation["runner_binary_check"]["target_path"] = "/opt/setuphelfer/backend/tools/other_runner.py"
        out = validate_runner_install_consistency(install_plan=plan, install_validation=validation, package_blueprint=blueprint)
        self.assertIn(out["consistency_status"], ["blocked", "review_required"])

    def test_jobdir_mismatch_blocked_or_review(self):
        plan, validation, blueprint = _base_triplet()
        blueprint["package_model"]["target_paths"][1] = "/var/lib/setuphelfer/other-jobs/"
        validation["job_directory_check"]["target_path"] = "/var/lib/setuphelfer/other-jobs/"
        out = validate_runner_install_consistency(install_plan=plan, install_validation=validation, package_blueprint=blueprint)
        self.assertIn(out["consistency_status"], ["blocked", "review_required"])

    def test_sudoers_path_mismatch_blocked_or_review(self):
        plan, validation, blueprint = _base_triplet()
        blueprint["sudoers_manifest"]["path"] = "/etc/sudoers.d/other-runner"
        out = validate_runner_install_consistency(install_plan=plan, install_validation=validation, package_blueprint=blueprint)
        self.assertIn(out["consistency_status"], ["blocked", "review_required"])

    def test_sudoers_without_env_reset_blocked(self):
        plan, validation, blueprint = _base_triplet()
        validation["sudoers_snippet_check"]["contains_env_reset"] = False
        out = validate_runner_install_consistency(install_plan=plan, install_validation=validation, package_blueprint=blueprint)
        self.assertEqual(out["consistency_status"], "blocked")

    def test_env_keep_pythonpath_conflict_blocked(self):
        plan, validation, blueprint = _base_triplet()
        validation["sudoers_snippet_check"]["errors"] = ["snippet_uses_env_keep"]
        out = validate_runner_install_consistency(install_plan=plan, install_validation=validation, package_blueprint=blueprint)
        self.assertEqual(out["consistency_status"], "blocked")

    def test_missing_rollback_code_blocked_or_review(self):
        plan, validation, blueprint = _base_triplet()
        blueprint["rollback_manifest"] = [x for x in blueprint["rollback_manifest"] if x.get("code") != "RUNNER_ROLLBACK_REMOVE_JOBDIR"]
        out = validate_runner_install_consistency(install_plan=plan, install_validation=validation, package_blueprint=blueprint)
        self.assertIn(out["consistency_status"], ["blocked", "review_required"])

    def test_rollback_auto_allowed_true_blocked(self):
        plan, validation, blueprint = _base_triplet()
        blueprint["rollback_manifest"][0]["auto_allowed"] = True
        out = validate_runner_install_consistency(install_plan=plan, install_validation=validation, package_blueprint=blueprint)
        self.assertEqual(out["consistency_status"], "blocked")

    def test_missing_validation_step_review_or_blocked(self):
        plan, validation, blueprint = _base_triplet()
        blueprint["validation_plan"] = [x for x in blueprint["validation_plan"] if x.get("code") != "RUNNER_VALIDATE_ROOTLESS_E2E_REPEAT"]
        out = validate_runner_install_consistency(install_plan=plan, install_validation=validation, package_blueprint=blueprint)
        self.assertIn(out["consistency_status"], ["review_required", "blocked"])

    def test_validation_auto_allowed_true_blocked(self):
        plan, validation, blueprint = _base_triplet()
        blueprint["validation_plan"][0]["auto_allowed"] = True
        out = validate_runner_install_consistency(install_plan=plan, install_validation=validation, package_blueprint=blueprint)
        self.assertEqual(out["consistency_status"], "blocked")

    def test_no_install_apply_execute_route_present(self):
        try:
            from fastapi import FastAPI
        except ImportError:
            self.skipTest("fastapi nicht installiert")
        import deploy.routes as routes_mod

        app = FastAPI()
        app.include_router(routes_mod.router)
        paths = {getattr(r, "path", "") for r in app.routes}
        self.assertIn("/api/deploy/runner/install/consistency", paths)
        self.assertNotIn("/api/deploy/runner/install/apply", paths)
        self.assertNotIn("/api/deploy/runner/install/execute", paths)

    def test_no_forbidden_systemcalls(self):
        src = (_BACKEND / "deploy" / "runner_install_consistency.py").read_text(encoding="utf-8").lower()
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

