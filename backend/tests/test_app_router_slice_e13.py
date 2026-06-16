"""Phase E.13: system mixer/update POST routes."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from api.routes.system import router as system_router

E13_ROUTES = {
    ("POST", "/api/system/run-update-in-terminal"),
    ("POST", "/api/system/run-mixer"),
    ("POST", "/api/system/install-mixer-packages"),
}


def _route_table(router) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for r in router.routes:
        methods = sorted(getattr(r, "methods", None) or [])
        path = getattr(r, "path", "")
        for m in methods:
            if m != "HEAD":
                out.append((m, path))
    return out


class TestAppRouterSliceE13(unittest.TestCase):
    def test_twenty_routes_total(self) -> None:
        tbl = _route_table(system_router)
        self.assertEqual(len(tbl), 20)

    def test_e13_routes_present(self) -> None:
        tbl = _route_table(system_router)
        for key in E13_ROUTES:
            self.assertIn(key, tbl)

    def test_no_system_post_left_in_app(self) -> None:
        app_text = (_backend / "app.py").read_text(encoding="utf-8")
        self.assertNotIn('@app.post("/api/system/', app_text)

    def test_run_update_manual_only(self) -> None:
        text = (_backend / "core/system_handlers.py").read_text(encoding="utf-8")
        block = text.split("async def run_update_in_terminal")[1].split("\n\nasync def")[0]
        self.assertIn("manual_required", block)
        self.assertIn("blocked_auto_execution", block)


if __name__ == "__main__":
    unittest.main()
