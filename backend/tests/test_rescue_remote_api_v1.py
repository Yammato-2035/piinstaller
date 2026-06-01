"""API tests for /api/rescue-remote/* (no QEMU, no subprocess on server)."""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

try:
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from rescue_remote.routers import router as rescue_remote_router

    HAS_CLIENT = True
except ImportError:
    HAS_CLIENT = False
    FastAPI = None
    TestClient = None
    rescue_remote_router = None


@unittest.skipUnless(HAS_CLIENT, "fastapi not installed")
class RescueRemoteApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self._td = tempfile.TemporaryDirectory()
        self.repo = Path(self._td.name)
        self._env = patch.dict(
            os.environ,
            {"SETUPHELFER_RESCUE_REMOTE_ENABLED": "true", "PI_INSTALLER_DEV": "1"},
            clear=False,
        )
        self._env.start()
        self._store = patch(
            "rescue_remote.service._store_dir",
            return_value=self.repo / "build/runtime/rescue-remote",
        )
        self._store.start()
        mini = FastAPI()
        mini.include_router(rescue_remote_router)
        self.client = TestClient(mini)
        self.agent_id = "agent_test_001"

    def tearDown(self) -> None:
        self._store.stop()
        self._env.stop()
        self._td.cleanup()

    def _register(self) -> None:
        r = self.client.post(
            "/api/rescue-remote/register",
            json={
                "agent_id": self.agent_id,
                "boot_id": "boot_test",
                "mode": "local_lab",
                "pairing_token": "pair_secret_token_value",
                "security": {"paired": True, "remote_shell": False, "controlled_write": False},
            },
        )
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(r.json()["code"], "RESCUE_REMOTE_AGENT_REGISTERED")
        self.assertNotIn("pair_secret", r.text)

    def test_register_local_lab(self) -> None:
        self._register()

    def test_allowlisted_job_created(self) -> None:
        self._register()
        r = self.client.post(
            "/api/rescue-remote/jobs",
            json={
                "agent_id": self.agent_id,
                "runbook_id": "collect_network_status",
                "mode": "read_only",
            },
        )
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(r.json()["code"], "RESCUE_REMOTE_JOB_CREATED")

    def test_arbitrary_command_plan_blocked(self) -> None:
        self._register()
        r = self.client.post(
            "/api/rescue-remote/jobs",
            json={
                "agent_id": self.agent_id,
                "runbook_id": "collect_boot_logs",
                "command_plan": ["rm", "-rf", "/"],
            },
        )
        self.assertEqual(r.status_code, 422)

    def test_shell_runbook_blocked(self) -> None:
        self._register()
        r = self.client.post(
            "/api/rescue-remote/jobs",
            json={"agent_id": self.agent_id, "runbook_id": "shell", "mode": "read_only"},
        )
        self.assertEqual(r.status_code, 403)
        self.assertEqual(r.json()["detail"]["code"], "RESCUE_REMOTE_JOB_BLOCKED")

    def test_dd_runbook_blocked(self) -> None:
        self._register()
        r = self.client.post(
            "/api/rescue-remote/jobs",
            json={"agent_id": self.agent_id, "runbook_id": "dd"},
        )
        self.assertEqual(r.status_code, 403)

    def test_result_accepted(self) -> None:
        self._register()
        job = self.client.post(
            "/api/rescue-remote/jobs",
            json={"agent_id": self.agent_id, "runbook_id": "collect_boot_logs"},
        ).json()["job"]
        r = self.client.post(
            f"/api/rescue-remote/jobs/{job['job_id']}/result",
            json={
                "agent_id": self.agent_id,
                "status": "success",
                "result": {"stdout_excerpt": "password=hidden", "stderr_excerpt": ""},
            },
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["code"], "RESCUE_REMOTE_JOB_RESULT_ACCEPTED")
        self.assertNotIn("hidden", r.json()["job"]["result"].get("stdout_excerpt", "hidden"))

    def test_disconnect_offline(self) -> None:
        self._register()
        r = self.client.post(
            "/api/rescue-remote/disconnect",
            json={"agent_id": self.agent_id},
        )
        self.assertEqual(r.json()["code"], "RESCUE_REMOTE_AGENT_DISCONNECTED")
        self.assertEqual(r.json()["agent"]["status"], "offline")

    def test_no_shell_route(self) -> None:
        paths = [getattr(r, "path", "") for r in self.client.app.routes]
        for p in paths:
            self.assertNotIn("/shell", p)
            self.assertNotIn("arbitrary", p)


if __name__ == "__main__":
    unittest.main()
