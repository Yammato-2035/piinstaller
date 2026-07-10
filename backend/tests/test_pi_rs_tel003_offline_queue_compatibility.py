"""PI-RS-TEL-003 offline queue compatibility tests."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from core.rescue_lab_telemetry_cross_repo_preview import build_rescue_cross_repo_telemetry_payload
from core.rescue_lab_telemetry_offline_queue_preview import (
    build_offline_queue_preview_item,
    write_offline_queue_preview_item,
)
from core.rescue_lab_telemetry_send_preview_gate import SendPreviewOptions, execute_send_preview


class OfflineQueueCompatibilityTests(unittest.TestCase):
    def test_cross_repo_payload_queues_without_crash(self) -> None:
        payload = build_rescue_cross_repo_telemetry_payload()
        item = build_offline_queue_preview_item(
            payload,
            "offline",
            {"network_state": "telemetry_unreachable"},
            would_send_to="http://127.0.0.1:8000/ingest",
        )
        self.assertFalse(item["auto_replay_enabled"])
        self.assertFalse(item["send_allowed_now"])

    def test_queue_writes_redacted_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            payload = build_rescue_cross_repo_telemetry_payload()
            item = build_offline_queue_preview_item(payload, "offline", None)
            path = write_offline_queue_preview_item(item, repo_root=root)
            text = path.read_text(encoding="utf-8")
            self.assertNotIn("Bearer", text)

    def test_send_preview_deferred_when_blocked(self) -> None:
        result = execute_send_preview(profile_allowed=False)
        inner = result.get("result") or {}
        self.assertFalse(inner.get("send_executed"))
        self.assertEqual(result.get("code"), "RESCUE_LAB_TELEMETRY_BLOCKED")
