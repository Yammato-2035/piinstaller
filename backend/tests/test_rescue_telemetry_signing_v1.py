"""Telemetry signing V1 tests."""

from __future__ import annotations

import unittest

from core.rescue_telemetry_signing_v1 import sign_payload_hmac, verify_payload_hmac


class RescueTelemetrySigningV1Tests(unittest.TestCase):
    def test_hmac_roundtrip(self) -> None:
        payload = {"event_id": "test-uuid", "schema_version": "telemetry.rescue.beta.v2"}
        sig = sign_payload_hmac(payload, secret="mock-secret-not-real")
        self.assertTrue(verify_payload_hmac(payload, sig["signature"], secret="mock-secret-not-real"))


if __name__ == "__main__":
    unittest.main()
