"""Rescue report aggregation v1."""

from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

_BACKEND = Path(__file__).resolve().parent.parent
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))


def _load(rel: str, mod_name: str):
    p = _BACKEND / rel
    spec = importlib.util.spec_from_file_location(mod_name, p)
    if not spec or not spec.loader:
        raise ImportError(rel)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


report_mod = _load("rescue/report.py", "setuphelfer_rescue_report_test")
routes_mod = _load("rescue/routes.py", "setuphelfer_rescue_routes_report_test")
orch = _load("rescue/orchestrator.py", "setuphelfer_rescue_orch_report_test")

build_rescue_report = report_mod.build_rescue_report


class TestRescueReportV1(unittest.TestCase):
    def test_empty_input_unknown(self):
        r = build_rescue_report()
        self.assertEqual(r.get("report_status"), "unknown")

    def test_safety_blocked_warns_and_blocks_action(self):
        r = build_rescue_report(safety_summary={"targets": [{"write_allowed": False}]})
        self.assertIn(r.get("report_status"), {"warning", "failed"})
        self.assertIn("ACTION_BLOCKED_WRITE_TO_SYSTEM_DISK", r.get("blocked_actions", []))

    def test_execute_completed_with_boot_warning_is_warning(self):
        r = build_rescue_report(
            preview_result={"code": "RESCUE_PREVIEW_CREATED"},
            execute_result={"code": "RESCUE_EXECUTE_COMPLETED"},
            boot_capability={"status": "boot_warning", "warnings": ["BOOT_KERNEL_MISSING"]},
        )
        self.assertEqual(r.get("report_status"), "warning")

    def test_post_restore_failed_means_failed(self):
        r = build_rescue_report(post_restore={"status": "failed", "errors": ["POST_RESTORE_TARGET_MISSING"]})
        self.assertEqual(r.get("report_status"), "failed")

    def test_boot_plan_manual_review_adds_next_step(self):
        r = build_rescue_report(boot_repair_plan={"plan_status": "review_required", "requires_manual_review": True})
        self.assertIn("NEXT_MANUAL_REVIEW_REQUIRED", r.get("next_steps", []))

    def test_setuphelfer_missing_recommendation(self):
        r = build_rescue_report(post_restore={"status": "warning", "warnings": ["POST_RESTORE_SETUPHELPER_PATH_MISSING"]})
        self.assertIn("NEXT_INSTALL_OR_UPDATE_SETUPHELPER", r.get("next_steps", []))

    def test_api_contract_rescue_report(self):
        app = FastAPI()
        app.include_router(routes_mod.router)
        c = TestClient(app)
        resp = c.post("/api/rescue/report", json={"execute_result": {"code": "RESCUE_EXECUTE_COMPLETED"}})
        self.assertEqual(resp.status_code, 200)
        payload = resp.json()
        self.assertIn(payload.get("code"), {"RESCUE_REPORT_OK", "RESCUE_REPORT_WARNING", "RESCUE_REPORT_FAILED", "RESCUE_REPORT_UNKNOWN"})
        self.assertIsInstance(payload.get("report"), dict)

    def test_execute_integration_has_rescue_report(self):
        old_collect = orch.collect_inspect_result
        old_eval = orch.evaluate_write_target
        old_verify = orch.verify_basic
        old_restore = orch.restore_files
        old_assert_backup = orch.assert_backup_readable_path
        old_assert_target = orch.assert_restore_live_target_directory
        old_validate = orch.validate_restored_target
        old_boot = orch.check_boot_capability
        old_plan = orch.generate_boot_repair_plan
        old_report = orch.build_rescue_report
        old_pf = dict(orch._PREFLIGHT_PLAN_STORE)
        old_preview = dict(orch._PREVIEW_SESSION_STORE)

        try:
            class _Resp:
                def model_dump(self):
                    return {"classification": {"system_type": "LINUX"}}

            orch.collect_inspect_result = lambda: _Resp()
            orch.evaluate_write_target = lambda *_a, **_k: {"allowed": True, "reason_code": "SAFETY_BACKUP_TARGET_OK", "risk_level": "low"}
            orch.verify_basic = lambda *_a, **_k: (True, "backup.verify_ok", None)
            orch.restore_files = lambda *_a, **_k: (True, "restore.ok", None)
            orch.assert_backup_readable_path = lambda p: Path(p)
            orch.assert_restore_live_target_directory = lambda p: Path(p)
            orch.validate_restored_target = lambda *_a, **_k: {"status": "valid", "warnings": [], "errors": []}
            orch.check_boot_capability = lambda *_a, **_k: {"status": "boot_warning", "warnings": []}
            orch.generate_boot_repair_plan = lambda *_a, **_k: {"plan_status": "review_required", "issues": [], "proposed_actions": [], "risks": [], "requires_manual_review": True}
            orch.build_rescue_report = lambda **_k: {"report_status": "warning", "summary": {}, "sections": [], "risks": [], "recommendations": [], "blocked_actions": [], "next_steps": [], "warnings": [], "errors": []}

            orch._PREFLIGHT_PLAN_STORE.clear()
            orch._PREFLIGHT_PLAN_STORE["pf1"] = {"plan_id": "pf1"}
            orch._PREVIEW_SESSION_STORE.clear()
            orch._PREVIEW_SESSION_STORE["pv1"] = {
                "preview_id": "pv1",
                "confirmation_token": "tok-valid-123",
                "backup_path": "/tmp/b.tar.gz",
                "target_device": "/dev/sdz",
                "target_path": "/tmp",
                "preflight_plan_id": "pf1",
                "safety_fingerprint": "/dev/sdz|True|SAFETY_BACKUP_TARGET_OK|low",
                "safety_reason": "SAFETY_BACKUP_TARGET_OK",
                "verify_result": {"ok": True},
                "preview_result": {"status": "ok"},
                "created_at": "2026-01-01T00:00:00+00:00",
                "expires_at": "2099-01-01T00:00:00+00:00",
            }
            r = orch.execute_rescue_restore({
                "preview_id": "pv1",
                "confirmation_token": "tok-valid-123",
                "backup_path": "/tmp/b.tar.gz",
                "target_device": "/dev/sdz",
                "target_path": "/tmp",
                "encryption_key_hex": "",
            })
            self.assertEqual(r.get("code"), "RESCUE_EXECUTE_COMPLETED")
            self.assertIn("rescue_report", r)
        finally:
            orch.collect_inspect_result = old_collect
            orch.evaluate_write_target = old_eval
            orch.verify_basic = old_verify
            orch.restore_files = old_restore
            orch.assert_backup_readable_path = old_assert_backup
            orch.assert_restore_live_target_directory = old_assert_target
            orch.validate_restored_target = old_validate
            orch.check_boot_capability = old_boot
            orch.generate_boot_repair_plan = old_plan
            orch.build_rescue_report = old_report
            orch._PREFLIGHT_PLAN_STORE.clear()
            orch._PREFLIGHT_PLAN_STORE.update(old_pf)
            orch._PREVIEW_SESSION_STORE.clear()
            orch._PREVIEW_SESSION_STORE.update(old_preview)

