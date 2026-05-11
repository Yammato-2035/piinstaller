"""Deploy write execute dry-run tests."""

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


mod = _load("deploy/write_execute.py", "setuphelfer_deploy_write_execute_test")
routes_mod = _load("deploy/routes.py", "setuphelfer_deploy_write_execute_routes_test")


def _write_plan(plan_status: str = "ok", blocked: list[str] | None = None, mode: str = "image_to_disk", inspect_code: str = "DEPLOY_IMAGE_INSPECT_WARNING") -> dict:
    return {
        "plan_status": plan_status,
        "target": {"target_device": "/dev/sdz", "write_allowed": True, "safety_reason_code": "SAFETY_EMPTY_DISK"},
        "image": {"path": "/mnt/setuphelfer/cache/deploy/test.img", "inspect_code": inspect_code},
        "write_strategy": {"mode": mode},
        "required_confirmations": [
            "CONFIRM_TARGET_DEVICE",
            "CONFIRM_DATA_LOSS",
            "CONFIRM_IMAGE_SOURCE",
            "CONFIRM_NO_WINDOWS_DUALBOOT",
            "CONFIRM_FINAL_DEPLOY_WRITE",
        ],
        "blocked_reasons": blocked or [],
    }


def _image_inspect(ok: bool = True) -> dict:
    if ok:
        return {"code": "DEPLOY_IMAGE_INSPECT_WARNING", "errors": [], "verification": {"checksum_expected": False}}
    return {"code": "DEPLOY_IMAGE_INSPECT_FAILED", "errors": ["DEPLOY_IMAGE_CHECKSUM_FAILED"], "verification": {"checksum_expected": True, "checksum_checked": True, "checksum_ok": False}}


class TestDeployWriteExecuteV1(unittest.TestCase):
    def setUp(self):
        mod._DEPLOY_WRITE_SESSION_STORE.clear()
        self.app = FastAPI()
        self.app.include_router(routes_mod.router)
        self.client = TestClient(self.app)

    def _create(self, **kwargs) -> dict:
        req = {
            "target_device": "/dev/sdz",
            "selected_profile": "DEPLOY_PROFILE_MINIMAL_LINUX",
            "image_inspect": _image_inspect(ok=True),
            "write_plan": _write_plan(),
            "confirmations": _write_plan()["required_confirmations"],
        }
        req.update(kwargs)
        return mod.create_deploy_write_session(req)

    def test_invalid_write_plan(self):
        out = self._create(write_plan=_write_plan(plan_status="blocked"))
        self.assertEqual(out["code"], "DEPLOY_WRITE_PLAN_INVALID")

    def test_missing_confirmation(self):
        conf = _write_plan()["required_confirmations"][:-1]
        out = self._create(confirmations=conf)
        self.assertEqual(out["code"], "DEPLOY_WRITE_CONFIRMATION_MISSING")

    def test_unknown_confirmation(self):
        conf = list(_write_plan()["required_confirmations"]) + ["CONFIRM_UNKNOWN"]
        out = self._create(confirmations=conf)
        self.assertEqual(out["code"], "DEPLOY_WRITE_CONFIRMATION_INVALID")

    def test_session_created(self):
        out = self._create()
        self.assertEqual(out["code"], "DEPLOY_WRITE_SESSION_CREATED")
        self.assertTrue(out["write_session_id"])
        self.assertTrue(out["confirmation_token"])

    def test_blocked_write_plan(self):
        out = self._create(write_plan=_write_plan(blocked=["DEPLOY_WRITE_BLOCKED_SYSTEM_DISK"]))
        self.assertEqual(out["code"], "DEPLOY_WRITE_SESSION_BLOCKED")

    def test_execute_ready(self):
        s = self._create()
        req = {
            "write_session_id": s["write_session_id"],
            "confirmation_token": s["confirmation_token"],
            "target_device": "/dev/sdz",
            "selected_profile": "DEPLOY_PROFILE_MINIMAL_LINUX",
            "image_path": "/mnt/setuphelfer/cache/deploy/test.img",
            "write_plan": _write_plan(),
        }
        out = mod.execute_deploy_write_dryrun(req)
        self.assertEqual(out["code"], "DEPLOY_WRITE_EXECUTE_READY")

    def test_wrong_token(self):
        s = self._create()
        out = mod.execute_deploy_write_dryrun(
            {
                "write_session_id": s["write_session_id"],
                "confirmation_token": "wrong",
                "target_device": "/dev/sdz",
                "selected_profile": "DEPLOY_PROFILE_MINIMAL_LINUX",
                "image_path": "/mnt/setuphelfer/cache/deploy/test.img",
                "write_plan": _write_plan(),
            }
        )
        self.assertEqual(out["code"], "DEPLOY_WRITE_TOKEN_INVALID")

    def test_session_expired(self):
        s = self._create()
        sid = s["write_session_id"]
        mod._DEPLOY_WRITE_SESSION_STORE[sid]["expires_at"] = (datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat()
        out = mod.execute_deploy_write_dryrun(
            {
                "write_session_id": sid,
                "confirmation_token": s["confirmation_token"],
                "target_device": "/dev/sdz",
                "selected_profile": "DEPLOY_PROFILE_MINIMAL_LINUX",
                "image_path": "/mnt/setuphelfer/cache/deploy/test.img",
                "write_plan": _write_plan(),
            }
        )
        self.assertEqual(out["code"], "DEPLOY_WRITE_SESSION_EXPIRED")

    def test_target_mismatch(self):
        s = self._create()
        out = mod.execute_deploy_write_dryrun(
            {
                "write_session_id": s["write_session_id"],
                "confirmation_token": s["confirmation_token"],
                "target_device": "/dev/sdy",
                "selected_profile": "DEPLOY_PROFILE_MINIMAL_LINUX",
                "image_path": "/mnt/setuphelfer/cache/deploy/test.img",
                "write_plan": _write_plan(),
            }
        )
        self.assertEqual(out["code"], "DEPLOY_WRITE_TARGET_MISMATCH")

    def test_profile_mismatch(self):
        s = self._create()
        out = mod.execute_deploy_write_dryrun(
            {
                "write_session_id": s["write_session_id"],
                "confirmation_token": s["confirmation_token"],
                "target_device": "/dev/sdz",
                "selected_profile": "DEPLOY_PROFILE_WEB_SERVER",
                "image_path": "/mnt/setuphelfer/cache/deploy/test.img",
                "write_plan": _write_plan(),
            }
        )
        self.assertEqual(out["code"], "DEPLOY_WRITE_PROFILE_MISMATCH")

    def test_image_mismatch(self):
        s = self._create()
        out = mod.execute_deploy_write_dryrun(
            {
                "write_session_id": s["write_session_id"],
                "confirmation_token": s["confirmation_token"],
                "target_device": "/dev/sdz",
                "selected_profile": "DEPLOY_PROFILE_MINIMAL_LINUX",
                "image_path": "/mnt/setuphelfer/cache/deploy/other.img",
                "write_plan": _write_plan(),
            }
        )
        self.assertEqual(out["code"], "DEPLOY_WRITE_IMAGE_MISMATCH")

    def test_plan_mismatch(self):
        s = self._create()
        bad = _write_plan()
        bad["write_strategy"] = {"mode": "installer_to_disk"}
        out = mod.execute_deploy_write_dryrun(
            {
                "write_session_id": s["write_session_id"],
                "confirmation_token": s["confirmation_token"],
                "target_device": "/dev/sdz",
                "selected_profile": "DEPLOY_PROFILE_MINIMAL_LINUX",
                "image_path": "/mnt/setuphelfer/cache/deploy/test.img",
                "write_plan": bad,
            }
        )
        self.assertEqual(out["code"], "DEPLOY_WRITE_PLAN_MISMATCH")

    def test_simulated_execution_stable(self):
        s = self._create()
        out = mod.execute_deploy_write_dryrun(
            {
                "write_session_id": s["write_session_id"],
                "confirmation_token": s["confirmation_token"],
                "target_device": "/dev/sdz",
                "selected_profile": "DEPLOY_PROFILE_MINIMAL_LINUX",
                "image_path": "/mnt/setuphelfer/cache/deploy/test.img",
                "write_plan": _write_plan(),
            }
        )
        self.assertEqual(out["code"], "DEPLOY_WRITE_EXECUTE_READY")
        steps = out.get("simulated_execution", [])
        self.assertEqual(len(steps), 9)
        self.assertEqual(steps[0]["code"], "DEPLOY_EXEC_RECHECK_TARGET")
        self.assertEqual(steps[-1]["code"], "DEPLOY_EXEC_FINALIZE")

    def test_auto_allowed_always_false(self):
        s = self._create()
        out = mod.execute_deploy_write_dryrun(
            {
                "write_session_id": s["write_session_id"],
                "confirmation_token": s["confirmation_token"],
                "target_device": "/dev/sdz",
                "selected_profile": "DEPLOY_PROFILE_MINIMAL_LINUX",
                "image_path": "/mnt/setuphelfer/cache/deploy/test.img",
                "write_plan": _write_plan(),
            }
        )
        for step in out.get("simulated_execution", []):
            self.assertFalse(bool(step.get("auto_allowed")))

    def test_no_forbidden_systemcalls(self):
        src = (_BACKEND / "deploy" / "write_execute.py").read_text(encoding="utf-8").lower()
        forbidden = [
            "dd ",
            "mkfs",
            "parted",
            "fdisk",
            "sfdisk",
            "losetup",
            "wipefs",
            "chroot",
            "os.system(",
            "subprocess.",
            "systemctl",
            "grub-install",
            "unsquashfs",
            "qemu-img",
            "kpartx",
        ]
        for token in forbidden:
            self.assertNotIn(token, src)

    def test_no_real_write_route(self):
        resp = self.client.post("/api/deploy/write/real", json={})
        self.assertEqual(resp.status_code, 404)


if __name__ == "__main__":
    unittest.main()
