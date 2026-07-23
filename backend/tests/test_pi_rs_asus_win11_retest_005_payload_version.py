"""Payload flag/version gate for PI-RS-ASUS-WIN11-RETEST-005."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]


class PayloadVersionRetest005(unittest.TestCase):
    def test_payload_bumped_with_flag(self) -> None:
        cfg = json.loads((_REPO / "config/rescue_payload_version.json").read_text(encoding="utf-8"))
        self.assertEqual(cfg["rescue_payload_version"], "1.10.3.0")
        self.assertEqual(cfg["previous_rescue_payload_version"], "1.10.2.9")
        self.assertTrue(cfg["pi_rs_asus_win11_retest_005"])
        self.assertTrue(cfg.get("pi_rs_asus_win11_stage_a_006"))
        self.assertTrue(cfg.get("pi_rs_asus_auto_win11_log_007"))
        self.assertTrue(cfg["pi_rs_asus_capture_finalize_004"])


if __name__ == "__main__":
    unittest.main()
