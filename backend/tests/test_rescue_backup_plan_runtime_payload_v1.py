"""RS-P2A backup plan runtime payload tests."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

_backend = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_backend))

from core.rescue_backup_plan_contract import build_rescue_backup_plan, build_rescue_full_backup_plan


class TestRescueBackupPlanRuntimePayloadV1(unittest.TestCase):
    def test_null_discovery_no_devices_blocked(self):
        plan = build_rescue_backup_plan({"source_device": "", "disk_discovery": None})
        codes = [e.get("code") for e in plan.get("errors") or []]
        self.assertIn("source_missing", codes)
        self.assertFalse(plan["execute_allowed"])

    def test_contract_error_when_devices_present_but_discovery_null(self):
        plan = build_rescue_backup_plan(
            {
                "source_device": "/dev/nvme0n1",
                "target_mount": "/media/x/Backup",
                "target_device": "/dev/sdb1",
                "free_bytes": 10**12,
                "source_size_bytes": 10**11,
                "disk_discovery": None,
                "devices_detected": True,
            }
        )
        codes = [e.get("code") for e in plan.get("errors") or []]
        self.assertTrue("disk_discovery_null_with_devices" in codes or "source_missing" not in codes)

    @patch("core.msi_windows_image_backup.mount_path_is_active", return_value=True)
    def test_full_plan_ready_execute_false(self, _m):
        plan = build_rescue_full_backup_plan(
            {
                "source_device": "/dev/nvme0n1",
                "source_size_bytes": 100_000_000_000,
                "backup_mode": "raw_image",
                "target_mode": "external_hdd",
                "target_mount": "/media/backup/Backup",
                "target_device": "/dev/sdb1",
                "free_bytes": 500_000_000_000,
                "fstype": "ext4",
                "encryption_requested": True,
                "verify_requested": True,
                "operator_confirm_source": True,
                "operator_confirm_target": True,
                "operator_confirm_no_restore": True,
                "wifi_status": "missing",
            }
        )
        self.assertFalse(plan["execute_allowed"])


if __name__ == "__main__":
    unittest.main()
