"""Boot Capability Check v1 (read-only)."""

from __future__ import annotations

import importlib.util
import sys
import tempfile
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


cap_mod = _load("boot/capability.py", "setuphelfer_boot_capability_test")
routes_mod = _load("boot/routes.py", "setuphelfer_boot_routes_test")
orch = _load("rescue/orchestrator.py", "setuphelfer_rescue_orch_bootcap_test")

check_boot_capability = cap_mod.check_boot_capability


class TestBootCapabilityV1(unittest.TestCase):
    def test_target_missing_failed(self):
        r = check_boot_capability("/tmp/does-not-exist-boot-capability")
        self.assertEqual(r.get("status"), "boot_failed")
        self.assertIn("BOOT_TARGET_MISSING", r.get("errors", []))

    def test_minimal_linux_likely(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "etc").mkdir()
            (root / "boot").mkdir()
            (root / "etc" / "fstab").write_text("UUID=x / ext4 defaults 0 1\n", encoding="utf-8")
            (root / "boot" / "vmlinuz-test").write_text("x", encoding="utf-8")
            (root / "boot" / "initrd.img-test").write_text("x", encoding="utf-8")

            r = check_boot_capability(str(root))
            self.assertEqual(r.get("status"), "boot_likely")

    def test_missing_fstab_warning(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "etc").mkdir()
            (root / "boot").mkdir()
            (root / "boot" / "vmlinuz-test").write_text("x", encoding="utf-8")
            (root / "boot" / "initrd.img-test").write_text("x", encoding="utf-8")
            r = check_boot_capability(str(root))
            self.assertEqual(r.get("status"), "boot_warning")
            self.assertIn("BOOT_FSTAB_MISSING", r.get("warnings", []))

    def test_missing_kernel_warning(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "etc").mkdir()
            (root / "boot").mkdir()
            (root / "etc" / "fstab").write_text("UUID=x / ext4 defaults 0 1\n", encoding="utf-8")
            (root / "boot" / "initrd.img-test").write_text("x", encoding="utf-8")
            r = check_boot_capability(str(root))
            self.assertEqual(r.get("status"), "boot_warning")
            self.assertIn("BOOT_KERNEL_MISSING", r.get("warnings", []))

    def test_windows_hint_not_likely(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "EFI" / "Microsoft" / "Boot").mkdir(parents=True)
            (root / "EFI" / "Microsoft" / "Boot" / "bootmgfw.efi").write_text("x", encoding="utf-8")
            r = check_boot_capability(str(root))
            self.assertIn(r.get("status"), {"boot_warning", "boot_unknown"})
            self.assertNotEqual(r.get("status"), "boot_likely")

    def test_dualboot_warning(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "etc").mkdir()
            (root / "boot" / "efi" / "EFI" / "Microsoft" / "Boot").mkdir(parents=True)
            (root / "boot").mkdir(exist_ok=True)
            (root / "etc" / "fstab").write_text("UUID=x / ext4 defaults 0 1\n", encoding="utf-8")
            (root / "boot" / "vmlinuz-test").write_text("x", encoding="utf-8")
            (root / "boot" / "initrd.img-test").write_text("x", encoding="utf-8")
            (root / "boot" / "efi" / "EFI" / "Microsoft" / "Boot" / "bootmgfw.efi").write_text("x", encoding="utf-8")
            r = check_boot_capability(str(root))
            self.assertEqual(r.get("status"), "boot_warning")
            self.assertIn("BOOT_DUALBOOT_RISK", r.get("warnings", []))

    def test_api_contract_boot_capability(self):
        app = FastAPI()
        app.include_router(routes_mod.router)
        c = TestClient(app)
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "etc").mkdir()
            (root / "boot").mkdir()
            (root / "etc" / "fstab").write_text("UUID=x / ext4 defaults 0 1\n", encoding="utf-8")
            (root / "boot" / "vmlinuz-test").write_text("x", encoding="utf-8")
            (root / "boot" / "initrd.img-test").write_text("x", encoding="utf-8")
            resp = c.post("/api/boot/capability", json={"target_path": str(root)})
            self.assertEqual(resp.status_code, 200)
            payload = resp.json()
            self.assertIn(payload.get("code"), {
                "BOOT_CAPABILITY_LIKELY",
                "BOOT_CAPABILITY_WARNING",
                "BOOT_CAPABILITY_FAILED",
                "BOOT_CAPABILITY_UNKNOWN",
            })
            self.assertIsInstance(payload.get("capability"), dict)

    def test_execute_integration_boot_capability_present(self):
        old_collect = orch.collect_inspect_result
        old_eval = orch.evaluate_write_target
        old_verify = orch.verify_basic
        old_restore = orch.restore_files
        old_assert_backup = orch.assert_backup_readable_path
        old_assert_target = orch.assert_restore_live_target_directory
        old_validate = orch.validate_restored_target
        old_boot = orch.check_boot_capability
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
            self.assertIn("boot_capability", r)
            self.assertEqual((r.get("boot_capability") or {}).get("status"), "boot_warning")
        finally:
            orch.collect_inspect_result = old_collect
            orch.evaluate_write_target = old_eval
            orch.verify_basic = old_verify
            orch.restore_files = old_restore
            orch.assert_backup_readable_path = old_assert_backup
            orch.assert_restore_live_target_directory = old_assert_target
            orch.validate_restored_target = old_validate
            orch.check_boot_capability = old_boot
            orch._PREFLIGHT_PLAN_STORE.clear()
            orch._PREFLIGHT_PLAN_STORE.update(old_pf)
            orch._PREVIEW_SESSION_STORE.clear()
            orch._PREVIEW_SESSION_STORE.update(old_preview)

