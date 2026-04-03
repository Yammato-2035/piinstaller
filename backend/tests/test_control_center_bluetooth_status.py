"""
Unit-Tests: ControlCenterModule.get_bluetooth_status (gemocktes subprocess).

Lauf: cd backend && python -m unittest tests.test_control_center_bluetooth_status -v
"""

import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from modules.control_center import (  # noqa: E402
    BLUETOOTH_ADAPTER_MISSING,
    BLUETOOTH_OK,
    BLUETOOTH_RFKILL_BLOCKED,
    BLUETOOTH_SERVICE_UNAVAILABLE,
    BLUETOOTH_UNKNOWN_ERROR,
    ControlCenterModule,
)


def _cp(cmd, returncode=0, stdout="", stderr=""):
    return subprocess.CompletedProcess(cmd, returncode, stdout, stderr)


class TestGetBluetoothStatus(unittest.TestCase):
    def setUp(self):
        self.m = ControlCenterModule()

    @patch("modules.control_center.subprocess.run")
    def test_bluetoothctl_missing_returns_service_unavailable(self, mock_run):
        def side_effect(cmd, **kwargs):
            if cmd[0] == "rfkill":
                return _cp(cmd, 0, "0: hci0: Bluetooth\n\tSoft blocked: no\n")
            if cmd[0] == "bluetoothctl" and "show" in cmd:
                raise FileNotFoundError()
            self.fail(f"unexpected cmd: {cmd}")

        mock_run.side_effect = side_effect
        r = self.m.get_bluetooth_status("")
        self.assertEqual(r["status"], "error")
        self.assertEqual(r["error_code"], BLUETOOTH_SERVICE_UNAVAILABLE)
        self.assertIn("bluetoothctl", r["message"].lower())

    @patch("modules.control_center.subprocess.run")
    def test_rfkill_soft_blocked_returns_success_with_code(self, mock_run):
        def side_effect(cmd, **kwargs):
            if cmd[0] == "rfkill":
                return _cp(cmd, 0, "0: hci0: Bluetooth\n\tSoft blocked: yes\n")
            self.fail("bluetoothctl should not run when rfkill blocks")

        mock_run.side_effect = side_effect
        r = self.m.get_bluetooth_status("")
        self.assertEqual(r["status"], "success")
        self.assertIs(r["enabled"], False)
        self.assertEqual(r["connected_devices"], [])
        self.assertEqual(r["code"], BLUETOOTH_RFKILL_BLOCKED)

    @patch("modules.control_center.subprocess.run")
    def test_normal_path_success(self, mock_run):
        def side_effect(cmd, **kwargs):
            if cmd[0] == "rfkill":
                return _cp(cmd, 0, "\tSoft blocked: no\n")
            if cmd[0] == "bluetoothctl" and "show" in cmd:
                return _cp(cmd, 0, "Controller AA:BB:CC:DD:EE:FF (public)\n\tPowered: yes\n")
            if cmd[0] == "bluetoothctl" and "Connected" in cmd:
                return _cp(cmd, 0, "Device 11:22:33:44:55:66 My Headphones\n")
            self.fail(f"unexpected cmd: {cmd}")

        mock_run.side_effect = side_effect
        r = self.m.get_bluetooth_status("")
        self.assertEqual(r["status"], "success")
        self.assertIs(r["enabled"], True)
        self.assertEqual(r["code"], BLUETOOTH_OK)
        self.assertEqual(len(r["connected_devices"]), 1)
        self.assertEqual(r["connected_devices"][0]["mac"], "11:22:33:44:55:66")
        self.assertEqual(r["connected_devices"][0]["name"], "My Headphones")

    @patch("modules.control_center.subprocess.run")
    def test_unexpected_devices_output_returns_error(self, mock_run):
        def side_effect(cmd, **kwargs):
            if cmd[0] == "rfkill":
                return _cp(cmd, 0, "soft blocked: no\n")
            if "show" in cmd:
                return _cp(cmd, 0, "Controller …\n")
            if "Connected" in cmd:
                return _cp(cmd, 0, "not a device line\n")
            self.fail(f"unexpected cmd: {cmd}")

        mock_run.side_effect = side_effect
        r = self.m.get_bluetooth_status("")
        self.assertEqual(r["status"], "error")
        self.assertEqual(r["error_code"], BLUETOOTH_UNKNOWN_ERROR)

    @patch("modules.control_center.subprocess.run")
    def test_no_default_controller_adapter_missing(self, mock_run):
        def side_effect(cmd, **kwargs):
            if cmd[0] == "rfkill":
                return _cp(cmd, 0, "")
            if "show" in cmd:
                return _cp(cmd, 1, "", "No default controller available\n")
            self.fail("devices Connected should not run")

        mock_run.side_effect = side_effect
        r = self.m.get_bluetooth_status("")
        self.assertEqual(r["status"], "error")
        self.assertEqual(r["error_code"], BLUETOOTH_ADAPTER_MISSING)

    @patch("modules.control_center.subprocess.run")
    def test_devices_connected_nonzero_rc_error(self, mock_run):
        def side_effect(cmd, **kwargs):
            if cmd[0] == "rfkill":
                return _cp(cmd, 0, "")
            if "show" in cmd:
                return _cp(cmd, 0, "ok\n")
            if "Connected" in cmd:
                return _cp(cmd, 1, "", "unknown subcommand\n")
            self.fail(f"unexpected cmd: {cmd}")

        mock_run.side_effect = side_effect
        r = self.m.get_bluetooth_status("")
        self.assertEqual(r["status"], "error")
        self.assertEqual(r["error_code"], BLUETOOTH_UNKNOWN_ERROR)


if __name__ == "__main__":
    unittest.main()
