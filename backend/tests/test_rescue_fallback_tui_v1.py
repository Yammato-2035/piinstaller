"""Fallback TUI launcher — UX and crash-safe network integration."""

from __future__ import annotations

import unittest
from pathlib import Path

from rescue.rescue_fallback_tui import (
    fallback_tui_explains_safe_mode,
    fallback_tui_has_branded_title,
    fallback_tui_has_required_menu,
    fallback_tui_network_uses_safe_wrapper,
    fallback_tui_no_restore_backup_repair,
    fallback_tui_status_not_raw_json_only,
)

REPO = Path(__file__).resolve().parents[2]
LAUNCHER = REPO / "scripts/rescue-live/image/setuphelfer-rescue-ui-launch"
COMMON = REPO / "scripts/rescue-live/image/setuphelfer-rescue-common.sh"


class RescueFallbackTuiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.launcher = LAUNCHER.read_text(encoding="utf-8")
        self.common = COMMON.read_text(encoding="utf-8")

    def test_fallback_tui_branded_title_and_safe_mode(self) -> None:
        self.assertTrue(fallback_tui_has_branded_title(self.launcher))
        self.assertTrue(fallback_tui_explains_safe_mode(self.launcher))

    def test_fallback_tui_required_menu_items(self) -> None:
        self.assertTrue(fallback_tui_has_required_menu(self.launcher))

    def test_status_summary_not_raw_json_only(self) -> None:
        self.assertTrue(fallback_tui_status_not_raw_json_only(self.launcher))
        self.assertIn("setuphelfer_rescue_summarize_ui_status", self.common)

    def test_logs_action_returns_to_menu(self) -> None:
        self.assertIn("while true", self.launcher)
        self.assertIn("Logs & Diagnose auf Stick schreiben", self.launcher)

    def test_network_uses_safe_wrapper(self) -> None:
        self.assertTrue(fallback_tui_network_uses_safe_wrapper(self.launcher))
        self.assertIn("setuphelfer_rescue_run_network_interactive", self.common)

    def test_no_restore_backup_repair_in_notmenu(self) -> None:
        self.assertTrue(fallback_tui_no_restore_backup_repair(self.launcher))

    def test_cancel_exits_menu_loop_gracefully(self) -> None:
        self.assertIn("|| break", self.launcher)

    def test_no_traceback_in_user_flow(self) -> None:
        self.assertNotIn("traceback", self.launcher.lower())


if __name__ == "__main__":
    unittest.main()
