"""Tests fuer Rollback Runtime Testdesign."""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

_BACKEND = Path(__file__).resolve().parent.parent
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

from deploy.runner_rollback_runtime_test_plan import build_runner_rollback_runtime_test_plan


class TestDeployRunnerRollbackRuntimeTestPlanV1(unittest.TestCase):
    def test_gap_code_correct(self):
        out = build_runner_rollback_runtime_test_plan()
        self.assertEqual("RUNNER_GAP_ROLLBACK_RUNTIME_OPEN", out["gap_code"])

    def test_preconditions_contain_manifest_disposable_backup(self):
        out = build_runner_rollback_runtime_test_plan()
        codes = {str((x or {}).get("code") or "") for x in list(out["preconditions"])}
        self.assertIn("PRECONDITION_ROLLBACK_MANIFEST_PRESENT", codes)
        self.assertIn("PRECONDITION_DISPOSABLE_TEST_MEDIA_AVAILABLE", codes)
        self.assertIn("PRECONDITION_FULL_BACKUP_AVAILABLE", codes)

    def test_test_steps_contain_no_system_path_change_check(self):
        out = build_runner_rollback_runtime_test_plan()
        codes = {str((x or {}).get("code") or "") for x in list(out["test_steps"])}
        self.assertIn("ROLLBACK_STEP_VALIDATE_NO_SYSTEM_PATH_CHANGES_PER_CASE", codes)

    def test_rollback_cases_contain_required_set(self):
        out = build_runner_rollback_runtime_test_plan()
        codes = {str((x or {}).get("code") or "") for x in list(out["rollback_cases"])}
        self.assertIn("ROLLBACK_CASE_STALE_LOCK_CLEANUP", codes)
        self.assertIn("ROLLBACK_CASE_EXPIRED_JOB_CLEANUP", codes)
        self.assertIn("ROLLBACK_CASE_TEMP_JOBFILE_CLEANUP", codes)
        self.assertIn("ROLLBACK_CASE_AUDIT_PRESERVATION_AFTER_ABORT", codes)
        self.assertIn("ROLLBACK_CASE_AFTER_TIMEOUT", codes)
        self.assertIn("ROLLBACK_CASE_AFTER_INVALID_JSON", codes)
        self.assertIn("ROLLBACK_CASE_AFTER_OPERATOR_ABORT", codes)
        self.assertIn("ROLLBACK_CASE_AFTER_FAILURE_INJECTION_ABORT", codes)
        self.assertIn("ROLLBACK_CASE_AFTER_HOTPLUG_RACE_ABORT", codes)

    def test_rollback_cases_auto_allowed_false(self):
        out = build_runner_rollback_runtime_test_plan()
        for item in out["rollback_cases"]:
            self.assertFalse(bool(item.get("auto_allowed")))

    def test_required_evidence_contains_proofs(self):
        out = build_runner_rollback_runtime_test_plan()
        ev = list(out["required_evidence"])
        self.assertIn("proof_no_etc_changes", ev)
        self.assertIn("proof_no_opt_changes", ev)
        self.assertIn("proof_no_var_lib_changes_except_allowed_testjobdir", ev)
        self.assertIn("proof_no_sudoers_changes", ev)
        self.assertIn("proof_no_device_write", ev)
        self.assertIn("proof_no_mount_changes", ev)

    def test_risk_controls_contain_no_symlink_and_no_recursive_without_prefix(self):
        out = build_runner_rollback_runtime_test_plan()
        controls = list(out["risk_controls"])
        self.assertIn("no_symlink_following", controls)
        self.assertIn("no_recursive_delete_without_prefix_check", controls)

    def test_stop_conditions_contain_system_or_root_path(self):
        out = build_runner_rollback_runtime_test_plan()
        self.assertIn("cleanup_path_points_to_system_or_root", list(out["stop_conditions"]))

    def test_cleanup_boundaries_forbid_symlinks_true(self):
        out = build_runner_rollback_runtime_test_plan()
        for item in out["cleanup_boundaries"]:
            self.assertTrue(bool(item.get("forbid_symlinks")))

    def test_no_execute_apply_install_write_delete_route_present(self):
        try:
            from fastapi import FastAPI
        except ImportError:
            self.skipTest("fastapi nicht installiert")
        import deploy.routes as routes_mod

        app = FastAPI()
        app.include_router(routes_mod.router)
        paths = {getattr(r, "path", "") for r in app.routes}
        self.assertIn("/api/deploy/runner/rollback-runtime/test-plan", paths)
        self.assertNotIn("/api/deploy/runner/rollback-runtime/execute", paths)
        self.assertNotIn("/api/deploy/runner/rollback-runtime/apply", paths)
        self.assertNotIn("/api/deploy/runner/rollback-runtime/install", paths)
        self.assertNotIn("/api/deploy/runner/rollback-runtime/write", paths)
        self.assertNotIn("/api/deploy/runner/rollback-runtime/delete", paths)

    def test_no_forbidden_systemcalls(self):
        src = (_BACKEND / "deploy" / "runner_rollback_runtime_test_plan.py").read_text(encoding="utf-8").lower()
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

