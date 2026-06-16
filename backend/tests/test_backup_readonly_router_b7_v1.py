"""Backup readonly router B.7 — clone disk-info GET/POST."""

from __future__ import annotations

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


class TestBackupReadonlyRouterB7(unittest.TestCase):
    def test_clone_disk_info_route(self) -> None:
        tbl = _route_table(backup_readonly_router)
        self.assertIn(("GET", "/api/backup/clone/disk-info"), tbl)
        self.assertIn(("POST", "/api/backup/clone/disk-info"), tbl)

    def test_no_duplicate_in_app(self) -> None:
        app_text = (_backend / "app.py").read_text(encoding="utf-8")
        self.assertNotIn('@app.api_route("/api/backup/clone/disk-info"', app_text)

    def test_sudo_store_uses_has_password(self) -> None:
        text = (_backend / "core/backup_readonly_handlers.py").read_text(encoding="utf-8")
        self.assertIn("has_password()", text)
        self.assertNotIn("if not rt.sudo_store().get_password():\n                        rt.sudo_store().store_password", text)


if __name__ == "__main__":
    unittest.main()
