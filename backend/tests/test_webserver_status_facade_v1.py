"""Phase G.7: Webserver Status Facade contract tests."""

from __future__ import annotations

import ast
import sys
import unittest
from pathlib import Path
from unittest import mock

_BACKEND = Path(__file__).resolve().parent.parent
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

FACADE_PATH = _BACKEND / "core" / "webserver_status_facade.py"

PUBLIC_FUNCTIONS = (
    "build_webserver_status",
    "build_webserver_status_section",
    "build_webserver_frontend_section",
    "build_webserver_status_diagnostics",
)

LEGACY_RESPONSE_KEYS = frozenset(
    {
        "pi_installer",
        "website_names",
        "nginx",
        "apache",
        "mysql",
        "mariadb",
        "php",
        "cockpit",
        "webmin",
        "network",
        "webserver_ports",
        "websites",
        "installed_cms",
    }
)


class TestWebserverStatusFacadeV1(unittest.TestCase):
    def test_facade_module_has_version_and_public_api(self) -> None:
        import core.webserver_status_facade as facade

        self.assertEqual(facade.WEBSERVER_STATUS_FACADE_VERSION, 1)
        for name in PUBLIC_FUNCTIONS:
            self.assertTrue(hasattr(facade, name), f"missing {name}")
            self.assertTrue(callable(getattr(facade, name)))

    def test_facade_source_has_no_direct_network_or_port_calls(self) -> None:
        tree = ast.parse(FACADE_PATH.read_text(encoding="utf-8"))
        banned = {"get_network_info", "_demo_network", "_detect_frontend_port"}
        for node in ast.walk(tree):
            if isinstance(node, ast.Name) and node.id in banned:
                self.fail(f"banned symbol in facade: {node.id}")

    def test_facade_uses_network_info_facade(self) -> None:
        text = FACADE_PATH.read_text(encoding="utf-8")
        self.assertIn("network_info_facade", text)
        self.assertIn("build_network_info", text)
        self.assertIn("webserver_service_discovery", text)

    def test_facade_ast_has_no_app_import(self) -> None:
        tree = ast.parse(FACADE_PATH.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    self.assertNotEqual(alias.name, "app")
            if isinstance(node, ast.ImportFrom) and node.module:
                self.assertFalse(node.module == "app" or node.module.startswith("app."))

    def test_build_webserver_status_legacy_shape(self) -> None:
        import core.webserver_service_discovery as discovery
        import core.webserver_status_facade as facade

        fake_network = {"ips": ["10.0.0.8"], "hostname": "host"}
        fake_running = {"nginx": True, "apache2": False, "mysql": False, "mariadb": False}
        fake_installed = {
            "nginx": True,
            "apache": False,
            "mysql": False,
            "mariadb": False,
            "php": True,
            "cockpit": False,
            "webmin": False,
            "wordpress": False,
            "wordpress_plugins": [],
            "nextcloud": False,
            "drupal": False,
            "websites": ["/var/www/html/site"],
        }
        with (
            mock.patch.object(facade, "discover_running_services", return_value=fake_running),
            mock.patch.object(facade, "discover_installed_web_services", return_value=fake_installed),
            mock.patch.object(facade, "get_website_names", return_value=["example.com"]),
            mock.patch.object(facade, "check_installed", return_value=False),
            mock.patch.object(
                facade,
                "run_command",
                return_value={"success": False, "stdout": "", "stderr": ""},
            ),
            mock.patch.object(facade, "build_network_info", return_value=fake_network),
            mock.patch.object(facade, "discover_frontend_port", return_value=3001),
        ):
            out = facade.build_webserver_status()
        self.assertEqual(set(out.keys()), LEGACY_RESPONSE_KEYS)
        self.assertEqual(out["network"], fake_network)
        self.assertEqual(out["pi_installer"]["port"], 3001)
        self.assertEqual(out["pi_installer"]["url"], "http://10.0.0.8:3001")
        self.assertTrue(out["nginx"]["running"])

    def test_build_webserver_frontend_section_localhost_fallback(self) -> None:
        import core.webserver_status_facade as facade

        section = facade.build_webserver_frontend_section(network={"ips": []}, port=5173)
        self.assertEqual(section["port"], 5173)
        self.assertEqual(section["url"], "http://localhost:5173")

    def test_section_failure_isolated(self) -> None:
        import core.webserver_status_facade as facade

        with mock.patch.object(facade, "build_webserver_status", side_effect=RuntimeError("boom")):
            section = facade.build_webserver_status_section()
        self.assertEqual(section["section_id"], "webserver")
        self.assertEqual(section["status"], "unavailable")
        self.assertTrue(section["errors"])

    def test_diagnostics_present(self) -> None:
        import core.webserver_status_facade as facade

        diag = facade.build_webserver_status_diagnostics()
        self.assertEqual(diag["facade_version"], 1)
        self.assertTrue(diag["network_via_network_info_facade"])
        self.assertTrue(diag.get("discovery_via_webserver_service_discovery"))
        self.assertFalse(diag.get("facade_imports_app"))
        self.assertIn("GET /api/webserver/status", diag["routes_migrated_to_facade"])
        for fn in PUBLIC_FUNCTIONS:
            self.assertIn(fn, diag["public_functions"])


if __name__ == "__main__":
    unittest.main()
