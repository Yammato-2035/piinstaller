"""Phase E.12: system status, freenove, ASUS ROG routes."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from api.routes.system import router as system_router

E12_ROUTES = {
    ("GET", "/api/system/status"),
    ("GET", "/api/system/freenove-detection"),
    ("GET", "/api/system/asus-rog/fan/profiles"),
    ("GET", "/api/system/asus-rog/fan/status"),
    ("POST", "/api/system/asus-rog/fan/set-profile"),
    ("GET", "/api/system/asus-rog/detection"),
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


class TestAppRouterSliceE12(unittest.TestCase):
    def test_seventeen_routes_minimum(self) -> None:
        tbl = _route_table(system_router)
        self.assertGreaterEqual(len(tbl), 17)

    def test_e12_routes_present(self) -> None:
        tbl = _route_table(system_router)
        for key in E12_ROUTES:
            self.assertIn(key, tbl)

    def test_no_duplicates_in_app(self) -> None:
        app_text = (_backend / "app.py").read_text(encoding="utf-8")
        for dup in (
            '@app.get("/api/system/status")',
            '@app.get("/api/system/freenove-detection")',
            '@app.get("/api/system/asus-rog/detection")',
            '@app.post("/api/system/asus-rog/fan/set-profile")',
        ):
            self.assertNotIn(dup, app_text)

    def test_freenove_detection_implemented(self) -> None:
        from core.hardware_discovery import detect_freenove_case

        out = detect_freenove_case()
        self.assertIn("detected", out)
        self.assertIn("dsi_display", out)


if __name__ == "__main__":
    unittest.main()
