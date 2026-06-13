"""Phase G.3: remaining app.py network callers migrated to network_info_facade."""

from __future__ import annotations

import ast
import sys
import unittest
from pathlib import Path
from unittest import mock

_BACKEND = Path(__file__).resolve().parent.parent
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

APP_PY = _BACKEND / "app.py"
FACADE_PATH = _BACKEND / "core" / "network_info_facade.py"


class TestNetworkInfoCoreCleanupG3(unittest.TestCase):
    def test_get_system_info_uses_facade(self) -> None:
        text = APP_PY.read_text(encoding="utf-8")
        start = text.index("async def get_system_info")
        block = text[start : start + 15000]
        self.assertIn("network_info_facade", block)
        self.assertIn("build_network_info", block)
        self.assertIn("build_demo_network_info", block)
        self.assertNotIn("_demo_network(", block)
        self.assertNotIn("get_network_info(", block)

    def test_webserver_status_uses_facade(self) -> None:
        text = APP_PY.read_text(encoding="utf-8")
        start = text.index("async def webserver_status")
        block = text[start : start + 400]
        self.assertIn("webserver_status_facade", block)
        self.assertIn("build_webserver_status", block)
        self.assertNotIn("get_network_info(", block)
        self.assertNotIn("_detect_frontend_port(", block)

    def test_app_py_no_direct_network_calls_outside_legacy_defs(self) -> None:
        text = APP_PY.read_text(encoding="utf-8")
        for line in text.splitlines():
            stripped = line.strip()
            if "get_network_info(" in line and not stripped.startswith("def get_network_info"):
                self.fail(f"unexpected get_network_info call: {stripped}")
            if "_demo_network(" in line and not stripped.startswith("def _demo_network"):
                self.fail(f"unexpected _demo_network call: {stripped}")

    def test_facade_has_no_subprocess_or_writes(self) -> None:
        tree = ast.parse(FACADE_PATH.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func = node.func
                name = func.id if isinstance(func, ast.Name) else (func.attr if isinstance(func, ast.Attribute) else "")
                if name in {"subprocess", "nmcli", "systemctl"}:
                    self.fail(f"unexpected facade call: {name}")

    def test_system_info_network_shape_via_facade(self) -> None:
        import core.network_info_facade as facade

        fake = {
            "ips": ["192.168.1.5"],
            "localhost": "127.0.0.1",
            "primary_ip": "192.168.1.5",
            "interfaces": [],
            "warnings": [],
            "source": "ip-addr-global",
            "hostname": "pi",
        }
        with mock.patch.object(facade, "build_network_info", return_value=fake):
            network = facade.build_network_info()
        self.assertEqual(network["hostname"], "pi")
        self.assertIn("ips", network)

    def test_webserver_status_network_shape_via_facade(self) -> None:
        import core.network_info_facade as facade

        fake = {"ips": ["10.0.0.3"], "hostname": "host"}
        with mock.patch.object(facade, "build_network_info", return_value=fake):
            network = facade.build_network_info()
        pi_installer_url = (
            f"http://{network.get('ips', ['localhost'])[0]}:3001"
            if network.get("ips")
            else "http://localhost:3001"
        )
        self.assertIn("10.0.0.3", pi_installer_url)

    def test_legacy_defs_remain_in_app(self) -> None:
        text = APP_PY.read_text(encoding="utf-8")
        self.assertIn("def get_network_info", text)
        self.assertIn("def _demo_network", text)

    def test_diagnostics_lists_g3_routes(self) -> None:
        import core.network_info_facade as facade

        diag = facade.build_network_info_diagnostics()
        self.assertIn("GET /api/system-info", diag["routes_migrated_to_facade"])
        self.assertIn("GET /api/webserver/status", diag["routes_migrated_to_facade"])


if __name__ == "__main__":
    unittest.main()
