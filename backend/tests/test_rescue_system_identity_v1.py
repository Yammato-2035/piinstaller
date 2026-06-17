"""RS-P1 system identity tests."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

_backend = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_backend))

from core.rescue_disk_role_classifier import ROLE_RESCUE_STICK
from core.rescue_system_identity import build_rescue_system_summary, detect_boot_mode


class TestRescueSystemIdentityV1(unittest.TestCase):
    def test_boot_mode_uefi_or_unknown(self):
        mode = detect_boot_mode()
        self.assertIn(mode, ("uefi", "bios", "unknown"))

    @patch("core.rescue_system_identity.discover_rescue_storage")
    def test_summary_execute_false(self, mock_disc):
        mock_disc.return_value = {
            "devices": [{"path": "/dev/sda", "label": "SETUPHELFER", "tran": "usb", "type": "disk"}],
            "blocked_devices": [],
        }
        summary = build_rescue_system_summary()
        self.assertFalse(summary["execute_allowed"])
        self.assertTrue(any(d.get("role") == ROLE_RESCUE_STICK for d in summary["devices"]))


if __name__ == "__main__":
    unittest.main()
