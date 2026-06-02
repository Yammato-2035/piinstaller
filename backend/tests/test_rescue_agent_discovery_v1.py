from __future__ import annotations

import unittest

from rescue_agent.discovery import discover_devserver


class RescueAgentDiscoveryTests(unittest.TestCase):
    def test_boot_param_endpoint_is_preferred(self) -> None:
        result = discover_devserver(
            profile="local_lab",
            rescue_mode_enabled=True,
            boot_param_endpoint="http://192.168.10.2:8000",
            mdns_endpoint="http://setuphelfer-dev.local:8000",
        )
        self.assertEqual(result["discovery_status"], "found")
        self.assertEqual(result["method"], "boot_param")

    def test_mdns_stub_finds_local_devserver(self) -> None:
        result = discover_devserver(
            profile="local_lab",
            rescue_mode_enabled=True,
            mdns_endpoint="http://setuphelfer-dev.local:8000",
        )
        self.assertEqual(result["discovery_status"], "found")
        self.assertEqual(result["method"], "mdns")

    def test_public_endpoint_blocked_without_allowlist(self) -> None:
        result = discover_devserver(
            profile="local_lab",
            rescue_mode_enabled=True,
            boot_param_endpoint="https://example.com",
        )
        self.assertEqual(result["discovery_status"], "blocked")
        self.assertIn("public_endpoint_blocked", result["errors"])

    def test_not_found_returns_clean_status(self) -> None:
        result = discover_devserver(profile="local_lab", rescue_mode_enabled=True)
        self.assertEqual(result["discovery_status"], "not_found")
        self.assertEqual(result["method"], "none")


if __name__ == "__main__":
    unittest.main()
