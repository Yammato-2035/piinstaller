"""Rescue UI smoke gate — static contract blocker before payload/repack builds."""

from __future__ import annotations

import re
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
RESCUE_SRC = REPO / "frontend/src/rescue"
CSS = RESCUE_SRC / "rescue-shell.css"


def _read(name: str) -> str:
    return (RESCUE_SRC / name).read_text(encoding="utf-8")


class RescueUiSmokeGateV1(unittest.TestCase):
    """All tests must pass before squashfs/repack (see RESCUE_UI_SMOKE_GATE_SPEC)."""

    def test_sg01_toolbar_visible_in_shell(self) -> None:
        shell = _read("RescueShellLayout.tsx")
        css = CSS.read_text(encoding="utf-8")
        self.assertIn("className=\"rescue-toolbar\"", shell)
        self.assertIn(".rescue-toolbar", css)
        self.assertRegex(css, r"\.rescue-toolbar\s*\{[^}]*position:\s*sticky")

    def test_sg02_shutdown_visible(self) -> None:
        shell = _read("RescueShellLayout.tsx")
        power = _read("RescuePowerButton.tsx")
        self.assertIn("RescuePowerButton", shell)
        self.assertIn('data-rescue-shutdown="true"', power)

    def test_sg03_language_select_visible(self) -> None:
        shell = _read("RescueShellLayout.tsx")
        lang = _read("RescueLanguageSelect.tsx")
        self.assertIn("RescueLanguageSelect", shell)
        self.assertIn("rescue-language-select", lang)

    def test_sg04_logo_visible_on_dashboard(self) -> None:
        dash = _read("RescueDashboard.tsx")
        css = CSS.read_text(encoding="utf-8")
        self.assertIn('data-rescue-logo="true"', dash)
        self.assertIn(".rescue-brand-row", css)
        self.assertIn(".rescue-brand-row .rescue-hero-logo", css)

    def test_sg05_dashboard_visible(self) -> None:
        app = _read("RescueApp.tsx")
        dash = _read("RescueDashboard.tsx")
        self.assertIn("RescueDashboard", app)
        self.assertIn('data-rescue-tiles="true"', dash)
        self.assertIn('data-rescue-wordmark="true"', dash)

    def test_sg06_tiles_visible(self) -> None:
        nav = (RESCUE_SRC / "rescueNavTiles.ts").read_text(encoding="utf-8")
        tile_ids = re.findall(r"id: '([a-z_]+)'", nav)
        self.assertGreaterEqual(len(tile_ids), 9)
        self.assertIn("backup_create", tile_ids)
        self.assertIn("settings", tile_ids)

    def test_sg07_tiles_clickable_routing(self) -> None:
        app = _read("RescueApp.tsx")
        dash = _read("RescueDashboard.tsx")
        self.assertIn("onSelectTile", app)
        self.assertIn("onSelectTile?.(tile.id)", dash)
        self.assertIn("case 'backup_create':", app)
        self.assertIn("case 'network':", app)
        self.assertIn("case 'settings':", app)

    def test_sg08_no_full_width_tile_layout(self) -> None:
        css = CSS.read_text(encoding="utf-8")
        self.assertIn("max-width: min(1100px", css)
        self.assertIn("max-width: 520px", css)
        self.assertNotRegex(
            css,
            r"\.rescue-tile-btn\s*\{[^}]*width:\s*100vw",
        )

    def test_sg09_safe_walk_activatable(self) -> None:
        safe = _read("rescueSafeMode.ts")
        app = _read("RescueApp.tsx")
        self.assertIn("isRescueUiSafeWalk", safe)
        self.assertIn("safe_walk", safe)
        self.assertIn("RESCUE_UI_SAFE_WALK", safe)
        self.assertIn("isRescueUiSafeWalk()", app)
        self.assertIn("data-rescue-safe-walk", app)

    def test_sg10_screenshot_api_present(self) -> None:
        core = (REPO / "backend/core/rescue_ui_screenshot.py").read_text(encoding="utf-8")
        routes = (REPO / "backend/api/routes/rescue_ui.py").read_text(encoding="utf-8")
        rescue = (REPO / "backend/api/routes/rescue.py").read_text(encoding="utf-8")
        self.assertIn("capture_rescue_screenshot", core)
        self.assertIn("/screenshot", routes)
        self.assertIn("rescue_ui_router", rescue)
        script = REPO / "scripts/rescue-live/capture-rescue-screenshot.sh"
        self.assertTrue(script.is_file())

    def test_sg11_screenshot_capabilities_api(self) -> None:
        routes = (REPO / "backend/api/routes/rescue_ui.py").read_text(encoding="utf-8")
        core = (REPO / "backend/core/rescue_ui_screenshot.py").read_text(encoding="utf-8")
        self.assertIn("/screenshot/capabilities", routes)
        self.assertIn("build_screenshot_capabilities", core)

    def test_sg_home_toolbar_brand_hidden(self) -> None:
        app = _read("RescueApp.tsx")
        self.assertIn("showToolbarBrand={view !== 'menu'}", app)


if __name__ == "__main__":
    unittest.main()
