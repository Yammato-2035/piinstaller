"""RS-P1 disk role classifier tests."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

_backend = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_backend))

from core.rescue_disk_role_classifier import (
    ROLE_EXTERNAL_BACKUP,
    ROLE_RESCUE_STICK,
    ROLE_SETUP_LOGS,
    ROLE_WINDOWS_SYSTEM,
    classify_disk_role,
    validate_source_target_pair,
)


class TestRescueDiskRoleClassifierV1(unittest.TestCase):
    def test_rescue_stick_blocked_as_target(self):
        role = classify_disk_role({"path": "/dev/sda", "label": "SETUPHELFER", "tran": "usb"})
        self.assertEqual(role, ROLE_RESCUE_STICK)
        pair = validate_source_target_pair(
            {"path": "/dev/nvme0n1", "fstype": "ntfs", "type": "disk"},
            {"path": "/dev/sda", "label": "SETUPHELFER"},
        )
        self.assertFalse(pair["ok"])

    def test_setup_logs_blocked(self):
        role = classify_disk_role({"path": "/dev/sda2", "label": "SETUP_LOGS"})
        self.assertEqual(role, ROLE_SETUP_LOGS)

    def test_windows_source(self):
        role = classify_disk_role({"path": "/dev/nvme0n1"})
        self.assertEqual(role, ROLE_WINDOWS_SYSTEM)

    def test_external_target(self):
        role = classify_disk_role({"path": "/dev/sdb1", "label": "Backup", "tran": "usb", "mountpoint": "/media/x/Backup"})
        self.assertEqual(role, ROLE_EXTERNAL_BACKUP)

    def test_internal_linux_target_blocked(self):
        pair = validate_source_target_pair(
            {"path": "/dev/nvme0n1", "type": "disk"},
            {"path": "/dev/nvme1n1p2", "type": "disk"},
        )
        self.assertFalse(pair["ok"])

    def test_source_equals_target(self):
        pair = validate_source_target_pair({"path": "/dev/sdb"}, {"path": "/dev/sdb"})
        self.assertFalse(pair["ok"])


if __name__ == "__main__":
    unittest.main()
