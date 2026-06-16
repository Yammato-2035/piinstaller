"""Backup execute router B.8 — create/verify/delete/restore POST slice."""

from __future__ import annotations

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


class TestBackupExecuteRouterB8(unittest.TestCase):
    def test_eighteen_post_routes(self) -> None:
        tbl = _route_table(backup_execute_router)
        self.assertEqual(len(tbl), 18)

    def test_b8_routes_present(self) -> None:
        tbl = _route_table(backup_execute_router)
        for key in (
            ("POST", "/api/backup/create"),
            ("POST", "/api/backup/verify"),
            ("POST", "/api/backup/delete"),
            ("POST", "/api/backup/restore"),
        ):
            self.assertIn(key, tbl)

    def test_no_backup_post_left_in_app(self) -> None:
        app_text = (_backend / "app.py").read_text(encoding="utf-8")
        self.assertNotIn('@app.post("/api/backup/', app_text)

    def test_handlers_use_runtime(self) -> None:
        text = (_backend / "core/backup_execute_handlers.py").read_text(encoding="utf-8")
        self.assertIn("rt.do_backup_logic", text)
        self.assertIn("rt.analyze_tar_members", text)
        self.assertIn("rt.validate_restore_target_dir", text)


if __name__ == "__main__":
    unittest.main()
