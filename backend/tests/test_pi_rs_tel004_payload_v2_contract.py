"""PI-RS-TEL-004 telemetry.rescue.beta.v2 preview payload contract tests."""

from __future__ import annotations

import unittest

from core.rescue_telemetry_client_contract_v2 import CONTRACT_SCHEMA_VERSION
from core.rescue_telemetry_payload_v2 import (
    PREVIEW_SOURCE_KIND,
    build_rescue_telemetry_preview_payload_v2,
    validate_preview_payload_security,
)


class Tel004PayloadV2ContractTests(unittest.TestCase):
    def test_schema_and_event_kind(self) -> None:
        payload = build_rescue_telemetry_preview_payload_v2(workspace_version="1.9.19.5")
        self.assertEqual(payload["schema_version"], CONTRACT_SCHEMA_VERSION)
        self.assertEqual(payload["event_kind"], CONTRACT_SCHEMA_VERSION)

    def test_source_kind_and_safety_flags(self) -> None:
        payload = build_rescue_telemetry_preview_payload_v2(workspace_version="1.9.19.5")
        self.assertEqual(payload["source_kind"], PREVIEW_SOURCE_KIND)
        self.assertFalse(payload["production_ready"])
        self.assertTrue(payload["preview_only"])
        self.assertTrue(payload["operator_approval_required"])
        self.assertFalse(payload["external_calls"])

    def test_build_metadata_and_aggregates(self) -> None:
        payload = build_rescue_telemetry_preview_payload_v2(workspace_version="1.9.19.5")
        assessment = payload["system_assessment"]
        self.assertEqual(assessment["build"]["workspace_version"], "1.9.19.5")
        self.assertEqual(assessment["build"]["stick_payload_version"], "1.10.0.12")
        self.assertIn("diagnostics_aggregates", assessment)
        self.assertIn("plesk", assessment["diagnostics_aggregates"])

    def test_no_plain_identifiers(self) -> None:
        payload = build_rescue_telemetry_preview_payload_v2(
            workspace_version="1.9.19.5",
            boot_id="boot-abc",
            device_seed="device-xyz",
        )
        blob = str(payload)
        self.assertNotIn("boot-abc", blob)
        self.assertNotIn("device-xyz", blob)
        self.assertNotIn("@", blob)

    def test_security_validator_clean(self) -> None:
        payload = build_rescue_telemetry_preview_payload_v2(workspace_version="1.9.19.5")
        errors = validate_preview_payload_security(payload)
        self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
