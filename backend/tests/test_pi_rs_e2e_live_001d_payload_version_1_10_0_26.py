"""PI-RS-E2E-LIVE-001D payload version tests (tracks current rescue_payload_version)."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from core.rescue_payload_version import load_rescue_payload_version_config, rescue_payload_version


class E2ELive001DPayloadVersionTests(unittest.TestCase):
    def test_rescue_payload_version_is_current(self) -> None:
        load_rescue_payload_version_config.cache_clear()
        self.assertEqual(rescue_payload_version(), "1.10.0.38")

    def test_config_file(self) -> None:
        path = Path(__file__).resolve().parents[2] / "config" / "rescue_payload_version.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(data["rescue_payload_version"], "1.10.0.38")
        self.assertEqual(data["previous_rescue_payload_version"], "1.10.0.37")


if __name__ == "__main__":
    unittest.main()
