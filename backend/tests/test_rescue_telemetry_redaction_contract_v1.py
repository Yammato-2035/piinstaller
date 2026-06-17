"""RS-F2B.1: telemetry redaction contract tests."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from core.telemetry_redaction_contract import redact_preview, redact_telemetry_payload


class TestRescueTelemetryRedactionContractV1(unittest.TestCase):
    def test_no_wifi_password(self):
        out = redact_telemetry_payload({"wifi_psk": "super-secret"})
        self.assertNotIn("super-secret", str(out))

    def test_no_cloud_credentials(self):
        out = redact_telemetry_payload({"password": "cloud-pass", "api_key": "sk-test-1234567890"})
        self.assertNotIn("cloud-pass", str(out))
        self.assertNotIn("sk-test", str(out))

    def test_redact_preview_structure(self):
        out = redact_preview({"ip": "192.168.0.1"})
        self.assertIn("redacted", out)


if __name__ == "__main__":
    unittest.main()
