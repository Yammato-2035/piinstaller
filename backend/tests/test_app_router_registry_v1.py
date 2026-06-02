from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from app_bootstrap.app_factory import create_app
from app_bootstrap.router_registry import register_all_routes


class AppRouterRegistryTests(unittest.TestCase):
    def _app(self):
        return create_app(title="t", description="d", version="1.0.0")

    def test_result_contains_rescue_agent(self) -> None:
        app = self._app()
        result = register_all_routes(
            app,
            {"install_profile": "release"},
            should_register_dev_server_router=lambda: False,
            should_register_fleet_router=lambda: False,
            should_register_dev_diagnostics_router=lambda: False,
            should_register_rescue_remote_router=lambda: False,
            should_register_rescue_agent_router=lambda: False,
        )
        routers = {x.router for x in result.statuses}
        self.assertIn("rescue_agent", routers)

    def test_release_profile_disabled_by_profile(self) -> None:
        app = self._app()
        result = register_all_routes(
            app,
            {"install_profile": "release"},
            should_register_dev_server_router=lambda: False,
            should_register_fleet_router=lambda: False,
            should_register_dev_diagnostics_router=lambda: False,
            should_register_rescue_remote_router=lambda: False,
            should_register_rescue_agent_router=lambda: False,
        )
        rescue = [x for x in result.statuses if x.router == "rescue_agent"][0]
        self.assertEqual(rescue.status, "disabled_by_profile")

    def test_optional_import_failure_does_not_crash(self) -> None:
        app = self._app()
        with patch.dict(os.environ, {}, clear=False):
            result = register_all_routes(
                app,
                {"install_profile": "local_lab"},
                should_register_dev_server_router=lambda: True,
                should_register_fleet_router=lambda: True,
                should_register_dev_diagnostics_router=lambda: True,
                should_register_rescue_remote_router=lambda: True,
                should_register_rescue_agent_router=lambda: True,
            )
        statuses = {x.router: x.status for x in result.statuses}
        self.assertIn(statuses["rescue_agent"], {"registered", "import_failed"})

    def test_no_forbidden_apply_execute_install_write_routes(self) -> None:
        app = self._app()
        result = register_all_routes(
            app,
            {"install_profile": "release"},
            should_register_dev_server_router=lambda: False,
            should_register_fleet_router=lambda: False,
            should_register_dev_diagnostics_router=lambda: False,
            should_register_rescue_remote_router=lambda: False,
            should_register_rescue_agent_router=lambda: False,
        )
        self.assertGreaterEqual(len(result.statuses), 1)
        forbidden = ("/apply", "/execute", "/install", "/write")
        for route in app.routes:
            p = getattr(route, "path", "").lower()
            for frag in forbidden:
                self.assertNotIn(frag, p)


if __name__ == "__main__":
    unittest.main()

