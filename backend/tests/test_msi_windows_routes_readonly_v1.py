"""Phase F.1: MSI Windows read-only routes — no execute endpoints."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from api.routes.msi_windows import router as msi_router

FORBIDDEN = (
    "backup/execute",
    "restore/execute",
    "wipe",
    "password-reset",
    "bitlocker-unlock",
)


def _routes():
    out = []
    for r in msi_router.routes:
        methods = sorted(getattr(r, "methods", None) or [])
        path = getattr(r, "path", "")
        for m in methods:
            if m != "HEAD":
                out.append((m, path))
    return out


class TestMsiWindowsRoutesReadonlyV1(unittest.TestCase):
    def test_three_readonly_routes(self):
        self.assertEqual(len(_routes()), 3)

    def test_capabilities_route(self):
        self.assertIn(("GET", "/api/msi/windows/capabilities"), _routes())

    def test_no_forbidden_routes(self):
        for _m, path in _routes():
            for bad in FORBIDDEN:
                self.assertNotIn(bad, path)

    def test_no_msi_routes_in_app_py(self):
        text = (_backend / "app.py").read_text(encoding="utf-8")
        self.assertNotIn('@app.get("/api/msi/windows', text)
        self.assertNotIn('@app.post("/api/msi/windows', text)

    def test_capabilities_handler_scope(self):
        from core.msi_windows_handlers import get_capabilities
        import asyncio

        caps = asyncio.get_event_loop().run_until_complete(get_capabilities())
        self.assertFalse(caps["supported"]["image_backup_execute"])


if __name__ == "__main__":
    unittest.main()
