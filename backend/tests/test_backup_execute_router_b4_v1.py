"""Backup execute router B.4 — first POST slice."""

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


class TestBackupExecuteRouterB4(unittest.TestCase):
    def test_four_post_routes(self) -> None:
        tbl = _route_table(backup_execute_router)
        self.assertGreaterEqual(len(tbl), 4)
        self.assertIn(("POST", "/api/backup/jobs/{job_id}/cancel"), tbl)
        self.assertIn(("POST", "/api/backup/profile-preview"), tbl)

    def test_no_duplicates_in_app(self) -> None:
        app_text = (_backend / "app.py").read_text(encoding="utf-8")
        for dup in (
            '@app.post("/api/backup/jobs/{job_id}/cancel")',
            '@app.post("/api/backup/profile-preview")',
        ):
            self.assertNotIn(dup, app_text)
        self.assertIn("include_router(backup_execute_router)", app_text)

    def test_handlers_use_runtime(self) -> None:
        text = (_backend / "core/backup_execute_handlers.py").read_text(encoding="utf-8")
        self.assertIn("rt.with_backup_contract", text)
        self.assertNotIn("BACKUP_JOBS", text)

    def test_remaining_backup_posts_in_app(self) -> None:
        """Nach B.4–B.8 gehören Backup-POST-Routen auf backup_execute_router, nicht app.py."""
        app_text = (_backend / "app.py").read_text(encoding="utf-8")
        remaining = re.findall(r'@app\.post\("/api/backup/', app_text)
        self.assertEqual(
            len(remaining),
            0,
            msg="backup POST routes must live on backup_execute_router, not app.py",
        )


if __name__ == "__main__":
    unittest.main()
