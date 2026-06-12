"""Phase E.3: third read-only router slice extracted from backend/app.py."""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from api.routes.capabilities import router as capabilities_router
from api.routes.catalog import router as catalog_router
from api.routes.health import router as health_router
from api.routes.status import router as status_router

E3_ROUTES = {
    ("GET", "/api/logs/tail"): "health.py",
    ("GET", "/api/self-update/status"): "status.py",
    ("GET", "/api/apps"): "catalog.py",
    ("GET", "/api/dev-dashboard/capability-status"): "capabilities.py",
    ("GET", "/api/dev-dashboard/compact-status"): "capabilities.py",
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

_BASELINE_E2_LINES = 17699


def _route_table(router) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for r in router.routes:
        methods = sorted(getattr(r, "methods", None) or [])
        path = getattr(r, "path", "")
        for m in methods:
            if m != "HEAD":
                out.append((m, path))
    return out


class TestAppRouterSliceE3(unittest.TestCase):
    def test_routers_import_without_side_effects(self) -> None:
        self.assertTrue(capabilities_router.routes)
        self.assertTrue(catalog_router.routes)

    def test_public_paths_and_methods_unchanged(self) -> None:
        combined = (
            _route_table(health_router)
            + _route_table(status_router)
            + _route_table(catalog_router)
            + _route_table(capabilities_router)
        )
        for key in E3_ROUTES:
            self.assertIn(key, combined, f"missing route {key}")

    def test_no_subprocess_storage_safety_mount_duplicates(self) -> None:
        for rel in ("api/routes/capabilities.py", "api/routes/catalog.py"):
            text = (_backend / rel).read_text(encoding="utf-8")
            for rx in FORBIDDEN_PATTERNS:
                self.assertIsNone(rx.search(text), f"{rel} must not match {rx.pattern}")
        for rel in ("api/routes/health.py", "api/routes/status.py"):
            text = (_backend / rel).read_text(encoding="utf-8")
            for rx in FORBIDDEN_PATTERNS:
                if rel == "api/routes/status.py" and rx.pattern == r"\bsudo\b":
                    continue
                self.assertIsNone(rx.search(text), f"{rel} E.3 additions must not match {rx.pattern}")

    def test_app_py_includes_routers_and_no_duplicate_handlers(self) -> None:
        app_text = (_backend / "app.py").read_text(encoding="utf-8")
        self.assertIn("include_router(capabilities_router)", app_text)
        self.assertIn("include_router(catalog_router)", app_text)
        for dup in (
            '@app.get("/api/logs/tail")',
            '@app.get("/api/self-update/status")',
            '@app.get("/api/apps")',
            '@app.get("/api/dev-dashboard/capability-status")',
            '@app.get("/api/dev-dashboard/compact-status")',
        ):
            self.assertNotIn(dup, app_text, f"duplicate handler still in app.py: {dup}")

    def test_app_py_line_count_reduced_after_e3(self) -> None:
        lines = (_backend / "app.py").read_text(encoding="utf-8").count("\n") + 1
        self.assertLess(lines, _BASELINE_E2_LINES, "app.py should be smaller after E.3 extraction")

    def test_e3_handlers_are_get_only(self) -> None:
        for rel in ("api/routes/capabilities.py", "api/routes/catalog.py"):
            text = (_backend / rel).read_text(encoding="utf-8")
            self.assertNotIn("@router.post", text)
            self.assertGreaterEqual(text.count("@router.get"), 1)


try:
    from fastapi.testclient import TestClient
    from app import app

    _HAS_APP = True
except Exception:
    _HAS_APP = False
    TestClient = None
    app = None


@unittest.skipUnless(_HAS_APP, "FastAPI TestClient nicht verfuegbar (httpx fehlt oder app-Import)")
class TestAppRouterSliceE3Integration(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app, base_url="http://localhost")

    def test_apps_catalog_still_ok(self) -> None:
        r = self.client.get("/api/apps")
        self.assertEqual(r.status_code, 200, r.text)
        self.assertIn("apps", r.json())
