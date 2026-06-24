"""Regression test: squashfs must contain chromium for GUI payload."""

from __future__ import annotations

import unittest
from pathlib import Path

from core.rescue_squashfs_react_shell_verify import squashfs_contains_react_rescue_shell

REPO = Path(__file__).resolve().parents[2]
BUILD = REPO / "build/rescue"


class RescueSquashfsChromiumGateTests(unittest.TestCase):
    def test_1_9_16_2_has_chromium_when_present(self) -> None:
        sq = BUILD / "filesystem.squashfs.repacked-1.9.16.2"
        if not sq.is_file():
            self.skipTest("1.9.16.2 squashfs not built")
        report = squashfs_contains_react_rescue_shell(sq)
        self.assertTrue(report["checks"]["chromium_browser"], report.get("checks"))

    def test_1_9_16_3_regression_missing_chromium(self) -> None:
        sq = BUILD / "filesystem.squashfs.repacked-1.9.16.3"
        if not sq.is_file():
            self.skipTest("1.9.16.3 squashfs not built")
        report = squashfs_contains_react_rescue_shell(sq)
        # Documents known-bad payload until repacked from 1.9.16.2 base.
        self.assertFalse(report["checks"]["chromium_browser"], "1.9.16.3 must be repacked — chromium missing")


if __name__ == "__main__":
    unittest.main()
