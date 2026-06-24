"""Read-only manual command run evidence for dev dashboard."""

import json
import sys
import tempfile
import unittest
from pathlib import Path

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from core.dev_dashboard_manual_command_runs import build_manual_command_runs_index  # noqa: E402

from tests.support.dcc_test_context import isolated_release_dcc_client  # noqa: E402

try:
    from fastapi.testclient import TestClient
    from app import app

    _HAS_APP = True
except Exception:
    _HAS_APP = False
    TestClient = None
    app = None


class TestManualCommandRunsLoader(unittest.TestCase):
    def test_missing_dir_returns_empty_not_crash(self):
        with tempfile.TemporaryDirectory() as td:
            out = build_manual_command_runs_index(repo_root=Path(td))
        self.assertEqual(out.get("status"), "success")
        self.assertEqual(out.get("runs"), [])
        self.assertIn("manual_command_runs_dir_missing", out.get("warnings") or [])

    def test_valid_json_loaded(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td) / "docs/evidence/dev-dashboard/manual_command_runs"
            base.mkdir(parents=True)
            payload = {
                "run_id": "t1",
                "created_at": "2026-05-27T12:00:00Z",
                "commands": [
                    {
                        "command": "echo ok",
                        "purpose": "test",
                        "exit_code": 0,
                        "safety_class": "read_only",
                    }
                ],
                "summary": {"status": "ok", "reason": "test"},
            }
            (base / "t1.json").write_text(json.dumps(payload), encoding="utf-8")
            out = build_manual_command_runs_index(repo_root=Path(td))
        self.assertEqual(len(out.get("runs") or []), 1)
        self.assertEqual((out["runs"][0]).get("run_id"), "t1")

    def test_invalid_json_adds_warning_not_crash(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td) / "docs/evidence/dev-dashboard/manual_command_runs"
            base.mkdir(parents=True)
            (base / "bad.json").write_text("{not json", encoding="utf-8")
            (base / "good.json").write_text(
                json.dumps(
                    {
                        "run_id": "g",
                        "created_at": "2026-05-27T12:00:00Z",
                        "commands": [],
                        "summary": {"status": "ok", "reason": ""},
                    }
                ),
                encoding="utf-8",
            )
            out = build_manual_command_runs_index(repo_root=Path(td))
        self.assertEqual(len(out.get("runs") or []), 1)
        self.assertTrue(any("json_error" in w for w in out.get("warnings") or []))

    def test_forbidden_sets_blocked_overall(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td) / "docs/evidence/dev-dashboard/manual_command_runs"
            base.mkdir(parents=True)
            (base / "f.json").write_text(
                json.dumps(
                    {
                        "run_id": "f",
                        "created_at": "2026-05-27T12:00:00Z",
                        "commands": [
                            {"command": "dd", "safety_class": "forbidden", "exit_code": 1}
                        ],
                        "summary": {"status": "ok", "reason": ""},
                    }
                ),
                encoding="utf-8",
            )
            out = build_manual_command_runs_index(repo_root=Path(td))
        self.assertEqual(out.get("overall_status"), "blocked")
        self.assertTrue(out["runs"][0].get("has_forbidden_commands"))


@unittest.skipUnless(_HAS_APP, "FastAPI TestClient oder app nicht verfuegbar")
class TestManualCommandRunsApi(unittest.TestCase):
    def setUp(self):
        self._dcc_ctx = isolated_release_dcc_client()
        self._dcc_headers = self._dcc_ctx.__enter__()
        self.client = TestClient(app, base_url="http://localhost")

    def tearDown(self):
        self._dcc_ctx.__exit__(None, None, None)

    def test_get_manual_command_runs_read_only(self):
        r = self.client.get("/api/dev-dashboard/manual-command-runs", headers=self._dcc_headers)
        self.assertEqual(r.status_code, 200, r.text)
        data = r.json()
        self.assertEqual(data.get("status"), "success")
        self.assertFalse(data.get("execution_allowed"))
        self.assertTrue(data.get("read_only"))

    def test_no_post_manual_command_runs_route(self):
        r = self.client.post("/api/dev-dashboard/manual-command-runs", json={})
        self.assertIn(r.status_code, (404, 405))


if __name__ == "__main__":
    unittest.main()
