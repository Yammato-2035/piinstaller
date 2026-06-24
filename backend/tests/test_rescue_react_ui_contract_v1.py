"""Rescue React UI contract tests — static file checks."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
RESCUE_SRC = REPO / "frontend/src/rescue"


class RescueReactUiContractTests(unittest.TestCase):
    def test_rescue_app_entry_exists(self) -> None:
        self.assertTrue((RESCUE_SRC / "RescueApp.tsx").is_file())
        self.assertTrue((REPO / "frontend/rescue.html").is_file())

    def test_main_menu_actions_defined(self) -> None:
        text = (RESCUE_SRC / "RescueMainMenu.tsx").read_text(encoding="utf-8")
        for action in ("safe_check", "network", "export_logs", "advanced"):
            self.assertIn(action, text)

    def test_i18n_de_en_present(self) -> None:
        de = json.loads((RESCUE_SRC / "i18n/de.json").read_text(encoding="utf-8"))
        en = json.loads((RESCUE_SRC / "i18n/en.json").read_text(encoding="utf-8"))
        self.assertIn("title", de)
        self.assertIn("title", en)
        self.assertIn("menu", de)
        self.assertIn("menu", en)

    def test_start_center_and_dashboard_present(self) -> None:
        self.assertTrue((RESCUE_SRC / "RescueStartCenter.tsx").is_file())
        self.assertTrue((RESCUE_SRC / "RescueDashboard.tsx").is_file())
        self.assertTrue((RESCUE_SRC / "rescueMenuItems.ts").is_file())
        app = (RESCUE_SRC / "RescueApp.tsx").read_text(encoding="utf-8")
        self.assertIn("RescueDashboard", app)
        self.assertIn("RescueShellLayout", app)

    def test_no_systemd_failure_in_beginner_ui(self) -> None:
        app = (RESCUE_SRC / "RescueApp.tsx").read_text(encoding="utf-8")
        self.assertNotIn("systemd", app.lower())
        self.assertNotIn("failed unit", app.lower())

    def test_build_script_no_npm_install(self) -> None:
        script = (REPO / "scripts/rescue-live/build-rescue-react-ui.sh").read_text(encoding="utf-8")
        self.assertNotIn("npm install ", script)
        self.assertNotIn("apt install", script)
        self.assertNotIn("apt-get install", script)


if __name__ == "__main__":
    unittest.main()
