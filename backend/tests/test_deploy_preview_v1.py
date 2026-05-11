"""Deploy preview tests (simulation only, no writes)."""

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


preview_mod = _load("deploy/preview.py", "setuphelfer_deploy_preview_test")
routes_mod = _load("deploy/routes.py", "setuphelfer_deploy_routes_preview_test")


def _plan(blocked_steps: list[str] | None = None) -> dict:
    return {
        "plan_status": "ok",
        "target": {"target_device": "/dev/sdx"},
        "deploy_profiles": [
            {
                "code": "DEPLOY_PROFILE_MINIMAL_LINUX",
                "suitable": True,
                "auto_allowed": False,
                "requires_confirmation": True,
                "risk_level": "low",
                "requirements": [],
            }
        ],
        "required_steps": [
            {
                "code": "DEPLOY_STEP_INSTALL_BASE_SYSTEM",
                "applicable": True,
                "auto_allowed": False,
                "requires_confirmation": True,
            }
        ],
        "blocked_steps": blocked_steps or [],
        "warnings": [],
        "errors": [],
    }


def _source(kind: str = "local_image") -> dict:
    if kind == "remote_image":
        return {"type": "remote_image", "name": "ubuntu-server-lts", "url": "https://example.invalid/os.img", "checksum": "sha256:abc"}
    if kind == "official_installer":
        return {"type": "official_installer", "name": "debian-minimal", "url": "", "checksum": ""}
    return {"type": "local_image", "name": "raspberry-pi-os-lite", "url": "", "checksum": ""}


class TestDeployPreviewV1(unittest.TestCase):
    def setUp(self):
        preview_mod._DEPLOY_SESSION_STORE.clear()

    def _session(self) -> dict:
        sid = "sess1234"
        tok = "token-12345678"
        now = datetime.now(timezone.utc)
        preview_mod._DEPLOY_SESSION_STORE[sid] = {
            "deploy_session_id": sid,
            "confirmation_token": tok,
            "target_device": "/dev/sdx",
            "selected_profile": "DEPLOY_PROFILE_MINIMAL_LINUX",
            "plan_snapshot_hash": preview_mod._hash_plan(_plan()),
            "created_at": now.isoformat(),
            "expires_at": (now + timedelta(minutes=15)).isoformat(),
            "used": False,
        }
        return {"deploy_session_id": sid, "confirmation_token": tok}

    def _preview(self, sess: dict, **override):
        req = {
            "deploy_session_id": sess.get("deploy_session_id"),
            "confirmation_token": sess.get("confirmation_token"),
            "target_device": "/dev/sdx",
            "selected_profile": "DEPLOY_PROFILE_MINIMAL_LINUX",
            "plan": _plan(),
            "os_source": _source("local_image"),
        }
        req.update(override)
        return preview_mod.preview_deploy(req)

    def test_missing_session(self):
        out = preview_mod.preview_deploy({})
        self.assertEqual(out.get("code"), "DEPLOY_PREVIEW_SESSION_NOT_FOUND")

    def test_wrong_token(self):
        s = self._session()
        out = self._preview(s, confirmation_token="wrong")
        self.assertEqual(out.get("code"), "DEPLOY_PREVIEW_TOKEN_INVALID")

    def test_expired_session(self):
        s = self._session()
        sid = str(s.get("deploy_session_id"))
        preview_mod._DEPLOY_SESSION_STORE[sid]["expires_at"] = (datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat()
        out = self._preview(s)
        self.assertEqual(out.get("code"), "DEPLOY_PREVIEW_SESSION_EXPIRED")

    def test_target_mismatch(self):
        s = self._session()
        out = self._preview(s, target_device="/dev/sdy")
        self.assertEqual(out.get("code"), "DEPLOY_PREVIEW_TARGET_MISMATCH")

    def test_profile_mismatch(self):
        s = self._session()
        out = self._preview(s, selected_profile="DEPLOY_PROFILE_WEB_SERVER")
        self.assertEqual(out.get("code"), "DEPLOY_PREVIEW_PROFILE_MISMATCH")

    def test_plan_mismatch(self):
        s = self._session()
        bad = _plan()
        bad["required_steps"].append({"code": "DEPLOY_STEP_ENABLE_SSH", "applicable": True, "auto_allowed": False, "requires_confirmation": True})
        out = self._preview(s, plan=bad)
        self.assertEqual(out.get("code"), "DEPLOY_PREVIEW_PLAN_MISMATCH")

    def test_safety_blocked(self):
        s = self._session()
        blocked = _plan(blocked_steps=["DEPLOY_BLOCKED_SYSTEM_DISK"])
        sid = str(s.get("deploy_session_id"))
        preview_mod._DEPLOY_SESSION_STORE[sid]["plan_snapshot_hash"] = preview_mod._hash_plan(blocked)
        out = self._preview(s, plan=blocked)
        self.assertEqual(out.get("code"), "DEPLOY_PREVIEW_SAFETY_BLOCKED")

    def test_remote_image_not_loaded(self):
        s = self._session()
        out = self._preview(s, os_source=_source("remote_image"))
        self.assertEqual(out.get("code"), "DEPLOY_PREVIEW_CREATED")
        self.assertIn("DEPLOY_PREVIEW_REMOTE_DOWNLOAD_BLOCKED", out.get("warnings", []))

    def test_preview_success_with_steps(self):
        s = self._session()
        out = self._preview(s)
        self.assertEqual(out.get("code"), "DEPLOY_PREVIEW_CREATED")
        steps = out.get("simulated_steps", [])
        self.assertTrue(isinstance(steps, list) and len(steps) >= 8)

    def test_all_steps_auto_allowed_false(self):
        s = self._session()
        out = self._preview(s)
        for step in out.get("simulated_steps", []):
            self.assertFalse(bool(step.get("auto_allowed")))

    def test_no_real_install_route(self):
        app = FastAPI()
        app.include_router(routes_mod.router)
        c = TestClient(app)
        resp = c.post("/api/deploy/install-real", json={})
        self.assertEqual(resp.status_code, 404)


if __name__ == "__main__":
    unittest.main()
