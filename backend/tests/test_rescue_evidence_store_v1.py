"""RS-F2B.1: SETUP_LOGS evidence store preference tests."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from core.rescue_setup_logs_persistence import detect_setup_logs_mount, resolve_rescue_evidence_root


class TestRescueEvidenceStoreV1(unittest.TestCase):
    def test_setup_logs_preferred_when_mounted(self):
        mounts = [
            {
                "target": "/media/volker/SETUP_LOGS",
                "source": "/dev/sda2",
                "fstype": "vfat",
                "options": "rw",
                "label": "SETUP_LOGS",
            }
        ]
        with patch("core.rescue_setup_logs_persistence.discover_mounts_flat", return_value=mounts):
            det = detect_setup_logs_mount()
        self.assertTrue(det["persistent"])
        self.assertIn("setuphelfer/evidence", det["evidence_root"])

    def test_run_fallback_non_persistent(self):
        with patch("core.rescue_setup_logs_persistence.discover_mounts_flat", return_value=[]):
            with patch("core.rescue_persistence.detect_rescue_stick_mount") as mock_stick:
                mock_stick.return_value = {"fallback": True, "writable_root": "/tmp/setuphelfer-evidence"}
                root = resolve_rescue_evidence_root()
        self.assertTrue(root.get("non_persistent"))

    def test_evidence_path_not_internal_disk(self):
        with patch("core.rescue_setup_logs_persistence.discover_mounts_flat", return_value=[]):
            root = resolve_rescue_evidence_root()
        path = str(root.get("evidence_root") or "")
        self.assertNotIn("/dev/nvme", path)
        self.assertNotIn("C:\\", path)


if __name__ == "__main__":
    unittest.main()
