"""RS-P1 full backup plan tests."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

_backend = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_backend))

from core.rescue_backup_plan_contract import build_rescue_full_backup_plan


class TestRescueBackupPlanFullBackupV1(unittest.TestCase):
    def _base(self, **kw):
        body = {
            "source_device": "/dev/nvme0n1",
            "source_size_bytes": 100_000_000_000,
            "backup_mode": "raw_image",
            "target_mode": "external_hdd",
            "target_mount": "/media/backup/Backup",
            "target_device": "/dev/sdb1",
            "target_label": "Backup",
            "free_bytes": 500_000_000_000,
            "fstype": "ext4",
            "encryption_requested": True,
            "verify_requested": True,
            "operator_confirm_source": True,
            "operator_confirm_target": True,
            "operator_confirm_no_restore": True,
        }
        body.update(kw)
        return body

    @patch("core.msi_windows_image_backup.mount_path_is_active", return_value=True)
    def test_windows_hdd_ready_execute_false(self, _m):
        plan = build_rescue_full_backup_plan(self._base())
        self.assertFalse(plan["execute_allowed"])
        self.assertTrue(plan["full_backup"])

    def test_stick_target_blocked(self):
        plan = build_rescue_full_backup_plan(
            self._base(target_mount="/media/volker/SETUP_LOGS", target_label="SETUP_LOGS")
        )
        codes = [e.get("code") for e in plan.get("errors") or []]
        self.assertIn("target_is_rescue_stick", codes)

    def test_cloud_pro_blocked(self):
        plan = build_rescue_full_backup_plan(self._base(target_mode="cloud_pro"))
        codes = [e.get("code") for e in plan.get("errors") or []]
        self.assertIn("cloud_pro_plan_only", codes)

    @patch("core.msi_windows_image_backup.mount_path_is_active", return_value=True)
    def test_encryption_blocks_execute(self, _m):
        plan = build_rescue_full_backup_plan(self._base(encryption_key_configured=False))
        self.assertFalse(plan["execute_allowed"])
        self.assertTrue(plan["encryption"]["blocks_execute"])


if __name__ == "__main__":
    unittest.main()
