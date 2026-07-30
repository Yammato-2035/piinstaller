"""Rescue telemetry opt-in state persistence tests."""

from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from core.rescue_telemetry_opt_in_state import (
    is_telemetry_opt_in_enabled,
    load_telemetry_opt_in,
    save_telemetry_opt_in,
)
from core.telemetry_client_contract import TelemetryOptInState


class RescueTelemetryOptInStateTests(unittest.TestCase):
    def test_defaults_to_disabled_when_missing(self) -> None:
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "opt-in.json"
            self.assertEqual(load_telemetry_opt_in(path), TelemetryOptInState.DISABLED)
            self.assertFalse(is_telemetry_opt_in_enabled(path))

    def test_save_then_load_roundtrip(self) -> None:
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "nested" / "opt-in.json"
            save_telemetry_opt_in(TelemetryOptInState.ENABLED, path=path)
            self.assertEqual(load_telemetry_opt_in(path), TelemetryOptInState.ENABLED)
            self.assertTrue(is_telemetry_opt_in_enabled(path))

    def test_corrupted_file_falls_back_to_disabled(self) -> None:
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "opt-in.json"
            path.write_text("not json", encoding="utf-8")
            self.assertEqual(load_telemetry_opt_in(path), TelemetryOptInState.DISABLED)


if __name__ == "__main__":
    unittest.main()
