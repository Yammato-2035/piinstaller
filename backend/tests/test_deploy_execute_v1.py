"""Deploy execute prep (session+token+binding, no-op execute) tests."""

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


mod = _load("deploy/execute.py", "setuphelfer_deploy_execute_test")
routes_mod = _load("deploy/routes.py", "setuphelfer_deploy_routes_execute_test")


def _plan(
    *,
    status: str = "ok",
    blocked_steps: list[str] | None = None,
    profile_suitable: bool = True,
    required_auto_allowed: bool = False,
) -> dict:
    return {
        "plan_status": status,
        "target": {"target_device": "/dev/sdx"},
        "deploy_profiles": [
            {
                "code": "DEPLOY_PROFILE_MINIMAL_LINUX",
                "suitable": profile_suitable,
                "auto_allowed": False,
                "requires_confirmation": True,
                "risk_level": "low",
                "requirements": [],
            }
        ],
        "recommended_profile": {},
        "required_steps": [
            {
                "code": "DEPLOY_STEP_INSTALL_BASE_SYSTEM",
                "applicable": True,
                "auto_allowed": required_auto_allowed,
                "requires_confirmation": True,
            }
        ],
        "blocked_steps": blocked_steps or [],
        "hardware_summary": {},
        "risks": [],
        "warnings": [],
        "errors": [],
        "requires_manual_review": True,
    }


class TestDeployExecuteV1(unittest.TestCase):
    def setUp(self):
        mod._DEPLOY_SESSION_STORE.clear()

    def _create(self, plan: dict, target_device: str = "/dev/sdx", selected_profile: str = "DEPLOY_PROFILE_MINIMAL_LINUX"):
        return mod.create_deploy_session(
            {
                "target_device": target_device,
                "selected_profile": selected_profile,
                "plan": plan,
            }
        )

    def _execute(
        self,
        sess: dict,
        *,
        target_device: str = "/dev/sdx",
        selected_profile: str = "DEPLOY_PROFILE_MINIMAL_LINUX",
        plan: dict | None = None,
        token: str | None = None,
    ):
        return mod.execute_deploy(
            {
                "deploy_session_id": sess.get("deploy_session_id"),
                "confirmation_token": token if token is not None else sess.get("confirmation_token"),
                "target_device": target_device,
                "selected_profile": selected_profile,
                "plan": _plan() if plan is None else plan,
            }
        )

    def test_session_invalid_plan_missing(self):
        r = self._create({})
        self.assertEqual(r.get("code"), "DEPLOY_PLAN_INVALID")

    def test_session_invalid_plan_status(self):
        r = self._create(_plan(status="blocked"))
        self.assertEqual(r.get("code"), "DEPLOY_PLAN_INVALID")

    def test_session_invalid_blocked_steps(self):
        r = self._create(_plan(blocked_steps=["DEPLOY_BLOCKED_WINDOWS"]))
        self.assertEqual(r.get("code"), "DEPLOY_PLAN_INVALID")

    def test_invalid_profile(self):
        r = self._create(_plan(), selected_profile="DEPLOY_PROFILE_UNKNOWN")
        self.assertEqual(r.get("code"), "DEPLOY_PROFILE_NOT_ALLOWED")

    def test_unsuitable_profile(self):
        r = self._create(_plan(profile_suitable=False))
        self.assertEqual(r.get("code"), "DEPLOY_PROFILE_NOT_ALLOWED")

    def test_session_created(self):
        r = self._create(_plan())
        self.assertEqual(r.get("code"), "DEPLOY_SESSION_CREATED")
        self.assertTrue(r.get("deploy_session_id"))
        self.assertTrue(r.get("confirmation_token"))

    def test_wrong_token(self):
        s = self._create(_plan())
        r = self._execute(s, token="wrong")
        self.assertEqual(r.get("code"), "DEPLOY_TOKEN_INVALID")

    def test_expired_session(self):
        s = self._create(_plan())
        sid = str(s.get("deploy_session_id"))
        mod._DEPLOY_SESSION_STORE[sid]["expires_at"] = (datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat()
        r = self._execute(s)
        self.assertEqual(r.get("code"), "DEPLOY_SESSION_EXPIRED")

    def test_target_mismatch(self):
        s = self._create(_plan())
        r = self._execute(s, target_device="/dev/sdy")
        self.assertEqual(r.get("code"), "DEPLOY_TARGET_MISMATCH")

    def test_profile_mismatch(self):
        s = self._create(_plan())
        r = self._execute(s, selected_profile="DEPLOY_PROFILE_WEB_SERVER")
        self.assertEqual(r.get("code"), "DEPLOY_PROFILE_MISMATCH")

    def test_plan_mismatch(self):
        s = self._create(_plan())
        wrong = _plan()
        wrong["required_steps"].append(
            {
                "code": "DEPLOY_STEP_ENABLE_SSH",
                "applicable": True,
                "auto_allowed": False,
                "requires_confirmation": True,
            }
        )
        r = self._execute(s, plan=wrong)
        self.assertEqual(r.get("code"), "DEPLOY_PLAN_MISMATCH")

    def test_execute_ready_noop(self):
        s = self._create(_plan())
        r = self._execute(s)
        self.assertEqual(r.get("code"), "DEPLOY_EXECUTE_READY")
        self.assertEqual(r.get("next_phase"), "deploy_preview")
        sid = str(s.get("deploy_session_id"))
        # In this prep phase, execute should not consume the session.
        self.assertFalse(bool(mod._DEPLOY_SESSION_STORE[sid].get("used")))

    def test_no_install_route_present(self):
        app = FastAPI()
        app.include_router(routes_mod.router)
        c = TestClient(app)
        resp = c.post("/api/deploy/install", json={})
        self.assertEqual(resp.status_code, 404)


if __name__ == "__main__":
    unittest.main()
