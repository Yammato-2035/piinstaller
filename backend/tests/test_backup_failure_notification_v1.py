"""Failure notification: enabled sends, disabled skips, no secrets."""

from __future__ import annotations

import unittest
from unittest import mock

from core.notification_service import (
    EmailNotificationResult,
    NotificationConfig,
    build_backup_failure_body,
    maybe_send_backup_failure_email,
    should_notify_backup_failure,
)


class TestBackupFailureNotificationV1(unittest.TestCase):
    def test_should_notify_when_enabled_and_error(self) -> None:
        cfg = NotificationConfig(
            email_enabled=True,
            email_to="a@b.com",
            email_from="from@b.com",
            smtp_host="smtp.test",
            smtp_port=587,
            smtp_username="u",
            smtp_password="p",
            smtp_security="starttls",
            smtp_starttls=True,
            notify_on_backup_success=True,
            notify_on_backup_failure=True,
        )
        self.assertTrue(should_notify_backup_failure(status="error", code="backup.failed", config=cfg))

    def test_skipped_when_disabled(self) -> None:
        cfg = NotificationConfig(
            email_enabled=True,
            email_to="a@b.com",
            email_from="from@b.com",
            smtp_host="smtp.test",
            smtp_port=587,
            smtp_username="u",
            smtp_password="p",
            smtp_security="starttls",
            smtp_starttls=True,
            notify_on_backup_success=True,
            notify_on_backup_failure=False,
        )
        r = maybe_send_backup_failure_email(
            job_id="j1",
            status="error",
            status_code="backup.failed",
            config=cfg,
        )
        self.assertEqual(r.status, "skipped_not_applicable")

    def test_failure_body_contains_job_and_no_archive(self) -> None:
        body = build_backup_failure_body(
            job_id="2a15912d1b52",
            status_code="backup.failed",
            abort_reason="tar_failed",
            tar_warning_classification="TAR_CRITICAL_WARNING",
            final_archive_exists=False,
            error_excerpt="Datei hat sich beim Lesen geändert",
        )
        self.assertIn("2a15912d1b52", body)
        self.assertIn("backup.failed", body)
        self.assertIn("Finales Archiv: nein", body)
        self.assertNotIn("smtp_password", body.lower())

    def test_enabled_calls_send(self) -> None:
        cfg = NotificationConfig(
            email_enabled=True,
            email_to="a@b.com",
            email_from="from@b.com",
            smtp_host="smtp.test",
            smtp_port=587,
            smtp_username="u",
            smtp_password="secret",
            smtp_security="starttls",
            smtp_starttls=True,
            notify_on_backup_success=False,
            notify_on_backup_failure=True,
        )

        def fake_send(c: NotificationConfig, msg: object) -> None:
            self.assertNotIn("secret", str(msg))

        with mock.patch(
            "core.notification_service._smtp_send_default",
            side_effect=fake_send,
        ):
            r = maybe_send_backup_failure_email(
                job_id="j1",
                status="error",
                status_code="backup.failed",
                config=cfg,
            )
        self.assertEqual(r.status, "sent")


if __name__ == "__main__":
    unittest.main()
