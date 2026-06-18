"""RS-P2C GUI watchdog contract tests."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

_backend = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_backend))

from core.rescue_gui_watchdog_contract import build_gui_watchdog_result


class TestRescueGuiWatchdogContractV1(unittest.TestCase):
    def test_missing_browser_fallback(self):
        out = build_gui_watchdog_result(
            backend_ok=True, frontend_ok=True, display_ok=True, browser_ok=False
        )
        self.assertTrue(out["fallback_to_tui"])
        self.assertEqual(out["gui_error_code"], "gui_browser_missing")

    def test_missing_display_fallback(self):
        out = build_gui_watchdog_result(
            backend_ok=True, frontend_ok=True, display_ok=False, browser_ok=True
        )
        self.assertEqual(out["gui_error_code"], "gui_display_missing")

    def test_backend_unreachable(self):
        out = build_gui_watchdog_result(
            backend_ok=False, frontend_ok=True, display_ok=True, browser_ok=True
        )
        self.assertEqual(out["gui_error_code"], "gui_backend_unreachable")

    def test_timeout(self):
        out = build_gui_watchdog_result(
            backend_ok=True,
            frontend_ok=True,
            display_ok=True,
            browser_ok=True,
            timed_out=True,
        )
        self.assertEqual(out["gui_error_code"], "gui_start_timeout")

    def test_evidence_no_execute(self):
        out = build_gui_watchdog_result(
            backend_ok=True, frontend_ok=True, display_ok=True, browser_ok=True, started=True
        )
        self.assertFalse(out["execute_allowed"])

    def test_no_backup_execute(self):
        out = build_gui_watchdog_result(
            backend_ok=False, frontend_ok=False, display_ok=False, browser_ok=False
        )
        self.assertFalse(out["execute_allowed"])


if __name__ == "__main__":
    unittest.main()
