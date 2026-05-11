"""Tests fuer Real Write Hardware E2E Testdesign."""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

_BACKEND = Path(__file__).resolve().parent.parent
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

from deploy.runner_real_write_hardware_e2e_test_plan import build_runner_real_write_hardware_e2e_test_plan


class TestDeployRunnerRealWriteHardwareE2ETestPlanV1(unittest.TestCase):
    def test_gap_code_correct(self):
        out = build_runner_real_write_hardware_e2e_test_plan()
        self.assertEqual("RUNNER_GAP_REAL_WRITE_HARDWARE_E2E_OPEN", out["gap_code"])

    def test_preconditions_contain_disposable_media_backup_operator(self):
        out = build_runner_real_write_hardware_e2e_test_plan()
        codes = {str((x or {}).get("code") or "") for x in list(out["preconditions"])}
        self.assertIn("PRECONDITION_DISPOSABLE_MEDIA_AVAILABLE", codes)
        self.assertIn("PRECONDITION_FULL_BACKUP_AVAILABLE", codes)
        self.assertIn("PRECONDITION_OPERATOR_MANUAL_CONFIRMATION", codes)

    def test_test_steps_contain_manual_real_write_step(self):
        out = build_runner_real_write_hardware_e2e_test_plan()
        codes = {str((x or {}).get("code") or "") for x in list(out["test_steps"])}
        self.assertIn("HW_E2E_STEP_MANUAL_PRIVILEGED_REAL_WRITE", codes)

    def test_test_steps_contain_verify_sha256(self):
        out = build_runner_real_write_hardware_e2e_test_plan()
        codes = {str((x or {}).get("code") or "") for x in list(out["test_steps"])}
        self.assertIn("HW_E2E_STEP_DOCUMENT_VERIFY_SHA256", codes)

    def test_negative_tests_cover_required_cases(self):
        out = build_runner_real_write_hardware_e2e_test_plan()
        codes = {str((x or {}).get("code") or "") for x in list(out["negative_tests"])}
        self.assertIn("HW_E2E_NEGATIVE_MEDIA_SUDDENLY_MOUNTED", codes)
        self.assertIn("HW_E2E_NEGATIVE_MEDIA_READONLY", codes)
        self.assertIn("HW_E2E_NEGATIVE_SNAPSHOT_FINGERPRINT_MISMATCH", codes)
        self.assertIn("HW_E2E_NEGATIVE_IMAGE_OVER_512MB", codes)

    def test_required_evidence_contains_bytes_sha_audit_lsblk_findmnt(self):
        out = build_runner_real_write_hardware_e2e_test_plan()
        evidence = list(out["required_evidence"])
        self.assertIn("bytes_written", evidence)
        self.assertIn("expected_sha256", evidence)
        self.assertIn("actual_sha256", evidence)
        self.assertIn("runner_audit_jsonl", evidence)
        self.assertIn("lsblk_before_after", evidence)
        self.assertIn("findmnt_before_after", evidence)

    def test_risk_controls_contain_single_media_no_retry_local_control(self):
        out = build_runner_real_write_hardware_e2e_test_plan()
        controls = list(out["risk_controls"])
        self.assertIn("single_disposable_test_media_only", controls)
        self.assertIn("no_retry_after_verify_mismatch", controls)
        self.assertIn("no_remote_test_without_local_control", controls)

    def test_stop_conditions_contain_systemdisk_and_operator_unsure(self):
        out = build_runner_real_write_hardware_e2e_test_plan()
        stops = list(out["stop_conditions"])
        self.assertIn("system_disk_as_target", stops)
        self.assertIn("operator_unsure", stops)

    def test_rollback_steps_auto_allowed_false(self):
        out = build_runner_real_write_hardware_e2e_test_plan()
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
        self.assertIn("/api/deploy/runner/real-write-hardware-e2e/test-plan", paths)
        self.assertNotIn("/api/deploy/runner/real-write-hardware-e2e/execute", paths)
        self.assertNotIn("/api/deploy/runner/real-write-hardware-e2e/apply", paths)
        self.assertNotIn("/api/deploy/runner/real-write-hardware-e2e/install", paths)
        self.assertNotIn("/api/deploy/runner/real-write-hardware-e2e/write", paths)

    def test_no_forbidden_systemcalls(self):
        src = (_BACKEND / "deploy" / "runner_real_write_hardware_e2e_test_plan.py").read_text(encoding="utf-8").lower()
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
            r"shell\s*=\s*true",
        ]
        for pat in forbidden_patterns:
            self.assertIsNone(re.search(pat, src), msg=pat)

