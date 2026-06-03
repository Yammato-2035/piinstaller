from __future__ import annotations

import json
import os
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

from core.dev_dashboard_backend_health import load_backend_health_snapshot


class DevDashboardBackendHealthTests(unittest.TestCase):
    def test_missing_file_returns_unknown(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "docs" / "evidence" / "dev-dashboard").mkdir(parents=True)
            with patch("core.dev_dashboard_backend_health.dev_dashboard_core._repo_root", return_value=repo):
                out = load_backend_health_snapshot()
        self.assertEqual(out["status"], "unknown")
        self.assertTrue(out["stale"])
        self.assertIsNone(out["current_health"])

    def test_ok_file_not_stale(self) -> None:
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        payload = {
            "task": "developer_backend_healthcheck",
            "generated_at": now,
            "overall_status": "ok",
            "failure_classification": "none",
        }
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            ev = repo / "docs" / "evidence" / "dev-dashboard"
            ev.mkdir(parents=True)
            (ev / "backend_health_latest.json").write_text(json.dumps(payload), encoding="utf-8")
            with patch("core.dev_dashboard_backend_health.dev_dashboard_core._repo_root", return_value=repo):
                out = load_backend_health_snapshot(stale_after_seconds=180)
        self.assertEqual(out["status"], "ok")
        self.assertFalse(out["stale"])
        self.assertEqual(out["current_health"]["overall_status"], "ok")

    def test_old_file_is_stale(self) -> None:
        old = (datetime.now(timezone.utc) - timedelta(hours=2)).strftime("%Y-%m-%dT%H:%M:%SZ")
        payload = {"generated_at": old, "overall_status": "ok"}
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            ev = repo / "docs" / "evidence" / "dev-dashboard"
            ev.mkdir(parents=True)
            (ev / "backend_health_latest.json").write_text(json.dumps(payload), encoding="utf-8")
            with patch("core.dev_dashboard_backend_health.dev_dashboard_core._repo_root", return_value=repo):
                out = load_backend_health_snapshot(stale_after_seconds=180)
        self.assertTrue(out["stale"])
        self.assertEqual(out["status"], "warning")

    def test_backend_down_maps_blocked(self) -> None:
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        payload = {
            "generated_at": now,
            "overall_status": "blocked",
            "failure_classification": "backend_down",
        }
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            ev = repo / "docs" / "evidence" / "dev-dashboard"
            ev.mkdir(parents=True)
            (ev / "backend_health_latest.json").write_text(json.dumps(payload), encoding="utf-8")
            with patch("core.dev_dashboard_backend_health.dev_dashboard_core._repo_root", return_value=repo):
                out = load_backend_health_snapshot()
        self.assertEqual(out["status"], "blocked")

    def test_history_tail_max_20(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            ev = repo / "docs" / "evidence" / "dev-dashboard"
            ev.mkdir(parents=True)
            now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            (ev / "backend_health_latest.json").write_text(
                json.dumps({"generated_at": now, "overall_status": "ok"}),
                encoding="utf-8",
            )
            hist = ev / "backend_health_history.jsonl"
            for i in range(25):
                hist.write_text(
                    (hist.read_text(encoding="utf-8") if hist.exists() else "")
                    + json.dumps({"i": i})
                    + "\n",
                    encoding="utf-8",
                )
            with patch("core.dev_dashboard_backend_health.dev_dashboard_core._repo_root", return_value=repo):
                out = load_backend_health_snapshot(history_limit=20)
        self.assertLessEqual(len(out["history_tail"]), 20)

    def test_api_route_blocked_in_release(self) -> None:
        from fastapi.testclient import TestClient

        import app as app_module

        with patch.dict(os.environ, {"SETUPHELFER_INSTALL_PROFILE": "release"}, clear=False):
            client = TestClient(app_module.app)
            r = client.get("/api/dev-dashboard/backend-health")
        self.assertEqual(r.status_code, 404)
        self.assertEqual(r.json().get("code"), "PROFILE_ROUTE_BLOCKED")


if __name__ == "__main__":
    unittest.main()
