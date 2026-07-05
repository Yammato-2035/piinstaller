"""RS-P3O rescue backup execute and telemetry status tests."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

_backend = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_backend))

from core.msi_windows_image_backup import is_allowed_backup_source  # noqa: E402
from core.rescue_backup_execute import execute_rescue_backup  # noqa: E402
from core.rescue_backup_plan_contract import build_rescue_full_backup_plan  # noqa: E402


class TestRescueBackupScopeV1(unittest.TestCase):
    def test_ntfs_partition_without_tran(self) -> None:
        ok, scope = is_allowed_backup_source("/dev/sdb1", fstype="ntfs")
        self.assertTrue(ok)
        self.assertEqual(scope, "ntfs_partition")

    def test_system_partition_allowed(self) -> None:
        ok, scope = is_allowed_backup_source("/dev/nvme0n1p4")
        self.assertTrue(ok)
        self.assertEqual(scope, "system_partition")

    @patch("core.msi_windows_image_backup.mount_path_is_active", return_value=True)
    @patch("core.rescue_backup_plan_contract.resolve_mount_free_bytes", return_value=500_000_000_000)
    def test_execute_allowed_without_encryption_on_rescue(self, _f, _m) -> None:
        plan = build_rescue_full_backup_plan(
            {
                "source_device": "/dev/sdb1",
                "source_size_bytes": 8_000_000_000,
                "source_tran": "usb",
                "source_fstype": "ntfs",
                "backup_mode": "raw_image",
                "target_mode": "external_hdd",
                "target_mount": "/media/user/Backup",
                "target_device": "/dev/sdc1",
                "target_label": "Backup",
                "fstype": "ext4",
                "encryption_requested": False,
                "verify_requested": True,
                "operator_confirm_source": True,
                "operator_confirm_target": True,
                "operator_confirm_no_restore": True,
                "booted_from_rescue": True,
            }
        )
        self.assertTrue(plan.get("execute_allowed"))
        self.assertEqual(plan.get("source_scope"), "external_test")


class TestRescueBackupExecuteV1(unittest.TestCase):
    @patch("core.rescue_backup_execute._booted_from_rescue", return_value=False)
    def test_blocks_off_rescue(self, _b) -> None:
        out = execute_rescue_backup({})
        self.assertFalse(out["success"])
        self.assertEqual(out["code"], "not_rescue_boot")


if __name__ == "__main__":
    unittest.main()
