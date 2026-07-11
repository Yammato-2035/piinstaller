"""PI-RS-TEL-SEND-001 contract tests."""

from __future__ import annotations

import unittest

from core.rescue_stick_cloud_lab_models import (
    DEFAULT_CLOUD_INGEST_URL,
    LAB_CLIENT_ID,
    LAB_EVENT_TYPE,
    LAB_PAYLOAD_SCHEMA_VERSION,
    LAB_SOURCE,
)
from core.rescue_stick_cloud_lab_payload import build_rescue_stick_lab_payload


class TelSend001ContractTests(unittest.TestCase):
    def test_payload_contract_fields(self) -> None:
        payload = build_rescue_stick_lab_payload(stick_version="1.9.19.5")
        self.assertEqual(payload["schema_version"], LAB_PAYLOAD_SCHEMA_VERSION)
        self.assertEqual(payload["source"], LAB_SOURCE)
        self.assertEqual(payload["event_type"], LAB_EVENT_TYPE)
        self.assertFalse(payload["production_ready"])
        self.assertFalse(payload["contains_pii"])
        self.assertFalse(payload["raw_logs_visible"])
        self.assertTrue(str(payload["payload_hash"]).startswith("sha256:"))

    def test_default_endpoint_is_cloud_ingest(self) -> None:
        self.assertEqual(DEFAULT_CLOUD_INGEST_URL, "https://telemetrie.setuphelfer.de/v1/telemetry/ingest")

    def test_client_id_constant(self) -> None:
        self.assertEqual(LAB_CLIENT_ID, "rescue_stick_lab")


if __name__ == "__main__":
    unittest.main()
