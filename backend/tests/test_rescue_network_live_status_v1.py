"""Rescue live boot status tests."""

from __future__ import annotations

import unittest
from unittest.mock import patch

from core.rescue_network_live_status_v1 import build_live_boot_status


class RescueNetworkLiveStatusV1Tests(unittest.TestCase):
    @patch("core.rescue_network_live_status_v1.build_telemetry_connectivity_v1")
    @patch("core.rescue_network_live_status_v1.build_network_connectivity_v2")
    def test_connected_when_wifi(self, net, tel) -> None:
        net.return_value = {
            "interfaces": {"wifi_connected": True, "lan_connected": False, "wlan_present": True},
        }
        tel.return_value = {"targets": {"x": 1}, "issue_codes": []}
        status = build_live_boot_status()
        self.assertEqual(status["network"]["status"], "connected")


if __name__ == "__main__":
    unittest.main()
