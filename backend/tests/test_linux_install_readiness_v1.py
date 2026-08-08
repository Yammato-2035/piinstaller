"""PI-RS-ASUS-AUTONOMOUS-DIAG-INSTALL-007: linux_install_readiness tests."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from core.hardware_baseline_contracts import BaselineStatus
from rescue.linux_install_readiness import evaluate_linux_install_readiness


def _disks() -> list[dict]:
    return [
        {
            "disk_id": "win-eui-aaa",
            "role_hint": "windows",
            "model": "Samsung SSD 970 EVO Plus 1TB",
            "capacity_bytes": 1000204886016,
            "critical_warning": 0,
            "media_errors": 0,
            "stable": True,
            "pci_path": "pci-0000:04:00.0",
        },
        {
            "disk_id": "linux-eui-bbb",
            "role_hint": "linux_target",
            "model": "Samsung SSD 970 EVO Plus 1TB",
            "capacity_bytes": 1000204886016,
            "critical_warning": 0,
            "media_errors": 0,
            "stable": True,
            "pci_path": "pci-0000:05:00.0",
        },
    ]


class TestLinuxInstallReadinessV1(unittest.TestCase):
    def test_ready_when_all_gates_pass(self) -> None:
        out = evaluate_linux_install_readiness(
            disks=_disks(),
            memory_status=BaselineStatus.NO_IMMEDIATE_ISSUE_DETECTED.value,
            cpu_status=BaselineStatus.NO_IMMEDIATE_ISSUE_DETECTED.value,
            windows_disk_id="win-eui-aaa",
            linux_target_disk_id="linux-eui-bbb",
            image_verified=True,
            efi_plan_isolated=True,
        )
        self.assertEqual(out["linux_install_readiness"], "ready")
        self.assertFalse(out["writes_allowed"])
        self.assertEqual(out["blockers"], [])
        self.assertIsNotNone(out["windows_device"])
        self.assertIsNotNone(out["linux_target"])
        self.assertNotEqual(out["windows_device"]["identity_hash"], out["linux_target"]["identity_hash"])
        self.assertTrue(str(out["windows_device"]["disk_id_redacted"]).startswith("disk:"))
        self.assertNotIn("nvme0n1", str(out["windows_device"]))
        self.assertNotIn("nvme1n1", str(out["linux_target"]))

    def test_same_target_blocked(self) -> None:
        out = evaluate_linux_install_readiness(
            disks=_disks(),
            memory_status=BaselineStatus.NO_IMMEDIATE_ISSUE_DETECTED.value,
            cpu_status=BaselineStatus.NO_IMMEDIATE_ISSUE_DETECTED.value,
            windows_disk_id="win-eui-aaa",
            linux_target_disk_id="win-eui-aaa",
            image_verified=True,
            efi_plan_isolated=True,
        )
        self.assertEqual(out["linux_install_readiness"], "blocked")
        self.assertIn("windows_and_linux_target_same_id", out["blockers"])
        self.assertFalse(out["writes_allowed"])

    def test_missing_dual_identity_blocked(self) -> None:
        out = evaluate_linux_install_readiness(
            disks=_disks(),
            memory_status=BaselineStatus.NO_IMMEDIATE_ISSUE_DETECTED.value,
            cpu_status=BaselineStatus.NO_IMMEDIATE_ISSUE_DETECTED.value,
            windows_disk_id="win-eui-aaa",
            linux_target_disk_id=None,
            image_verified=True,
            efi_plan_isolated=True,
        )
        self.assertEqual(out["linux_install_readiness"], "blocked")
        self.assertIn("missing_dual_identity", out["blockers"])

    def test_memory_immediate_issue_blocked(self) -> None:
        out = evaluate_linux_install_readiness(
            disks=_disks(),
            memory_status=BaselineStatus.IMMEDIATE_ISSUE_DETECTED.value,
            cpu_status=BaselineStatus.NO_IMMEDIATE_ISSUE_DETECTED.value,
            windows_disk_id="win-eui-aaa",
            linux_target_disk_id="linux-eui-bbb",
            image_verified=True,
            efi_plan_isolated=True,
        )
        self.assertEqual(out["linux_install_readiness"], "blocked")
        self.assertIn("memory_immediate_issue_detected", out["blockers"])

    def test_image_or_efi_gate_blocked(self) -> None:
        base = dict(
            disks=_disks(),
            memory_status=BaselineStatus.NO_IMMEDIATE_ISSUE_DETECTED.value,
            cpu_status=BaselineStatus.NO_IMMEDIATE_ISSUE_DETECTED.value,
            windows_disk_id="win-eui-aaa",
            linux_target_disk_id="linux-eui-bbb",
        )
        no_image = evaluate_linux_install_readiness(**base, image_verified=False, efi_plan_isolated=True)
        self.assertEqual(no_image["linux_install_readiness"], "blocked")
        self.assertIn("image_not_verified", no_image["blockers"])

        no_efi = evaluate_linux_install_readiness(**base, image_verified=True, efi_plan_isolated=False)
        self.assertEqual(no_efi["linux_install_readiness"], "blocked")
        self.assertIn("efi_plan_not_isolated", no_efi["blockers"])

    def test_target_critical_warning_and_media_errors_blocked(self) -> None:
        disks = _disks()
        disks[1]["critical_warning"] = 1
        out = evaluate_linux_install_readiness(
            disks=disks,
            memory_status=BaselineStatus.NO_IMMEDIATE_ISSUE_DETECTED.value,
            cpu_status=BaselineStatus.NO_IMMEDIATE_ISSUE_DETECTED.value,
            windows_disk_id="win-eui-aaa",
            linux_target_disk_id="linux-eui-bbb",
            image_verified=True,
            efi_plan_isolated=True,
        )
        self.assertEqual(out["linux_install_readiness"], "blocked")
        self.assertIn("linux_target_critical_warning", out["blockers"])

        disks = _disks()
        disks[1]["media_errors"] = 3
        out2 = evaluate_linux_install_readiness(
            disks=disks,
            memory_status=BaselineStatus.NO_IMMEDIATE_ISSUE_DETECTED.value,
            cpu_status=BaselineStatus.NO_IMMEDIATE_ISSUE_DETECTED.value,
            windows_disk_id="win-eui-aaa",
            linux_target_disk_id="linux-eui-bbb",
            image_verified=True,
            efi_plan_isolated=True,
        )
        self.assertEqual(out2["linux_install_readiness"], "blocked")
        self.assertIn("linux_target_media_errors", out2["blockers"])

    def test_degraded_memory_is_review_required(self) -> None:
        out = evaluate_linux_install_readiness(
            disks=_disks(),
            memory_status=BaselineStatus.DEGRADED.value,
            cpu_status=BaselineStatus.NO_IMMEDIATE_ISSUE_DETECTED.value,
            windows_disk_id="win-eui-aaa",
            linux_target_disk_id="linux-eui-bbb",
            image_verified=True,
            efi_plan_isolated=True,
        )
        self.assertEqual(out["linux_install_readiness"], "review_required")
        self.assertFalse(out["writes_allowed"])


if __name__ == "__main__":
    unittest.main()
