"""Telemetry client contract V2 tests."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from core.rescue_telemetry_client_contract_v2 import (
    CONTRACT_SCHEMA_VERSION,
    TelemetryUploadMode,
    build_telemetry_payload_v2,
    upload_allowed_for_mode,
    validate_telemetry_payload_v2,
)


class RescueTelemetryClientContractV2Tests(unittest.TestCase):
    def test_schema_valid_payload(self) -> None:
        payload = build_telemetry_payload_v2(
            rescue_version="1.9.17.0",
            build_id="build-mock",
            boot_session_id="boot-1",
            stick_id="stick-pseudo-001",
            stick_type="team_provisioned",
            device_public_key_id="key-001",
            attestation_mode="mock",
            system_assessment={"hardware_summary": {}},
            upload_allowed=False,
        )
        self.assertEqual(payload["schema_version"], CONTRACT_SCHEMA_VERSION)
        self.assertEqual(validate_telemetry_payload_v2(payload), [])

    def test_upload_blocked_without_verified_stick(self) -> None:
        allowed, reason = upload_allowed_for_mode(
            TelemetryUploadMode.BETA_SERVER_ACCEPTED,
            stick_verified=False,
            agreement_valid=True,
        )
        self.assertFalse(allowed)
        self.assertEqual(reason, "stick_not_verified")

    def test_json_schema_file_validates(self) -> None:
        schema_path = Path(__file__).resolve().parents[2] / "docs/architecture/telemetry_rescue_beta_v2.schema.json"
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        self.assertEqual(schema["properties"]["schema_version"]["const"], CONTRACT_SCHEMA_VERSION)


if __name__ == "__main__":
    unittest.main()
