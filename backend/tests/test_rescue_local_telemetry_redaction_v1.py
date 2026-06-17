"""RS-F2S: rescue stick local telemetry redaction contract tests."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from core.rescue_local_telemetry_queue import enqueue_local_telemetry_event
from core.telemetry_redaction_contract import redact_preview, redact_telemetry_payload


class TestRescueLocalTelemetryRedactionV1(unittest.TestCase):
    def test_ip_redacted(self):
        out = redact_telemetry_payload({"host": "10.20.30.40"})
        self.assertNotIn("10.20.30.40", str(out))
        self.assertIn("[REDACTED:ip]", str(out))

    def test_mac_redacted(self):
        out = redact_telemetry_payload({"mac": "aa:bb:cc:dd:ee:ff"})
        self.assertNotIn("aa:bb:cc:dd:ee:ff", str(out))

    def test_hostname_redacted(self):
        out = redact_telemetry_payload({"fqdn": "msi.example.com"})
        self.assertNotIn("msi.example.com", str(out))

    def test_user_paths_redacted(self):
        out = redact_telemetry_payload({"path": "/home/volker/secret"})
        self.assertNotIn("/home/volker", str(out))

    def test_serial_redacted(self):
        out = redact_telemetry_payload({"serial": "S736NL0X905337T"})
        self.assertNotIn("S736NL0X905337T", str(out))

    def test_token_blocked(self):
        out = redact_telemetry_payload({"api_key": "sk-live-abcdefghijklmnop"})
        self.assertNotIn("sk-live", str(out))

    def test_no_raw_ip_in_event(self):
        event = enqueue_local_telemetry_event({"client_ip": "192.168.1.50"}, stick_build_id="build-1")
        self.assertEqual(event.get("status"), "ok")
        path = event.get("path")
        self.assertTrue(path)
        text = Path(path).read_text(encoding="utf-8")
        self.assertNotIn("192.168.1.50", text)

    def test_offline_event_network_upload_false(self):
        out = redact_telemetry_payload({"foo": "bar"})
        self.assertFalse(out.get("redaction", {}).get("network_upload_attempted", True))

    def test_evidence_contains_stick_build_id(self):
        event = enqueue_local_telemetry_event({"phase": "preflight"}, stick_build_id="RS-F2S-TEST")
        text = Path(event["path"]).read_text(encoding="utf-8")
        self.assertIn("RS-F2S-TEST", text)

    def test_no_private_server_endpoints(self):
        out = redact_telemetry_payload(
            {"ingest_url": "https://telemetry.internal.example.com/v1/ingest"}
        )
        self.assertNotIn("telemetry.internal.example.com", str(out))


if __name__ == "__main__":
    unittest.main()
