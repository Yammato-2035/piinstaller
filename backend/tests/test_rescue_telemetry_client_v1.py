"""Rescue-stick telemetry client — public contract integration (Set C)."""

from __future__ import annotations

import unittest

from core.rescue_telemetry_client import (
    build_rescue_stick_client_envelope,
    build_rescue_stick_telemetry_client_preview,
    map_operator_consent_to_opt_in,
)
from core.telemetry_client_contract import TelemetryOptInState


class RescueTelemetryClientTests(unittest.TestCase):
    def _sample_report(self) -> dict:
        return {
            "host": {"edition": "Windows 11 Pro"},
            "hardware": {"cpu_vendor": "GenuineIntel", "memory_bytes": 16_000_000_000},
            "diagnostics": {"codes": ["rescue.inspect.ok"], "severity": "info"},
            "storage": {"windows_candidates": ["/dev/sda1"]},
            "bitlocker": {"status": "unknown"},
            "backup_selection": {},
            "dualboot_readiness": {"planning_only": True},
        }

    def test_map_operator_consent_granted(self) -> None:
        self.assertEqual(map_operator_consent_to_opt_in("granted"), TelemetryOptInState.ENABLED)

    def test_preview_blocked_when_opt_in_disabled(self) -> None:
        out = build_rescue_stick_telemetry_client_preview(
            self._sample_report(),
            run_id="run-test-001",
            opt_in_state=TelemetryOptInState.DISABLED,
        )
        self.assertEqual(out["status"], "blocked")
        self.assertIn("opt_in_required", out["validation_errors"])
        self.assertFalse(out["send_allowed"])

    def test_preview_ok_when_opt_in_enabled(self) -> None:
        out = build_rescue_stick_telemetry_client_preview(
            self._sample_report(),
            run_id="run-test-002",
            opt_in_state=TelemetryOptInState.ENABLED,
        )
        self.assertEqual(out["status"], "ok")
        self.assertEqual(out["validation_errors"], [])
        self.assertTrue(out["send_allowed"])
        env = out["client_envelope"]
        self.assertFalse(env["endpoint_configured"])
        self.assertIn("rescue_session_meta", env["data_categories"])

    def test_redaction_applied_to_envelope(self) -> None:
        report = self._sample_report()
        report["notes"] = "contact user@secret.example path /home/volker/data"
        envelope = build_rescue_stick_client_envelope(
            report,
            run_id="run-redact-001",
            opt_in_state=TelemetryOptInState.ENABLED,
        )
        self.assertTrue(envelope.redaction_applied)
        blob = str(envelope.payload)
        self.assertNotIn("user@secret.example", blob)
        self.assertNotIn("/home/volker", blob)


if __name__ == "__main__":
    unittest.main()
