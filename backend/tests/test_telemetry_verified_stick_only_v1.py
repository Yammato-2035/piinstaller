"""Verified stick only upload policy tests."""

from __future__ import annotations

import unittest

from core.rescue_telemetry_client_contract_v2 import TelemetryUploadMode, upload_allowed_for_mode


class TelemetryVerifiedStickOnlyV1Tests(unittest.TestCase):
    def test_beta_server_requires_verified_stick(self) -> None:
        allowed, _ = upload_allowed_for_mode(
            TelemetryUploadMode.BETA_SERVER_ACCEPTED,
            stick_verified=False,
            agreement_valid=True,
        )
        self.assertFalse(allowed)

    def test_mock_always_allowed(self) -> None:
        allowed, _ = upload_allowed_for_mode(
            TelemetryUploadMode.MOCK_SERVER,
            stick_verified=False,
            agreement_valid=False,
        )
        self.assertTrue(allowed)


if __name__ == "__main__":
    unittest.main()
