"""Heartbeat-Payload-Vertrag für Fleet Sessions (Phase 1)."""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from core.fleet_session_state import (
    FleetSessionError,
    create_fleet_session,
    finish_fleet_session,
    heartbeat_fleet_session,
)


class FleetSessionHeartbeatPayloadTests(unittest.TestCase):
    def setUp(self) -> None:
        self._td = tempfile.TemporaryDirectory()
        self.repo = Path(self._td.name)
        self._env = patch.dict(os.environ, {"SETUPHELFER_FLEET_SESSIONS_ENABLED": "true"}, clear=False)
        self._env.start()

    def tearDown(self) -> None:
        self._env.stop()
        self._td.cleanup()

    def _create(self, run_id: str = "hb-contract") -> str:
        created = create_fleet_session({"run_id": run_id}, repo_root=self.repo)
        return str(created["session"]["session_id"])

    def test_heartbeat_without_status_is_valid(self) -> None:
        sid = self._create("hb-no-status")
        result = heartbeat_fleet_session(sid, {"heartbeat": {"healthy": True}}, repo_root=self.repo)
        self.assertEqual(result["code"], "FLEET_SESSION_HEARTBEAT_OK")

    def test_heartbeat_with_allowed_status_is_valid(self) -> None:
        sid = self._create("hb-allowed-status")
        result = heartbeat_fleet_session(sid, {"status": "serial_active"}, repo_root=self.repo)
        self.assertEqual(result["code"], "FLEET_SESSION_HEARTBEAT_OK")
        self.assertEqual(result["session"]["status"], "serial_active")

    def test_heartbeat_status_running_is_ignored_and_maps_to_alive(self) -> None:
        sid = self._create("hb-running")
        result = heartbeat_fleet_session(sid, {"status": "running"}, repo_root=self.repo)
        self.assertEqual(result["code"], "FLEET_SESSION_HEARTBEAT_OK")
        self.assertEqual(result["session"]["status"], "starting")
        self.assertEqual(result["session"]["agent_state"], "alive")

    def test_heartbeat_with_agent_state_alive_is_valid(self) -> None:
        sid = self._create("hb-agent-state")
        result = heartbeat_fleet_session(sid, {"agent_state": "alive"}, repo_root=self.repo)
        self.assertEqual(result["code"], "FLEET_SESSION_HEARTBEAT_OK")
        self.assertEqual(result["session"]["agent_state"], "alive")

    def test_create_heartbeat_finish_flow_works(self) -> None:
        sid = self._create("hb-flow")
        heartbeat_fleet_session(sid, {"agent_state": "checking"}, repo_root=self.repo)
        finished = finish_fleet_session(sid, "success", {"guest": {"report_seen": False}}, repo_root=self.repo)
        self.assertEqual(finished["session"]["status"], "success")
        self.assertIsNone(finished["session"]["guest"].get("guest_node_id"))

    def test_heartbeat_with_invalid_agent_state_is_rejected(self) -> None:
        sid = self._create("hb-invalid-agent")
        with self.assertRaises(FleetSessionError):
            heartbeat_fleet_session(sid, {"agent_state": "running"}, repo_root=self.repo)


if __name__ == "__main__":
    unittest.main()
