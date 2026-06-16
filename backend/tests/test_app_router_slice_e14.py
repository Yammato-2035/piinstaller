"""Phase E.14: security routes extracted from app.py."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from api.routes.security import router as security_router

E14_ROUTES = {
    ("POST", "/api/security/scan"),
    ("GET", "/api/security/status"),
    ("POST", "/api/security/firewall/enable"),
    ("POST", "/api/security/firewall/install"),
    ("GET", "/api/security/firewall/rules"),
    ("POST", "/api/security/firewall/rules/add"),
    ("DELETE", "/api/security/firewall/rules/{rule_number}"),
    ("POST", "/api/security/configure"),
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


class TestAppRouterSliceE14(unittest.TestCase):
    def test_eight_routes_total(self) -> None:
        tbl = _route_table(security_router)
        self.assertEqual(len(tbl), 8)

    def test_e14_routes_present(self) -> None:
        tbl = _route_table(security_router)
        for key in E14_ROUTES:
            self.assertIn(key, tbl)

    def test_no_security_routes_left_in_app(self) -> None:
        app_text = (_backend / "app.py").read_text(encoding="utf-8")
        self.assertNotIn('@app.post("/api/security/', app_text)
        self.assertNotIn('@app.get("/api/security/', app_text)
        self.assertNotIn('@app.delete("/api/security/', app_text)

    def test_configure_uses_has_password_guard(self) -> None:
        text = (_backend / "core/security_handlers.py").read_text(encoding="utf-8")
        block = text.split("async def configure_security")[1].split("\n\nasync def")[0]
        self.assertIn("has_password()", block)


if __name__ == "__main__":
    unittest.main()
