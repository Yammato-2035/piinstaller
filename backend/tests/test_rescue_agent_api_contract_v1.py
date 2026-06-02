from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from rescue_agent.routers import router as rescue_agent_router


class RescueAgentApiContractTests(unittest.TestCase):
    def _client(self, profile: str) -> TestClient:
        env = {
            "SETUPHELFER_INSTALL_PROFILE": profile,
            "SETUPHELFER_RESCUE_REMOTE_ENABLED": "1",
        }
        self._patch = patch.dict(os.environ, env, clear=False)
        self._patch.start()
        app = FastAPI()
        app.include_router(rescue_agent_router)
        return TestClient(app)

    def tearDown(self) -> None:
        p = getattr(self, "_patch", None)
        if p:
            p.stop()

    def test_register_stub_in_local_lab(self) -> None:
        client = self._client("local_lab")
        r = client.post("/api/rescue-agent/register", json={})
        self.assertEqual(r.status_code, 200)
        self.assertIn(r.json()["registration_status"], {"pending", "accepted"})

    def test_release_profile_blocks_registration(self) -> None:
        client = self._client("release")
        r = client.post("/api/rescue-agent/register", json={})
        self.assertEqual(r.status_code, 403)

    def test_system_report_requires_valid_session(self) -> None:
        client = self._client("local_lab")
        r = client.post("/api/rescue-agent/system-report", json={"session_id": "x", "agent_id": "a"})
        self.assertEqual(r.status_code, 403)

    def test_unencrypted_report_blocked_without_test_mode(self) -> None:
        client = self._client("local_lab")
        reg = client.post("/api/rescue-agent/register", json={}).json()
        r = client.post(
            "/api/rescue-agent/system-report",
            json={"session_id": reg["session_id"], "agent_id": reg["agent_id"]},
        )
        self.assertEqual(r.status_code, 400)

    def test_heartbeat_accepted_after_valid_session(self) -> None:
        client = self._client("local_lab")
        reg = client.post("/api/rescue-agent/register", json={}).json()
        hb = client.post(
            "/api/rescue-agent/heartbeat",
            json={"session_id": reg["session_id"], "agent_state": "alive"},
        )
        self.assertEqual(hb.status_code, 200)

    def test_sessions_list_shows_rescue_agent(self) -> None:
        client = self._client("local_lab")
        client.post("/api/rescue-agent/register", json={})
        listed = client.get("/api/rescue-agent/sessions")
        self.assertEqual(listed.status_code, 200)
        self.assertGreaterEqual(listed.json().get("count", 0), 1)

    def test_forbidden_apply_execute_install_write_routes_not_present(self) -> None:
        app = FastAPI()
        app.include_router(rescue_agent_router)
        paths = [getattr(r, "path", "") for r in app.routes]
        forbidden = ("/apply", "/execute", "/install", "/write")
        for path in paths:
            low = path.lower()
            for frag in forbidden:
                self.assertNotIn(frag, low)


if __name__ == "__main__":
    unittest.main()
