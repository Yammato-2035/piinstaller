"""Phase G.2: Network Info Facade contract tests."""

from __future__ import annotations

import ast
import sys
import unittest
from pathlib import Path
from unittest import mock

_BACKEND = Path(__file__).resolve().parent.parent
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

FACADE_PATH = _BACKEND / "core" / "network_info_facade.py"

PUBLIC_FUNCTIONS = (
    "build_network_info",
    "build_network_status_section",
    "build_demo_network_info",
    "detect_frontend_port",
    "build_api_status_payload",
    "build_system_network_response",
    "build_network_info_diagnostics",
    "normalize_legacy_network_info",
    "build_unavailable_network_section",
)

LEGACY_INFO_KEYS = frozenset(
    {
        "ips",
        "localhost",
        "primary_ip",
        "interfaces",
        "warnings",
        "source",
        "hostname",
    }
)


class TestNetworkInfoFacadeV1(unittest.TestCase):
    def test_facade_module_has_version_and_public_api(self) -> None:
        import core.network_info_facade as facade

        self.assertEqual(facade.FACADE_VERSION, 1)
        for name in PUBLIC_FUNCTIONS:
            self.assertTrue(hasattr(facade, name), f"missing {name}")
            self.assertTrue(callable(getattr(facade, name)))

    def test_facade_source_no_network_write_commands(self) -> None:
        tree = ast.parse(FACADE_PATH.read_text(encoding="utf-8"))
        banned_calls = {"nmcli", "ip", "ifconfig", "netplan", "systemctl"}
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func = node.func
                name = ""
                if isinstance(func, ast.Name):
                    name = func.id
                elif isinstance(func, ast.Attribute):
                    name = func.attr
                if name in banned_calls:
                    self.fail(f"unexpected network write call: {name}")
        text = FACADE_PATH.read_text(encoding="utf-8")
        self.assertNotIn(".write_text(", text)
        self.assertNotIn("subprocess", text)

    def test_facade_import_ast_no_module_level_app_import(self) -> None:
        tree = ast.parse(FACADE_PATH.read_text(encoding="utf-8"))
        for node in tree.body:
            if isinstance(node, ast.Import):
                for alias in node.names:
                    self.assertNotEqual(alias.name, "app")
            if isinstance(node, ast.ImportFrom) and node.module == "app":
                self.fail("module-level import from app")

    def test_normalize_legacy_network_info_preserves_keys(self) -> None:
        import core.network_info_facade as facade

        info = {
            "ips": ["192.168.1.10"],
            "localhost": "127.0.0.1",
            "primary_ip": "192.168.1.10",
            "interfaces": [{"name": "eth0", "ip": "192.168.1.10", "source": "ip-addr-global"}],
            "warnings": [],
            "source": "ip-addr-global",
            "hostname": "host-a",
        }
        out = facade.normalize_legacy_network_info(info)
        self.assertEqual(out["status"], "ok")
        self.assertEqual(out["normalized"]["hostname"], "host-a")
        self.assertEqual(set(out["legacy"].keys()), LEGACY_INFO_KEYS)

    def test_demo_network_legacy_shape(self) -> None:
        import core.network_info_facade as facade

        with mock.patch.object(facade, "discover_demo_network", return_value={"ips": ["192.168.1.100"], "hostname": "raspberrypi"}):
            out = facade.build_demo_network_info()
        self.assertEqual(out["ips"], ["192.168.1.100"])
        self.assertEqual(out["hostname"], "raspberrypi")

    def test_build_network_info_delegates_to_legacy(self) -> None:
        import core.network_info_facade as facade

        fake = {
            "ips": ["10.0.0.2"],
            "localhost": "127.0.0.1",
            "primary_ip": "10.0.0.2",
            "interfaces": [],
            "warnings": [],
            "source": "hostname-I",
            "hostname": "pi",
        }
        with mock.patch.object(facade, "discover_network_info", return_value=fake):
            out = facade.build_network_info()
        self.assertEqual(out, fake)

    def test_section_failure_isolated(self) -> None:
        import core.network_info_facade as facade

        with mock.patch.object(facade, "build_network_info", side_effect=RuntimeError("boom")):
            section = facade.build_network_status_section()
        self.assertEqual(section["section_id"], "network")
        self.assertEqual(section["status"], "unavailable")
        self.assertTrue(section["errors"])

    def test_diagnostics_present(self) -> None:
        import core.network_info_facade as facade

        diag = facade.build_network_info_diagnostics()
        self.assertEqual(diag["facade_version"], 1)
        self.assertFalse(diag["network_writes_allowed"])
        self.assertIn("GET /api/status", diag["routes_migrated_to_facade"])
        self.assertIn("GET /api/status", diag["routes_extracted_to_network_router"])
        self.assertEqual(diag["network_router_module"], "api.routes.network")
        for fn in PUBLIC_FUNCTIONS:
            self.assertIn(fn, diag["public_functions"])


if __name__ == "__main__":
    unittest.main()
