"""Install profile defaults and capability gates."""

from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from core.install_profile import (
    FORBIDDEN_API_PREFIXES_RELEASE,
    get_install_profile_state,
    path_allowed_for_active_profile,
    profile_gate_audit_route_paths,
)


class InstallProfileGateTests(unittest.TestCase):
    def test_default_profile_is_release(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            os.environ.pop("SETUPHELFER_INSTALL_PROFILE", None)
            os.environ.pop("PI_INSTALLER_DEV", None)
            st = get_install_profile_state()
            self.assertEqual(st.install_profile, "release")
            self.assertFalse(st.fleet_sessions_enabled)
            self.assertFalse(st.dev_diagnostics_enabled)
            self.assertFalse(st.rescue_remote_enabled)

    def test_local_lab_enables_dev_capabilities(self) -> None:
        with patch.dict(os.environ, {"SETUPHELFER_INSTALL_PROFILE": "local_lab"}, clear=True):
            st = get_install_profile_state()
            self.assertTrue(st.fleet_sessions_enabled)
            self.assertTrue(st.dev_diagnostics_enabled)
            self.assertTrue(st.rescue_remote_enabled)
            self.assertFalse(st.write_runbooks_enabled)

    def test_public_exposure_default_false(self) -> None:
        with patch.dict(os.environ, {"SETUPHELFER_INSTALL_PROFILE": "local_lab"}, clear=True):
            st = get_install_profile_state()
            self.assertFalse(st.public_exposure_allowed)

    def test_release_blocks_fleet_path(self) -> None:
        with patch.dict(os.environ, {"SETUPHELFER_INSTALL_PROFILE": "release"}, clear=True):
            self.assertFalse(path_allowed_for_active_profile("/api/fleet/sessions"))

    def test_release_audit_red_when_fleet_http_accessible(self) -> None:
        with patch.dict(os.environ, {"SETUPHELFER_INSTALL_PROFILE": "release"}, clear=True):
            audit = profile_gate_audit_route_paths(
                ["/api/fleet/sessions"],
                http_accessible_prefixes=["/api/fleet/sessions"],
            )
            self.assertEqual(audit["profile_gate_status"], "red")
            self.assertTrue(audit["profile_gate_errors"])

    def test_local_lab_audit_warns_missing_required(self) -> None:
        with patch.dict(os.environ, {"SETUPHELFER_INSTALL_PROFILE": "local_lab"}, clear=True):
            audit = profile_gate_audit_route_paths(["/api/version"])
            self.assertIn(audit["profile_gate_status"], ("yellow", "red"))


if __name__ == "__main__":
    unittest.main()
