"""PI-RS-ASUS-AUTONOMOUS-DIAG-INSTALL-007 integration contract tests."""

from __future__ import annotations

import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


class AsusAutonomous007Contracts(unittest.TestCase):
    def test_highinfo_profile_exists(self) -> None:
        from rescue.asus_boot_profiles import ASUS_PROFILES, get_asus_profile

        self.assertIn("ASUS-TUI-BASELINE-HIGHINFO", ASUS_PROFILES)
        profile = get_asus_profile("ASUS-TUI-BASELINE-HIGHINFO")
        self.assertTrue(profile.get("highinfo"))
        self.assertFalse(profile.get("allows_chromium"))
        self.assertTrue(profile.get("xorg_probe_isolated"))
        self.assertIn("setuphelfer_highinfo=1", profile["cmdline_extra"])
        self.assertIn("setuphelfer_xorg_probe=1", profile["cmdline_extra"])

    def test_highinfo_boot_script_present(self) -> None:
        script = REPO / "scripts/rescue-live/image/setuphelfer-rescue-highinfo-boot.sh"
        self.assertTrue(script.is_file())
        text = script.read_text(encoding="utf-8")
        self.assertIn("chromium_started", text)
        self.assertIn("False", text)
        self.assertIn("setuphelfer-rescue-startx-forensic", text)

    def test_repack_installs_highinfo_script(self) -> None:
        text = (REPO / "scripts/rescue-live/repack-rescue-squashfs-react-shell.sh").read_text(
            encoding="utf-8"
        )
        self.assertIn("setuphelfer-rescue-highinfo-boot.sh", text)

    def test_entrypoint_calls_highinfo(self) -> None:
        text = (REPO / "scripts/rescue-live/image/setuphelfer-rescue-entrypoint.sh").read_text(
            encoding="utf-8"
        )
        self.assertIn("setuphelfer_rescue_highinfo_active", text)
        self.assertIn("setuphelfer-rescue-highinfo-boot", text)

    def test_install_readiness_never_allows_writes(self) -> None:
        from core.hardware_baseline_contracts import BaselineStatus
        from rescue.linux_install_readiness import evaluate_linux_install_readiness

        result = evaluate_linux_install_readiness(
            disks=[
                {
                    "disk_id": "stable-win",
                    "model": "WIN",
                    "capacity_bytes": 1,
                    "role_hint": "windows",
                    "stable": True,
                    "critical_warning": 0,
                },
                {
                    "disk_id": "stable-linux",
                    "model": "LIN",
                    "capacity_bytes": 1,
                    "role_hint": "linux_target",
                    "stable": True,
                    "critical_warning": 0,
                    "media_errors": 0,
                },
            ],
            memory_status=BaselineStatus.NO_IMMEDIATE_ISSUE_DETECTED.value,
            cpu_status=BaselineStatus.NO_IMMEDIATE_ISSUE_DETECTED.value,
            windows_disk_id="stable-win",
            linux_target_disk_id="stable-linux",
            image_verified=True,
            efi_plan_isolated=True,
        )
        self.assertFalse(result.get("writes_allowed", True))


if __name__ == "__main__":
    unittest.main()
