"""Phase G.11: Webserver Service Discovery Core contract tests."""

from __future__ import annotations

import ast
import sys
import unittest
from pathlib import Path
from unittest import mock

_BACKEND = Path(__file__).resolve().parent.parent
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

DISCOVERY_PATH = _BACKEND / "core" / "webserver_service_discovery.py"
FACADE_PATH = _BACKEND / "core" / "webserver_status_facade.py"

PUBLIC_FUNCTIONS = (
    "discover_running_services",
    "discover_frontend_port",
    "discover_webserver_stack",
    "discover_installed_web_services",
    "build_webserver_service_diagnostics",
)


class TestWebserverServiceDiscoveryV1(unittest.TestCase):
    def test_discovery_module_has_version_and_public_api(self) -> None:
        import core.webserver_service_discovery as discovery

        self.assertEqual(discovery.WEBSERVER_SERVICE_DISCOVERY_VERSION, 1)
        for name in PUBLIC_FUNCTIONS:
            self.assertTrue(hasattr(discovery, name), f"missing {name}")
            self.assertTrue(callable(getattr(discovery, name)))

    def test_discovery_ast_has_no_app_import(self) -> None:
        tree = ast.parse(DISCOVERY_PATH.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    self.assertNotEqual(alias.name, "app")
            if isinstance(node, ast.ImportFrom) and node.module:
                self.assertFalse(node.module == "app" or node.module.startswith("app."))

    def test_discover_webserver_stack_shape(self) -> None:
        import core.webserver_service_discovery as discovery

        fake_running = {"nginx": True, "apache2": False}
        fake_installed = {"nginx": True, "wordpress": False}
        with (
            mock.patch.object(discovery, "discover_running_services", return_value=fake_running),
            mock.patch.object(discovery, "discover_installed_web_services", return_value=fake_installed),
            mock.patch.object(discovery, "get_website_names", return_value=["a.example"]),
            mock.patch.object(discovery, "run_command", return_value={"success": False, "stdout": "", "stderr": ""}),
            mock.patch.object(discovery, "check_installed", return_value=False),
        ):
            out = discovery.discover_webserver_stack()
        self.assertEqual(out["running"], fake_running)
        self.assertEqual(out["installed"], fake_installed)
        self.assertEqual(out["website_names"], ["a.example"])
        self.assertIn("nginx_running", out)

    def test_facade_has_no_app_import_g11(self) -> None:
        tree = ast.parse(FACADE_PATH.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    self.assertNotEqual(alias.name, "app")
            if isinstance(node, ast.ImportFrom) and node.module:
                self.assertFalse(node.module == "app" or node.module.startswith("app."))


if __name__ == "__main__":
    unittest.main()
