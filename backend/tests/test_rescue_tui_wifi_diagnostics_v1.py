"""RS-P2C TUI WLAN diagnostics contract."""

from __future__ import annotations

import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
TUI = REPO / "scripts/rescue-live/image/setuphelfer-rescue-tui.sh"


class TestRescueTuiWifiDiagnosticsV1(unittest.TestCase):
    def setUp(self) -> None:
        self.tui = TUI.read_text(encoding="utf-8")

    def test_wifi_menu_item(self):
        self.assertIn("Hardware/WLAN", self.tui)

    def test_classify_wifi_status(self):
        self.assertIn("classify_wifi_status", self.tui)

    def test_nmcli_output(self):
        self.assertIn("nmcli radio", self.tui)

    def test_no_password_logging(self):
        self.assertNotIn("PSK", self.tui)


if __name__ == "__main__":
    unittest.main()
