"""Backup execute router B.6 — target-prepare + USB mount/prepare/eject."""

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


class TestBackupExecuteRouterB6(unittest.TestCase):
    def test_thirteen_post_routes(self) -> None:
        tbl = _route_table(backup_execute_router)
        self.assertEqual(len(tbl), 13)

    def test_b6_routes_present(self) -> None:
        tbl = _route_table(backup_execute_router)
        for key in (
            ("POST", "/api/backup/target-prepare"),
            ("POST", "/api/backup/usb/mount"),
            ("POST", "/api/backup/usb/prepare"),
            ("POST", "/api/backup/usb/eject"),
        ):
            self.assertIn(key, tbl)

    def test_no_duplicates_in_app(self) -> None:
        app_text = (_backend / "app.py").read_text(encoding="utf-8")
        for dup in (
            '@app.post("/api/backup/target-prepare")',
            '@app.post("/api/backup/usb/mount")',
            '@app.post("/api/backup/usb/prepare")',
            '@app.post("/api/backup/usb/eject")',
        ):
            self.assertNotIn(dup, app_text)

    def test_handlers_use_runtime(self) -> None:
        text = (_backend / "core/backup_execute_handlers.py").read_text(encoding="utf-8")
        self.assertIn("rt.mountpoints_for_disk", text)
        self.assertIn("rt.sanitize_label", text)
        self.assertIn("rt.find_lsblk_by_name", text)


if __name__ == "__main__":
    unittest.main()
