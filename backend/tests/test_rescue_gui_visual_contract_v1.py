"""RS-P3L Rescue GUI visual contract — static source + built artifact checks."""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
RESCUE_SRC = REPO / "frontend/src/rescue"
UI_OUT = REPO / "build/rescue/ui"
CSS = RESCUE_SRC / "rescue-shell.css"


class RescueGuiVisualContractV1(unittest.TestCase):
    def test_dashboard_has_eight_tiles(self) -> None:
        text = (RESCUE_SRC / "RescueDashboard.tsx").read_text(encoding="utf-8")
        self.assertIn("RESCUE_TILE_COUNT", text)
        self.assertIn("RESCUE_NAV_TILES.map", text)
        nav = (RESCUE_SRC / "rescueNavTiles.ts").read_text(encoding="utf-8")
        tile_ids = re.findall(r"id: '([a-z_]+)'", nav)
        self.assertIn("linux_migration", tile_ids)
        self.assertEqual(len(tile_ids), 9)
        self.assertIn("data_rescue", tile_ids)

    def test_required_markers_in_dashboard(self) -> None:
        dash = (RESCUE_SRC / "RescueDashboard.tsx").read_text(encoding="utf-8")
        for marker in (
            'data-rescue-logo="true"',
            'data-rescue-wordmark="true"',
            'data-rescue-version="true"',
            'data-rescue-tiles="true"',
        ):
            self.assertIn(marker, dash)

    def test_shell_toolbar_not_absolute_overlay(self) -> None:
        css = CSS.read_text(encoding="utf-8")
        self.assertNotIn(".rescue-top-bar", css)
        self.assertIn(".rescue-toolbar", css)
        self.assertNotRegex(css, r"\.rescue-toolbar\s*\{[^}]*position:\s*absolute")

    def test_main_uses_flex_scroll_viewport(self) -> None:
        css = CSS.read_text(encoding="utf-8")
        self.assertIn("min-height: 0", css)
        self.assertRegex(css, r"\.rescue-main\s*\{[^}]*overflow-y:\s*auto")

    def test_dark_background_no_white_main(self) -> None:
        css = CSS.read_text(encoding="utf-8")
        self.assertIn("#000000", css)
        self.assertIn("var(--rescue-bg)", css)
        self.assertNotRegex(css, r"background:\s*#fff", re.I)
        self.assertNotRegex(css, r"background:\s*white", re.I)

    def test_typography_minimums(self) -> None:
        css = CSS.read_text(encoding="utf-8")
        self.assertIn("font-size: 18px", css)
        self.assertIn("font-size: 42px", css)
        self.assertIn("font-size: 22px", css)
        self.assertIn("font-size: 16px", css)

    def test_system_and_shutdown_visible_in_shell(self) -> None:
        shell = (RESCUE_SRC / "RescueShellLayout.tsx").read_text(encoding="utf-8")
        self.assertIn("RescueSystemMenu", shell)
        self.assertIn("RescuePowerButton", shell)
        self.assertIn('data-rescue-shutdown="true"', (RESCUE_SRC / "RescuePowerButton.tsx").read_text(encoding="utf-8"))

    def test_language_flags_visible(self) -> None:
        flags = (RESCUE_SRC / "RescueLanguageFlags.tsx").read_text(encoding="utf-8")
        self.assertIn('data-rescue-language="true"', flags)
        self.assertIn("🇩🇪", flags)
        self.assertIn("🇬🇧", flags)

    def test_keyboard_navigation_present(self) -> None:
        self.assertTrue((RESCUE_SRC / "rescueKeyboardNav.ts").is_file())
        dash = (RESCUE_SRC / "RescueDashboard.tsx").read_text(encoding="utf-8")
        self.assertIn("moveTileFocus", dash)
        self.assertIn("rescue-focus-ring", dash)

    def test_analysis_cards_min_width(self) -> None:
        css = CSS.read_text(encoding="utf-8")
        self.assertIn("minmax(320px", css)

    def test_built_rescue_html_exists_after_build(self) -> None:
        if not UI_OUT.is_dir():
            self.skipTest("build/rescue/ui missing — run build-rescue-react-ui.sh first")
        self.assertTrue((UI_OUT / "rescue.html").is_file())
        bundle = next(UI_OUT.glob("assets/rescue-*.js"), None)
        self.assertIsNotNone(bundle)
        js = bundle.read_text(encoding="utf-8", errors="ignore")
        self.assertIn("Setuphelfer", js)
        self.assertIn("rescue-dashboard", js)


if __name__ == "__main__":
    unittest.main()
