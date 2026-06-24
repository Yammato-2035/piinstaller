"""Automatische Vorbereitung /media/setuphelfer/<label>."""

from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from core.backup_target_auto_prepare import (
    BACKUP_TARGET_AUTO_MOUNT_FAILED,
    BACKUP_TARGET_AUTO_MOUNT_READY,
    ExternalBackupCandidate,
    discover_external_backup_candidates,
    prepare_setuphelfer_external_target,
    sanitize_setuphelfer_label,
)
from core.safe_device import WriteTargetProtectionError, validate_write_target

_MISSING_SETUPHELFER_TARGET = "/media/setuphelfer/__pytest_missing_br001__"


class TestBackupTargetAutoPrepareV1(unittest.TestCase):
    def test_sanitize_label(self) -> None:
        self.assertEqual(sanitize_setuphelfer_label("BR-001"), "br-001")
        self.assertEqual(sanitize_setuphelfer_label(""), "br001")

    @patch("core.backup_target_auto_prepare.list_classified_devices")
    def test_discover_skips_system_disk(self, mock_list) -> None:
        from core.safe_device import ClassifiedDevice, PartitionInfo

        mock_list.return_value = [
            ClassifiedDevice(
                id="/dev/nvme0n1",
                name="nvme0n1",
                type="nvme",
                size="1T",
                removable=False,
                mountpoints=["/"],
                filesystems=["ext4"],
                partitions=[
                    PartitionInfo(
                        name="nvme0n1p2",
                        device_id="/dev/nvme0n1p2",
                        filesystem="ext4",
                        mountpoints=["/"],
                        size="1T",
                        size_bytes=0,
                        flags=[],
                    )
                ],
                is_system_disk=True,
                is_boot_disk=False,
                is_foreign_os_disk=False,
                is_write_allowed=False,
            )
        ]
        self.assertEqual(discover_external_backup_candidates(), [])

    def test_prepare_bind_mount_success(self) -> None:
        cand = ExternalBackupCandidate(
            disk_id="/dev/sda",
            partition_id="/dev/sda1",
            uuid="44ce6f76-7896-4623-87b0-d81aedbed6d5",
            fstype="ext4",
            label="Backup",
            size_human="931G",
            existing_mount="/media/gabriel/Backup",
            transport="usb",
            removable=True,
        )

        calls: list[str] = []

        def fake_run(cmd, sudo=False, sudo_password=None, timeout=10):
            calls.append(cmd)
            if "findmnt -rn -T" in cmd:
                return {"success": True, "stdout": "/dev/sda1 /media/setuphelfer/br001 ext4\n"}
            return {"success": True, "stdout": "", "stderr": ""}

        with patch("core.backup_target_auto_prepare.discover_external_backup_candidates", return_value=[cand]):
            with patch("core.backup_target_auto_prepare._target_already_valid", side_effect=[False, True]):
                with patch("core.backup_target_auto_prepare._findmnt_target_mounted", return_value=True):
                    out = prepare_setuphelfer_external_target(
                        label="br001",
                        sudo_password="test",
                        run=fake_run,
                        mode="bind",
                    )
        self.assertEqual(out["status"], "ready")
        self.assertEqual(out["diagnosis_id"], BACKUP_TARGET_AUTO_MOUNT_READY)
        self.assertEqual(out.get("action"), "prepared")

    def test_missing_path_on_root_not_001(self) -> None:
        with patch("core.safe_device._assert_media_tree_traversable", lambda _p: None):
            with self.assertRaises(WriteTargetProtectionError) as ctx:
                validate_write_target(_MISSING_SETUPHELFER_TARGET)
        self.assertEqual(ctx.exception.diagnosis_id, "STORAGE-PROTECTION-007")


if __name__ == "__main__":
    unittest.main()
