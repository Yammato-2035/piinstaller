"""Phase E.9: control-center API routes extracted from app.py."""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from api.routes.control_center import router as control_center_router

E9_ROUTE_COUNT = 33

FORBIDDEN_IN_ROUTER = (
    re.compile(r"\bsubprocess\b"),
    re.compile(r"modules\.control_center"),
)


def _route_table(router) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for r in router.routes:
        methods = sorted(getattr(r, "methods", None) or [])
        path = getattr(r, "path", "")
        for m in methods:
            if m != "HEAD":
                out.append((m, path))
    return out


class TestAppRouterSliceE9(unittest.TestCase):
    def test_router_imports(self) -> None:
        self.assertTrue(control_center_router.routes)

    def test_thirty_three_routes(self) -> None:
        tbl = _route_table(control_center_router)
        cc = [p for m, p in tbl if p.startswith("/api/control-center/")]
        self.assertEqual(len(cc), E9_ROUTE_COUNT)

    def test_handlers_delegate_to_runtime(self) -> None:
        text = (_backend / "core/control_center_handlers.py").read_text(encoding="utf-8")
        self.assertIn("rt.get_control_center_module()", text)
        self.assertNotIn("ControlCenterModule()", text)

    def test_router_thin(self) -> None:
        text = (_backend / "api/routes/control_center.py").read_text(encoding="utf-8")
        for rx in FORBIDDEN_IN_ROUTER:
            self.assertIsNone(rx.search(text), rx.pattern)
        self.assertIn("control_center_handlers", text)

    def test_no_duplicate_handlers_in_app(self) -> None:
        app_text = (_backend / "app.py").read_text(encoding="utf-8")
        self.assertNotIn('@app.get("/api/control-center/wifi/networks")', app_text)
        self.assertIn("include_router(control_center_router)", app_text)

    def test_wifi_networks_route_present(self) -> None:
        tbl = _route_table(control_center_router)
        self.assertIn(("GET", "/api/control-center/wifi/networks"), tbl)
        self.assertIn(("POST", "/api/control-center/bluetooth/enabled"), tbl)


if __name__ == "__main__":
    unittest.main()
