"""Phase F.2: MSI Windows image backup execution gate — no real device writes in tests."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from core.msi_windows_image_backup import (
    F2_ALLOWED_SOURCE,
    OPERATOR_CONFIRMATION_1,
    OPERATOR_CONFIRMATION_2,
    build_backup_paths,
    discover_external_backup_mount,
    is_blockdevice_output_path,
    run_f2_preflight,
    validate_operator_confirmations,
)


class TestMsiWindowsImageBackupExecutionV1(unittest.TestCase):
    def test_source_must_be_nvme0n1(self):
        with patch.object(Path, "exists", return_value=True):
            pf = run_f2_preflight(
            source_device="/dev/nvme1n1",
            source_size_bytes=1000,
            target_mount="/media/user/Backup",
            target_device="/dev/sda1",
            free_bytes=10**15,
            fstype="ext4",
            operator_confirmation_1=OPERATOR_CONFIRMATION_1,
            operator_confirmation_2=OPERATOR_CONFIRMATION_2,
            )
        self.assertFalse(pf.ok)
        self.assertEqual(pf.reason, "blocked_invalid_source")

    def test_nvme1n1_as_target_mount_blocked_via_invalid(self):
        with patch.object(Path, "exists", return_value=True):
            pf = run_f2_preflight(
            source_device=F2_ALLOWED_SOURCE,
            source_size_bytes=1000,
            target_mount="/",
            target_device="/dev/nvme1n1",
            free_bytes=10**15,
            fstype="ext4",
            operator_confirmation_1=OPERATOR_CONFIRMATION_1,
            operator_confirmation_2=OPERATOR_CONFIRMATION_2,
            )
        self.assertFalse(pf.ok)

    def test_sdb_target_pattern_blocked(self):
        with patch.object(Path, "exists", return_value=True):
            pf = run_f2_preflight(
            source_device=F2_ALLOWED_SOURCE,
            source_size_bytes=1000,
            target_mount="/home/user",
            target_device="/dev/sdb",
            free_bytes=10**15,
            fstype="ext4",
            operator_confirmation_1=OPERATOR_CONFIRMATION_1,
            operator_confirmation_2=OPERATOR_CONFIRMATION_2,
            )
        self.assertFalse(pf.ok)

    def test_operator_confirmation_required(self):
        c1, c2 = validate_operator_confirmations("", "")
        self.assertFalse(c1 or c2)
        with patch.object(Path, "exists", return_value=True):
            pf = run_f2_preflight(
                source_device=F2_ALLOWED_SOURCE,
                source_size_bytes=1000,
                target_mount="/media/user/Backup",
                target_device="/dev/sda1",
                free_bytes=10**15,
                fstype="ext4",
            )
        self.assertEqual(pf.reason, "blocked_operator_confirmation_missing")

    def test_insufficient_capacity(self):
        with patch.object(Path, "exists", return_value=True):
            pf = run_f2_preflight(
            source_device=F2_ALLOWED_SOURCE,
            source_size_bytes=2_000_000_000_000,
            target_mount="/media/user/Backup",
            target_device="/dev/sda1",
            free_bytes=100_000_000_000,
            fstype="ext4",
            operator_confirmation_1=OPERATOR_CONFIRMATION_1,
            operator_confirmation_2=OPERATOR_CONFIRMATION_2,
            )
        self.assertFalse(pf.ok)
        self.assertEqual(pf.reason, "blocked_insufficient_target_capacity")

    def test_target_not_blockdevice_path(self):
        paths = build_backup_paths("/media/user/Backup", "20260616T120000Z")
        self.assertFalse(is_blockdevice_output_path(paths["image_partial"]))
        self.assertTrue(is_blockdevice_output_path("/dev/sda"))

    def test_partial_before_final_naming(self):
        paths = build_backup_paths("/media/x/Backup", "ts1")
        self.assertTrue(paths["image_partial"].endswith(".img.partial"))
        self.assertTrue(paths["image_final"].endswith(".img"))
        self.assertNotIn(".partial", paths["image_final"])

    def test_ok_preflight_has_manifest_paths(self):
        with patch.object(Path, "exists", return_value=True):
            pf = run_f2_preflight(
            source_device=F2_ALLOWED_SOURCE,
            source_size_bytes=1_000_000,
            target_mount="/media/user/Backup",
            target_device="/dev/sda1",
            free_bytes=9_000_000,
            fstype="ext4",
            operator_confirmation_1=OPERATOR_CONFIRMATION_1,
            operator_confirmation_2=OPERATOR_CONFIRMATION_2,
            timestamp="20260616T120000Z",
            )
        self.assertTrue(pf.ok)
        self.assertIn("manifest_json", pf.paths)
        self.assertIn("sha256_file", pf.paths)

    def test_discover_external_backup_mount_nested_findmnt(self):
        nested = {
            "filesystems": [
                {
                    "target": "/",
                    "source": "/dev/nvme1n1p2",
                    "fstype": "ext4",
                    "children": [
                        {
                            "target": "/media/user/Backup",
                            "source": "/dev/sda1",
                            "fstype": "ext4",
                        }
                    ],
                }
            ]
        }
        found = discover_external_backup_mount(nested)
        self.assertIsNotNone(found)
        self.assertEqual(found, ("/media/user/Backup", "/dev/sda1", "ext4"))

    def test_no_restore_fields_in_status_template(self):
        from core.msi_windows_image_backup import initial_status_payload

        with patch.object(Path, "exists", return_value=True):
            pf = run_f2_preflight(
            source_device=F2_ALLOWED_SOURCE,
            source_size_bytes=1_000_000,
            target_mount="/media/user/Backup",
            target_device="/dev/sda1",
            free_bytes=9_000_000,
            fstype="ext4",
            operator_confirmation_1=OPERATOR_CONFIRMATION_1,
            operator_confirmation_2=OPERATOR_CONFIRMATION_2,
            )
        st = initial_status_payload(pf, "job-1")
        self.assertFalse(st["restore_executed"])
        self.assertFalse(st["wipe_executed"])
        self.assertFalse(st["format_executed"])
        self.assertFalse(st["ntfs_mounted"])
        self.assertFalse(st["bitlocker_action_executed"])


if __name__ == "__main__":
    unittest.main()
