"""Telemetry server must not expose remote command routes."""

from __future__ import annotations

import unittest

from dev.telemetry_mock_server_v2 import FORBIDDEN_PATH_PREFIXES


class TelemetryNoRemoteCommandsV1Tests(unittest.TestCase):
    def test_forbidden_routes_listed(self) -> None:
        for route in ("/execute", "/command", "/shell", "/fix", "/wipe"):
            self.assertIn(route, FORBIDDEN_PATH_PREFIXES)


if __name__ == "__main__":
    unittest.main()
