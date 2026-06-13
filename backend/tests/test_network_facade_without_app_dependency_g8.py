"""Phase G.8: network_info_facade no longer depends on lazy app imports."""

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
APP_PY = _BACKEND / "app.py"


class TestNetworkFacadeWithoutAppDependencyG8(unittest.TestCase):
    def test_facade_ast_has_no_app_import(self) -> None:
        tree = ast.parse(FACADE_PATH.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    self.assertNotEqual(alias.name, "app", "facade must not import app")
            if isinstance(node, ast.ImportFrom) and node.module:
                self.assertFalse(node.module == "app" or node.module.startswith("app."))

    def test_facade_source_mentions_network_discovery(self) -> None:
        text = FACADE_PATH.read_text(encoding="utf-8")
        self.assertIn("core.network_discovery", text)
        self.assertIn("discover_network_info", text)
        self.assertNotIn("import app", text)

    def test_app_legacy_wrappers_delegate_to_discovery(self) -> None:
        text = APP_PY.read_text(encoding="utf-8")
        for fn, core_fn in (
            ("def get_network_info", "discover_network_info"),
            ("def _demo_network", "discover_demo_network"),
            ("def _detect_frontend_port", "detect_frontend_port"),
        ):
            start = text.index(fn)
            block = text[start : start + 300]
            self.assertIn("network_discovery", block, fn)
            self.assertIn(core_fn, block, fn)

    def test_build_network_info_via_discovery(self) -> None:
        import core.network_info_facade as facade

        fake = {
            "ips": ["10.0.0.2"],
            "localhost": "127.0.0.1",
            "primary_ip": "10.0.0.2",
            "interfaces": [],
            "warnings": [],
            "source": "ip-addr-global",
            "hostname": "host",
        }
        with mock.patch.object(facade, "discover_network_info", return_value=fake):
            out = facade.build_network_info()
        self.assertEqual(out, fake)

    def test_build_demo_network_info_via_discovery(self) -> None:
        import core.network_info_facade as facade

        fake = {"ips": ["192.168.1.100"], "hostname": "raspberrypi"}
        with mock.patch.object(facade, "discover_demo_network", return_value=fake):
            out = facade.build_demo_network_info()
        self.assertEqual(out, fake)

    def test_detect_frontend_port_reexported(self) -> None:
        import core.network_info_facade as facade

        with mock.patch.object(facade, "detect_frontend_port", return_value=5173) as mocked:
            self.assertEqual(facade.detect_frontend_port(), 5173)
            mocked.assert_called_once()

    def test_diagnostics_delegate_to_network_discovery(self) -> None:
        import core.network_info_facade as facade

        diag = facade.build_network_info_diagnostics()
        joined = " ".join(diag.get("delegates_to", []))
        self.assertIn("network_discovery.discover_network_info", joined)
        self.assertNotIn("app.get_network_info", joined)


if __name__ == "__main__":
    unittest.main()
