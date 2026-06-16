"""Phase E.10: system paths/devices/terminal + reboot/packagekit."""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from api.routes.system import router as system_router

E10_ROUTES = {
    ("GET", "/api/system/paths"),
    ("GET", "/api/system/devices"),
    ("GET", "/api/system/terminal-available"),
    ("POST", "/api/system/reboot"),
    ("POST", "/api/system/packagekit/stop"),
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


class TestAppRouterSliceE10(unittest.TestCase):
    def test_five_routes(self) -> None:
        tbl = _route_table(system_router)
        self.assertEqual(len(tbl), 5)
        for key in E10_ROUTES:
            self.assertIn(key, tbl)

    def test_handlers_use_runtime(self) -> None:
        text = (_backend / "core/system_handlers.py").read_text(encoding="utf-8")
        self.assertIn("rt.root_mount_device", text)
        self.assertIn("list_devices_for_api", text)
        self.assertNotIn("def run_command", text)

    def test_no_duplicate_handlers_in_app(self) -> None:
        app_text = (_backend / "app.py").read_text(encoding="utf-8")
        for dup in (
            '@app.get("/api/system/paths")',
            '@app.post("/api/system/reboot")',
            '@app.get("/api/system/devices")',
        ):
            self.assertNotIn(dup, app_text)
        self.assertIn("include_router(system_router)", app_text)


if __name__ == "__main__":
    unittest.main()
