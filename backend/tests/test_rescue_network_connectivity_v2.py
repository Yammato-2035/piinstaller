"""Network connectivity V2 tests."""

from __future__ import annotations

import unittest
from unittest.mock import patch

from core.rescue_network_connectivity_v2 import (
    build_network_connectivity_v2,
    detect_lan_blocks_wifi_regression,
)


class RescueNetworkConnectivityV2Tests(unittest.TestCase):
    def test_lan_blocks_wifi_regression(self) -> None:
        self.assertTrue(
            detect_lan_blocks_wifi_regression(
                {
                    "lan_connected": True,
                    "wlan_present": True,
                    "wifi_connected": False,
                    "wlan_link_up": False,
                }
            )
        )

    @patch("core.rescue_network_connectivity_v2._https_get", return_value=True)
    @patch("core.rescue_network_connectivity_v2._dns_lookup", return_value=True)
    @patch("core.rescue_network_connectivity_v2._default_route", return_value=True)
    @patch("core.rescue_network_connectivity_v2._interface_states")
    def test_full_chain_ok(self, iface, _route, _dns, _https) -> None:
        iface.return_value = {
            "lan_present": True,
            "wlan_present": True,
            "lan_link_up": True,
            "wifi_connected": True,
            "lan_connected": True,
            "wlan_link_up": True,
        }
        result = build_network_connectivity_v2()
        self.assertIn("dns_ok", result["issue_codes"])
        self.assertIn("https_ok", result["issue_codes"])


if __name__ == "__main__":
    unittest.main()
