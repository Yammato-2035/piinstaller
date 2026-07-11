"""PI-RS-MSI-FIX-001 boot-progress tty1 race tests."""

from __future__ import annotations

import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
BOOT_PROGRESS = REPO_ROOT / "scripts/rescue-live/image/setuphelfer-rescue-boot-progress"


class MsiFix001BootProgressTests(unittest.TestCase):
    def test_no_forced_tty_clear_on_last_step(self) -> None:
        text = BOOT_PROGRESS.read_text(encoding="utf-8")
        self.assertNotIn('show_tty "$msg" 1', text)
        self.assertNotIn('show_tty "Bootvorbereitung abgeschlossen — GUI übernimmt." 1', text)

    def test_safe_ui_final_message(self) -> None:
        text = BOOT_PROGRESS.read_text(encoding="utf-8")
        self.assertIn("Textmenü bereit", text)
        self.assertIn("setuphelfer_rescue_tty1_clear_allowed", text)

    def test_shield_called_at_start(self) -> None:
        text = BOOT_PROGRESS.read_text(encoding="utf-8")
        self.assertIn("setuphelfer_rescue_shield_console_early", text)


if __name__ == "__main__":
    unittest.main()
