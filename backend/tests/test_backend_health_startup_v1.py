"""Backend startup availability: health/version must stay fast and lightweight."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

try:
    from fastapi.testclient import TestClient
    from app import app

    _HAS_APP = True
except Exception:
    _HAS_APP = False
    TestClient = None
    app = None


@unittest.skipUnless(_HAS_APP, "FastAPI TestClient oder app nicht verfuegbar")
class TestBackendHealthStartupV1(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app, base_url="http://localhost")

    def test_health_returns_minimal_runtime_payload(self) -> None:
        r = self.client.get("/health")
        self.assertEqual(r.status_code, 200, r.text)
        data = r.json()
        self.assertEqual(data.get("status"), "ok")
        self.assertEqual(data.get("service"), "setuphelfer-backend")
        self.assertIn("timestamp", data)
        self.assertIn("runtime_path", data)
        self.assertIn("version", data)

    def test_health_does_not_require_project_version_loader(self) -> None:
        with patch("core.liveness._read_version_file_fast", return_value=None):
            r = self.client.get("/health")
        self.assertEqual(r.status_code, 200, r.text)
        data = r.json()
        self.assertEqual(data.get("status"), "ok")
        self.assertEqual(data.get("version"), "unknown")

    def test_version_omits_git_commit_unless_opt_in(self) -> None:
        with patch("core.liveness._git_head_optional", return_value=None):
            r = self.client.get("/api/version")
        self.assertEqual(r.status_code, 200, r.text)
        self.assertNotIn("git_commit", r.json())

    def test_version_endpoint_stays_available_without_dashboard_routes(self) -> None:
        with patch("core.dev_dashboard.build_dashboard_status", side_effect=RuntimeError("must_not_be_called")):
            r = self.client.get("/api/version")
        self.assertEqual(r.status_code, 200, r.text)
        data = r.json()
        self.assertEqual(data.get("status"), "success")
        self.assertIn("project_version", data)

