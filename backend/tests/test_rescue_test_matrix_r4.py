"""Phase R.4: rescue_test_matrix static build probes."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

_BACKEND = Path(__file__).resolve().parent.parent
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))


class TestRescueTestMatrixR4(unittest.TestCase):
    def test_r4_static_entries_present(self) -> None:
        import core.rescue_test_matrix as tm

        entries = tm.build_r4_static_matrix_entries()
        ids = {e["id"] for e in entries}
        for expected in (
            "R4-BROWSER-PKG-001",
            "R4-DISPLAY-PKG-001",
            "R4-KIOSK-001",
            "R4-GRUB-THEME-001",
            "R4-GRUB-ASSETS-001",
            "R4-TELEM-SPOOL-INT-001",
            "R4-TELEM-PUSH-001",
        ):
            self.assertIn(expected, ids)

    def test_browser_package_green_after_r4(self) -> None:
        import core.rescue_test_matrix as tm

        browser = next(e for e in tm.build_r4_static_matrix_entries() if e["id"] == "R4-BROWSER-PKG-001")
        self.assertEqual(browser["status"], "green")
        self.assertIn("chromium", browser["observed"])

    def test_telemetry_spool_integration_detected(self) -> None:
        import core.rescue_test_matrix as tm

        entry = next(e for e in tm.build_r4_static_matrix_entries() if e["id"] == "R4-TELEM-SPOOL-INT-001")
        self.assertEqual(entry["status"], "green")

    def test_full_matrix_includes_r4(self) -> None:
        import core.rescue_test_matrix as tm

        entries = tm.build_rescue_test_matrix_entries()
        ids = {e["id"] for e in entries}
        self.assertIn("R4-KIOSK-001", ids)
        self.assertGreaterEqual(len(entries), 25)


if __name__ == "__main__":
    unittest.main()
