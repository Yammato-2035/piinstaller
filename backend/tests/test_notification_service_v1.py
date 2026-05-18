"""Backup success email notifications (mocked SMTP, no real mail)."""

from __future__ import annotations

import os
import unittest
from email.message import EmailMessage
from unittest import mock

from core.notification_service import (
    EmailNotificationResult,
    NotificationConfig,
    _smtp_send_default,
    build_backup_success_body,
    build_backup_success_subject,
    load_notification_config,
    mask_email_address,
    maybe_send_backup_success_email,
    normalize_smtp_security,
    notification_status_fields,
    send_backup_success_email,
    should_notify_backup_success,
)


def _full_config(**overrides: object) -> NotificationConfig:
    base = dict(
        email_enabled=True,
        email_to="user@example.com",
        email_from="backup@example.com",
        smtp_host="smtp.example.com",
        smtp_port=587,
        smtp_username="user",
        smtp_password="secret",
        smtp_security="starttls",
        smtp_starttls=True,
        notify_on_backup_success=True,
        notify_on_backup_failure=False,
    )
    base.update(overrides)
    return NotificationConfig(**base)  # type: ignore[arg-type]


class TestNotificationServiceV1(unittest.TestCase):
    def test_disabled_skipped(self) -> None:
        cfg = _full_config(email_enabled=False)
        r = maybe_send_backup_success_email(
            job_id="j1",
            status_code="backup.success",
            config=cfg,
        )
        self.assertEqual(r.status, "skipped_disabled")

    def test_missing_smtp_skipped_not_configured(self) -> None:
        cfg = _full_config(smtp_host="")
        r = maybe_send_backup_success_email(
            job_id="j1",
            status_code="backup.success",
            config=cfg,
        )
        self.assertEqual(r.status, "skipped_not_configured")

    def test_subject_contains_job_id(self) -> None:
        self.assertIn("abc123", build_backup_success_subject("abc123"))

    def test_body_contains_archive_and_hash(self) -> None:
        body = build_backup_success_body(
            job_id="j1",
            status_code="backup.success",
            archive_path="/media/x/a.tar.gz",
            manifest_hash="sha256:deadbeef",
            verify_deep_ok=True,
        )
        self.assertIn("j1", body)
        self.assertIn("/media/x/a.tar.gz", body)
        self.assertIn("sha256:deadbeef", body)
        self.assertIn("Verify Deep: ok", body)

    def test_success_with_warnings_body_hint(self) -> None:
        body = build_backup_success_body(
            job_id="j2",
            status_code="backup.success_with_warnings",
            warning_status="completed_with_warnings",
            warnings_summary="tar_volatile_warnings",
        )
        self.assertIn("completed_with_warnings", body)
        self.assertIn("tar_volatile_warnings", body)

    def test_failed_code_not_notified(self) -> None:
        cfg = _full_config()
        self.assertFalse(
            should_notify_backup_success(
                code="backup.failed",
                verify_deep_ok=None,
                backup_integrity_status=None,
                config=cfg,
            )
        )
        r = maybe_send_backup_success_email(job_id="j", status_code="backup.failed", config=cfg)
        self.assertEqual(r.status, "skipped_not_applicable")

    def test_warning_not_promoted_not_notified(self) -> None:
        cfg = _full_config()
        r = maybe_send_backup_success_email(
            job_id="j",
            status_code="backup.warning_not_promoted",
            config=cfg,
        )
        self.assertEqual(r.status, "skipped_not_applicable")

    def test_verify_deep_false_blocks_with_warnings(self) -> None:
        cfg = _full_config()
        self.assertFalse(
            should_notify_backup_success(
                code="backup.success_with_warnings",
                verify_deep_ok=False,
                backup_integrity_status="verified",
                config=cfg,
            )
        )

    def test_smtp_failure_does_not_raise(self) -> None:
        cfg = _full_config()

        def boom(_cfg: NotificationConfig, _msg: object) -> None:
            raise smtplib.SMTPException("auth failed password=secret")

        import smtplib

        r = send_backup_success_email(
            job_id="j3",
            status_code="backup.success",
            config=cfg,
            smtp_send=boom,
        )
        self.assertEqual(r.status, "failed")
        self.assertNotIn("secret", r.error or "")

    def test_mask_email(self) -> None:
        self.assertEqual(mask_email_address("volker.glienke@googlemail.com"), "v***@googlemail.com")

    def test_status_fields_no_password(self) -> None:
        cfg = _full_config()
        fields = notification_status_fields(cfg, EmailNotificationResult(status="sent", recipient_masked="v***@example.com"))
        self.assertTrue(fields["notification_email_sent"])
        blob = str(fields)
        self.assertNotIn("secret", blob)

    def test_normalize_port_465_defaults_ssl(self) -> None:
        self.assertEqual(normalize_smtp_security(None, port=465, smtp_starttls=True), "ssl")

    def test_normalize_starttls_flag(self) -> None:
        self.assertEqual(normalize_smtp_security(None, port=587, smtp_starttls=True), "starttls")
        self.assertEqual(normalize_smtp_security(None, port=587, smtp_starttls=False), "none")

    def test_smtp_ssl_uses_smtp_ssl_class(self) -> None:
        cfg = _full_config(smtp_security="ssl", smtp_port=465, smtp_starttls=False)
        msg = EmailMessage()
        msg["Subject"] = "t"
        msg["From"] = cfg.email_from
        msg["To"] = cfg.email_to
        msg.set_content("body")
        with mock.patch("smtplib.SMTP_SSL") as mock_ssl, mock.patch("smtplib.SMTP") as mock_plain:
            mock_ssl.return_value.__enter__.return_value = mock.Mock()
            _smtp_send_default(cfg, msg)
            mock_ssl.assert_called_once()
            mock_plain.assert_not_called()

    def test_smtp_starttls_uses_smtp_and_starttls(self) -> None:
        cfg = _full_config(smtp_security="starttls", smtp_port=587)
        msg = EmailMessage()
        msg["Subject"] = "t"
        msg["From"] = cfg.email_from
        msg["To"] = cfg.email_to
        msg.set_content("body")
        with mock.patch("smtplib.SMTP_SSL") as mock_ssl, mock.patch("smtplib.SMTP") as mock_plain:
            smtp = mock_plain.return_value.__enter__.return_value
            _smtp_send_default(cfg, msg)
            mock_plain.assert_called_once()
            mock_ssl.assert_not_called()
            smtp.starttls.assert_called_once()

    def test_env_example_has_empty_placeholders(self) -> None:
        root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        path = os.path.join(root, ".env.example")
        with open(path, encoding="utf-8") as f:
            text = f.read()
        self.assertIn("SETUPHELFER_NOTIFY_EMAIL_TO=", text)
        self.assertIn("SETUPHELFER_NOTIFY_SMTP_SECURITY=", text)
        self.assertNotIn("googlemail.com", text)
        self.assertNotIn("SETUPHELFER_NOTIFY_SMTP_PASSWORD=secret", text)


if __name__ == "__main__":
    unittest.main()
