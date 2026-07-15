"""PI-RS-E2E-LIVE-001D7 payload version tests (1.10.0.25 — auto discovery)."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from core.rescue_payload_version import load_rescue_payload_version_config, rescue_payload_version


class E2ELive001D7PayloadVersionTests(unittest.TestCase):
    def test_rescue_payload_version_is_1_10_0_25(self) -> None:
        load_rescue_payload_version_config.cache_clear()
        self.assertEqual(rescue_payload_version(), "1.10.0.25")

    def test_config_file(self) -> None:
        path = Path(__file__).resolve().parents[2] / "config" / "rescue_payload_version.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(data["rescue_payload_version"], "1.10.0.25")


if __name__ == "__main__":
    unittest.main()
