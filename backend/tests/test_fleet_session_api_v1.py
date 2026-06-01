"""Tests für /api/fleet/sessions (keine Control-Routen)."""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

try:
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from fleet.routers import router as fleet_router

    HAS_TEST_CLIENT = True
except ImportError:
    HAS_TEST_CLIENT = False
    FastAPI = None
    TestClient = None
    fleet_router = None

from core.fleet_session_state import FORBIDDEN_ROUTE_FRAGMENTS, assert_no_forbidden_routes


def _mini_client(repo: Path) -> TestClient:
    assert FastAPI is not None and TestClient is not None and fleet_router is not None
    mini = FastAPI()
    mini.include_router(fleet_router)
    return TestClient(mini)


@unittest.skipUnless(HAS_TEST_CLIENT, "fastapi TestClient not installed")
class FleetSessionApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self._td = tempfile.TemporaryDirectory()
        self.repo = Path(self._td.name)
        self._env = patch.dict(
            os.environ,
            {"SETUPHELFER_FLEET_SESSIONS_ENABLED": "true", "PI_INSTALLER_DEV": "1"},
            clear=False,
        )
        self._env.start()
        self._repo_patch = patch("core.fleet_session_state._repo_root", return_value=self.repo)
        self._repo_patch.start()
        self.client = _mini_client(self.repo)

    def tearDown(self) -> None:
        self._repo_patch.stop()
        self._env.stop()
        self._td.cleanup()

    def test_create_and_list(self) -> None:
        r = self.client.post(
            "/api/fleet/sessions",
            json={"run_id": "api_run_1", "session_type": "local_qemu_smoke"},
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["code"], "FLEET_SESSION_CREATED")
        listed = self.client.get("/api/fleet/sessions")
        self.assertEqual(listed.status_code, 200)
        self.assertEqual(listed.json()["code"], "FLEET_SESSION_LIST_OK")
        self.assertGreaterEqual(listed.json()["count"], 1)

    def test_summary_endpoint(self) -> None:
        r = self.client.get("/api/fleet/sessions/summary")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["code"], "FLEET_SESSION_SUMMARY_OK")

    def test_finish_timeout_124(self) -> None:
        created = self.client.post(
            "/api/fleet/sessions",
            json={"run_id": "api_to_124"},
        ).json()
        sid = created["session"]["session_id"]
        fin = self.client.post(
            f"/api/fleet/sessions/{sid}/finish",
            json={"status": "failed", "qemu_exit_code": 124},
        )
        self.assertEqual(fin.status_code, 200)
        self.assertEqual(fin.json()["session"]["status"], "timeout")

    def test_no_control_routes_registered(self) -> None:
        assert fleet_router is not None
        paths = [getattr(r, "path", "") for r in fleet_router.routes]
        for p in paths:
            low = p.lower()
            for frag in FORBIDDEN_ROUTE_FRAGMENTS:
                self.assertNotIn(frag, low, msg=f"forbidden {frag} in {p}")


class FleetSessionApiStaticTests(unittest.TestCase):
    def test_forbidden_route_guard(self) -> None:
        assert_no_forbidden_routes("/sessions")
        with self.assertRaises(Exception):
            assert_no_forbidden_routes("/sessions/1/execute")


if __name__ == "__main__":
    unittest.main()
