"""Fallback TUI menu contract tests — workspace scripts."""

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
from rescue.rescue_ui_launcher_contract import evaluate_workspace_launcher_contract

REPO = Path(__file__).resolve().parents[2]
LAUNCHER = REPO / "scripts/rescue-live/image/setuphelfer-rescue-ui-launch"
COMMON = REPO / "scripts/rescue-live/image/setuphelfer-rescue-common.sh"
NETWORK = REPO / "scripts/rescue-live/image/setuphelfer-rescue-network-onboarding"


class RescueFallbackTuiMenuContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.launcher = LAUNCHER.read_text(encoding="utf-8")
        self.common = COMMON.read_text(encoding="utf-8")
        self.network = NETWORK.read_text(encoding="utf-8")

    def test_menu_title_setuphelfer_rettungsstick(self) -> None:
        self.assertTrue(fallback_tui_has_branded_title(self.launcher))

    def test_safe_mode_explanation(self) -> None:
        self.assertTrue(fallback_tui_explains_safe_mode(self.launcher))

    def test_required_menu_items(self) -> None:
        self.assertTrue(fallback_tui_has_required_menu(self.launcher))

    def test_status_summary_not_raw_json(self) -> None:
        self.assertTrue(fallback_tui_status_not_raw_json_only(self.launcher))
        self.assertIn("setuphelfer_rescue_summarize_ui_status", self.common)

    def test_details_under_separate_option(self) -> None:
        self.assertIn("Details", self.launcher)

    def test_logs_action_feedback(self) -> None:
        self.assertIn("Logs", self.launcher)
        self.assertIn("best effort", self.launcher.lower())

    def test_network_safe_wrapper(self) -> None:
        self.assertTrue(fallback_tui_network_uses_safe_wrapper(self.launcher))
        self.assertIn("setuphelfer_rescue_run_network_interactive", self.common)

    def test_network_nmcli_missing_handled(self) -> None:
        self.assertIn("NMCLI_MISSING", self.network)

    def test_network_return_to_menu(self) -> None:
        self.assertIn("return_to_menu", self.network)

    def test_no_backup_restore_in_menu(self) -> None:
        self.assertTrue(fallback_tui_no_restore_backup_repair(self.launcher))

    def test_workspace_contract_ok(self) -> None:
        result = evaluate_workspace_launcher_contract(REPO)
        self.assertTrue(result["contract_ok"], result)


if __name__ == "__main__":
    unittest.main()
