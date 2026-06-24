from __future__ import annotations

import json
import os
import stat
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

from core.dev_dashboard_backend_health import (
    build_health_evidence_search_paths,
    load_backend_health_snapshot,
)


class DevDashboardBackendHealthTests(unittest.TestCase):
    def test_missing_file_returns_unknown_with_searched_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "docs" / "evidence" / "dev-dashboard").mkdir(parents=True)
            with patch(
                "core.dev_dashboard_backend_health.build_health_evidence_search_paths",
                return_value=[repo / "docs/evidence/dev-dashboard/backend_health_latest.json"],
            ):
                out = load_backend_health_snapshot()
        self.assertEqual(out["status"], "unknown")
        self.assertTrue(out["stale"])
        self.assertIsNone(out["current_health"])
        self.assertGreaterEqual(len(out.get("searched_paths") or []), 1)

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
            latest = ev / "backend_health_latest.json"
            latest.write_text(json.dumps(payload), encoding="utf-8")
            with patch(
                "core.dev_dashboard_backend_health.build_health_evidence_search_paths",
                return_value=[latest],
            ):
                out = load_backend_health_snapshot(stale_after_seconds=180)
        self.assertEqual(out["status"], "ok")
        self.assertFalse(out["stale"])
        self.assertEqual(str(out["source_path"]), str(latest))

    def test_old_file_is_stale(self) -> None:
        old = (datetime.now(timezone.utc) - timedelta(hours=2)).strftime("%Y-%m-%dT%H:%M:%SZ")
        payload = {"generated_at": old, "overall_status": "ok"}
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            ev = repo / "docs" / "evidence" / "dev-dashboard"
            ev.mkdir(parents=True)
            latest = ev / "backend_health_latest.json"
            latest.write_text(json.dumps(payload), encoding="utf-8")
            with patch(
                "core.dev_dashboard_backend_health.build_health_evidence_search_paths",
                return_value=[latest],
            ):
                out = load_backend_health_snapshot(stale_after_seconds=180)
        self.assertTrue(out["stale"])
        self.assertEqual(out["status"], "warning")

    def test_opt_path_preferred_when_backend_under_opt(self) -> None:
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        with tempfile.TemporaryDirectory() as tmp:
            opt = Path(tmp) / "opt"
            ws = Path(tmp) / "ws"
            for root in (opt, ws):
                (root / "docs/evidence/dev-dashboard").mkdir(parents=True)
            (opt / "docs/evidence/dev-dashboard/backend_health_latest.json").write_text(
                json.dumps({"generated_at": now, "overall_status": "ok"}),
                encoding="utf-8",
            )
            (ws / "docs/evidence/dev-dashboard/backend_health_latest.json").write_text(
                json.dumps({"generated_at": now, "overall_status": "warning"}),
                encoding="utf-8",
            )
            opt_latest = opt / "docs/evidence/dev-dashboard/backend_health_latest.json"
            ws_latest = ws / "docs/evidence/dev-dashboard/backend_health_latest.json"
            with patch(
                "core.dev_dashboard_backend_health._OPT_INSTALL_ROOT",
                opt,
            ), patch(
                "core.dev_dashboard_backend_health.__file__",
                str(opt / "backend/core/dev_dashboard_backend_health.py"),
            ), patch(
                "core.dev_dashboard_backend_health.build_health_evidence_search_paths",
                return_value=[opt_latest, ws_latest],
            ):
                out = load_backend_health_snapshot(stale_after_seconds=3600)
        self.assertEqual(out["status"], "ok")
        self.assertEqual(out["current_health"]["overall_status"], "ok")

    def test_permission_denied_surfaces_message(self) -> None:
        latest = Path("/tmp/backend_health_test_denied.json")
        with patch(
            "core.dev_dashboard_backend_health.build_health_evidence_search_paths",
            return_value=[latest],
        ), patch(
            "core.dev_dashboard_backend_health._probe_evidence_file",
            return_value=("permission_denied", None),
        ):
            out = load_backend_health_snapshot()
        self.assertEqual(out["status"], "unknown")
        self.assertIn("permission", (out.get("message") or "").lower())
        self.assertEqual((out.get("searched_paths") or [{}])[0].get("state"), "permission_denied")

    def test_history_tail_max_20(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ev = Path(tmp)
            now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            latest = ev / "backend_health_latest.json"
            latest.write_text(
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
            with patch(
                "core.dev_dashboard_backend_health.build_health_evidence_search_paths",
                return_value=[latest],
            ):
                out = load_backend_health_snapshot(history_limit=20)
        self.assertLessEqual(len(out["history_tail"]), 20)

    def test_env_evidence_dir_override(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            custom = Path(tmp) / "custom_evidence"
            custom.mkdir()
            latest = custom / "backend_health_latest.json"
            latest.write_text(
                json.dumps(
                    {
                        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                        "overall_status": "ok",
                    }
                ),
                encoding="utf-8",
            )
            with patch.dict(os.environ, {"SETUPHELFER_HEALTH_EVIDENCE_DIR": str(custom)}, clear=False):
                paths = build_health_evidence_search_paths()
            self.assertEqual(paths[0], latest)

    def test_api_route_blocked_in_release(self) -> None:
        from fastapi.testclient import TestClient

        import app as app_module

        from tests.support.dcc_test_context import isolated_release_no_dcc

        with isolated_release_no_dcc():
            client = TestClient(app_module.app)
            r = client.get("/api/dev-dashboard/backend-health")
        self.assertEqual(r.status_code, 404)
        self.assertEqual(r.json().get("code"), "PROFILE_ROUTE_BLOCKED")


if __name__ == "__main__":
    unittest.main()
