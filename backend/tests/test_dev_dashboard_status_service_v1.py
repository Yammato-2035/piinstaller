from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from core.dev_dashboard_status_service import build_dcc_profile_block_response  # noqa: E402

from tests.support.dcc_test_context import (  # noqa: E402
    RELEASE_DCC_HEADERS,
    isolated_release_dcc_client,
    isolated_release_no_dcc,
)

try:
    from fastapi.testclient import TestClient

    from app import app as fastapi_app

    _HAS_TC = True
except Exception:
    TestClient = None  # type: ignore[misc, assignment]
    fastapi_app = None  # type: ignore[misc, assignment]
    _HAS_TC = False


class DevDashboardStatusServiceTests(unittest.TestCase):
    def test_release_without_token_blocked(self) -> None:
        with isolated_release_no_dcc():
            body = build_dcc_profile_block_response()
        self.assertIsNotNone(body)
        assert body is not None
        self.assertEqual(body["code"], "PROFILE_ROUTE_BLOCKED")
        self.assertNotIn("required_profile", body)

    def test_release_with_valid_developer_capability_not_blocked(self) -> None:
        with patch.dict(
            os.environ,
            {
                "SETUPHELFER_INSTALL_PROFILE": "release",
                "DCC_DEVELOPER_ENABLED": "1",
                "DCC_DEVELOPER_TOKEN": "release-dev-token",
            },
            clear=False,
        ):
            body = build_dcc_profile_block_response(
                request_headers={"X-Setuphelfer-Developer-Token": "release-dev-token"},
            )
        self.assertIsNone(body)

    def test_local_lab_without_token_blocked_capability_required(self) -> None:
        with patch.dict(
            os.environ,
            {"SETUPHELFER_INSTALL_PROFILE": "local_lab", "DCC_DEVELOPER_TOKEN": "lab-token"},
            clear=False,
        ):
            body = build_dcc_profile_block_response()
        self.assertIsNotNone(body)
        assert body is not None
        self.assertEqual(body["code"], "DEVELOPER_CAPABILITY_REQUIRED")

    def test_local_lab_with_token_not_blocked(self) -> None:
        with patch.dict(
            os.environ,
            {"SETUPHELFER_INSTALL_PROFILE": "local_lab", "DCC_DEVELOPER_TOKEN": "lab-token"},
            clear=False,
        ):
            body = build_dcc_profile_block_response(
                request_headers={"Authorization": "Bearer lab-token"},
            )
        self.assertIsNone(body)

    def test_block_response_never_contains_token(self) -> None:
        with patch.dict(
            os.environ,
            {"SETUPHELFER_INSTALL_PROFILE": "release", "DCC_DEVELOPER_TOKEN": "hidden-secret"},
            clear=False,
        ):
            body = build_dcc_profile_block_response()
        dumped = str(body)
        self.assertNotIn("hidden-secret", dumped)


@unittest.skipUnless(_HAS_TC, "FastAPI TestClient nicht verfügbar")
class DevDashboardStatusHttpTests(unittest.TestCase):
    def test_release_status_blocked_without_token(self) -> None:
        with isolated_release_no_dcc():
            client = TestClient(fastapi_app, base_url="http://localhost")
            r = client.get("/api/dev-dashboard/status")
            self.assertEqual(r.status_code, 404)
            self.assertEqual(r.json().get("code"), "PROFILE_ROUTE_BLOCKED")
            self.assertNotIn("release-dev-token", r.text)

    def test_release_status_200_with_valid_developer_token(self) -> None:
        with patch.dict(
            os.environ,
            {
                "SETUPHELFER_INSTALL_PROFILE": "release",
                "DCC_DEVELOPER_ENABLED": "1",
                "DCC_DEVELOPER_TOKEN": "release-dev-token",
            },
            clear=False,
        ):
            client = TestClient(fastapi_app, base_url="http://localhost")
            r = client.get(
                "/api/dev-dashboard/status",
                headers={"X-Setuphelfer-Developer-Token": "release-dev-token"},
            )
            self.assertEqual(r.status_code, 200, r.text)
            data = r.json()
            self.assertIn(data.get("status"), ("success", "degraded"))
            self.assertNotIn("release-dev-token", r.text)
            self.assertNotEqual(data.get("code"), "PROFILE_ROUTE_BLOCKED")

    def test_capability_status_visible_with_token_no_secret_leak(self) -> None:
        with patch.dict(
            os.environ,
            {
                "SETUPHELFER_INSTALL_PROFILE": "release",
                "DCC_DEVELOPER_ENABLED": "1",
                "DCC_DEVELOPER_TOKEN": "release-dev-token",
            },
            clear=False,
        ):
            client = TestClient(fastapi_app, base_url="http://localhost")
            r = client.get(
                "/api/dev-dashboard/capability-status",
                headers={"X-Setuphelfer-Developer-Token": "release-dev-token"},
            )
            self.assertEqual(r.status_code, 200)
            body = r.json()
            self.assertTrue(body.get("dcc_visible"))
            self.assertEqual(body.get("reason"), "DEVELOPER_CAPABILITY_VALID")
            self.assertNotIn("release-dev-token", r.text)

    def test_telemetry_health_200_independent_of_dcc_token(self) -> None:
        with patch.dict(
            os.environ,
            {
                "SETUPHELFER_INSTALL_PROFILE": "release",
                "RESCUE_TELEMETRY_INGEST_ENABLED": "0",
            },
            clear=False,
        ):
            client = TestClient(fastapi_app, base_url="http://localhost")
            r = client.get("/api/rescue/telemetry/health")
            self.assertEqual(r.status_code, 200)
            self.assertTrue(r.json().get("profile_gate_independent"))


if __name__ == "__main__":
    unittest.main()
