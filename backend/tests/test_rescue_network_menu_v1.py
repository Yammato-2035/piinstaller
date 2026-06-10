"""Rescue network menu — crash-safe interactive flow."""

from __future__ import annotations

import unittest
from pathlib import Path

from rescue.rescue_network_menu import (
    INTERACTIVE_NON_FATAL_ERRORS,
    network_common_checks_nmcli,
    network_common_has_safe_interactive_wrapper,
    network_common_tty_override,
    network_onboarding_skips_boot_without_user,
    network_script_disables_errexit_after_common,
    network_script_has_interactive_non_fatal_exit,
)

REPO = Path(__file__).resolve().parents[2]
NETWORK = REPO / "scripts/rescue-live/image/setuphelfer-rescue-network-onboarding"
COMMON = REPO / "scripts/rescue-live/image/setuphelfer-rescue-common.sh"


class RescueNetworkMenuTests(unittest.TestCase):
    def setUp(self) -> None:
        self.network = NETWORK.read_text(encoding="utf-8")
        self.common = COMMON.read_text(encoding="utf-8")

    def test_nmcli_missing_handled(self) -> None:
        self.assertIn("NMCLI_MISSING", self.network)
        self.assertTrue(network_common_checks_nmcli(self.common))

    def test_no_wlan_hardware_non_fatal_interactive(self) -> None:
        self.assertIn("WIFI_DEVICE_NOT_FOUND", self.network)
        self.assertIn("WIFI_DEVICE_NOT_FOUND", INTERACTIVE_NON_FATAL_ERRORS)

    def test_no_networks_return_to_menu(self) -> None:
        self.assertIn("return_to_menu", self.network)
        self.assertIn("OFFLINE_BY_OPERATOR", self.network)

    def test_user_abort_returns_to_menu(self) -> None:
        self.assertIn("return 20", self.common)
        self.assertIn("OFFLINE_BY_OPERATOR", self.network)

    def test_errexit_disabled_after_common(self) -> None:
        self.assertTrue(network_script_disables_errexit_after_common(self.network))

    def test_interactive_non_fatal_exit_codes(self) -> None:
        self.assertTrue(network_script_has_interactive_non_fatal_exit(self.network))

    def test_safe_wrapper_in_common(self) -> None:
        self.assertTrue(network_common_has_safe_interactive_wrapper(self.common))
        self.assertTrue(network_common_tty_override(self.common))

    def test_no_network_before_main_menu(self) -> None:
        self.assertTrue(network_onboarding_skips_boot_without_user(self.network))

    def test_no_secrets_in_network_json_template(self) -> None:
        self.assertIn('"secrets_exposed": false', self.network)
        self.assertNotIn("wifi_password", self.network.lower())
        self.assertNotIn("psk=", self.network.lower())


if __name__ == "__main__":
    unittest.main()
