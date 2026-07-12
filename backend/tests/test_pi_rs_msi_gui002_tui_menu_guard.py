"""PI-RS-MSI-GUI-002 TUI menu guard tests."""

from __future__ import annotations

import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
TUI = REPO_ROOT / "scripts/rescue-live/image/setuphelfer-rescue-tui.sh"


class MsiGui002TuiMenuGuardTests(unittest.TestCase):
    def test_gui_menu_checks_msi_disable_before_watchdog(self) -> None:
        text = TUI.read_text(encoding="utf-8")
        gui_fn = text.split("_tui_start_gui()")[1].split("_tui_shell()")[0]
        self.assertIn("setuphelfer_rescue_should_disable_gui_for_msi_compat", gui_fn)
        self.assertIn("setuphelfer_rescue_gui_disabled_message", gui_fn)
        watchdog_pos = gui_fn.find("setuphelfer-rescue-gui-watchdog")
        disable_pos = gui_fn.find("setuphelfer_rescue_should_disable_gui_for_msi_compat")
        self.assertGreater(watchdog_pos, disable_pos)

    def test_operator_message_present(self) -> None:
        text = COMMON.read_text(encoding="utf-8") if (COMMON := REPO_ROOT / "scripts/rescue-live/image/setuphelfer-rescue-common.sh").is_file() else ""
        self.assertIn("MSI-Kompatibilitätsmodus nicht verfügbar", text)

    def test_tui_rerender_after_failure(self) -> None:
        text = TUI.read_text(encoding="utf-8")
        self.assertIn("setuphelfer_rescue_mark_tui_rerender_after_gui_failure", text)


if __name__ == "__main__":
    unittest.main()
