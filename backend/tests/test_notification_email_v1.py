from __future__ import annotations

import json
import unittest

from core.notification_email import send_email_for_event
from core.notification_events import coerce_notification_event
from core.notification_service import NotificationConfig


def _config(**overrides: object) -> NotificationConfig:
    base = dict(
        email_enabled=True,
        email_to="user@example.com",
        email_from="setuphelfer@example.com",
        smtp_host="smtp.example.com",
        smtp_port=587,
        smtp_username="user@example.com",
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


class NotificationEmailTests(unittest.TestCase):
    def test_missing_smtp_config_results_not_configured(self) -> None:
        from unittest.mock import patch

        with patch("core.notification_email.load_effective_notification_config", return_value=_config(smtp_host="", smtp_password="")):
            result = send_email_for_event(_event())
        self.assertEqual(result["email_status"], "not_configured")

    def test_smtp_failure_redacts_secret(self) -> None:
        from unittest.mock import patch

        def _boom(_cfg: NotificationConfig, _msg: object) -> None:
            raise RuntimeError("auth failed password=secret token=abc")

        with patch("core.notification_email.load_effective_notification_config", return_value=_config()):
            result = send_email_for_event(_event(), smtp_send=_boom)
        self.assertEqual(result["email_status"], "failed")
        self.assertIn("[redacted]", result["email_error"] or "")
        self.assertNotIn("secret", result["email_error"] or "")
        self.assertNotIn("abc", result["email_error"] or "")

    def test_successful_mock_send_returns_sent(self) -> None:
        from unittest.mock import patch

        def _ok(_cfg: NotificationConfig, _msg: object) -> None:
            return None

        with patch("core.notification_email.load_effective_notification_config", return_value=_config()):
            result = send_email_for_event(_event(), smtp_send=_ok)
        self.assertEqual(result["email_status"], "sent")

    def test_password_not_present_in_result(self) -> None:
        from unittest.mock import patch

        def _boom(_cfg: NotificationConfig, _msg: object) -> None:
            raise RuntimeError("smtp password=secret")

        with patch("core.notification_email.load_effective_notification_config", return_value=_config()):
            result = send_email_for_event(_event(), smtp_send=_boom)
        blob = json.dumps(result, ensure_ascii=False)
        self.assertNotIn("secret", blob)

    def test_recipient_comes_from_config(self) -> None:
        from unittest.mock import patch

        seen_to: list[str] = []

        def _capture(_cfg: NotificationConfig, msg: object) -> None:
            seen_to.append(str(getattr(msg, "__getitem__")("To")))

        cfg = _config(email_to="alerts@example.com")
        with patch("core.notification_email.load_effective_notification_config", return_value=cfg):
            result = send_email_for_event(_event(), smtp_send=_capture)
        self.assertEqual(result["email_status"], "sent")
        self.assertEqual(seen_to, ["alerts@example.com"])
        self.assertEqual(result["email_recipient_masked"], "a***@example.com")


if __name__ == "__main__":
    unittest.main()
