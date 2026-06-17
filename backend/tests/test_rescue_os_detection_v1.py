"""RS-P1 OS detection tests."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

_backend = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_backend))

from core.rescue_os_detection import classify_detected_os, detect_encryption_indicators


class TestRescueOsDetectionV1(unittest.TestCase):
    def test_windows_ntfs(self):
        out = classify_detected_os({"path": "/dev/nvme0n1p4", "fstype": "ntfs", "type": "disk"})
        self.assertEqual(out["os_family"], "windows")
        self.assertIn("raw_image", out["backup_modes"])

    def test_linux_ext4(self):
        out = classify_detected_os({"path": "/dev/nvme1n1p2", "fstype": "ext4", "type": "disk"})
        self.assertEqual(out["os_family"], "linux")

    def test_bitlocker_review(self):
        enc = detect_encryption_indicators({"fstype": "bitlocker"})
        self.assertEqual(enc["bitlocker_status"], "detected_key_missing")
        out = classify_detected_os({"path": "/dev/nvme0n1", "fstype": "BitLocker", "type": "disk"})
        self.assertTrue(out["review_required"])

    def test_luks_review(self):
        enc = detect_encryption_indicators({"fstype": "crypto_LUKS"})
        self.assertTrue(enc["luks_detected"])


if __name__ == "__main__":
    unittest.main()
