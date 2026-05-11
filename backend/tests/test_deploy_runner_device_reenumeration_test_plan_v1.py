"""Tests fuer Device Reenumeration Testdesign."""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

_BACKEND = Path(__file__).resolve().parent.parent
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

from deploy.runner_device_reenumeration_test_plan import build_runner_device_reenumeration_test_plan


class TestDeployRunnerDeviceReenumerationTestPlanV1(unittest.TestCase):
    def test_gap_code_correct(self):
        out = build_runner_device_reenumeration_test_plan()
        self.assertEqual("RUNNER_GAP_DEVICE_REENUMERATION_OPEN", out["gap_code"])

    def test_preconditions_contain_snapshot_fingerprint_disposable(self):
        out = build_runner_device_reenumeration_test_plan()
        codes = {str((x or {}).get("code") or "") for x in list(out["preconditions"])}
        self.assertIn("PRECONDITION_SNAPSHOT_FINGERPRINT_AVAILABLE", codes)
        self.assertIn("PRECONDITION_DISPOSABLE_MEDIA_AVAILABLE", codes)

    def test_test_steps_contain_realpath_fingerprint_compare(self):
        out = build_runner_device_reenumeration_test_plan()
        codes = {str((x or {}).get("code") or "") for x in list(out["test_steps"])}
        self.assertIn("REENUM_STEP_COMPARE_TARGET_REALPATH_FINGERPRINT_AFTER_EACH_CASE", codes)

    def test_reenumeration_cases_cover_required_set(self):
        out = build_runner_device_reenumeration_test_plan()
        codes = {str((x or {}).get("code") or "") for x in list(out["reenumeration_cases"])}
        self.assertIn("REENUM_CASE_USB_REPLUG_SHORT", codes)
        self.assertIn("REENUM_CASE_SAME_MEDIA_NEW_KERNEL_NAME", codes)
        self.assertIn("REENUM_CASE_OTHER_MEDIA_ON_OLD_PATH", codes)
        self.assertIn("REENUM_CASE_TWO_SIMILAR_USB_MEDIA", codes)
        self.assertIn("REENUM_CASE_PARTITION_VS_DISK_PATH_CONFUSION", codes)

    def test_reenumeration_cases_auto_allowed_false(self):
        out = build_runner_device_reenumeration_test_plan()
        for item in out["reenumeration_cases"]:
            self.assertFalse(bool(item.get("auto_allowed")))

    def test_required_evidence_contains_target_realpath_fingerprint_before_after(self):
        out = build_runner_device_reenumeration_test_plan()
        ev = list(out["required_evidence"])
        self.assertIn("target_device_before", ev)
        self.assertIn("target_device_after", ev)
        self.assertIn("realpath_before", ev)
        self.assertIn("realpath_after", ev)
        self.assertIn("fingerprint_before", ev)
        self.assertIn("fingerprint_after", ev)

    def test_risk_controls_contain_no_retry_after_device_change(self):
        out = build_runner_device_reenumeration_test_plan()
        self.assertIn("no_retry_after_device_change", list(out["risk_controls"]))

    def test_stop_conditions_contain_other_media_old_path_and_operator_unsure(self):
        out = build_runner_device_reenumeration_test_plan()
        stops = list(out["stop_conditions"])
        self.assertIn("other_media_on_old_path", stops)
        self.assertIn("operator_unsure", stops)

    def test_rollback_steps_auto_allowed_false(self):
        out = build_runner_device_reenumeration_test_plan()
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
        self.assertIn("/api/deploy/runner/device-reenumeration/test-plan", paths)
        self.assertNotIn("/api/deploy/runner/device-reenumeration/execute", paths)
        self.assertNotIn("/api/deploy/runner/device-reenumeration/apply", paths)
        self.assertNotIn("/api/deploy/runner/device-reenumeration/install", paths)
        self.assertNotIn("/api/deploy/runner/device-reenumeration/write", paths)

    def test_no_forbidden_systemcalls(self):
        src = (_BACKEND / "deploy" / "runner_device_reenumeration_test_plan.py").read_text(encoding="utf-8").lower()
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
        ]
        for pat in forbidden_patterns:
            self.assertIsNone(re.search(pat, src), msg=pat)

