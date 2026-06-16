"""Phase G.1b: GET /api/system/status migrated to system_status_facade."""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path
from unittest import mock

_BACKEND = Path(__file__).resolve().parent.parent
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

HANDLERS_PY = _BACKEND / "core" / "system_handlers.py"
FACADE_PATH = _BACKEND / "core" / "system_status_facade.py"

LEGACY_RESPONSE_KEYS = frozenset(
    {
        "status",
        "api_status",
        "message",
        "data",
        "backup",
        "restore",
        "security",
        "updates",
        "realtest_state",
    }
)


class TestSystemStatusRouteMigrationG1b(unittest.TestCase):
    def test_system_status_handler_uses_facade(self) -> None:
        text = HANDLERS_PY.read_text(encoding="utf-8")
        start = text.index("async def system_status")
        block = text[start : start + 600]
        self.assertIn("build_system_status", block)
        self.assertIn("system_status_facade", block)
        self.assertNotIn("_compute_system_status", block)
        self.assertNotIn("APP_SETTINGS", block)

    def test_get_status_moved_to_network_router(self) -> None:
        router_text = (_BACKEND / "api" / "routes" / "network.py").read_text(encoding="utf-8")
        self.assertIn('@router.get("/api/status")', router_text)
        status_start = router_text.index("async def get_status")
        block = router_text[status_start : status_start + 500]
        self.assertIn("build_api_status_payload", block)
        self.assertNotIn("build_system_status", block)

    def test_system_network_moved_to_network_router(self) -> None:
        router_text = (_BACKEND / "api" / "routes" / "network.py").read_text(encoding="utf-8")
        self.assertIn('@router.get("/api/system/network")', router_text)

    def test_facade_module_has_no_network_subprocess(self) -> None:
        import ast

        tree = ast.parse(FACADE_PATH.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Name) and node.id == "get_network_info":
                self.fail("get_network_info reference in facade")
        text = FACADE_PATH.read_text(encoding="utf-8")
        self.assertNotIn("import subprocess", text)

    def test_build_system_status_exact_legacy_keys(self) -> None:
        import core.system_status_facade as facade

        fake_ampel = {"backup": "green", "restore": "yellow", "security": "red", "updates": "green"}
        with (
            mock.patch.object(facade, "_legacy_compute_ampel_status", return_value=fake_ampel),
            mock.patch.object(facade, "_legacy_backup_realtest_state", return_value={"x": 1}),
            mock.patch.object(
                facade,
                "build_backend_runtime_section",
                return_value={
                    "section_id": "backend_runtime",
                    "status": "ok",
                    "data": {},
                    "warnings": [],
                    "errors": [],
                },
            ),
            mock.patch.object(
                facade,
                "build_installation_section",
                return_value={
                    "section_id": "installation",
                    "status": "ok",
                    "data": {},
                    "warnings": [],
                    "errors": [],
                },
            ),
            mock.patch.object(
                facade,
                "build_profile_section",
                return_value={
                    "section_id": "profile",
                    "status": "ok",
                    "data": {},
                    "warnings": [],
                    "errors": [],
                },
            ),
        ):
            out = facade.build_system_status()
        self.assertEqual(set(out.keys()), LEGACY_RESPONSE_KEYS)
        self.assertEqual(out["status"], "success")
        self.assertEqual(out["api_status"], "ok")
        self.assertEqual(out["backup"], "green")
        self.assertEqual(out["data"]["backup"], "green")
        self.assertEqual(out["realtest_state"], {"x": 1})

    def test_compute_system_status_still_defined_for_tests(self) -> None:
        text = (_BACKEND / "app.py").read_text(encoding="utf-8")
        self.assertIn("def _compute_system_status", text)

    def test_error_response_shape_unchanged(self) -> None:
        text = HANDLERS_PY.read_text(encoding="utf-8")
        self.assertIn('"status": "error"', text)
        self.assertIn('"api_status": "error"', text)
        self.assertIn('"data": {}', text)


if __name__ == "__main__":
    unittest.main()
