"""PI-RS-MSI-FIX-001 console shield script tests."""

from __future__ import annotations

import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
COMMON = REPO_ROOT / "scripts/rescue-live/image/setuphelfer-rescue-common.sh"


class MsiFix001ConsoleShieldTests(unittest.TestCase):
    def test_shield_writes_status_json(self) -> None:
        text = COMMON.read_text(encoding="utf-8")
        self.assertIn("console-shield.json", text)
        self.assertIn("journal_to_console_blocked", text)
        self.assertIn("dmesg --console-off", text)

    def test_shield_is_non_fatal(self) -> None:
        text = COMMON.read_text(encoding="utf-8")
        self.assertIn("setuphelfer_rescue_shield_console_early() {", text)
        self.assertIn("return 0", text.split("setuphelfer_rescue_shield_console_early() {", 1)[1][:2000])


if __name__ == "__main__":
    unittest.main()
