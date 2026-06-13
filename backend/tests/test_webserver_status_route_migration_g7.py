"""Phase G.7: GET /api/webserver/status migrated to webserver_status_facade."""

from __future__ import annotations

import ast
import sys
import unittest
from pathlib import Path

_BACKEND = Path(__file__).resolve().parent.parent
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

APP_PY = _BACKEND / "app.py"
FACADE_PATH = _BACKEND / "core" / "webserver_status_facade.py"


class TestWebserverStatusRouteMigrationG7(unittest.TestCase):
    def test_webserver_status_handler_uses_facade(self) -> None:
        text = APP_PY.read_text(encoding="utf-8")
        start = text.index("async def webserver_status")
        block = text[start : start + 400]
        self.assertIn("webserver_status_facade", block)
        self.assertIn("build_webserver_status", block)
        self.assertNotIn("network_info_facade", block)
        self.assertNotIn("build_network_info", block)

    def test_webserver_status_no_direct_network_or_port_calls(self) -> None:
        text = APP_PY.read_text(encoding="utf-8")
        start = text.index("async def webserver_status")
        block = text[start : start + 400]
        self.assertNotIn("get_network_info(", block)
        self.assertNotIn("_demo_network(", block)
        self.assertNotIn("_detect_frontend_port(", block)
        self.assertNotIn("get_running_services(", block)
        self.assertNotIn("run_command(", block)

    def test_facade_has_no_subprocess_module_calls(self) -> None:
        tree = ast.parse(FACADE_PATH.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func = node.func
                name = func.id if isinstance(func, ast.Name) else (func.attr if isinstance(func, ast.Attribute) else "")
                if name in {"subprocess", "nmcli", "systemctl"}:
                    self.fail(f"unexpected call in facade: {name}")

    def test_facade_delegates_network_to_network_info_facade(self) -> None:
        text = FACADE_PATH.read_text(encoding="utf-8")
        self.assertIn("from core.network_info_facade import build_network_info, detect_frontend_port", text)
        self.assertNotIn("get_network_info(", text)
        self.assertNotIn("_detect_frontend_port(", text)

    def test_error_response_unchanged(self) -> None:
        text = APP_PY.read_text(encoding="utf-8")
        start = text.index("async def webserver_status")
        block = text[start : start + 400]
        self.assertIn("HTTPException", block)
        self.assertIn("status_code=500", block)


if __name__ == "__main__":
    unittest.main()
