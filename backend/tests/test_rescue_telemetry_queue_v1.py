"""Telemetry queue V1 tests."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from core.rescue_telemetry_queue_v1 import TelemetryQueueV1
from core.rescue_telemetry_client_contract_v2 import build_telemetry_payload_v2


class RescueTelemetryQueueV1Tests(unittest.TestCase):
    def test_enqueue_and_drain(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            q = TelemetryQueueV1(Path(tmp))
            payload = build_telemetry_payload_v2(
                rescue_version="1.9.17.0",
                build_id="b",
                boot_session_id="s",
                stick_id="stick-1",
                stick_type="mock",
                device_public_key_id="k",
                attestation_mode="mock",
                system_assessment={},
            )
            result = q.enqueue(payload, signing_secret="mock")
            self.assertEqual(result["status"], "queued")
            self.assertEqual(len(q.list_items()), 1)

    def test_rejects_pii(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            q = TelemetryQueueV1(Path(tmp))
            bad = {"system_assessment": {"email": "a@b.co"}, "privacy": {}}
            result = q.enqueue(bad)
            self.assertEqual(result["status"], "rejected")


if __name__ == "__main__":
    unittest.main()
