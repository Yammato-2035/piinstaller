"""Phase F.1: windows_ntfs_detection_contract — read-only, no bypass."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from core import windows_ntfs_detection_contract as c


def _win_layout_partitions():
    return [
        {"name": "nvme0n1p1", "fstype": "ntfs", "size_bytes": 800_000_000, "parttypename": "microsoft basic data"},
        {"name": "nvme0n1p2", "fstype": "vfat", "size_bytes": 500_000_000, "parttypename": "efi system"},
        {"name": "nvme0n1p4", "fstype": "ntfs", "size_bytes": 60 * 1024**3, "parttypename": "microsoft basic data"},
    ]


class TestWindowsNtfsDetectionContractV1(unittest.TestCase):
    def test_ntfs_efi_windows_detected(self):
        parts = _win_layout_partitions()
        cls = c.classify_windows_ntfs_layout(parts, [], [])
        self.assertTrue(cls["windows_detected"])
        self.assertTrue(cls["efi_detected"])
        self.assertTrue(cls["ntfs_detected"])

    def test_ntfs_only_review_path(self):
        parts = [{"name": "sdb1", "fstype": "ntfs", "size_bytes": 1_000_000_000}]
        win = c.detect_windows_indicators(parts)
        self.assertFalse(win["detected"])

    def test_bitlocker_no_file_access_claim(self):
        parts = [{"name": "nvme0n1p4", "fstype": "bitlocker", "parttypename": "bitlocker", "size_bytes": 0}]
        bl = c.detect_bitlocker_indicators(parts, [])
        self.assertEqual(bl["status"], "detected_key_missing")
        self.assertFalse(bl["file_access_without_key"])

    def test_no_source_blocked(self):
        cls = c.classify_windows_ntfs_layout([], [], [])
        dec = c.build_msi_windows_precheck_decision(cls)
        self.assertEqual(dec["status"], "blocked")
        self.assertFalse(dec["backup_allowed"])

    def test_write_and_backup_always_false_f1(self):
        parts = _win_layout_partitions()
        cls = c.classify_windows_ntfs_layout(
            parts,
            [],
            [],
            live_root_device="/dev/nvme1n1p2",
            efi_boot_hints=["Windows Boot Manager"],
        )
        dec = c.build_msi_windows_precheck_decision(
            cls,
            backup_target_candidates=[{"device": "/dev/sda", "external_confirmed": True, "role": "backup_target_candidate"}],
            operator_selected_source="/dev/nvme0n1",
        )
        self.assertFalse(dec["backup_allowed"])
        self.assertFalse(dec["restore_allowed"])
        self.assertFalse(dec["write_allowed"])
        self.assertTrue(dec["image_backup_plan_allowed"])

    def test_no_mount_fields_in_contract(self):
        payload = c.capabilities_payload()
        self.assertFalse(payload["supported"]["ntfs_write"])

    def test_no_password_bypass_fields(self):
        caps = c.capabilities_payload()["supported"]
        self.assertFalse(caps["password_reset"])
        self.assertFalse(caps["bitlocker_unlock"])

    def test_serial_redacted(self):
        a = c.redact_serial("S736NL0X905337T")
        b = c.redact_serial("S736NL0X905337T")
        c2 = c.redact_serial("OTHER")
        self.assertTrue(a.startswith("sha256:"))
        self.assertEqual(a, b)
        self.assertNotEqual(a, c2)

    def test_import_without_app(self):
        self.assertEqual(c.CONTRACT_VERSION, "1.0.0")

    def test_ambiguous_sources_review(self):
        parts = _win_layout_partitions()
        cls = c.classify_windows_ntfs_layout(parts, [], [])
        cls["source_device_candidates"] = ["/dev/nvme0n1", "/dev/nvme2n1"]
        dec = c.build_msi_windows_precheck_decision(cls)
        self.assertEqual(dec["status"], "review_required")


if __name__ == "__main__":
    unittest.main()
