"""Deploy write harness tests (isolated test targets only)."""

from __future__ import annotations

import hashlib
import importlib.util
import os
import shutil
import sys
import tempfile
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


mod = _load("deploy/write_harness.py", "setuphelfer_deploy_write_harness_test")
routes_mod = _load("deploy/routes.py", "setuphelfer_deploy_harness_routes_test")


class TestDeployWriteHarnessV1(unittest.TestCase):
    def setUp(self):
        self._old_test_mode = os.environ.get("SETUPHELFER_DEPLOY_TEST_MODE")
        os.environ.pop("SETUPHELFER_DEPLOY_TEST_MODE", None)
        mod._DEPLOY_WRITE_HARNESS_SESSION_STORE.clear()
        mod._DEPLOY_FINAL_CONFIRMATION_STORE.clear()
        self.base = Path("/tmp/setuphelfer-deploy-test").resolve()
        self.base.mkdir(parents=True, exist_ok=True)
        self.cache = Path("/mnt/setuphelfer/cache/deploy").resolve()
        self.cache.mkdir(parents=True, exist_ok=True)
        self.image = self.cache / "harness-src.img"
        self.image.write_bytes(b"abcdefghijklmnopqrstuvwxyz")
        self.target = self.base / "harness-target.img"
        if self.target.exists():
            self.target.unlink()
        mod._DEPLOY_FINAL_CONFIRMATION_STORE["fc1"] = {
            "final_confirmation_id": "fc1",
            "confirmation_token": "tok",
            "target_snapshot_fingerprint": "fp123",
            "write_session_id": "ws1",
            "target_device": "/dev/sdz",
            "selected_profile": "DEPLOY_PROFILE_MINIMAL_LINUX",
            "image_path": str(self.image),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "expires_at": (datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat(),
            "used": False,
        }
        self.app = FastAPI()
        self.app.include_router(routes_mod.router)
        self.client = TestClient(self.app)

    def tearDown(self):
        if self._old_test_mode is None:
            os.environ.pop("SETUPHELFER_DEPLOY_TEST_MODE", None)
        else:
            os.environ["SETUPHELFER_DEPLOY_TEST_MODE"] = self._old_test_mode
        if self.target.exists():
            self.target.unlink()

    def _final_result(self, code: str = "DEPLOY_FINAL_CONFIRMATION_READY"):
        return {
            "code": code,
            "final_confirmation_id": "fc1",
            "target_snapshot": {"target_device": "/dev/sdz", "fingerprint": "fp123"},
        }

    def _img_ok(self, ok: bool = True):
        if ok:
            return {"code": "DEPLOY_IMAGE_INSPECT_OK", "errors": []}
        return {"code": "DEPLOY_IMAGE_INSPECT_FAILED", "errors": ["x"]}

    def _create(self, **kwargs):
        req = {
            "final_confirmation_result": self._final_result(),
            "image_inspect": self._img_ok(True),
            "test_target_path": str(self.target),
        }
        req.update(kwargs)
        return mod.create_deploy_write_harness_session(req)

    def test_invalid_final_confirmation(self):
        out = self._create(final_confirmation_result=self._final_result(code="DEPLOY_FINAL_CONFIRMATION_BLOCKED"))
        self.assertEqual(out["code"], "DEPLOY_WRITE_HARNESS_INVALID_FINAL_CONFIRMATION")

    def test_image_invalid(self):
        out = self._create(image_inspect=self._img_ok(False))
        self.assertEqual(out["code"], "DEPLOY_WRITE_HARNESS_INVALID_IMAGE")

    def test_target_dev_blocked(self):
        out = self._create(test_target_path="/dev/sda")
        self.assertEqual(out["code"], "DEPLOY_WRITE_HARNESS_INVALID_TEST_TARGET")

    def test_target_symlink_blocked(self):
        with tempfile.NamedTemporaryFile() as tmp:
            link = self.base / "symlink-target.img"
            if link.exists() or link.is_symlink():
                link.unlink()
            link.symlink_to(Path(tmp.name))
            out = self._create(test_target_path=str(link))
            self.assertEqual(out["code"], "DEPLOY_WRITE_HARNESS_INVALID_TEST_TARGET")
            link.unlink()

    def test_parent_missing_blocked(self):
        p = self.base / "missing-parent" / "x.img"
        out = self._create(test_target_path=str(p))
        self.assertEqual(out["code"], "DEPLOY_WRITE_HARNESS_INVALID_TEST_TARGET")

    def test_session_created(self):
        out = self._create()
        self.assertEqual(out["code"], "DEPLOY_WRITE_HARNESS_SESSION_CREATED")
        self.assertTrue(out["harness_session_id"])

    def test_wrong_token(self):
        s = self._create()
        out = mod.execute_deploy_write_harness(
            {
                "harness_session_id": s["harness_session_id"],
                "confirmation_token": "wrong",
                "image_path": str(self.image.resolve()),
                "test_target_path": str(self.target.resolve()),
                "max_bytes": 16,
            }
        )
        self.assertEqual(out["code"], "DEPLOY_WRITE_HARNESS_TOKEN_INVALID")

    def test_session_expired(self):
        s = self._create()
        sid = s["harness_session_id"]
        mod._DEPLOY_WRITE_HARNESS_SESSION_STORE[sid]["expires_at"] = (datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat()
        out = mod.execute_deploy_write_harness(
            {
                "harness_session_id": sid,
                "confirmation_token": s["confirmation_token"],
                "image_path": str(self.image.resolve()),
                "test_target_path": str(self.target.resolve()),
                "max_bytes": 16,
            }
        )
        self.assertEqual(out["code"], "DEPLOY_WRITE_HARNESS_SESSION_EXPIRED")

    def test_image_mismatch(self):
        s = self._create()
        out = mod.execute_deploy_write_harness(
            {
                "harness_session_id": s["harness_session_id"],
                "confirmation_token": s["confirmation_token"],
                "image_path": str((self.cache / "other.img").resolve()),
                "test_target_path": str(self.target.resolve()),
                "max_bytes": 16,
            }
        )
        self.assertEqual(out["code"], "DEPLOY_WRITE_HARNESS_IMAGE_MISMATCH")

    def test_target_mismatch(self):
        s = self._create()
        other = self.base / "other-target.img"
        out = mod.execute_deploy_write_harness(
            {
                "harness_session_id": s["harness_session_id"],
                "confirmation_token": s["confirmation_token"],
                "image_path": str(self.image.resolve()),
                "test_target_path": str(other.resolve()),
                "max_bytes": 16,
            }
        )
        self.assertEqual(out["code"], "DEPLOY_WRITE_HARNESS_TARGET_MISMATCH")

    def test_max_bytes_limit(self):
        s = self._create()
        out = mod.execute_deploy_write_harness(
            {
                "harness_session_id": s["harness_session_id"],
                "confirmation_token": s["confirmation_token"],
                "image_path": str(self.image.resolve()),
                "test_target_path": str(self.target.resolve()),
                "max_bytes": 10 * 1024 * 1024 + 1,
            }
        )
        self.assertEqual(out["code"], "DEPLOY_WRITE_HARNESS_MAX_BYTES_INVALID")

    def test_execute_writes_limited_and_sha(self):
        s = self._create()
        out = mod.execute_deploy_write_harness(
            {
                "harness_session_id": s["harness_session_id"],
                "confirmation_token": s["confirmation_token"],
                "image_path": str(self.image.resolve()),
                "test_target_path": str(self.target.resolve()),
                "max_bytes": 10,
            }
        )
        self.assertEqual(out["code"], "DEPLOY_WRITE_HARNESS_COMPLETED")
        self.assertEqual(out["write_result"]["bytes_written"], 10)
        data = self.target.read_bytes()
        self.assertEqual(len(data), 10)
        self.assertEqual(out["write_result"]["sha256"], hashlib.sha256(data).hexdigest())

    def test_single_use(self):
        s = self._create()
        req = {
            "harness_session_id": s["harness_session_id"],
            "confirmation_token": s["confirmation_token"],
            "image_path": str(self.image.resolve()),
            "test_target_path": str(self.target.resolve()),
            "max_bytes": 10,
        }
        out1 = mod.execute_deploy_write_harness(req)
        out2 = mod.execute_deploy_write_harness(req)
        self.assertEqual(out1["code"], "DEPLOY_WRITE_HARNESS_COMPLETED")
        self.assertEqual(out2["code"], "DEPLOY_WRITE_HARNESS_SESSION_ALREADY_USED")

    def test_no_forbidden_calls(self):
        src = (_BACKEND / "deploy" / "write_harness.py").read_text(encoding="utf-8").lower()
        forbidden = [
            "subprocess.",
            "os.system(",
            "dd ",
            "mkfs",
            "parted",
            "fdisk",
            "sfdisk",
            "mount(",
            "losetup",
            "wipefs",
            "grub-install",
            "chroot",
            "systemctl",
        ]
        for x in forbidden:
            self.assertNotIn(x, src)

    def test_no_real_write_routes(self):
        self.assertEqual(self.client.post("/api/deploy/write/real", json={}).status_code, 404)
        self.assertEqual(self.client.post("/api/deploy/write/device", json={}).status_code, 404)
        self.assertEqual(self.client.post("/api/deploy/write/blockdevice", json={}).status_code, 404)
        self.assertEqual(self.client.post("/api/deploy/write/install", json={}).status_code, 404)

    def test_tmp_test_cache_blocked_without_test_mode(self):
        tmp_cache = Path("/tmp/setuphelfer-deploy-test/cache/source-testmode.img")
        tmp_cache.parent.mkdir(parents=True, exist_ok=True)
        tmp_cache.write_bytes(b"abc")
        mod._DEPLOY_FINAL_CONFIRMATION_STORE["fc1"]["image_path"] = str(tmp_cache)
        out = self._create()
        self.assertEqual(out["code"], "DEPLOY_WRITE_HARNESS_INVALID_IMAGE")

    def test_tmp_test_cache_allowed_with_test_mode(self):
        os.environ["SETUPHELFER_DEPLOY_TEST_MODE"] = "1"
        tmp_cache = Path("/tmp/setuphelfer-deploy-test/cache/source-testmode.img")
        tmp_cache.parent.mkdir(parents=True, exist_ok=True)
        tmp_cache.write_bytes(b"abc")
        mod._DEPLOY_FINAL_CONFIRMATION_STORE["fc1"]["image_path"] = str(tmp_cache)
        out = self._create()
        self.assertEqual(out["code"], "DEPLOY_WRITE_HARNESS_SESSION_CREATED")

    def test_tmp_general_still_blocked_in_test_mode(self):
        os.environ["SETUPHELFER_DEPLOY_TEST_MODE"] = "1"
        other_tmp = Path("/tmp/source-outside-harness-cache.img")
        other_tmp.write_bytes(b"abc")
        mod._DEPLOY_FINAL_CONFIRMATION_STORE["fc1"]["image_path"] = str(other_tmp)
        out = self._create()
        self.assertEqual(out["code"], "DEPLOY_WRITE_HARNESS_INVALID_IMAGE")


if __name__ == "__main__":
    unittest.main()
