"""Phase G.4: network router extracted from backend/app.py."""

from __future__ import annotations

import ast
import re
import sys
import unittest
from pathlib import Path

_BACKEND = Path(__file__).resolve().parent.parent
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

NETWORK_ROUTER = _BACKEND / "api" / "routes" / "network.py"
APP_PY = _BACKEND / "app.py"
FACADE_PATH = _BACKEND / "core" / "network_info_facade.py"

G4_ROUTES = {
    ("GET", "/api/status"): "network.py",
    ("GET", "/api/system/network"): "network.py",
}

FORBIDDEN_PATTERNS = (
    re.compile(r"\bsubprocess\b"),
    re.compile(r"\bsystemctl\b"),
    re.compile(r"\bnmcli\b"),
    re.compile(r"\bget_network_info\s*\("),
    re.compile(r"\b_demo_network\s*\("),
)


def _route_table_from_source(text: str) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for m in re.finditer(r'@router\.get\("([^"]+)"\)', text):
        out.append(("GET", m.group(1)))
    return out


class TestNetworkRouterExtractionG4(unittest.TestCase):
    def test_router_module_present(self) -> None:
        self.assertTrue(NETWORK_ROUTER.is_file())
        text = NETWORK_ROUTER.read_text(encoding="utf-8")
        self.assertIn("APIRouter", text)
        self.assertTrue(text.strip())

    def test_public_paths_and_methods_unchanged(self) -> None:
        combined = _route_table_from_source(NETWORK_ROUTER.read_text(encoding="utf-8"))
        for key in G4_ROUTES:
            self.assertIn(key, combined, f"missing route {key}")

    def test_network_router_delegates_only_to_facade(self) -> None:
        text = NETWORK_ROUTER.read_text(encoding="utf-8")
        self.assertIn("core.network_info_facade", text)
        self.assertIn("build_api_status_payload", text)
        self.assertIn("build_system_network_response", text)
        for rx in FORBIDDEN_PATTERNS:
            self.assertIsNone(rx.search(text), f"network.py must not match {rx.pattern}")

    def test_app_py_includes_router_and_no_duplicate_handlers(self) -> None:
        app_text = APP_PY.read_text(encoding="utf-8")
        self.assertIn("include_router(network_router)", app_text)
        for dup in (
            '@app.get("/api/status")',
            '@app.get("/api/system/network")',
        ):
            self.assertNotIn(dup, app_text, f"duplicate handler still in app.py: {dup}")

    def test_blocked_handlers_remain_in_app_py(self) -> None:
        app_text = APP_PY.read_text(encoding="utf-8")
        self.assertIn('async def get_system_info', app_text)
        self.assertIn('async def webserver_status', app_text)
        self.assertIn('def get_network_info', app_text)
        self.assertIn('def _demo_network', app_text)

    def test_facade_has_build_api_status_payload(self) -> None:
        import core.network_info_facade as facade

        self.assertTrue(hasattr(facade, "build_api_status_payload"))
        tree = ast.parse(FACADE_PATH.read_text(encoding="utf-8"))
        banned_calls = {"subprocess", "nmcli", "systemctl"}
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func = node.func
                name = func.id if isinstance(func, ast.Name) else (func.attr if isinstance(func, ast.Attribute) else "")
                if name in banned_calls:
                    self.fail(f"unexpected call in facade: {name}")

    def test_app_py_line_count_reduced_after_g4(self) -> None:
        lines = APP_PY.read_text(encoding="utf-8").count("\n") + 1
        self.assertLess(lines, 17380, "app.py should shrink after G.4 extraction")


if __name__ == "__main__":
    unittest.main()
