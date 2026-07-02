"""Telemetry redaction V2 tests."""

from __future__ import annotations

import unittest

from core.rescue_telemetry_payload_redaction_v2 import redact_telemetry_payload_v2


class RescueTelemetryRedactionV2Tests(unittest.TestCase):
    def test_strips_pii_from_payload(self) -> None:
        payload = {
            "system_assessment": {"note": "email leak@example.com 10.0.0.1"},
            "privacy": {
                "redaction_version": "x",
                "contains_mac": False,
                "contains_ip": False,
                "contains_email": False,
                "contains_serial_plaintext": False,
                "contains_file_list": False,
                "contains_user_files": False,
                "contains_secrets": False,
            },
        }
        redacted, report = redact_telemetry_payload_v2(payload)
        self.assertNotIn("leak@example.com", str(redacted))
        self.assertFalse(redacted["privacy"]["contains_email"])


if __name__ == "__main__":
    unittest.main()
