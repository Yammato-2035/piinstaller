"""Phase E.11: system resources/updates/conflicts + inventory GETs."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from api.routes.system import router as system_router

E11_ROUTES = {
    ("GET", "/api/system/service-conflicts"),
    ("GET", "/api/system/resources"),
    ("GET", "/api/system/installed-packages"),
    ("GET", "/api/system/running-processes"),
    ("GET", "/api/system/security-config"),
    ("GET", "/api/system/updates"),
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


class TestAppRouterSliceE11(unittest.TestCase):
    def test_seventeen_routes_total(self) -> None:
        tbl = _route_table(system_router)
        self.assertEqual(len(tbl), 17)

    def test_e11_routes_present(self) -> None:
        tbl = _route_table(system_router)
        for key in E11_ROUTES:
            self.assertIn(key, tbl)

    def test_handlers_use_runtime(self) -> None:
        text = (_backend / "core/system_handlers.py").read_text(encoding="utf-8")
        self.assertIn("rt.get_updates_categorized", text)
        self.assertIn("rt.list_running_processes", text)
        self.assertIn("build_service_conflict_report", text)
        self.assertNotIn("def _open_terminal_with_command", text)

    def test_no_duplicate_handlers_in_app(self) -> None:
        app_text = (_backend / "app.py").read_text(encoding="utf-8")
        for dup in (
            '@app.get("/api/system/resources")',
            '@app.get("/api/system/updates")',
            '@app.get("/api/system/service-conflicts")',
        ):
            self.assertNotIn(dup, app_text)
        self.assertIn("include_router(system_router)", app_text)


if __name__ == "__main__":
    unittest.main()
