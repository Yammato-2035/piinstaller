"""Deploy real write guard prototype tests (no write engine)."""

from __future__ import annotations

import importlib.util
import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

_BACKEND = Path(__file__).resolve().parent.parent
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))


def _load(rel: str, name: str):
    p = _BACKEND / rel
    spec = importlib.util.spec_from_file_location(name, p)
    if not spec or not spec.loader:
        raise ImportError(rel)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


mod = _load("deploy/real_write_guard.py", "setuphelfer_real_write_guard_test")
routes_mod = _load("deploy/routes.py", "setuphelfer_real_write_guard_routes_test")


def _harness_proof(ok: bool = True) -> dict:
    if ok:
        return {
            "execute_code": "DEPLOY_WRITE_HARNESS_COMPLETED",
            "sha256_matches": True,
            "single_use_code": "DEPLOY_WRITE_HARNESS_SESSION_ALREADY_USED",
            "host_changes_detected": False,
        }
    return {"execute_code": "DEPLOY_WRITE_HARNESS_FAILED"}


def _inspect(system_type: str = "EMPTY", target_device: str = "/dev/sdz", removable: bool = True, transport: str = "usb", partitions: list[dict] | None = None):
    return {
        "classification": {"system_type": system_type},
        "storage": {
            "devices_classified": [
                {
                    "device": target_device,
                    "size": "64G",
                    "transport": transport,
                    "removable": removable,
                    "partitions": partitions or [],
                }
            ]
        },
        "filesystems": {"detected": {}},
    }


def _safety(reason: str = "SAFETY_EMPTY_DISK", allowed: bool = True, device: str = "/dev/sdz"):
    return {"policy_code": "safety.summary.v1", "targets": [{"device": device, "reason_code": reason, "write_allowed": allowed}]}


def _write_plan(blocked: bool = False):
    return {"plan_status": "ok", "blocked_reasons": ["DEPLOY_WRITE_BLOCKED_SYSTEM_DISK"] if blocked else []}


def _write_execute(device: str = "/dev/sdz"):
    return {
        "code": "DEPLOY_WRITE_EXECUTE_READY",
        "write_session_id": "ws1",
        "target_device": device,
        "selected_profile": "DEPLOY_PROFILE_MINIMAL_LINUX",
        "image_path": "/tmp/setuphelfer-deploy-test/cache/source.img",
    }


class TestDeployRealWriteGuardV1(unittest.TestCase):
    def setUp(self):
        mod._DEPLOY_REAL_WRITE_GUARD_STORE.clear()
        self.app = FastAPI()
        self.app.include_router(routes_mod.router)
        self.client = TestClient(self.app)

    def _create(self, **kwargs):
        req = {
            "final_confirmation_result": {"code": "DEPLOY_FINAL_CONFIRMATION_READY"},
            "write_session_result": {"code": "DEPLOY_WRITE_SESSION_CREATED"},
            "write_execute_result": _write_execute(),
            "write_plan": _write_plan(),
            "inspect_result": _inspect(),
            "safety_summary": _safety(),
            "write_harness_result": _harness_proof(True),
        }
        req.update(kwargs)
        return mod.create_real_write_guard_session(req)

    def test_systemdisk_blocked(self):
        out = self._create(safety_summary=_safety("SAFETY_SYSTEM_DISK", False))
        self.assertEqual(out["code"], "DEPLOY_REAL_WRITE_BLOCKED_SYSTEM_DISK")

    def test_windows_blocked(self):
        out = self._create(inspect_result=_inspect(system_type="WINDOWS"))
        self.assertEqual(out["code"], "DEPLOY_REAL_WRITE_BLOCKED_WINDOWS")

    def test_dualboot_blocked(self):
        out = self._create(inspect_result=_inspect(system_type="DUALBOOT"))
        self.assertEqual(out["code"], "DEPLOY_REAL_WRITE_BLOCKED_DUALBOOT")

    def test_mounted_blocked(self):
        out = self._create(inspect_result=_inspect(partitions=[{"device": "/dev/sdz1", "mountpoint": "/mnt/x"}]))
        self.assertEqual(out["code"], "DEPLOY_REAL_WRITE_BLOCKED_MOUNTED")

    def test_non_removable_blocked(self):
        out = self._create(inspect_result=_inspect(removable=False))
        self.assertEqual(out["code"], "DEPLOY_REAL_WRITE_BLOCKED_NON_REMOVABLE")

    def test_lvm_blocked(self):
        out = self._create(write_execute_result=_write_execute("/dev/mapper/vg-lv"), inspect_result=_inspect(target_device="/dev/mapper/vg-lv"))
        self.assertEqual(out["code"], "DEPLOY_REAL_WRITE_BLOCKED_LVM")

    def test_raid_blocked(self):
        out = self._create(write_execute_result=_write_execute("/dev/md0"), inspect_result=_inspect(target_device="/dev/md0"))
        self.assertEqual(out["code"], "DEPLOY_REAL_WRITE_BLOCKED_RAID")

    def test_loop_blocked(self):
        out = self._create(write_execute_result=_write_execute("/dev/loop0"), inspect_result=_inspect(target_device="/dev/loop0"))
        self.assertEqual(out["code"], "DEPLOY_REAL_WRITE_BLOCKED_LOOP")

    def test_harness_missing_blocked(self):
        out = self._create(write_harness_result={})
        self.assertEqual(out["code"], "DEPLOY_REAL_WRITE_BLOCKED_NO_HARNESS_PROOF")

    def test_fingerprint_mismatch_blocked(self):
        s = self._create()
        snap = dict(s["snapshot"])
        snap["fingerprint"] = "deadbeef"
        out = mod.check_real_write_guard(
            {
                "real_write_guard_id": s["real_write_guard_id"],
                "confirmation_token": s["confirmation_token"],
                "snapshot": snap,
                "inspect_result": _inspect(),
                "safety_summary": _safety(),
                "write_plan": _write_plan(),
                "write_harness_result": _harness_proof(True),
            }
        )
        self.assertEqual(out["code"], "DEPLOY_REAL_WRITE_BLOCKED_FINGERPRINT_MISMATCH")

    def test_snapshot_changed_blocked(self):
        s = self._create()
        snap = dict(s["snapshot"])
        snap["device_summary"] = dict(snap.get("device_summary") or {})
        snap["device_summary"]["model"] = "changed"
        out = mod.check_real_write_guard(
            {
                "real_write_guard_id": s["real_write_guard_id"],
                "confirmation_token": s["confirmation_token"],
                "snapshot": snap,
                "inspect_result": _inspect(),
                "safety_summary": _safety(),
                "write_plan": _write_plan(),
                "write_harness_result": _harness_proof(True),
            }
        )
        self.assertEqual(out["code"], "DEPLOY_REAL_WRITE_BLOCKED_SNAPSHOT_CHANGED")

    def test_ready_on_valid_removable_target(self):
        s = self._create()
        out = mod.check_real_write_guard(
            {
                "real_write_guard_id": s["real_write_guard_id"],
                "confirmation_token": s["confirmation_token"],
                "snapshot": s["snapshot"],
                "inspect_result": _inspect(),
                "safety_summary": _safety(),
                "write_plan": _write_plan(),
                "write_harness_result": _harness_proof(True),
            }
        )
        self.assertEqual(out["code"], "DEPLOY_REAL_WRITE_READY")
        self.assertEqual(len(out["would_execute_steps"]), 6)

    def test_single_use_consumed(self):
        s = self._create()
        req = {
            "real_write_guard_id": s["real_write_guard_id"],
            "confirmation_token": s["confirmation_token"],
            "snapshot": s["snapshot"],
            "inspect_result": _inspect(),
            "safety_summary": _safety(),
            "write_plan": _write_plan(),
            "write_harness_result": _harness_proof(True),
        }
        out1 = mod.check_real_write_guard(req)
        out2 = mod.check_real_write_guard(req)
        self.assertEqual(out1["code"], "DEPLOY_REAL_WRITE_READY")
        self.assertEqual(out2["code"], "DEPLOY_REAL_WRITE_GUARD_BLOCKED")

    def test_no_execute_route(self):
        self.assertEqual(self.client.post("/api/deploy/real-write/execute", json={}).status_code, 404)

    def test_no_forbidden_systemcalls(self):
        src = (_BACKEND / "deploy" / "real_write_guard.py").read_text(encoding="utf-8").lower()
        forbidden = [
            "subprocess.",
            "os.system(",
            "dd ",
            "mkfs",
            "parted",
            "fdisk",
            "sfdisk",
            "mount(",
            "umount(",
            "losetup",
            "wipefs",
            "grub-install",
            "chroot",
            "systemctl",
            "sudo",
        ]
        for token in forbidden:
            self.assertNotIn(token, src)


if __name__ == "__main__":
    unittest.main()
