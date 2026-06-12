"""Phase E.1: first read-only router slice extracted from backend/app.py."""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from api.routes.health import router as health_router
from api.routes.version import router as version_router

E1_ROUTES = {
    ("GET", "/health"): "health.py",
    ("GET", "/api/init/status"): "health.py",
    ("GET", "/api/logs/path"): "health.py",
    ("GET", "/api/version"): "version.py",
}

FORBIDDEN_PATTERNS = (
    re.compile(r"\bsubprocess\b"),
    re.compile(r"\bsystemctl\b"),
    re.compile(r"\bsudo\b", re.I),
    re.compile(r"\blsblk\b"),
    re.compile(r"\bblkid\b"),
    re.compile(r"validate_write_target"),
    re.compile(r"write_guard"),
)


def _route_table(router) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for r in router.routes:
        methods = sorted(getattr(r, "methods", None) or [])
        path = getattr(r, "path", "")
        for m in methods:
            if m != "HEAD":
                out.append((m, path))
    return out


class TestAppRouterSliceE1(unittest.TestCase):
    def test_routers_import_without_side_effects(self) -> None:
        self.assertTrue(health_router.routes)
        self.assertTrue(version_router.routes)

    def test_public_paths_and_methods_unchanged(self) -> None:
        health_tbl = _route_table(health_router)
        version_tbl = _route_table(version_router)
        combined = health_tbl + version_tbl
        for key in E1_ROUTES:
            self.assertIn(key, combined, f"missing route {key}")

    def test_no_subprocess_storage_safety_mount_duplicates(self) -> None:
        for rel in ("api/routes/health.py", "api/routes/version.py"):
            text = (_backend / rel).read_text(encoding="utf-8")
            for rx in FORBIDDEN_PATTERNS:
                self.assertIsNone(rx.search(text), f"{rel} must not match {rx.pattern}")

    def test_app_py_includes_routers_and_no_duplicate_handlers(self) -> None:
        app_text = (_backend / "app.py").read_text(encoding="utf-8")
        self.assertIn("include_router(health_router)", app_text)
        self.assertIn("include_router(version_router)", app_text)
        for dup in (
            '@app.get("/health")',
            '@app.get("/api/version")',
            '@app.get("/api/init/status")',
            '@app.get("/api/logs/path")',
        ):
            self.assertNotIn(dup, app_text, f"duplicate handler still in app.py: {dup}")

    def test_app_py_line_count_reduced(self) -> None:
        lines = (_backend / "app.py").read_text(encoding="utf-8").count("\n") + 1
        self.assertLess(lines, 17857, "app.py should be smaller after E.1 extraction")

    def test_handlers_are_async_get_only(self) -> None:
        for rel in ("api/routes/health.py", "api/routes/version.py"):
            text = (_backend / rel).read_text(encoding="utf-8")
            self.assertNotIn("@router.post", text)
            self.assertNotIn("@router.put", text)
            self.assertNotIn("@router.delete", text)
            self.assertGreaterEqual(text.count("@router.get"), 1)


try:
    from fastapi.testclient import TestClient
    from app import app

    _HAS_APP = True
except Exception:
    _HAS_APP = False
    TestClient = None
    app = None


@unittest.skipUnless(_HAS_APP, "FastAPI TestClient oder app nicht verfuegbar")
class TestAppRouterSliceE1Integration(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app, base_url="http://localhost")

    def test_health_endpoint_still_ok(self) -> None:
        r = self.client.get("/health")
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(r.json().get("status"), "ok")

    def test_version_endpoint_still_ok(self) -> None:
        r = self.client.get("/api/version")
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(r.json().get("status"), "success")
