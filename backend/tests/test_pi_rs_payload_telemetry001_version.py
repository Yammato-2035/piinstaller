"""PI-RS-PAYLOAD-TELEMETRY-001 version tests."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from core.rescue_payload_version import (
    load_rescue_payload_version_config,
    previous_rescue_payload_version,
    rescue_payload_version,
)


class PayloadTelemetry001VersionTests(unittest.TestCase):
    def test_rescue_payload_version_is_1_10_0_13(self) -> None:
        self.assertEqual(rescue_payload_version(), "1.10.0.13")

    def test_previous_version_documented(self) -> None:
        self.assertEqual(previous_rescue_payload_version(), "1.10.0.12")

    def test_config_file_present(self) -> None:
        path = Path(__file__).resolve().parents[2] / "config" / "rescue_payload_version.json"
        self.assertTrue(path.is_file())
        data = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(data["rescue_payload_version"], "1.10.0.13")
        self.assertTrue(data.get("includes_lab_telemetry_send"))

    def test_load_config_cached(self) -> None:
        load_rescue_payload_version_config.cache_clear()
        cfg = load_rescue_payload_version_config()
        self.assertEqual(cfg["rescue_payload_version"], "1.10.0.13")


if __name__ == "__main__":
    unittest.main()
