"""RS-P2A GUI autostart contract tests."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

_backend = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_backend))

from core.rescue_gui_autostart_contract import build_gui_autostart_status


class TestRescueGuiAutostartContractV1(unittest.TestCase):
    def test_gui_opt_in_not_default(self):
        out = build_gui_autostart_status(
            html_present=True, backend_running=True, kiosk_launcher_present=True
        )
        self.assertFalse(out["gui_enabled_by_default"])

    def test_text_fallback_on_backend_missing(self):
        out = build_gui_autostart_status(
            html_present=True, backend_running=False, kiosk_launcher_present=True
        )
        self.assertEqual(out["reason"], "backend_not_running")
        self.assertEqual(out["display_mode"], "text_fallback")

    def test_frontend_missing(self):
        out = build_gui_autostart_status(
            html_present=False, backend_running=True, kiosk_launcher_present=True
        )
        self.assertEqual(out["reason"], "frontend_missing")

    def test_no_execute(self):
        out = build_gui_autostart_status(
            html_present=True, backend_running=True, kiosk_launcher_present=True
        )
        self.assertFalse(out["execute_allowed"])


if __name__ == "__main__":
    unittest.main()
