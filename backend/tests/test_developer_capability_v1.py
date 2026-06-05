"""Tests for developer DCC capability token gate."""

from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from core.developer_capability import (
    assess_developer_capability,
    developer_capability_status_for_api,
    is_dcc_route_allowed,
)


class DeveloperCapabilityTests(unittest.TestCase):
    def test_release_blocks_dcc_without_token(self) -> None:
        st = assess_developer_capability(
            install_profile="release",
            dev_control_enabled=False,
        )
        self.assertFalse(st["dcc_allowed"])
        self.assertFalse(st["developer_capability_valid"])

    def test_developer_profile_requires_valid_token(self) -> None:
        with patch.dict(os.environ, {"DCC_DEVELOPER_TOKEN": "dev-secret"}, clear=False):
            blocked, code = is_dcc_route_allowed(
                path="/api/dev-dashboard/status",
                install_profile="developer",
                dev_control_enabled=True,
                request_headers={},
            )
            self.assertFalse(blocked)
            self.assertEqual(code, "DEVELOPER_CAPABILITY_REQUIRED")

            allowed, code2 = is_dcc_route_allowed(
                path="/api/dev-dashboard/status",
                install_profile="developer",
                dev_control_enabled=True,
                request_headers={"Authorization": "Bearer dev-secret"},
            )
            self.assertTrue(allowed)
            self.assertIsNone(code2)

    def test_developer_profile_not_configured(self) -> None:
        with patch("core.developer_capability.load_configured_dcc_token", return_value=(None, None)):
            blocked, code = is_dcc_route_allowed(
                path="/api/dev-dashboard/status",
                install_profile="developer",
                dev_control_enabled=True,
                request_headers={"Authorization": "Bearer anything"},
            )
            self.assertFalse(blocked)
            self.assertEqual(code, "DEVELOPER_CAPABILITY_NOT_CONFIGURED")

    def test_status_api_never_exposes_token(self) -> None:
        with patch.dict(os.environ, {"DCC_DEVELOPER_TOKEN": "hidden-value"}, clear=False):
            st = developer_capability_status_for_api(
                install_profile="developer",
                dev_control_enabled=True,
            )
            dumped = str(st)
            self.assertNotIn("hidden-value", dumped)
            self.assertTrue(st["developer_capability_available"])
            self.assertFalse(st["developer_capability_valid"])
            self.assertFalse(st["dcc_allowed"])

    def test_header_token_source(self) -> None:
        with patch.dict(os.environ, {"DCC_DEVELOPER_TOKEN": "lab-token"}, clear=False):
            st = assess_developer_capability(
                install_profile="local_lab",
                dev_control_enabled=True,
                request_headers={"X-Setuphelfer-Developer-Token": "lab-token"},
            )
            self.assertTrue(st["developer_capability_valid"])
            self.assertTrue(st["dcc_allowed"])


if __name__ == "__main__":
    unittest.main()
