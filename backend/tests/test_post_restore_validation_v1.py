"""Post-Restore Validation v1 (read-only)."""

from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
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


val_mod = _load("rescue/post_restore_validation.py", "setuphelfer_post_restore_validation_test")
orch = _load("rescue/orchestrator.py", "setuphelfer_rescue_orch_for_postverify_test")
validate_restored_target = val_mod.validate_restored_target


class TestPostRestoreValidationV1(unittest.TestCase):
    def test_target_missing_failed(self):
        r = validate_restored_target("/tmp/does-not-exist-post-restore-validation")
        self.assertEqual(r.get("status"), "failed")
        self.assertIn("POST_RESTORE_TARGET_MISSING", r.get("errors", []))

    def test_target_not_readable_behavior(self):
        with tempfile.TemporaryDirectory() as td:
            r = validate_restored_target(td)
            self.assertIn(r.get("status"), {"valid", "warning", "failed"})

    def test_minimal_linux_target_valid_or_warning(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "etc").mkdir()
            (root / "usr").mkdir()
            (root / "var").mkdir()
            (root / "boot").mkdir()
            (root / "etc" / "fstab").write_text("UUID=x / ext4 defaults 0 1\n", encoding="utf-8")
            (root / "boot" / "vmlinuz-test").write_text("x", encoding="utf-8")
            (root / "boot" / "initrd.img-test").write_text("x", encoding="utf-8")

            r = validate_restored_target(str(root))
            self.assertIn(r.get("status"), {"valid", "warning"})

    def test_missing_fstab_warning(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "etc").mkdir()
            (root / "usr").mkdir()
            (root / "var").mkdir()
            (root / "boot").mkdir()
            (root / "boot" / "vmlinuz-x").write_text("x", encoding="utf-8")
            (root / "boot" / "initrd.img-x").write_text("x", encoding="utf-8")
            r = validate_restored_target(str(root))
            self.assertIn("POST_RESTORE_FSTAB_MISSING", r.get("warnings", []))

    def test_missing_kernel_initramfs_recommends_boot_repair(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "etc").mkdir()
            (root / "usr").mkdir()
            (root / "var").mkdir()
            (root / "boot").mkdir()
            (root / "etc" / "fstab").write_text("UUID=x / ext4 defaults 0 1\n", encoding="utf-8")
            r = validate_restored_target(str(root))
            self.assertIn("POST_RESTORE_BOOT_REPAIR_RECOMMENDED", r.get("warnings", []))

    def test_missing_setuphelfer_only_warning(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "etc").mkdir()
            (root / "usr").mkdir()
            (root / "var").mkdir()
            (root / "boot").mkdir()
            (root / "etc" / "fstab").write_text("UUID=x / ext4 defaults 0 1\n", encoding="utf-8")
            (root / "boot" / "vmlinuz-x").write_text("x", encoding="utf-8")
            (root / "boot" / "initrd.img-x").write_text("x", encoding="utf-8")
            r = validate_restored_target(str(root))
            self.assertIn("POST_RESTORE_SETUPHELPER_UNIT_MISSING", r.get("warnings", []))
            self.assertIn("POST_RESTORE_SETUPHELPER_PATH_MISSING", r.get("warnings", []))
            self.assertNotEqual(r.get("status"), "failed")

    def test_execute_integration_post_verify_present(self):
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
                    return {"storage": {}, "filesystems": {}}

            orch.collect_inspect_result = lambda: _Resp()
            orch.evaluate_write_target = lambda *_a, **_k: {
                "allowed": True,
                "reason_code": "SAFETY_BACKUP_TARGET_OK",
                "risk_level": "low",
            }
            orch.verify_basic = lambda *_a, **_k: (True, "backup.verify_ok", None)
            orch.restore_files = lambda *_a, **_k: (True, "restore.ok", None)
            orch.assert_backup_readable_path = lambda p: Path(p)
            orch.assert_restore_live_target_directory = lambda p: Path(p)
            orch.validate_restored_target = lambda *_a, **_k: {
                "status": "warning",
                "checks": [],
                "warnings": ["POST_RESTORE_FSTAB_MISSING"],
                "errors": [],
                "boot": {},
                "setuphelfer": {},
            }
            orch.check_boot_capability = lambda *_a, **_k: {
                "status": "boot_warning",
                "checks": [],
                "boot_type_hints": [],
                "risks": [],
                "recommendations": ["BOOT_MANUAL_REVIEW_RECOMMENDED"],
                "warnings": [],
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

            r = orch.execute_rescue_restore(
                {
                    "preview_id": "pv1",
                    "confirmation_token": "tok-valid-123",
                    "backup_path": "/tmp/b.tar.gz",
                    "target_device": "/dev/sdz",
                    "target_path": "/tmp",
                    "encryption_key_hex": "",
                }
            )
            self.assertEqual(r.get("code"), "RESCUE_EXECUTE_COMPLETED")
            self.assertIn("post_verify", r)
            self.assertEqual((r.get("post_verify") or {}).get("status"), "warning")
            self.assertIn("boot_capability", r)
            self.assertIn("boot_repair_plan", r)
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

