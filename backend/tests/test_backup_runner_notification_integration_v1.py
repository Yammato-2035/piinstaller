"""Backup runner attaches notification fields without failing on SMTP errors."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from core.notification_service import NotificationConfig
from tools import backup_runner as br


class TestBackupRunnerNotificationIntegrationV1(unittest.TestCase):
    def test_attach_success_merges_notification_fields(self) -> None:
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
        sent: list[object] = []

        def fake_send(**kwargs: object) -> object:
            from core.notification_service import EmailNotificationResult

            sent.append(kwargs)
            return EmailNotificationResult(status="sent", recipient_masked="a***@b.com")

        with tempfile.TemporaryDirectory() as td:
            status_dir = Path(td)
            job_id = "notif01"
            job_dir = status_dir / job_id
            job_dir.mkdir()
            status_file = job_dir / "status.json"
            state: dict = {
                "job_id": job_id,
                "backup_type": "full",
                "backup_dir": "/media/setuphelfer/br001",
                "progress_optional": {"bytes_current": 1000, "running_for_s": 42},
            }
            with mock.patch.object(br, "load_notification_config", return_value=cfg), mock.patch.object(
                br, "maybe_send_backup_success_email", side_effect=fake_send
            ):
                br._attach_backup_success_notification(
                    status_file,
                    state,
                    job_id=job_id,
                    code="backup.success",
                    backup_type="full",
                    backup_profile="full-expert",
                    backup_dir="/media/setuphelfer/br001",
                    archive_path="/media/setuphelfer/br001/x.tar.gz",
                    manifest_hash="sha256:abc",
                )
            data = json.loads(status_file.read_text(encoding="utf-8"))
            self.assertEqual(data["notification_email_status"], "sent")
            self.assertTrue(data["notification_email_sent"])
            self.assertEqual(data["notification_email_recipient_masked"], "a***@b.com")

    def test_smtp_fail_leaves_success_code_unchanged(self) -> None:
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
        from core.notification_service import EmailNotificationResult

        with tempfile.TemporaryDirectory() as td:
            status_file = Path(td) / "j" / "status.json"
            status_file.parent.mkdir(parents=True)
            state = {"job_id": "j", "code": "backup.success", "status": "success"}
            status_file.write_text(json.dumps(state), encoding="utf-8")
            with mock.patch.object(br, "load_notification_config", return_value=cfg), mock.patch.object(
                br,
                "maybe_send_backup_success_email",
                return_value=EmailNotificationResult(status="failed", error="smtp down"),
            ):
                br._attach_backup_success_notification(
                    status_file,
                    state,
                    job_id="j",
                    code="backup.success",
                    backup_type="full",
                    backup_profile="full-expert",
                    backup_dir="/media/setuphelfer/br001",
                    archive_path="/x.tar.gz",
                    manifest_hash="sha256:x",
                )
            data = json.loads(status_file.read_text(encoding="utf-8"))
            self.assertEqual(data.get("code", state.get("code")), "backup.success")
            self.assertEqual(data["notification_email_status"], "failed")


if __name__ == "__main__":
    unittest.main()
