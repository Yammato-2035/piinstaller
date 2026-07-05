"""PI-RS-TEL-002 offline queue preview tests."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from core.rescue_lab_telemetry_model import build_synthetic_rescue_lab_payload
from core.rescue_lab_telemetry_offline_queue_preview import (
    build_offline_queue_preview_item,
    build_offline_queue_preview_summary,
    list_offline_queue_preview_items,
    validate_offline_queue_preview_item_no_pii,
    write_offline_queue_preview_item,
)


class OfflineQueuePreviewTests(unittest.TestCase):
    def test_preview_writes_redacted_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            item = build_offline_queue_preview_item(
                build_synthetic_rescue_lab_payload().to_dict(),
                "offline",
                {"network_state": "telemetry_unreachable"},
                would_send_to="https://lab.example.test/ingest",
            )
            path = write_offline_queue_preview_item(item, repo_root=root)
            self.assertTrue(path.is_file())
            data = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(data["would_send_to"], "https://lab.example.test/[redacted]")

    def test_auto_replay_always_false(self) -> None:
        item = build_offline_queue_preview_item(
            build_synthetic_rescue_lab_payload().to_dict(),
            "offline",
            None,
        )
        self.assertFalse(item["auto_replay_enabled"])

    def test_send_allowed_now_false(self) -> None:
        item = build_offline_queue_preview_item(
            build_synthetic_rescue_lab_payload().to_dict(),
            "offline",
            None,
        )
        self.assertFalse(item["send_allowed_now"])

    def test_pii_blocked(self) -> None:
        payload = build_synthetic_rescue_lab_payload().to_dict()
        payload["hostname"] = "host.example.com"
        with self.assertRaises(ValueError):
            build_offline_queue_preview_item(payload, "offline", None)

    def test_secret_not_written(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            item = build_offline_queue_preview_item(
                build_synthetic_rescue_lab_payload().to_dict(),
                "missing_secret",
                None,
                would_send_to="http://lab.example.test",
            )
            path = write_offline_queue_preview_item(item, repo_root=root)
            text = path.read_text(encoding="utf-8")
            self.assertNotIn("test-secret", text)

    def test_no_worker_function(self) -> None:
        from pathlib import Path as P

        text = (P(__file__).resolve().parents[1] / "core/rescue_lab_telemetry_offline_queue_preview.py").read_text()
        self.assertNotIn("def worker", text)
        self.assertNotIn("retry", text.lower().replace("auto_replay", ""))

    def test_list_redacted_items(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for _ in range(2):
                write_offline_queue_preview_item(
                    build_offline_queue_preview_item(
                        build_synthetic_rescue_lab_payload().to_dict(),
                        "offline",
                        None,
                    ),
                    repo_root=root,
                )
            items = list_offline_queue_preview_items(limit=10, repo_root=root)
            self.assertGreaterEqual(len(items), 1)
            summary = build_offline_queue_preview_summary(repo_root=root)
            self.assertFalse(summary["auto_replay_enabled"])


if __name__ == "__main__":
    unittest.main()
