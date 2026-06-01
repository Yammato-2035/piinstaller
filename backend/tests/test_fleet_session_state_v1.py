"""Tests für core.fleet_session_state."""

from __future__ import annotations

import os
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

from core.fleet_session_state import (
    FleetSessionError,
    create_fleet_session,
    detect_stale_sessions,
    finish_fleet_session,
    heartbeat_fleet_session,
    list_fleet_sessions,
)


class FleetSessionStateTests(unittest.TestCase):
    def setUp(self) -> None:
        self._td = tempfile.TemporaryDirectory()
        self.repo = Path(self._td.name)

    def tearDown(self) -> None:
        self._td.cleanup()

    def test_create_session_valid(self) -> None:
        with patch.dict(os.environ, {"SETUPHELFER_FLEET_SESSIONS_ENABLED": "true"}, clear=False):
            r = create_fleet_session(
                {"run_id": "qemu_test_1", "session_type": "local_qemu_smoke"},
                repo_root=self.repo,
            )
        self.assertEqual(r["code"], "FLEET_SESSION_CREATED")
        session = r["session"]
        self.assertEqual(session["run_id"], "qemu_test_1")
        self.assertEqual(session["session_id"], "fleet-qemu_test_1")
        self.assertIn("heartbeat", session)

    def test_heartbeat_updates_age(self) -> None:
        with patch.dict(os.environ, {"SETUPHELFER_FLEET_SESSIONS_ENABLED": "true"}, clear=False):
            created = create_fleet_session({"run_id": "hb_test"}, repo_root=self.repo)
            sid = created["session"]["session_id"]
            from core import fleet_session_state as fss

            session = created["session"]
            past = (datetime.now(tz=timezone.utc) - timedelta(seconds=90)).replace(microsecond=0).isoformat()
            session["heartbeat"]["last_heartbeat_at"] = past
            session["updated_at"] = past
            index = fss._load_latest_index(self.repo)
            index[sid] = session
            fss._save_latest_index(index, self.repo)
            detect_stale_sessions(repo_root=self.repo)
            got = fss.get_fleet_session(sid, repo_root=self.repo)["session"]
        self.assertGreaterEqual(got["heartbeat"]["age_seconds"], 60)
        self.assertIn("heartbeat_delayed", got.get("findings", []))

    def test_finish_terminal_status(self) -> None:
        with patch.dict(os.environ, {"SETUPHELFER_FLEET_SESSIONS_ENABLED": "true"}, clear=False):
            created = create_fleet_session({"run_id": "fin_test"}, repo_root=self.repo)
            sid = created["session"]["session_id"]
            r = finish_fleet_session(sid, "success", repo_root=self.repo)
        self.assertEqual(r["code"], "FLEET_SESSION_FINISHED")
        self.assertEqual(r["session"]["status"], "success")
        self.assertIsNotNone(r["session"]["finished_at"])

    def test_qemu_exit_124_maps_timeout(self) -> None:
        with patch.dict(os.environ, {"SETUPHELFER_FLEET_SESSIONS_ENABLED": "true"}, clear=False):
            created = create_fleet_session({"run_id": "to_test"}, repo_root=self.repo)
            sid = created["session"]["session_id"]
            r = finish_fleet_session(sid, "failed", {"qemu_exit_code": 124}, repo_root=self.repo)
        self.assertEqual(r["session"]["status"], "timeout")
        self.assertIn("qemu_timeout_124", r["session"].get("findings", []))

    def test_stale_heartbeat_timeout_warning(self) -> None:
        with patch.dict(os.environ, {"SETUPHELFER_FLEET_SESSIONS_ENABLED": "true"}, clear=False):
            created = create_fleet_session(
                {"run_id": "stale_test", "status": "booting", "qemu": {"timeout_seconds": 60}},
                repo_root=self.repo,
            )
            sid = created["session"]["session_id"]
            from core import fleet_session_state as fss

            session = created["session"]
            past = (datetime.now(tz=timezone.utc) - timedelta(seconds=200)).replace(microsecond=0).isoformat()
            session["heartbeat"]["last_heartbeat_at"] = past
            session["updated_at"] = past
            index = fss._load_latest_index(self.repo)
            index[sid] = session
            fss._save_latest_index(index, self.repo)
            detect_stale_sessions(repo_root=self.repo)
            got = fss.get_fleet_session(sid, repo_root=self.repo)["session"]
        self.assertIn(got["status"], ("timeout_warning", "timeout"))

    def test_serial_empty_warning_not_auto_fail(self) -> None:
        with patch.dict(os.environ, {"SETUPHELFER_FLEET_SESSIONS_ENABLED": "true"}, clear=False):
            serial_path = self.repo / "qemu-serial.log"
            serial_path.write_text("", encoding="utf-8")
            created = create_fleet_session(
                {
                    "run_id": "serial_test",
                    "status": "booting",
                    "serial": {"path": str(serial_path), "exists": True, "size_bytes": 0},
                },
                repo_root=self.repo,
            )
            from core import fleet_session_state as fss

            session = created["session"]
            past = (datetime.now(tz=timezone.utc) - timedelta(seconds=130)).replace(microsecond=0).isoformat()
            session["started_at"] = past
            sid = session["session_id"]
            index = fss._load_latest_index(self.repo)
            index[sid] = session
            fss._save_latest_index(index, self.repo)
            fss._apply_serial_observation(session)
            fss._persist_session(session, self.repo)
            got = fss.get_fleet_session(sid, repo_root=self.repo)["session"]
        self.assertIn("serial_empty", got.get("findings", []))
        self.assertNotEqual(got["status"], "failed")

    def test_guest_report_missing_visible(self) -> None:
        with patch.dict(os.environ, {"SETUPHELFER_FLEET_SESSIONS_ENABLED": "true"}, clear=False):
            created = create_fleet_session({"run_id": "guest_miss"}, repo_root=self.repo)
            sid = created["session"]["session_id"]
            r = finish_fleet_session(
                sid,
                "timeout",
                {"guest": {"report_seen": False}, "qemu_exit_code": 124},
                repo_root=self.repo,
            )
        self.assertIn("guest_report_missing", r["session"].get("findings", []))

    def test_list_sessions_newest_first(self) -> None:
        with patch.dict(os.environ, {"SETUPHELFER_FLEET_SESSIONS_ENABLED": "true"}, clear=False):
            create_fleet_session({"run_id": "a"}, repo_root=self.repo)
            import time

            time.sleep(0.01)
            create_fleet_session({"run_id": "b"}, repo_root=self.repo)
            listed = list_fleet_sessions(repo_root=self.repo)
        ids = [s["run_id"] for s in listed["sessions"]]
        self.assertEqual(ids[0], "b")

    def test_invalid_payload_blocked(self) -> None:
        with patch.dict(os.environ, {"SETUPHELFER_FLEET_SESSIONS_ENABLED": "true"}, clear=False):
            with self.assertRaises(FleetSessionError) as ctx:
                create_fleet_session({"run_id": "../evil"}, repo_root=self.repo)
        self.assertEqual(ctx.exception.code, "FLEET_SESSION_BLOCKED_INVALID_PAYLOAD")


if __name__ == "__main__":
    unittest.main()
