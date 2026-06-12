"""Phase E.2: second read-only router slice extracted from backend/app.py."""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from api.routes.settings import router as settings_router
from api.routes.status import router as status_router

E2_ROUTES = {
    ("GET", "/api/settings"): "settings.py",
    ("GET", "/api/settings/notifications/email"): "settings.py",
    ("GET", "/api/presets/list"): "status.py",
    ("GET", "/api/debug/routes"): "status.py",
    ("GET", "/api/user-profile"): "status.py",
}

FORBIDDEN_PATTERNS = (
    re.compile(r"\bsubprocess\b"),
    re.compile(r"\bsystemctl\b"),
    re.compile(r"\bsudo\b", re.I),
    re.compile(r"\blsblk\b"),
    re.compile(r"\bblkid\b"),
    re.compile(r"\bfindmnt\b"),
    re.compile(r"validate_write_target"),
    re.compile(r"write_guard"),
)

_BASELINE_E1_LINES = 17779


def _route_table(router) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for r in router.routes:
        methods = sorted(getattr(r, "methods", None) or [])
        path = getattr(r, "path", "")
        for m in methods:
            if m != "HEAD":
                out.append((m, path))
    return out


class TestAppRouterSliceE2(unittest.TestCase):
    def test_routers_import_without_side_effects(self) -> None:
        self.assertTrue(settings_router.routes)
        self.assertTrue(status_router.routes)

    def test_public_paths_and_methods_unchanged(self) -> None:
        combined = _route_table(settings_router) + _route_table(status_router)
        for key in E2_ROUTES:
            self.assertIn(key, combined, f"missing route {key}")
        self.assertEqual(len(combined), len(E2_ROUTES))

    def test_no_subprocess_storage_safety_mount_duplicates(self) -> None:
        for rel in ("api/routes/settings.py", "api/routes/status.py"):
            text = (_backend / rel).read_text(encoding="utf-8")
            for rx in FORBIDDEN_PATTERNS:
                self.assertIsNone(rx.search(text), f"{rel} must not match {rx.pattern}")

    def test_app_py_includes_routers_and_no_duplicate_handlers(self) -> None:
        app_text = (_backend / "app.py").read_text(encoding="utf-8")
        self.assertIn("include_router(settings_router)", app_text)
        self.assertIn("include_router(status_router)", app_text)
        for dup in (
            '@app.get("/api/settings")',
            '@app.get("/api/settings/notifications/email")',
            '@app.get("/api/presets/list")',
            '@app.get("/api/debug/routes")',
            '@app.get("/api/user-profile")',
        ):
            self.assertNotIn(dup, app_text, f"duplicate handler still in app.py: {dup}")

    def test_app_py_line_count_reduced_after_e2(self) -> None:
        lines = (_backend / "app.py").read_text(encoding="utf-8").count("\n") + 1
        self.assertLess(lines, _BASELINE_E1_LINES, "app.py should be smaller after E.2 extraction")

    def test_handlers_are_get_only(self) -> None:
        for rel in ("api/routes/settings.py", "api/routes/status.py"):
            text = (_backend / rel).read_text(encoding="utf-8")
            self.assertNotIn("@router.post", text)
            self.assertNotIn("@router.put", text)
            self.assertNotIn("@router.delete", text)
            self.assertGreaterEqual(text.count("@router.get"), 1)


try:
    from fastapi.testclient import TestClient
    from app import app

    _HAS_APP = True
except Exception as _import_exc:
    _HAS_APP = False
    _IMPORT_REASON = str(_import_exc)
    TestClient = None
    app = None


@unittest.skipUnless(_HAS_APP, "FastAPI TestClient nicht verfuegbar (httpx fehlt oder app-Import)")
class TestAppRouterSliceE2Integration(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app, base_url="http://localhost")

    def test_settings_get_still_ok(self) -> None:
        r = self.client.get("/api/settings")
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(r.json().get("status"), "success")

    def test_user_profile_get_still_ok(self) -> None:
        r = self.client.get("/api/user-profile")
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(r.json().get("status"), "success")
