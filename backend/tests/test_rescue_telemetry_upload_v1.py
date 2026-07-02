"""Rescue telemetry upload V1 tests."""

from __future__ import annotations

import unittest

from core.rescue_telemetry_client_contract_v2 import build_telemetry_payload_v2
from core.rescue_telemetry_upload_v1 import upload_telemetry_payload_v1


class RescueTelemetryUploadV1Tests(unittest.TestCase):
    def _payload(self) -> dict:
        return build_telemetry_payload_v2(
            rescue_version="1.9.17.1",
            build_id="b",
            boot_session_id="s",
            stick_id="stick-mock",
            stick_type="mock",
            device_public_key_id="k",
            attestation_mode="mock",
            system_assessment={},
        )

    def test_dry_run_ok(self) -> None:
        result = upload_telemetry_payload_v1(self._payload(), mode="dry_run_local")
        self.assertEqual(result["status"], "dry_run_ok")
        self.assertFalse(result["uploaded"])

    def test_beta_blocked_without_stick(self) -> None:
        result = upload_telemetry_payload_v1(
            self._payload(),
            mode="beta_server_accepted",
            stick_verified=False,
            agreement_valid=True,
        )
        self.assertEqual(result["status"], "blocked")


if __name__ == "__main__":
    unittest.main()
