"""Deploy final confirmation dry-run tests."""

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


mod = _load("deploy/final_confirmation.py", "setuphelfer_deploy_final_confirmation_test")
routes_mod = _load("deploy/routes.py", "setuphelfer_deploy_final_confirmation_routes_test")


def _inspect() -> dict:
    return {
        "storage": {
            "devices_classified": [
                {
                    "device": "/dev/sdz",
                    "size": "64G",
                    "transport": "usb",
                    "removable": True,
                    "model": "TestDrive",
                    "vendor": "Acme",
                    "partitions": [],
                }
            ]
        },
        "filesystems": {"detected": {}},
    }


def _write_plan(blocked: bool = False) -> dict:
    return {"plan_status": "ok", "blocked_reasons": ["DEPLOY_WRITE_BLOCKED_SYSTEM_DISK"] if blocked else []}


def _write_exec_result(code: str = "DEPLOY_WRITE_EXECUTE_READY") -> dict:
    return {
        "code": code,
        "write_session_id": "ws123456",
        "target_device": "/dev/sdz",
        "selected_profile": "DEPLOY_PROFILE_MINIMAL_LINUX",
        "image_path": "/mnt/setuphelfer/cache/deploy/test.img",
        "simulated_execution": [{"code": "DEPLOY_EXEC_WRITE_IMAGE", "status": "simulated"}],
    }


def _confirmations() -> list[str]:
    return [
        "CONFIRM_ALL_DATA_WILL_BE_DESTROYED",
        "CONFIRM_TARGET_DEVICE_AGAIN",
        "CONFIRM_NO_SYSTEM_DISK",
        "CONFIRM_NO_WINDOWS_DUALBOOT",
        "CONFIRM_IMAGE_AND_PROFILE_MATCH",
        "CONFIRM_FINAL_DEPLOY_DRYRUN",
    ]


class TestDeployFinalConfirmationV1(unittest.TestCase):
    def setUp(self):
        mod._DEPLOY_FINAL_CONFIRMATION_STORE.clear()
        mod._DEPLOY_WRITE_SESSION_STORE.clear()
        mod._DEPLOY_WRITE_SESSION_STORE["ws123456"] = {
            "write_session_id": "ws123456",
            "confirmation_token": "tok",
            "target_device": "/dev/sdz",
            "selected_profile": "DEPLOY_PROFILE_MINIMAL_LINUX",
            "image_path": "/mnt/setuphelfer/cache/deploy/test.img",
            "write_plan_hash": "x",
            "required_confirmations": [],
            "created_at": datetime.now(timezone.utc).isoformat(),
            "expires_at": (datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat(),
            "used": False,
        }
        self.app = FastAPI()
        self.app.include_router(routes_mod.router)
        self.client = TestClient(self.app)

    def test_invalid_write_execute_result(self):
        out = mod.create_final_confirmation_session(
            {"write_execute_result": _write_exec_result(code="DEPLOY_WRITE_EXECUTE_BLOCKED"), "write_plan": _write_plan(), "inspect_result": _inspect(), "confirmations": _confirmations()}
        )
        self.assertEqual(out["code"], "DEPLOY_FINAL_CONFIRMATION_INVALID")

    def test_missing_confirmation(self):
        out = mod.create_final_confirmation_session(
            {"write_execute_result": _write_exec_result(), "write_plan": _write_plan(), "inspect_result": _inspect(), "confirmations": _confirmations()[:-1]}
        )
        self.assertEqual(out["code"], "DEPLOY_FINAL_CONFIRMATION_CONFIRMATION_INVALID")

    def test_additional_confirmation(self):
        out = mod.create_final_confirmation_session(
            {"write_execute_result": _write_exec_result(), "write_plan": _write_plan(), "inspect_result": _inspect(), "confirmations": _confirmations() + ["CONFIRM_EXTRA"]}
        )
        self.assertEqual(out["code"], "DEPLOY_FINAL_CONFIRMATION_CONFIRMATION_INVALID")

    def test_session_created(self):
        out = mod.create_final_confirmation_session(
            {"write_execute_result": _write_exec_result(), "write_plan": _write_plan(), "inspect_result": _inspect(), "confirmations": _confirmations()}
        )
        self.assertEqual(out["code"], "DEPLOY_FINAL_CONFIRMATION_CREATED")
        self.assertTrue(out["target_snapshot"].get("fingerprint"))

    def test_wrong_token(self):
        s = mod.create_final_confirmation_session(
            {"write_execute_result": _write_exec_result(), "write_plan": _write_plan(), "inspect_result": _inspect(), "confirmations": _confirmations()}
        )
        out = mod.check_final_confirmation_dryrun(
            {"final_confirmation_id": s["final_confirmation_id"], "confirmation_token": "wrong", "target_snapshot": s["target_snapshot"]}
        )
        self.assertEqual(out["code"], "DEPLOY_FINAL_CONFIRMATION_TOKEN_INVALID")

    def test_session_expired(self):
        s = mod.create_final_confirmation_session(
            {"write_execute_result": _write_exec_result(), "write_plan": _write_plan(), "inspect_result": _inspect(), "confirmations": _confirmations()}
        )
        mod._DEPLOY_FINAL_CONFIRMATION_STORE[s["final_confirmation_id"]]["expires_at"] = (datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat()
        out = mod.check_final_confirmation_dryrun(
            {"final_confirmation_id": s["final_confirmation_id"], "confirmation_token": s["confirmation_token"], "target_snapshot": s["target_snapshot"]}
        )
        self.assertEqual(out["code"], "DEPLOY_FINAL_CONFIRMATION_SESSION_EXPIRED")

    def test_snapshot_mismatch(self):
        s = mod.create_final_confirmation_session(
            {"write_execute_result": _write_exec_result(), "write_plan": _write_plan(), "inspect_result": _inspect(), "confirmations": _confirmations()}
        )
        snap = dict(s["target_snapshot"])
        snap["fingerprint"] = "deadbeef"
        out = mod.check_final_confirmation_dryrun(
            {"final_confirmation_id": s["final_confirmation_id"], "confirmation_token": s["confirmation_token"], "target_snapshot": snap}
        )
        self.assertEqual(out["code"], "DEPLOY_FINAL_CONFIRMATION_SNAPSHOT_MISMATCH")

    def test_target_mismatch(self):
        s = mod.create_final_confirmation_session(
            {"write_execute_result": _write_exec_result(), "write_plan": _write_plan(), "inspect_result": _inspect(), "confirmations": _confirmations()}
        )
        snap = dict(s["target_snapshot"])
        snap["target_device"] = "/dev/sdy"
        out = mod.check_final_confirmation_dryrun(
            {"final_confirmation_id": s["final_confirmation_id"], "confirmation_token": s["confirmation_token"], "target_snapshot": snap}
        )
        self.assertEqual(out["code"], "DEPLOY_FINAL_CONFIRMATION_TARGET_MISMATCH")

    def test_blocked_write_plan(self):
        out = mod.create_final_confirmation_session(
            {"write_execute_result": _write_exec_result(), "write_plan": _write_plan(blocked=True), "inspect_result": _inspect(), "confirmations": _confirmations()}
        )
        self.assertEqual(out["code"], "DEPLOY_FINAL_CONFIRMATION_BLOCKED")

    def test_ready_success(self):
        s = mod.create_final_confirmation_session(
            {"write_execute_result": _write_exec_result(), "write_plan": _write_plan(), "inspect_result": _inspect(), "confirmations": _confirmations()}
        )
        out = mod.check_final_confirmation_dryrun(
            {"final_confirmation_id": s["final_confirmation_id"], "confirmation_token": s["confirmation_token"], "target_snapshot": s["target_snapshot"]}
        )
        self.assertEqual(out["code"], "DEPLOY_FINAL_CONFIRMATION_READY")

    def test_fingerprint_stable(self):
        a = mod.build_target_snapshot(_write_exec_result(), _inspect())
        b = mod.build_target_snapshot(_write_exec_result(), _inspect())
        self.assertEqual(a["fingerprint"], b["fingerprint"])

    def test_destructive_operations_stable(self):
        s = mod.create_final_confirmation_session(
            {"write_execute_result": _write_exec_result(), "write_plan": _write_plan(), "inspect_result": _inspect(), "confirmations": _confirmations()}
        )
        out = mod.check_final_confirmation_dryrun(
            {"final_confirmation_id": s["final_confirmation_id"], "confirmation_token": s["confirmation_token"], "target_snapshot": s["target_snapshot"]}
        )
        self.assertEqual(
            out["destructive_operations"],
            ["DEPLOY_EXEC_WRITE_IMAGE", "DEPLOY_EXEC_EXPAND_FILESYSTEM", "DEPLOY_EXEC_INSTALL_SETUPHELPER"],
        )

    def test_no_forbidden_systemcalls(self):
        src = (_BACKEND / "deploy" / "final_confirmation.py").read_text(encoding="utf-8").lower()
        forbidden = [
            "subprocess.",
            "os.system(",
            "dd ",
            "mkfs",
            "parted",
            "fdisk",
            "sfdisk",
            "losetup",
            "wipefs",
            "grub-install",
            "chroot",
        ]
        for x in forbidden:
            self.assertNotIn(x, src)

    def test_no_real_write_route(self):
        resp = self.client.post("/api/deploy/write/real", json={})
        self.assertEqual(resp.status_code, 404)


if __name__ == "__main__":
    unittest.main()
