from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tests.support.dcc_test_context import isolated_release_dcc_client

from fastapi.testclient import TestClient

from app import app
from core.notification_email import send_email_for_event
from core.notification_events import coerce_notification_event
from core.notification_service import NotificationConfig
from core.notification_settings import classify_smtp_error
from core.notification_state import build_notification_summary, emit_notification_event, list_notification_events


def _config(**overrides: object) -> NotificationConfig:
    base = dict(
        email_enabled=True,
        email_to="alerts@example.com",
        email_from="setuphelfer@example.com",
        smtp_host="smtp.example.com",
        smtp_port=587,
        smtp_username="alerts@example.com",
        smtp_password="secret",
        smtp_security="starttls",
        smtp_starttls=True,
        notify_on_backup_success=True,
        notify_on_backup_failure=True,
    )
    base.update(overrides)
    return NotificationConfig(**base)  # type: ignore[arg-type]


def _event() -> dict[str, object]:
    return coerce_notification_event(
        {
            "severity": "error",
            "area": "rescue",
            "event_type": "rescue_iso_build_failed",
            "title": "Rescue ISO Build fehlgeschlagen",
            "message": "LB_EXIT=127; keine ISO erzeugt",
            "technical_summary": "rsvg fehlt; USB nicht gestartet",
            "evidence_paths": ["docs/evidence/rescue/RESCUE_CONTROLLED_ISO_BUILD_RESULT.md"],
            "dashboard_visible": True,
            "email_requested": True,
            "email_status": "not_configured",
            "email_error": None,
            "acknowledged": False,
        }
    )


def _provider_limit_error() -> RuntimeError:
    return RuntimeError(
        "(554, b'5.7.0 Your message could not be sent. The limit on the number of allowed outgoing messages was exceeded. Try again later.')"
    )


class NotificationEmailProviderLimitTests(unittest.TestCase):
    def test_classify_provider_limit_error(self) -> None:
        cls = classify_smtp_error(str(_provider_limit_error()))
        self.assertEqual(cls, "notification.email.provider_limit_exceeded")

    def test_send_email_provider_limit_sets_failed_and_next_action(self) -> None:
        def _boom(_cfg: NotificationConfig, _msg: object) -> None:
            raise _provider_limit_error()

        with patch("core.notification_email.load_effective_notification_config", return_value=_config()):
            result = send_email_for_event(_event(), smtp_send=_boom)

        self.assertEqual(result["email_status"], "failed")
        self.assertEqual(result["classification"], "notification.email.provider_limit_exceeded")
        self.assertEqual(result["email_error_class"], "notification.email.provider_limit_exceeded")
        self.assertEqual(result["next_action"], "check_smtp_provider_limit_or_wait")
        self.assertEqual(result["email_error"], "554 5.7.0 outgoing message limit exceeded")
        self.assertNotIn("alerts@example.com", str(result.get("email_error") or ""))

    def test_summary_reports_provider_limit_as_yellow(self) -> None:
        def _boom(_cfg: NotificationConfig, _msg: object) -> None:
            raise _provider_limit_error()

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            with (
                patch("core.notification_state.get_install_profile", return_value="repo"),
                patch("core.notification_state._workspace_root", return_value=root),
                patch("core.notification_state.publish_fire_and_forget", return_value=None),
                patch("core.notification_email.load_effective_notification_config", return_value=_config()),
            ):
                emit_notification_event(_event(), smtp_send=_boom)
                summary = build_notification_summary()

        self.assertEqual(summary["status"], "green")
        self.assertEqual(summary["email"]["status"], "provider_limit")
        self.assertEqual(summary["email"]["severity"], "yellow")
        self.assertEqual(summary["email"]["classification"], "notification.email.provider_limit_exceeded")
        self.assertEqual(summary["email"]["next_action"], "check_smtp_provider_limit_or_wait")
        self.assertEqual(summary["last_event"]["email_status"], "failed")

    def test_provider_limit_does_not_trigger_retry_loop(self) -> None:
        calls = {"count": 0}

        def _boom(_cfg: NotificationConfig, _msg: object) -> None:
            calls["count"] += 1
            raise _provider_limit_error()

        with patch("core.notification_email.load_effective_notification_config", return_value=_config()):
            send_email_for_event(_event(), smtp_send=_boom)

        self.assertEqual(calls["count"], 1)

    def test_historical_generic_failure_is_normalized_to_provider_limit(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            notif_dir = root / "docs/evidence/runtime-results/notifications"
            notif_dir.mkdir(parents=True, exist_ok=True)
            (notif_dir / "notification_events.jsonl").write_text(
                '{"event_id":"1","created_at":"2026-05-25T20:09:00+00:00","severity":"error","area":"rescue","event_type":"rescue_iso_build_failed","title":"Rescue ISO Build fehlgeschlagen","message":"msg","technical_summary":"tech","evidence_paths":[],"dashboard_visible":true,"email_requested":true,"email_status":"failed","email_error":"(554, b\'5.7.0 Your message could not be sent. The limit on the number of allowed outgoing messages was exceeded. Try again later.\')","acknowledged":false,"email_error_class":"smtp_send_failed"}\n',
                encoding="utf-8",
            )
            with (
                patch("core.notification_state.get_install_profile", return_value="repo"),
                patch("core.notification_state._workspace_root", return_value=root),
                patch("core.notification_email.load_effective_notification_config", return_value=_config()),
            ):
                events = list_notification_events(limit=10, workspace_root=root, notification_dir=root)
                summary = build_notification_summary(workspace_root=root, notification_dir=root)

        self.assertEqual(events["events"][0]["classification"], "notification.email.provider_limit_exceeded")
        self.assertEqual(events["events"][0]["email_error"], "554 5.7.0 outgoing message limit exceeded")
        self.assertEqual(events["events"][0]["next_action"], "check_smtp_provider_limit_or_wait")
        self.assertEqual(summary["email"]["status"], "provider_limit")
        self.assertEqual(summary["email"]["classification"], "notification.email.provider_limit_exceeded")

    def test_test_email_endpoint_never_reports_sent_on_provider_limit(self) -> None:
        with (
            patch("core.notification_email.load_effective_notification_config", return_value=_config()),
            patch("core.notification_email._smtp_send", side_effect=_provider_limit_error()),
        ):
            with isolated_release_dcc_client() as headers:
                with TestClient(app) as client:
                    res = client.post(
                        "/api/dev-dashboard/notifications/test-email",
                        json={"message": "Setuphelfer provider limit classification smoke test"},
                        headers=headers,
                    )

        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertEqual(body["code"], "DEV_DASHBOARD_NOTIFICATION_EMAIL_PROVIDER_LIMIT")
        self.assertEqual(body["status"], "failed")
        self.assertEqual(body["email_status"], "failed")
        self.assertEqual(body["classification"], "notification.email.provider_limit_exceeded")
        self.assertEqual(body["next_action"], "check_smtp_provider_limit_or_wait")
        self.assertNotEqual(body["status"], "sent")


if __name__ == "__main__":
    unittest.main()
