from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from core.notification_events import coerce_notification_event
from core.notification_state import emit_notification_event, list_notification_events


class NotificationEventContractTests(unittest.TestCase):
    def _base_event(self, **overrides: object) -> dict[str, object]:
        body: dict[str, object] = {
            "severity": "warning",
            "area": "runtime",
            "event_type": "runtime_gate_failed",
            "title": "Runtime Gate fehlgeschlagen",
            "message": "Runtime Gate fehlgeschlagen",
            "technical_summary": "runtime gate summary",
            "evidence_paths": ["docs/evidence/runtime-results/sample.json"],
            "dashboard_visible": True,
            "email_requested": False,
            "email_status": "disabled",
            "email_error": None,
            "acknowledged": False,
        }
        body.update(overrides)
        return body

    def test_event_has_required_fields(self) -> None:
        event = coerce_notification_event(self._base_event())
        for key in (
            "event_id",
            "created_at",
            "severity",
            "area",
            "event_type",
            "title",
            "message",
            "technical_summary",
            "evidence_paths",
            "dashboard_visible",
            "email_requested",
            "email_status",
            "email_error",
            "acknowledged",
        ):
            self.assertIn(key, event)

    def test_invalid_severity_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            coerce_notification_event(self._base_event(severity="fatal"))

    def test_secrets_are_redacted(self) -> None:
        event = coerce_notification_event(
            self._base_event(message="SMTP failure password=secret token=abc", technical_summary="api_key=xyz")
        )
        blob = json.dumps(event, ensure_ascii=False)
        self.assertIn("[redacted]", blob)
        self.assertNotIn("secret", blob)
        self.assertNotIn("abc", blob)
        self.assertNotIn("xyz", blob)

    def test_event_is_persisted(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            with (
                patch("core.notification_state.get_install_profile", return_value="repo"),
                patch("core.notification_state._workspace_root", return_value=root),
                patch("core.notification_state.publish_fire_and_forget", return_value=None),
            ):
                event = emit_notification_event(self._base_event())
            path = root / "docs/evidence/runtime-results/notifications/notification_events.jsonl"
            self.assertTrue(path.is_file())
            lines = path.read_text(encoding="utf-8").strip().splitlines()
            self.assertEqual(len(lines), 1)
            stored = json.loads(lines[0])
            self.assertEqual(stored["event_id"], event["event_id"])

    def test_event_list_sorted_by_created_at_desc(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            with (
                patch("core.notification_state.get_install_profile", return_value="repo"),
                patch("core.notification_state._workspace_root", return_value=root),
                patch("core.notification_state.publish_fire_and_forget", return_value=None),
            ):
                emit_notification_event(self._base_event(created_at="2026-05-25T19:00:00+00:00"))
                emit_notification_event(self._base_event(created_at="2026-05-25T20:00:00+00:00"))
                payload = list_notification_events()
            created = [item["created_at"] for item in payload["events"]]
            self.assertEqual(created, sorted(created, reverse=True))


if __name__ == "__main__":
    unittest.main()
