"""Payload version gate for PI-RS-ASUS-WIN11-LINUX-001 (floor maintained)."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class PayloadVersionTests(unittest.TestCase):
    def test_payload_version(self) -> None:
        data = json.loads((ROOT / "config/rescue_payload_version.json").read_text(encoding="utf-8"))
        self.assertGreaterEqual(tuple(int(x) for x in data["rescue_payload_version"].split(".")), (1, 10, 1, 3))
        self.assertTrue(data.get("pi_rs_asus_win11_linux_001"))

    def test_app_version(self) -> None:
        data = json.loads((ROOT / "config/version.json").read_text(encoding="utf-8"))
        self.assertGreaterEqual(tuple(int(x) for x in data["project_version"].split(".")), (1, 9, 21, 0))


if __name__ == "__main__":
    unittest.main()
