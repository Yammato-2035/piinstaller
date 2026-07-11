"""PI-RS-MSI-FIX-001 GUI VT fallback tests."""

from __future__ import annotations

import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
COMMON = REPO_ROOT / "scripts/rescue-live/image/setuphelfer-rescue-common.sh"
GUI = REPO_ROOT / "scripts/rescue-live/image/setuphelfer-rescue-gui-watchdog.sh"


class MsiFix001GuiVtFallbackTests(unittest.TestCase):
    def test_gui_failure_classification(self) -> None:
        text = COMMON.read_text(encoding="utf-8")
        self.assertIn("openvt_console_2_not_released", text)
        self.assertIn("use_tui_safe_mode", text)
        self.assertIn("tui_preserved", text)

    def test_gui_watchdog_writes_fallback_and_preserves_tui(self) -> None:
        text = GUI.read_text(encoding="utf-8")
        self.assertIn("setuphelfer_rescue_write_gui_fallback_status", text)
        self.assertIn("setuphelfer_rescue_tty1_clear_allowed", text)
        self.assertIn("chvt 1", text)


if __name__ == "__main__":
    unittest.main()
