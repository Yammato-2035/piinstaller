"""SquashFS React shell content verification tests."""

from __future__ import annotations

import unittest
from pathlib import Path

from core.rescue_squashfs_react_shell_verify import (
    squashfs_contains_react_rescue_shell,
    squashfs_verify_launcher_payload,
)

REPO = Path(__file__).resolve().parents[2]
REPACKED = REPO / "build/rescue/filesystem.squashfs.repacked-1.7.10.1"


class RescueSquashfsReactShellVerifyTests(unittest.TestCase):
    def test_repacked_squashfs_contains_react_shell(self) -> None:
        if not REPACKED.is_file():
            self.skipTest("repacked squashfs not built yet")
        report = squashfs_contains_react_rescue_shell(REPACKED)
        self.assertTrue(report["unsquashfs_ok"])
        self.assertTrue(report["contains_react_rescue_shell"], report.get("checks"))
        self.assertFalse(report["network_required_before_menu"])
        self.assertFalse(report["telemetry_required_before_menu"])

    def test_repacked_squashfs_contains_launcher_boot_fix(self) -> None:
        if not REPACKED.is_file():
            self.skipTest("repacked squashfs not built yet")
        report = squashfs_verify_launcher_payload(REPACKED)
        self.assertTrue(report["contains_rescue_ui_launcher_fix"], report)
        self.assertTrue(report["contains_fallback_tui"])
        self.assertTrue(report["contains_network_boot_skip"])
        self.assertTrue(report["contains_telemetry_default_skipped"])
        self.assertTrue(report["contains_wait_online_neutralization"])
        self.assertFalse(report["network_boot_autostart"])
        self.assertFalse(report["telemetry_boot_autostart"])


if __name__ == "__main__":
    unittest.main()
