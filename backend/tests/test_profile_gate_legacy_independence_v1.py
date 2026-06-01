"""Profile gate independence from legacy dev-dashboard and opt mapping."""

from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from core.install_profile import (
    get_install_profile_state,
    profile_gate_audit_route_paths,
    should_register_dev_server_router,
)


class ProfileGateLegacyIndependenceTests(unittest.TestCase):
    def test_opt_env_maps_to_release(self) -> None:
        with patch.dict(os.environ, {"SETUPHELFER_INSTALL_PROFILE": "opt"}, clear=True):
            st = get_install_profile_state()
            self.assertEqual(st.install_profile, "release")
            self.assertEqual(st.raw_install_profile, "opt")
            self.assertIn("legacy_profile_opt_mapped_to_release", st.profile_warnings)

    def test_release_registered_dev_routes_not_red_when_capabilities_off(self) -> None:
        with patch.dict(os.environ, {"SETUPHELFER_INSTALL_PROFILE": "release"}, clear=True):
            audit = profile_gate_audit_route_paths(
                ["/api/dev-dashboard/status", "/api/fleet/sessions"],
            )
            self.assertEqual(audit["profile_gate_status"], "green")

    def test_release_http_accessible_dev_route_red(self) -> None:
        with patch.dict(os.environ, {"SETUPHELFER_INSTALL_PROFILE": "release"}, clear=True):
            audit = profile_gate_audit_route_paths(
                [],
                http_accessible_prefixes=["/api/dev-dashboard/status"],
            )
            self.assertEqual(audit["profile_gate_status"], "red")

    def test_release_ignores_dev_server_override(self) -> None:
        with patch.dict(
            os.environ,
            {
                "SETUPHELFER_INSTALL_PROFILE": "release",
                "SETUPHELFER_DEV_SERVER_ENABLED": "true",
            },
            clear=True,
        ):
            st = get_install_profile_state()
            self.assertFalse(st.dev_server_enabled)
            self.assertFalse(should_register_dev_server_router())


if __name__ == "__main__":
    unittest.main()
