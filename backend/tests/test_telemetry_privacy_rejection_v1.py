"""Telemetry privacy rejection tests."""

from __future__ import annotations

import unittest

from core.rescue_telemetry_client_contract_v2 import build_telemetry_payload_v2, validate_telemetry_payload_v2


class TelemetryPrivacyRejectionV1Tests(unittest.TestCase):
    def test_forbidden_privacy_flags_rejected(self) -> None:
        payload = build_telemetry_payload_v2(
            rescue_version="1.9.17.0",
            build_id="b",
            boot_session_id="s",
            stick_id="stick",
            stick_type="mock",
            device_public_key_id="k",
            attestation_mode="mock",
            system_assessment={},
        )
        payload["privacy"]["contains_ip"] = True
        errors = validate_telemetry_payload_v2(payload)
        self.assertTrue(any("forbidden_privacy" in e for e in errors))


if __name__ == "__main__":
    unittest.main()
