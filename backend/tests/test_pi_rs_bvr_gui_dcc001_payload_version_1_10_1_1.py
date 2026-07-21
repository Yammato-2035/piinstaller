"""PI-RS-BVR-GUI-DCC-001 payload version pin (1.10.1.1)."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from core.rescue_payload_version import (
    load_rescue_payload_version_config,
    previous_rescue_payload_version,
    rescue_payload_version,
)


class PiRsBvrGuiDcc001PayloadVersionTests(unittest.TestCase):
    def test_rescue_payload_version_is_1_10_1_1(self) -> None:
        load_rescue_payload_version_config.cache_clear()
        self.assertEqual(rescue_payload_version(), "1.10.1.1")

    def test_previous_is_1_10_1_0(self) -> None:
        load_rescue_payload_version_config.cache_clear()
        self.assertEqual(previous_rescue_payload_version(), "1.10.1.0")

    def test_flag_present(self) -> None:
        path = Path(__file__).resolve().parents[2] / "config" / "rescue_payload_version.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        self.assertTrue(data.get("pi_rs_bvr_gui_dcc_001"))
        self.assertEqual(data["rescue_payload_version"], "1.10.1.1")


if __name__ == "__main__":
    unittest.main()
