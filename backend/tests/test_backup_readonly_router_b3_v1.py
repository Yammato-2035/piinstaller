"""Backup readonly router B.3 — target-check extraction."""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from api.routes.backup_readonly import router as backup_readonly_router


def _route_table(router) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for r in router.routes:
        methods = sorted(getattr(r, "methods", None) or [])
        path = getattr(r, "path", "")
        for m in methods:
            if m != "HEAD":
                out.append((m, path))
    return out


class TestBackupReadonlyRouterB3(unittest.TestCase):
    def test_target_check_route_on_readonly_router(self) -> None:
        tbl = _route_table(backup_readonly_router)
        self.assertIn(("GET", "/api/backup/target-check"), tbl)

    def test_app_py_has_no_duplicate_target_check(self) -> None:
        app_text = (_backend / "app.py").read_text(encoding="utf-8")
        self.assertNotIn('@app.get("/api/backup/target-check")', app_text)

    def test_handler_module_exists(self) -> None:
        handler = _backend / "core" / "backup_target_check_handler.py"
        self.assertTrue(handler.is_file())
        text = handler.read_text(encoding="utf-8")
        self.assertIn("rt.findmnt_mounts", text)
        self.assertIn("rt.validate_backup_dir", text)

    def test_fourteen_get_routes_on_backup_readonly(self) -> None:
        tbl = _route_table(backup_readonly_router)
        get_routes = [p for m, p in tbl if m == "GET"]
        self.assertEqual(len(get_routes), 14)

    def test_no_backup_get_routes_left_in_app(self) -> None:
        app_text = (_backend / "app.py").read_text(encoding="utf-8")
        self.assertIsNone(re.search(r'@app\.get\("/api/backup/', app_text))


if __name__ == "__main__":
    unittest.main()
