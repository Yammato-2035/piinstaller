"""Phase G.6: GET /api/system-info migrated to system_info_facade."""

from __future__ import annotations

import ast
import sys
import unittest
from pathlib import Path

_BACKEND = Path(__file__).resolve().parent.parent
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

APP_PY = _BACKEND / "app.py"
FACADE_PATH = _BACKEND / "core" / "system_info_facade.py"


class TestSystemInfoRouteMigrationG6(unittest.TestCase):
    def test_system_info_handler_uses_facade(self) -> None:
        text = APP_PY.read_text(encoding="utf-8")
        start = text.index("async def get_system_info")
        block = text[start : start + 400]
        self.assertIn("system_info_facade", block)
        self.assertIn("build_system_info", block)
        self.assertNotIn("network_info_facade", block)
        self.assertNotIn("build_network_info", block)

    def test_system_info_no_direct_network_or_hardware_calls(self) -> None:
        text = APP_PY.read_text(encoding="utf-8")
        start = text.index("async def get_system_info")
        block = text[start : start + 400]
        self.assertNotIn("get_network_info(", block)
        self.assertNotIn("_demo_network(", block)
        self.assertNotIn("psutil", block)
        self.assertNotIn("get_cpu_temp(", block)
        self.assertNotIn("get_motherboard_info(", block)

    def test_facade_network_only_via_network_info_facade(self) -> None:
        text = FACADE_PATH.read_text(encoding="utf-8")
        self.assertIn(
            "from core.network_info_facade import build_demo_network_info, build_network_info",
            text,
        )
        self.assertNotIn("get_network_info(", text)
        self.assertNotIn("discover_network_info(", text)

    def test_facade_has_no_subprocess_module_calls(self) -> None:
        tree = ast.parse(FACADE_PATH.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func = node.func
                name = func.id if isinstance(func, ast.Name) else (func.attr if isinstance(func, ast.Attribute) else "")
                if name in {"subprocess", "nmcli", "systemctl"}:
                    self.fail(f"unexpected call in facade: {name}")

    def test_error_response_unchanged(self) -> None:
        text = FACADE_PATH.read_text(encoding="utf-8")
        self.assertIn('return {"error": str(exc)}', text)


if __name__ == "__main__":
    unittest.main()
