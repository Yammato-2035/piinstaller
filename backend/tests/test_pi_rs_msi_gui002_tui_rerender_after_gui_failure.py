"""PI-RS-MSI-GUI-002 TUI rerender after GUI failure tests."""

from __future__ import annotations

import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
COMMON = REPO_ROOT / "scripts/rescue-live/image/setuphelfer-rescue-common.sh"
TUI = REPO_ROOT / "scripts/rescue-live/image/setuphelfer-rescue-tui.sh"


class MsiGui002TuiRerenderTests(unittest.TestCase):
    def test_mark_rerender_helper_present(self) -> None:
        text = COMMON.read_text(encoding="utf-8")
        self.assertIn("setuphelfer_rescue_mark_tui_rerender_after_gui_failure", text)
        self.assertIn("tui_rerendered_after_gui_failure", text)

    def test_blocked_status_sets_tui_rerendered(self) -> None:
        text = COMMON.read_text(encoding="utf-8")
        fn = text.split("setuphelfer_rescue_write_gui_blocked_msi_status()")[1].split("setuphelfer_rescue_mark_tui_rerender_after_gui_failure()")[0]
        self.assertIn("tui_rerendered", fn)
        self.assertIn("tui_preserved", fn)

    def test_tui_menu_returns_to_loop_after_gui_block(self) -> None:
        text = TUI.read_text(encoding="utf-8")
        self.assertIn("_tui_start_gui", text)
        self.assertIn("return 0", text.split("_tui_start_gui()")[1].split("_tui_shell()")[0])


if __name__ == "__main__":
    unittest.main()
