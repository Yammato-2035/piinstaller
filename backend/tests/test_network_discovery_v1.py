"""Phase G.8: Network Discovery Core contract tests."""

from __future__ import annotations

import ast
import sys
import unittest
from pathlib import Path
from unittest import mock

_BACKEND = Path(__file__).resolve().parent.parent
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

DISCOVERY_PATH = _BACKEND / "core" / "network_discovery.py"

PUBLIC_FUNCTIONS = (
    "discover_network_info",
    "discover_demo_network",
    "detect_frontend_port",
    "build_network_discovery_diagnostics",
)

NETWORK_INFO_KEYS = frozenset(
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


class TestNetworkDiscoveryV1(unittest.TestCase):
    def test_discovery_module_has_version_and_public_api(self) -> None:
        import core.network_discovery as discovery

        self.assertEqual(discovery.DISCOVERY_VERSION, 1)
        for name in PUBLIC_FUNCTIONS:
            self.assertTrue(hasattr(discovery, name), f"missing {name}")
            self.assertTrue(callable(getattr(discovery, name)))

    def test_discovery_source_has_no_app_import(self) -> None:
        tree = ast.parse(DISCOVERY_PATH.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    self.assertNotEqual(alias.name, "app")
            if isinstance(node, ast.ImportFrom) and node.module:
                self.assertFalse(node.module.startswith("app"))

    def test_discover_demo_network_legacy_shape(self) -> None:
        import core.network_discovery as discovery

        out = discovery.discover_demo_network()
        self.assertEqual(out["ips"], ["192.168.1.100"])
        self.assertEqual(out["hostname"], "raspberrypi")

    def test_detect_frontend_port_defaults(self) -> None:
        import core.network_discovery as discovery

        with mock.patch.object(discovery, "_shell_run", return_value={"success": False, "stdout": ""}):
            self.assertEqual(discovery.detect_frontend_port(), 3001)

    def test_detect_frontend_port_prefers_5173(self) -> None:
        import core.network_discovery as discovery

        with mock.patch.object(
            discovery,
            "_shell_run",
            return_value={"success": True, "stdout": "LISTEN 0 128 *:5173"},
        ):
            self.assertEqual(discovery.detect_frontend_port(), 5173)

    def test_discover_network_info_ip_path_shape(self) -> None:
        import core.network_discovery as discovery

        ip_stdout = "2: eth0    inet 192.168.1.50/24 brd 192.168.1.255 scope global eth0\n"
        with (
            mock.patch.object(discovery, "_shell_run", return_value={"success": True, "stdout": ip_stdout}),
            mock.patch.object(
                discovery.subprocess,
                "run",
                return_value=mock.Mock(stdout="pi-host\n", returncode=0),
            ),
        ):
            out = discovery.discover_network_info()
        self.assertEqual(set(out.keys()), NETWORK_INFO_KEYS)
        self.assertEqual(out["ips"], ["192.168.1.50"])
        self.assertEqual(out["hostname"], "pi-host")
        self.assertEqual(out["source"], "ip-addr-global")

    def test_discover_network_info_error_shape(self) -> None:
        import core.network_discovery as discovery

        with mock.patch.object(discovery, "_shell_run", side_effect=RuntimeError("boom")):
            out = discovery.discover_network_info()
        self.assertEqual(out["ips"], [])
        self.assertEqual(out["hostname"], "unknown")

    def test_diagnostics_present(self) -> None:
        import core.network_discovery as discovery

        diag = discovery.build_network_discovery_diagnostics()
        self.assertEqual(diag["discovery_version"], 1)
        self.assertFalse(diag["app_import_required"])
        for fn in PUBLIC_FUNCTIONS:
            self.assertIn(fn, diag["public_functions"])


if __name__ == "__main__":
    unittest.main()
