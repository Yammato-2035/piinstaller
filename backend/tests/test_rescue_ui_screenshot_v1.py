"""Rescue UI screenshot API + safe-walk contract tests."""

from __future__ import annotations

import unittest
from pathlib import Path
from unittest.mock import patch

REPO = Path(__file__).resolve().parents[2]
RESCUE_SRC = REPO / "frontend/src/rescue"


class RescueUiScreenshotCoreTests(unittest.TestCase):
    def test_capabilities_blocked_without_tool(self) -> None:
        from core.rescue_ui_screenshot import build_screenshot_capabilities

        with patch("core.rescue_ui_screenshot._pick_tool", return_value=(None, [])):
            with patch(
                "core.rescue_ui_screenshot._screenshot_dir",
                return_value=(None, "setup_logs_not_writable"),
            ):
                body = build_screenshot_capabilities()
        self.assertEqual(body["status"], "blocked")
        self.assertIn("screenshot_tool_missing", body["errors"])

    def test_capture_invalid_label(self) -> None:
        from core.rescue_ui_screenshot import capture_rescue_screenshot

        result = capture_rescue_screenshot("bad label!")
        self.assertEqual(result["status"], "failed")
        self.assertIn("invalid_label", result["errors"])

    def test_capture_blocked_without_setup_logs(self) -> None:
        from core.rescue_ui_screenshot import capture_rescue_screenshot

        with patch("core.rescue_ui_screenshot._pick_tool", return_value=("grim", ["/usr/bin/grim"])):
            with patch(
                "core.rescue_ui_screenshot._screenshot_dir",
                return_value=(None, "setup_logs_not_writable"),
            ):
                result = capture_rescue_screenshot("start-menu")
        self.assertEqual(result["status"], "blocked")


class RescueStartMenuLayoutContractTests(unittest.TestCase):
    def test_rescue_app_uses_shell_and_dashboard(self) -> None:
        app = (RESCUE_SRC / "RescueApp.tsx").read_text(encoding="utf-8")
        self.assertIn("RescueShellLayout", app)
        self.assertIn("RescueDashboard", app)
        self.assertIn("showToolbarBrand={view !== 'menu'}", app)
        self.assertIn("onSelectTile", app)

    def test_safe_walk_module_present(self) -> None:
        text = (RESCUE_SRC / "rescueSafeMode.ts").read_text(encoding="utf-8")
        self.assertIn("isRescueUiSafeWalk", text)
        self.assertIn("safe_walk", text)

    def test_tile_grid_max_width_in_css(self) -> None:
        css = (RESCUE_SRC / "rescue-shell.css").read_text(encoding="utf-8")
        self.assertIn("max-width: min(1100px", css)
        self.assertIn("max-width: 520px", css)

    def test_toolbar_sticky_visible(self) -> None:
        css = (RESCUE_SRC / "rescue-shell.css").read_text(encoding="utf-8")
        self.assertRegex(css, r"\.rescue-toolbar\s*\{[^}]*position:\s*sticky")

    def test_screenshot_script_exists(self) -> None:
        script = REPO / "scripts/rescue-live/capture-rescue-screenshot.sh"
        self.assertTrue(script.is_file())
        self.assertIn("/api/rescue/ui/screenshot", script.read_text(encoding="utf-8"))

    def test_screenshot_api_route_registered(self) -> None:
        rescue = (REPO / "backend/api/routes/rescue.py").read_text(encoding="utf-8")
        self.assertIn("rescue_ui_router", rescue)


if __name__ == "__main__":
    unittest.main()
