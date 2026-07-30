"""Rescue assessment telemetry V1 tests — early opt-in-gated send of real assessment data."""

from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from core.rescue_assessment_telemetry_v1 import (
    build_assessment_telemetry_payload,
    maybe_send_assessment_telemetry_early,
)
from core.rescue_telemetry_client_contract_v2 import validate_telemetry_payload_v2
from core.rescue_telemetry_opt_in_state import save_telemetry_opt_in
from core.telemetry_client_contract import TelemetryOptInState


class RescueAssessmentTelemetryPayloadTests(unittest.TestCase):
    def test_payload_carries_real_assessment_and_validates(self) -> None:
        payload = build_assessment_telemetry_payload(rescue_version="1.9.17.0")
        self.assertEqual(validate_telemetry_payload_v2(payload), [])
        self.assertIn("mainboard", payload["system_assessment"]["system_assessment"]["assessment"])


class MaybeSendAssessmentTelemetryEarlyTests(unittest.TestCase):
    def test_skips_when_opt_in_disabled(self) -> None:
        with TemporaryDirectory() as tmp:
            opt_in_path = Path(tmp) / "opt-in.json"
            result = maybe_send_assessment_telemetry_early(
                queue_root=Path(tmp) / "queue", opt_in_path=opt_in_path
            )
            self.assertEqual(result, {"attempted": False, "reason": "opt_in_disabled"})

    def test_queues_real_assessment_when_opted_in(self) -> None:
        with TemporaryDirectory() as tmp:
            opt_in_path = Path(tmp) / "opt-in.json"
            save_telemetry_opt_in(TelemetryOptInState.ENABLED, path=opt_in_path)
            queue_root = Path(tmp) / "queue"
            result = maybe_send_assessment_telemetry_early(
                queue_root=queue_root, opt_in_path=opt_in_path
            )
            self.assertTrue(result["attempted"])
            self.assertEqual(result["status"], "queued")
            self.assertTrue((queue_root / "telemetry-queue-v1.jsonl").is_file())


if __name__ == "__main__":
    unittest.main()
