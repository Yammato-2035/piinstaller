"""Explicit setuphelfer_mode=gui must allow GUI try (watchdog → TUI)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from core.rescue_msi_boot_profile import should_disable_gui_for_msi_compat  # noqa: E402


class GuiModeBypassMsiDisableTests(unittest.TestCase):
    def test_explicit_gui_mode_not_disabled_under_msi_nomodeset(self) -> None:
        cmd = (
            "boot=live setuphelfer_mode=gui setuphelfer_kiosk=1 setuphelfer_gui_watchdog=1 "
            "setuphelfer_msi_compat=1 pci=noaer nouveau.modeset=0 nomodeset"
        )
        self.assertFalse(should_disable_gui_for_msi_compat(cmd, dmi_suggests_msi_ge63=True))

    def test_text_msi_nomodeset_still_disables(self) -> None:
        cmd = (
            "boot=live setuphelfer_mode=text setuphelfer_msi_compat=1 "
            "pci=noaer nouveau.modeset=0 nomodeset"
        )
        self.assertTrue(should_disable_gui_for_msi_compat(cmd, dmi_suggests_msi_ge63=True))


if __name__ == "__main__":
    unittest.main()
