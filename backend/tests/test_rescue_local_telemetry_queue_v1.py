"""RS-F2B.1: local telemetry queue SETUP_LOGS tests."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from core.rescue_local_telemetry_queue import enqueue_local_telemetry_event


class TestRescueLocalTelemetryQueueV1(unittest.TestCase):
    def test_event_redacted_no_ip(self):
        event = enqueue_local_telemetry_event({"client_ip": "10.0.0.5"}, stick_build_id="RS-F2B1")
        text = Path(event["path"]).read_text(encoding="utf-8")
        self.assertNotIn("10.0.0.5", text)
        self.assertEqual(event.get("status"), "ok")

    def test_network_upload_false(self):
        event = enqueue_local_telemetry_event({"phase": "test"}, stick_build_id="RS-F2B1")
        text = Path(event["path"]).read_text(encoding="utf-8")
        self.assertIn("network_upload_attempted", text)
        self.assertIn("false", text.lower())

    def test_setup_logs_preferred_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "setuphelfer" / "evidence"
            with patch("core.rescue_persistence.build_rescue_evidence_root") as mock_root:
                mock_root.return_value = {
                    "evidence_root": str(root),
                    "fallback": False,
                    "writable": True,
                }
                event = enqueue_local_telemetry_event({"phase": "stick"}, stick_build_id="RS-F2B1")
        self.assertIn("telemetry", event.get("path", ""))


if __name__ == "__main__":
    unittest.main()
