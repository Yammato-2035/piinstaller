"""Backup execute router B.5 — settings, schedule, cloud POST slice."""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from api.routes.backup_execute import router as backup_execute_router


def _route_table(router) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for r in router.routes:
        methods = sorted(getattr(r, "methods", None) or [])
        path = getattr(r, "path", "")
        for m in methods:
            if m != "HEAD":
                out.append((m, path))
    return out


class TestBackupExecuteRouterB5(unittest.TestCase):
    def test_nine_post_routes(self) -> None:
        tbl = _route_table(backup_execute_router)
        self.assertEqual(len(tbl), 9)

    def test_b5_routes_present(self) -> None:
        tbl = _route_table(backup_execute_router)
        for key in (
            ("POST", "/api/backup/settings"),
            ("POST", "/api/backup/schedule/run-now"),
            ("POST", "/api/backup/cloud/test"),
            ("POST", "/api/backup/cloud/delete"),
            ("POST", "/api/backup/cloud/verify"),
        ):
            self.assertIn(key, tbl)

    def test_no_duplicates_in_app(self) -> None:
        app_text = (_backend / "app.py").read_text(encoding="utf-8")
        self.assertNotIn('@app.post("/api/backup/settings")', app_text)
        self.assertNotIn('@app.post("/api/backup/cloud/test")', app_text)

    def test_handlers_use_runtime(self) -> None:
        text = (_backend / "core/backup_execute_handlers.py").read_text(encoding="utf-8")
        self.assertIn("rt.write_backup_settings", text)
        self.assertIn("rt.run_command_async", text)


if __name__ == "__main__":
    unittest.main()
