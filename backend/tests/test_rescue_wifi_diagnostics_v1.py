"""RS-P1 WiFi diagnostics tests."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

_backend = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_backend))

from core.rescue_wifi_diagnostics import classify_wifi_status


class TestRescueWifiDiagnosticsV1(unittest.TestCase):
    @patch("core.rescue_wifi_diagnostics._run")
    def test_unmanaged_suggestion(self, mock_run):
        responses = {
            ("rfkill", "list"): "Soft blocked: no",
            ("iw", "dev"): "Interface wlo1",
            ("nmcli", "radio"): "WIFI enabled",
            ("nmcli", "-t", "-f", "DEVICE,TYPE,STATE", "device", "status"): "wlo1:wifi:unmanaged",
            ("lsmod",): "iwlwifi",
            ("dmesg", "--ctime"): "",
        }
        mock_run.side_effect = lambda cmd: responses.get(tuple(cmd), "")
        out = classify_wifi_status()
        self.assertIn("nmcli_device_set_managed_yes", out["fix_suggestions"])
        self.assertEqual(out["ui_status"], "interface_unmanaged")

    @patch("core.rescue_wifi_diagnostics._run")
    def test_hdd_not_blocked(self, mock_run):
        responses = {
            ("rfkill", "list"): "",
            ("iw", "dev"): "",
            ("nmcli", "radio"): "",
            ("nmcli", "-t", "-f", "DEVICE,TYPE,STATE", "device", "status"): "wlo1:wifi:disconnected",
            ("lsmod",): "",
            ("dmesg", "--ctime"): "",
        }
        mock_run.side_effect = lambda cmd: responses.get(tuple(cmd), "")
        out = classify_wifi_status()
        self.assertFalse(out["blocks_local_hdd_backup"])


if __name__ == "__main__":
    unittest.main()
