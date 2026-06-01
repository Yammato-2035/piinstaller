"""Router registration helpers vs install profile."""

from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from core.install_profile import (
    should_register_dev_diagnostics_router,
    should_register_fleet_router,
    should_register_rescue_remote_router,
)


class ProfileRouterRegistrationTests(unittest.TestCase):
    def test_release_no_fleet_router(self) -> None:
        with patch.dict(os.environ, {"SETUPHELFER_INSTALL_PROFILE": "release"}, clear=True):
            self.assertFalse(should_register_fleet_router())
            self.assertFalse(should_register_dev_diagnostics_router())
            self.assertFalse(should_register_rescue_remote_router())

    def test_local_lab_registers_dev_routers(self) -> None:
        with patch.dict(os.environ, {"SETUPHELFER_INSTALL_PROFILE": "local_lab"}, clear=True):
            self.assertTrue(should_register_fleet_router())
            self.assertTrue(should_register_dev_diagnostics_router())
            self.assertTrue(should_register_rescue_remote_router())

    def test_rescue_lab_remote_readonly(self) -> None:
        with patch.dict(os.environ, {"SETUPHELFER_INSTALL_PROFILE": "rescue_lab"}, clear=True):
            self.assertTrue(should_register_rescue_remote_router())
            st = __import__("core.install_profile", fromlist=["get_install_profile_state"]).get_install_profile_state()
            self.assertFalse(st.write_runbooks_enabled)


if __name__ == "__main__":
    unittest.main()
