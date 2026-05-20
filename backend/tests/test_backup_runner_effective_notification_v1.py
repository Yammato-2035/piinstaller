"""Runner loads notification.env via load_effective_notification_config (not bare os.environ)."""

from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from core.notification_settings import ENV_KEYS  # noqa: E402
from core.notification_service import EmailNotificationResult, NotificationConfig  # noqa: E402
from tools import backup_runner as br  # noqa: E402


class TestBackupRunnerEffectiveNotificationV1(unittest.TestCase):
    def test_failure_attach_reads_env_file_when_process_env_empty(self) -> None:
        lines = [
            f"{ENV_KEYS['enabled']}=true",
            f"{ENV_KEYS['on_backup_failure']}=true",
            f"{ENV_KEYS['on_backup_success']}=false",
            f"{ENV_KEYS['email_to']}=ops@example.com",
            f"{ENV_KEYS['email_from']}=from@example.com",
            f"{ENV_KEYS['smtp_host']}=smtp.example.com",
            f"{ENV_KEYS['smtp_port']}=587",
            f"{ENV_KEYS['smtp_username']}=user",
            f"{ENV_KEYS['smtp_password']}=secret",
            f"{ENV_KEYS['smtp_security']}=starttls",
        ]
        with tempfile.TemporaryDirectory() as td:
            env_path = Path(td) / "notification.env"
            env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
            status_file = Path(td) / "job1" / "status.json"
            status_file.parent.mkdir(parents=True)
            state = {
                "job_id": "job1",
                "status": "error",
                "code": "backup.failed",
                "backup_type": "full",
                "backup_dir": "/media/setuphelfer/br001",
                "abort_reason": "tar_failed",
            }
            status_file.write_text(json.dumps(state), encoding="utf-8")

            cleared = {k: "" for k in ENV_KEYS.values()}
            with mock.patch("core.notification_settings.notification_env_path", return_value=env_path):
                with mock.patch.dict(os.environ, cleared, clear=False):
                    with mock.patch(
                        "core.notification_service._smtp_send_default",
                        return_value=None,
                    ) as smtp_mock:
                        br._attach_backup_failure_notification(
                            status_file,
                            state,
                            job_id="job1",
                            code="backup.failed",
                            stderr_excerpt="timeshift changed",
                            tar_return_code=1,
                        )
                    self.assertTrue(smtp_mock.called)

            data = json.loads(status_file.read_text(encoding="utf-8"))
            self.assertEqual(data["notification_status"], "sent")
            raw = status_file.read_text(encoding="utf-8")
            self.assertNotIn("secret", raw.lower())

    def test_failure_skipped_disabled_when_env_file_disables(self) -> None:
        lines = [
            f"{ENV_KEYS['enabled']}=true",
            f"{ENV_KEYS['on_backup_failure']}=false",
            f"{ENV_KEYS['email_to']}=ops@example.com",
            f"{ENV_KEYS['email_from']}=from@example.com",
            f"{ENV_KEYS['smtp_host']}=smtp.example.com",
            f"{ENV_KEYS['smtp_port']}=587",
            f"{ENV_KEYS['smtp_username']}=user",
            f"{ENV_KEYS['smtp_password']}=secret",
        ]
        with tempfile.TemporaryDirectory() as td:
            env_path = Path(td) / "notification.env"
            env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
            status_file = Path(td) / "job2" / "status.json"
            status_file.parent.mkdir(parents=True)
            state = {"job_id": "job2", "status": "error", "code": "backup.failed"}
            status_file.write_text(json.dumps(state), encoding="utf-8")
            cleared = {k: "" for k in ENV_KEYS.values()}
            with mock.patch("core.notification_settings.notification_env_path", return_value=env_path):
                with mock.patch.dict(os.environ, cleared, clear=False):
                    with mock.patch("core.notification_service._smtp_send_default") as smtp_mock:
                        br._attach_backup_failure_notification(
                            status_file,
                            state,
                            job_id="job2",
                            code="backup.failed",
                        )
                    smtp_mock.assert_not_called()
            data = json.loads(status_file.read_text(encoding="utf-8"))
            self.assertEqual(data["notification_status"], "skipped_not_applicable")


if __name__ == "__main__":
    unittest.main()
