"""Tests fuer Hotplug/Race Testdesign."""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

_BACKEND = Path(__file__).resolve().parent.parent
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

from deploy.runner_hotplug_race_test_plan import build_runner_hotplug_race_test_plan


class TestDeployRunnerHotplugRaceTestPlanV1(unittest.TestCase):
    def test_gap_code_correct(self):
        out = build_runner_hotplug_race_test_plan()
        self.assertEqual("RUNNER_GAP_HOTPLUG_RACE_OPEN", out["gap_code"])

    def test_preconditions_contain_disposable_backup_gate_guard(self):
        out = build_runner_hotplug_race_test_plan()
        codes = {str((x or {}).get("code") or "") for x in list(out["preconditions"])}
        self.assertIn("PRECONDITION_DISPOSABLE_MEDIA_AVAILABLE", codes)
        self.assertIn("PRECONDITION_FULL_BACKUP_AVAILABLE", codes)
        self.assertIn("PRECONDITION_HARDWARE_GATE_TEST_READY", codes)
        self.assertIn("PRECONDITION_REAL_WRITE_GUARD_READY", codes)

    def test_test_steps_contain_trigger_audit_lock_medium_state(self):
        out = build_runner_hotplug_race_test_plan()
        codes = {str((x or {}).get("code") or "") for x in list(out["test_steps"])}
        self.assertIn("HOTPLUG_STEP_DOCUMENT_TRIGGER_POINT_PER_CASE", codes)
        self.assertIn("HOTPLUG_STEP_DOCUMENT_AUDIT_LOCK_STOPCODE_PER_CASE", codes)
        self.assertIn("HOTPLUG_STEP_DOCUMENT_MEDIA_MOUNT_STATE_PER_CASE", codes)

    def test_race_cases_cover_required_hotplug_points(self):
        out = build_runner_hotplug_race_test_plan()
        codes = {str((x or {}).get("code") or "") for x in list(out["race_cases"])}
        self.assertIn("RACE_CASE_HOTPLUG_DURING_PREWRITE_RECHECK", codes)
        self.assertIn("RACE_CASE_HOTPLUG_AFTER_DEVICE_OPEN", codes)
        self.assertIn("RACE_CASE_HOTPLUG_DURING_WRITE_CHUNK", codes)
        self.assertIn("RACE_CASE_HOTPLUG_BEFORE_FSYNC", codes)
        self.assertIn("RACE_CASE_HOTPLUG_DURING_VERIFY", codes)

    def test_race_cases_cover_mount_readonly_parallel(self):
        out = build_runner_hotplug_race_test_plan()
        codes = {str((x or {}).get("code") or "") for x in list(out["race_cases"])}
        self.assertIn("RACE_CASE_UNEXPECTED_MOUNT_BEFORE_WRITE", codes)
        self.assertIn("RACE_CASE_READONLY_FLIP_BEFORE_WRITE", codes)
        self.assertIn("RACE_CASE_PARALLEL_RUNNER_STARTS_DURING_RACE", codes)

    def test_race_cases_auto_allowed_false(self):
        out = build_runner_hotplug_race_test_plan()
        for item in out["race_cases"]:
            self.assertFalse(bool(item.get("auto_allowed")))

    def test_required_evidence_contains_trigger_mount_readonly_abort_audit(self):
        out = build_runner_hotplug_race_test_plan()
        ev = list(out["required_evidence"])
        self.assertIn("trigger_point", ev)
        self.assertIn("mount_state_before_after", ev)
        self.assertIn("readonly_state_before_after", ev)
        self.assertIn("expected_abort_code", ev)
        self.assertIn("actual_abort_code", ev)
        self.assertIn("audit_jsonl", ev)

    def test_risk_controls_contain_no_retry_and_individual_cases(self):
        out = build_runner_hotplug_race_test_plan()
        controls = list(out["risk_controls"])
        self.assertIn("no_retry_after_race_abort", controls)
        self.assertIn("run_race_cases_individually", controls)

    def test_stop_conditions_contain_internal_drive_and_operator_unsure(self):
        out = build_runner_hotplug_race_test_plan()
        stops = list(out["stop_conditions"])
        self.assertIn("internal_drive_becomes_target", stops)
        self.assertIn("operator_unsure", stops)

    def test_rollback_steps_auto_allowed_false(self):
        out = build_runner_hotplug_race_test_plan()
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
        self.assertIn("/api/deploy/runner/hotplug-race/test-plan", paths)
        self.assertNotIn("/api/deploy/runner/hotplug-race/execute", paths)
        self.assertNotIn("/api/deploy/runner/hotplug-race/apply", paths)
        self.assertNotIn("/api/deploy/runner/hotplug-race/install", paths)
        self.assertNotIn("/api/deploy/runner/hotplug-race/write", paths)

    def test_no_forbidden_systemcalls(self):
        src = (_BACKEND / "deploy" / "runner_hotplug_race_test_plan.py").read_text(encoding="utf-8").lower()
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
            r"umount\(",
        ]
        for pat in forbidden_patterns:
            self.assertIsNone(re.search(pat, src), msg=pat)

