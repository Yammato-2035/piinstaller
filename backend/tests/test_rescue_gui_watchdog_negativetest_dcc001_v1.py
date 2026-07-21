"""Watchdog fallback negativetest — GUI fail must not fake-green BVR (DCC-001)."""

from __future__ import annotations

import unittest

from core.rescue_bvr_dcc_status import map_overall_status
from core.rescue_gui_watchdog_contract import build_gui_watchdog_result


class WatchdogFallbackNegativetestDcc001(unittest.TestCase):
    def test_http_not_ready_triggers_fallback_and_bvr_continues(self) -> None:
        out = build_gui_watchdog_result(
            backend_ok=False,
            frontend_ok=True,
            display_ok=True,
            browser_ok=True,
            timed_out=True,
        )
        self.assertTrue(out["fallback_to_tui"])
        self.assertFalse(out["execute_allowed"])  # watchdog itself does not execute BVR
        overall = map_overall_status(
            bvr_core_status="passed",
            gui_status="fallback",
            evidence_status="complete",
        )
        self.assertEqual(overall, "passed_with_gui_fallback")
        self.assertNotEqual(overall, "passed")

    def test_no_fake_green_when_gui_failed(self) -> None:
        overall = map_overall_status(
            bvr_core_status="passed",
            gui_status="failed",
            evidence_status="complete",
        )
        self.assertEqual(overall, "passed_with_gui_fallback")


if __name__ == "__main__":
    unittest.main()
