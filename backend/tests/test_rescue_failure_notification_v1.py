from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from core.notification_state import list_notification_events, sync_rescue_failure_notification
from core.notification_service import NotificationConfig


def _smtp_cfg() -> NotificationConfig:
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


class RescueFailureNotificationTests(unittest.TestCase):
    def test_lb_exit_127_creates_rescue_failure_event(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            summary_path = root / "docs/evidence/runtime-results/rescue/controlled_iso_build_latest_summary.json"
            summary_path.parent.mkdir(parents=True, exist_ok=True)
            summary_path.write_text(
                json.dumps(
                    {
                        "updated_at": "2026-05-25T20:09:00+00:00",
                        "status": "failed",
                        "last_exit_code": 127,
                        "primary_error": "/usr/bin/env: 'rsvg': No such file or directory",
                        "iso_found": False,
                        "usb_write_started": False,
                        "dashboard_status_after_failure": "red",
                        "next_required_action": "fix_missing_rsvg_or_remove_rsvg_dependency",
                    },
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            with (
                patch("core.notification_state.get_install_profile", return_value="repo"),
                patch("core.notification_state._workspace_root", return_value=root),
                patch("core.notification_state.publish_fire_and_forget", return_value=None),
                patch("core.notification_email.load_effective_notification_config", return_value=_smtp_cfg()),
            ):
                event = sync_rescue_failure_notification()
                payload = list_notification_events()
                again = sync_rescue_failure_notification()
            self.assertIsNotNone(event)
            assert event is not None
            self.assertEqual(event["event_type"], "rescue_iso_build_failed")
            self.assertIn("LB_EXIT=127", event["technical_summary"])
            self.assertIn("rsvg", event["technical_summary"])
            self.assertIn("USB nicht gestartet", event["message"])
            self.assertTrue(event["dashboard_visible"])
            self.assertEqual(event["email_status"], "not_configured")
            self.assertIn("docs/evidence/runtime-results/rescue/controlled_iso_build_latest_summary.json", event["evidence_paths"])
            self.assertEqual(payload["event_count"], 1)
            self.assertEqual(again["event_id"], event["event_id"])


if __name__ == "__main__":
    unittest.main()
