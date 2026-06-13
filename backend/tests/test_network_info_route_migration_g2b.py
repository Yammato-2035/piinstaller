"""Phase G.2b: GET /api/status and GET /api/system/network migrated to network_info_facade."""

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
NETWORK_ROUTER = _BACKEND / "api" / "routes" / "network.py"
FACADE_PATH = _BACKEND / "core" / "network_info_facade.py"

STATUS_TOP_LEVEL_KEYS = frozenset({"status", "hostname", "version", "network"})
SYSTEM_NETWORK_KEYS = frozenset(
    {
        "status",
        "ips",
        "localhost",
        "primary_ip",
        "interfaces",
        "warnings",
        "source",
        "hostname",
        "frontend_port",
        "backend_port",
    }
)


class TestNetworkInfoRouteMigrationG2b(unittest.TestCase):
    def test_get_status_handler_uses_facade(self) -> None:
        text = NETWORK_ROUTER.read_text(encoding="utf-8")
        start = text.index("async def get_status")
        block = text[start : start + 500]
        self.assertIn("network_info_facade", block)
        self.assertIn("build_api_status_payload", block)
        self.assertNotIn("_demo_network(", block)
        self.assertNotIn("get_network_info(", block)

    def test_get_system_network_handler_uses_facade(self) -> None:
        text = NETWORK_ROUTER.read_text(encoding="utf-8")
        start = text.index("async def get_system_network")
        block = text[start : start + 700]
        self.assertIn("network_info_facade", block)
        self.assertIn("build_system_network_response", block)
        self.assertNotIn("_demo_network(", block)
        self.assertNotIn("get_network_info(", block)
        self.assertNotIn("_detect_frontend_port(", block)

    def test_facade_module_has_no_subprocess_or_network_writes(self) -> None:
        tree = ast.parse(FACADE_PATH.read_text(encoding="utf-8"))
        banned_calls = {"subprocess", "nmcli", "systemctl"}
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func = node.func
                name = ""
                if isinstance(func, ast.Name):
                    name = func.id
                elif isinstance(func, ast.Attribute):
                    name = func.attr
                if name in banned_calls:
                    self.fail(f"unexpected call in facade: {name}")

    def test_build_system_network_response_demo_legacy_shape(self) -> None:
        import core.network_info_facade as facade

        with mock.patch.object(
            facade,
            "build_demo_network_info",
            return_value={"ips": ["192.168.1.100"], "hostname": "raspberrypi"},
        ):
            out = facade.build_system_network_response(use_demo=True)
        self.assertEqual(set(out.keys()), SYSTEM_NETWORK_KEYS)
        self.assertEqual(out["status"], "success")
        self.assertEqual(out["ips"], ["192.168.1.100"])
        self.assertEqual(out["hostname"], "raspberrypi")
        self.assertEqual(out["source"], "demo")
        self.assertEqual(out["frontend_port"], 3001)
        self.assertEqual(out["backend_port"], 8000)

    def test_build_system_network_response_live_legacy_shape(self) -> None:
        import core.network_info_facade as facade

        fake_info = {
            "ips": ["10.0.0.5"],
            "localhost": "127.0.0.1",
            "primary_ip": "10.0.0.5",
            "interfaces": [{"name": "eth0", "ip": "10.0.0.5", "source": "ip-addr-global"}],
            "warnings": [],
            "source": "ip-addr-global",
            "hostname": "host-b",
        }
        with (
            mock.patch.object(facade, "build_network_info", return_value=fake_info),
            mock.patch.object(facade, "detect_frontend_port", return_value=5173),
        ):
            out = facade.build_system_network_response(use_demo=False)
        self.assertEqual(set(out.keys()), SYSTEM_NETWORK_KEYS)
        self.assertEqual(out["status"], "success")
        self.assertEqual(out["hostname"], "host-b")
        self.assertEqual(out["frontend_port"], 5173)
        self.assertEqual(out["backend_port"], 8000)

    def test_status_network_block_shape_via_facade(self) -> None:
        import core.network_info_facade as facade

        fake = {"ips": ["10.0.0.1"], "hostname": "pi"}
        with mock.patch.object(facade, "build_network_info", return_value=fake):
            net = facade.build_network_info()
        payload = {
            "status": "healthy",
            "hostname": net["hostname"],
            "version": "1.0.0",
            "network": net,
        }
        self.assertEqual(set(payload.keys()), STATUS_TOP_LEVEL_KEYS)
        self.assertEqual(payload["network"], fake)

    def test_get_network_info_remains_legacy_wrapper(self) -> None:
        text = APP_PY.read_text(encoding="utf-8")
        self.assertIn("def get_network_info", text)
        self.assertIn("discover_network_info", text)
        self.assertIn("def _demo_network", text)
        self.assertIn("discover_demo_network", text)

    def test_system_network_error_response_unchanged(self) -> None:
        text = NETWORK_ROUTER.read_text(encoding="utf-8")
        start = text.index("async def get_system_network")
        block = text[start : start + 1200]
        self.assertIn('"status": "error"', block)
        self.assertIn("JSONResponse", block)


if __name__ == "__main__":
    unittest.main()
