"""Backup execute router B.7 — clone POST slice."""

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


class TestBackupExecuteRouterB7(unittest.TestCase):
    def test_b7_routes_subset(self) -> None:
        tbl = _route_table(backup_execute_router)
        self.assertGreaterEqual(len(tbl), 14)

    def test_clone_route_present(self) -> None:
        tbl = _route_table(backup_execute_router)
        self.assertIn(("POST", "/api/backup/clone"), tbl)

    def test_no_duplicate_clone_in_app(self) -> None:
        app_text = (_backend / "app.py").read_text(encoding="utf-8")
        self.assertNotIn('@app.post("/api/backup/clone")', app_text)
        self.assertIn("def _do_clone_logic", app_text)

    def test_handler_uses_runtime(self) -> None:
        text = (_backend / "core/backup_execute_handlers.py").read_text(encoding="utf-8")
        self.assertIn("rt.do_clone_logic", text)
        self.assertIn("rt.has_active_long_running_job", text)


if __name__ == "__main__":
    unittest.main()
