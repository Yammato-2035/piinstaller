"""RS-P2C boot mode contract tests."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

_backend = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_backend))

from core.rescue_boot_mode_contract import parse_cmdline, should_start_gui, should_start_text_tui


class TestRescueBootModeContractV1(unittest.TestCase):
    def test_no_param_defaults_text(self):
        out = parse_cmdline("boot=live setuphelfer_rescue=1")
        self.assertEqual(out["setuphelfer_mode"], "text")
        self.assertFalse(out["setuphelfer_kiosk"])
        self.assertFalse(out["backup_execute_allowed"])

    def test_text_mode_no_gui(self):
        cmd = "boot=live setuphelfer_mode=text setuphelfer_kiosk=0"
        self.assertFalse(should_start_gui(cmd))
        self.assertTrue(should_start_text_tui(cmd))

    def test_gui_mode_with_watchdog(self):
        cmd = "boot=live setuphelfer_mode=gui setuphelfer_kiosk=1 setuphelfer_gui_watchdog=1"
        self.assertTrue(should_start_gui(cmd))

    def test_gui_failure_fallback_tui_allowed(self):
        cmd = "boot=live setuphelfer_mode=gui setuphelfer_kiosk=1"
        self.assertTrue(should_start_text_tui(cmd) or should_start_gui(cmd))

    def test_diagnostics_mode(self):
        out = parse_cmdline("setuphelfer_mode=diagnostics setuphelfer_collect_diagnostics=1")
        self.assertTrue(out["diagnostics_mode"])

    def test_backup_execute_false(self):
        out = parse_cmdline("setuphelfer_mode=text")
        self.assertFalse(out["backup_execute_allowed"])


if __name__ == "__main__":
    unittest.main()
