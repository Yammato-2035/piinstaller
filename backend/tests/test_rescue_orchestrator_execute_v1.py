"""Rescue Orchestrator Phase 2: Execute nur aus gültiger Preview-Session."""

from __future__ import annotations

import importlib.util
import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

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


orch = _load("rescue/orchestrator.py", "setuphelfer_rescue_orch_exec_test")


class _Resp:
    def __init__(self, data: dict):
        self._data = data

    def model_dump(self):
        return self._data


class TestRescueOrchestratorExecuteV1(unittest.TestCase):
    def setUp(self):
        self.old_collect = orch.collect_inspect_result
        self.old_eval = orch.evaluate_write_target
        self.old_verify = orch.verify_basic
        self.old_restore = orch.restore_files
        self.old_assert_backup = orch.assert_backup_readable_path
        self.old_assert_target = orch.assert_restore_live_target_directory
        self.old_validate = orch.validate_restored_target
        self.old_boot_capability = orch.check_boot_capability
        self.old_boot_plan = orch.generate_boot_repair_plan
        self.old_report = orch.build_rescue_report
        self.old_pf = dict(orch._PREFLIGHT_PLAN_STORE)
        self.old_preview = dict(orch._PREVIEW_SESSION_STORE)

        orch._PREFLIGHT_PLAN_STORE.clear()
        orch._PREVIEW_SESSION_STORE.clear()

        orch.collect_inspect_result = lambda: _Resp({"storage": {}, "filesystems": {}})
        orch.evaluate_write_target = lambda *_a, **_k: {
            "allowed": True,
            "reason_code": "SAFETY_BACKUP_TARGET_OK",
            "risk_level": "low",
        }
        orch.verify_basic = lambda *_a, **_k: (True, "backup.verify_ok", None)
        orch.restore_files = lambda *_a, **_k: (True, "restore.ok", None)
        orch.assert_backup_readable_path = lambda p: Path(p)
        orch.assert_restore_live_target_directory = lambda p: Path("/tmp")
        orch.validate_restored_target = lambda *_a, **_k: {
            "status": "valid",
            "checks": [],
            "warnings": [],
            "errors": [],
            "boot": {},
            "setuphelfer": {},
        }
        orch.check_boot_capability = lambda *_a, **_k: {
            "status": "boot_warning",
            "checks": [],
            "boot_type_hints": ["BOOT_GRUB_HINT_FOUND"],
            "risks": [],
            "recommendations": ["BOOT_MANUAL_REVIEW_RECOMMENDED"],
            "warnings": ["BOOT_FSTAB_UUID_REFERENCES_MISSING"],
            "errors": [],
        }
        orch.generate_boot_repair_plan = lambda *_a, **_k: {
            "plan_status": "review_required",
            "issues": ["missing_fstab"],
            "proposed_actions": [
                {
                    "code": "REPAIR_REGENERATE_FSTAB",
                    "applicable": True,
                    "risk_level": "medium",
                    "requires_confirmation": True,
                    "auto_allowed": False,
                }
            ],
            "risks": ["BOOT_REPAIR_RISK_DATA_LOSS"],
            "requires_manual_review": True,
        }
        orch.build_rescue_report = lambda **_k: {
            "report_status": "warning",
            "summary": {},
            "sections": [],
            "risks": [],
            "recommendations": [],
            "blocked_actions": [],
            "next_steps": [],
            "warnings": [],
            "errors": [],
        }

    def tearDown(self):
        orch.collect_inspect_result = self.old_collect
        orch.evaluate_write_target = self.old_eval
        orch.verify_basic = self.old_verify
        orch.restore_files = self.old_restore
        orch.assert_backup_readable_path = self.old_assert_backup
        orch.assert_restore_live_target_directory = self.old_assert_target
        orch.validate_restored_target = self.old_validate
        orch.check_boot_capability = self.old_boot_capability
        orch.generate_boot_repair_plan = self.old_boot_plan
        orch.build_rescue_report = self.old_report

        orch._PREFLIGHT_PLAN_STORE.clear()
        orch._PREFLIGHT_PLAN_STORE.update(self.old_pf)
        orch._PREVIEW_SESSION_STORE.clear()
        orch._PREVIEW_SESSION_STORE.update(self.old_preview)

    def _seed_session(self, **overrides):
        base = {
            "preview_id": "pv1",
            "confirmation_token": "tok-valid-123456",
            "backup_path": "/tmp/b.tar.gz",
            "target_device": "/dev/sdz",
            "target_path": "/mnt/setuphelfer-restore-live/target",
            "preflight_plan_id": "pf1",
            "safety_fingerprint": "/dev/sdz|True|SAFETY_BACKUP_TARGET_OK|low",
            "safety_reason": "SAFETY_BACKUP_TARGET_OK",
            "verify_result": {"ok": True, "key": "backup.verify_ok"},
            "preview_result": {"status": "ok"},
            "created_at": datetime.now(timezone.utc).isoformat(),
            "expires_at": (datetime.now(timezone.utc) + timedelta(minutes=15)).isoformat(),
        }
        base.update(overrides)
        orch._PREVIEW_SESSION_STORE[base["preview_id"]] = base
        orch._PREFLIGHT_PLAN_STORE["pf1"] = {"plan_id": "pf1"}

    def _req(self, **ov):
        req = {
            "preview_id": "pv1",
            "confirmation_token": "tok-valid-123456",
            "backup_path": "/tmp/b.tar.gz",
            "target_device": "/dev/sdz",
            "target_path": "/mnt/setuphelfer-restore-live/target",
            "encryption_key_hex": "",
        }
        req.update(ov)
        return req

    def test_execute_without_preview_session(self):
        r = orch.execute_rescue_restore(self._req())
        self.assertEqual(r.get("code"), "RESCUE_PREVIEW_SESSION_NOT_FOUND")

    def test_execute_invalid_token(self):
        self._seed_session()
        r = orch.execute_rescue_restore(self._req(confirmation_token="wrong-token"))
        self.assertEqual(r.get("code"), "RESCUE_PREVIEW_TOKEN_INVALID")

    def test_execute_expired_session(self):
        self._seed_session(expires_at=(datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat())
        r = orch.execute_rescue_restore(self._req())
        self.assertEqual(r.get("code"), "RESCUE_PREVIEW_SESSION_EXPIRED")

    def test_execute_mismatch_backup_or_target(self):
        self._seed_session()
        r = orch.execute_rescue_restore(self._req(backup_path="/tmp/other.tar.gz"))
        self.assertEqual(r.get("code"), "RESCUE_PREVIEW_MISMATCH")

    def test_execute_safety_now_blocked(self):
        self._seed_session()
        orch.evaluate_write_target = lambda *_a, **_k: {
            "allowed": False,
            "reason_code": "SAFETY_SYSTEM_DISK",
            "risk_level": "high",
        }
        r = orch.execute_rescue_restore(self._req())
        self.assertIn(r.get("code"), {"RESCUE_TARGET_BLOCKED", "RESCUE_SAFETY_CHANGED"})

    def test_execute_verify_failed(self):
        self._seed_session()
        orch.verify_basic = lambda *_a, **_k: (False, "backup.verify_failed", None)
        r = orch.execute_rescue_restore(self._req())
        self.assertEqual(r.get("code"), "RESCUE_BACKUP_VERIFY_FAILED")

    def test_execute_restore_engine_failed(self):
        self._seed_session()
        orch.restore_files = lambda *_a, **_k: (False, "restore.failed", "detail")
        r = orch.execute_rescue_restore(self._req())
        self.assertEqual(r.get("code"), "RESCUE_RESTORE_ENGINE_FAILED")

    def test_execute_success_with_mocked_restore_engine(self):
        self._seed_session()
        r = orch.execute_rescue_restore(self._req())
        self.assertEqual(r.get("code"), "RESCUE_EXECUTE_COMPLETED")
        self.assertIn("boot_capability", r)
        self.assertEqual((r.get("boot_capability") or {}).get("status"), "boot_warning")
        self.assertIn("boot_repair_plan", r)
        self.assertEqual((r.get("boot_repair_plan") or {}).get("plan_status"), "review_required")
        self.assertIn("rescue_report", r)
        self.assertEqual((r.get("rescue_report") or {}).get("report_status"), "warning")

    def test_no_restore_without_valid_token(self):
        calls = {"restore": 0}

        def fake_restore(*_a, **_k):
            calls["restore"] += 1
            return (True, "restore.ok", None)

        orch.restore_files = fake_restore
        self._seed_session()
        r = orch.execute_rescue_restore(self._req(confirmation_token="bad"))
        self.assertEqual(r.get("code"), "RESCUE_PREVIEW_TOKEN_INVALID")
        self.assertEqual(calls["restore"], 0)

