from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tests.support.dcc_test_context import isolated_release_dcc_client

try:
    from fastapi.testclient import TestClient
    from app import app
    from core.notification_service import NotificationConfig

    _HAS_APP = True
except Exception:
    TestClient = None
    app = None
    NotificationConfig = None
    _HAS_APP = False


def _smtp_cfg() -> NotificationConfig:
    assert NotificationConfig is not None
    return NotificationConfig(
        email_enabled=True,
        email_to="",
        email_from="",
        smtp_host="",
        smtp_port=587,
        smtp_username="",
        smtp_password="",
        smtp_security="starttls",
        smtp_starttls=True,
        notify_on_backup_success=True,
        notify_on_backup_failure=True,
    )


@unittest.skipUnless(_HAS_APP, "FastAPI TestClient oder app nicht verfuegbar")
class NotificationDashboardApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self._dcc_ctx = isolated_release_dcc_client()
        self._dcc_headers = self._dcc_ctx.__enter__()

    def tearDown(self) -> None:
        self._dcc_ctx.__exit__(None, None, None)
    def test_status_endpoint_responds_without_persistence_file(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            with (
                patch("core.notification_state._workspace_root", return_value=root),
                patch("core.notification_state.publish_fire_and_forget", return_value=None),
                patch("core.notification_email.load_effective_notification_config", return_value=_smtp_cfg()),
            ):
                with TestClient(app) as client:
                    res = client.get("/api/dev-dashboard/notifications/status", headers=self._dcc_headers)
            self.assertEqual(res.status_code, 200)
            body = res.json()
            self.assertEqual(body["code"], "DEV_DASHBOARD_NOTIFICATIONS_STATUS_OK")
            self.assertIn(body["status"], ("gray", "yellow"))

    def test_events_endpoint_responds(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            with (
                patch("core.notification_state._workspace_root", return_value=root),
                patch("core.notification_state.publish_fire_and_forget", return_value=None),
                patch("core.notification_email.load_effective_notification_config", return_value=_smtp_cfg()),
            ):
                with TestClient(app) as client:
                    res = client.get("/api/dev-dashboard/notifications/events", headers=self._dcc_headers)
            self.assertEqual(res.status_code, 200)
            body = res.json()
            self.assertEqual(body["code"], "DEV_DASHBOARD_NOTIFICATIONS_EVENTS_OK")
            self.assertIn("events", body)

    def test_test_dashboard_creates_event(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            with (
                patch("core.notification_state._workspace_root", return_value=root),
                patch("core.notification_state.publish_fire_and_forget", return_value=None),
                patch("core.notification_email.load_effective_notification_config", return_value=_smtp_cfg()),
            ):
                with TestClient(app) as client:
                    res = client.post(
                        "/api/dev-dashboard/notifications/test-dashboard",
                        json={"severity": "warning", "area": "dev_dashboard", "message": "Dashboard notification smoke test"},
                        headers=self._dcc_headers,
                    )
                    events = client.get("/api/dev-dashboard/notifications/events", headers=self._dcc_headers)
            self.assertEqual(res.status_code, 200)
            body = res.json()
            self.assertEqual(body["code"], "DEV_DASHBOARD_NOTIFICATION_TEST_EVENT_CREATED")
            self.assertEqual(body["event"]["event_type"], "notification_test_dashboard")
            events_body = events.json()
            self.assertEqual(events_body["event_count"], 1)

    def test_dashboard_test_event_does_not_require_email(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            with (
                patch("core.notification_state._workspace_root", return_value=root),
                patch("core.notification_state.publish_fire_and_forget", return_value=None),
                patch("core.notification_email.load_effective_notification_config", return_value=_smtp_cfg()),
            ):
                with TestClient(app) as client:
                    res = client.post("/api/dev-dashboard/notifications/test-dashboard", json={}, headers=self._dcc_headers)
            self.assertEqual(res.status_code, 200)
            body = res.json()
            self.assertEqual(body["event"]["email_status"], "disabled")

    def test_missing_persistence_file_does_not_crash_events_endpoint(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            with (
                patch("core.notification_state._workspace_root", return_value=root),
                patch("core.notification_state.publish_fire_and_forget", return_value=None),
                patch("core.notification_email.load_effective_notification_config", return_value=_smtp_cfg()),
            ):
                with TestClient(app) as client:
                    res = client.get("/api/dev-dashboard/notifications/events", headers=self._dcc_headers)
            self.assertEqual(res.status_code, 200)
            self.assertEqual(res.json()["events"], [])


if __name__ == "__main__":
    unittest.main()
