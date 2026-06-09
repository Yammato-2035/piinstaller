"""Rescue UI launcher script and status model tests."""

from __future__ import annotations

import unittest
from pathlib import Path

from rescue.rescue_ui_launcher import (
    build_rescue_ui_status,
    launcher_declares_review_when_no_graphical_browser,
    launcher_does_not_claim_success_on_url_only,
    launcher_has_fallback_tui,
    launcher_writes_status_json,
    prepare_tree_skips_boot_network_onboarding,
    prepare_tree_skips_boot_telemetry_push,
    validate_rescue_ui_status_payload,
)

REPO = Path(__file__).resolve().parents[2]
LAUNCHER = REPO / "scripts/rescue-live/image/setuphelfer-rescue-ui-launch"
PREPARE = REPO / "scripts/rescue-live/prepare-controlled-live-build-tree.sh"
UI_SERVICE = REPO / "scripts/rescue-live/image/systemd/setuphelfer-rescue-ui.service"


class RescueUiLauncherTests(unittest.TestCase):
    def test_launcher_writes_status_and_fallback(self) -> None:
        text = LAUNCHER.read_text(encoding="utf-8")
        self.assertTrue(launcher_writes_status_json(text))
        self.assertTrue(launcher_has_fallback_tui(text))
        self.assertTrue(launcher_declares_review_when_no_graphical_browser(text))
        self.assertTrue(launcher_does_not_claim_success_on_url_only(text))
        self.assertIn("no_graphical_browser_available_or_not_started", text)

    def test_url_only_status_is_review_required_not_ready(self) -> None:
        payload = build_rescue_ui_status(
            ui_url="http://127.0.0.1:8765/rescue.html",
            server_started=True,
            display_mode="url_only",
            menu_visible=False,
            status="review_required",
            reason="no_graphical_browser_available_or_not_started",
        )
        self.assertEqual(validate_rescue_ui_status_payload(payload), [])

    def test_fallback_tui_cannot_be_ready(self) -> None:
        payload = build_rescue_ui_status(
            ui_url="http://127.0.0.1:8765/rescue.html",
            server_started=True,
            display_mode="fallback_tui",
            menu_visible=True,
            status="ready",
        )
        self.assertIn("NON_GRAPHICAL_CANNOT_BE_READY", validate_rescue_ui_status_payload(payload))

    def test_prepare_tree_skips_boot_network_and_telemetry(self) -> None:
        text = PREPARE.read_text(encoding="utf-8")
        self.assertTrue(prepare_tree_skips_boot_network_onboarding(text))
        self.assertTrue(prepare_tree_skips_boot_telemetry_push(text))

    def test_ui_service_no_network_online(self) -> None:
        text = UI_SERVICE.read_text(encoding="utf-8")
        self.assertNotIn("Requires=network-online.target", text)
        self.assertNotIn("Wants=network-online.target", text)


if __name__ == "__main__":
    unittest.main()
