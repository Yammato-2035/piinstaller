"""Phase E.8: DCC read-only GET routes in dev_dashboard_readonly.py (backend-health, notifications)."""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from api.routes.dev_dashboard_readonly import router as dev_dashboard_readonly_router

E8_ROUTES = {
    ("GET", "/api/dev-dashboard/backend-health"): "dev_dashboard_readonly.py",
    ("GET", "/api/dev-dashboard/notifications/status"): "dev_dashboard_readonly.py",
    ("GET", "/api/dev-dashboard/notifications/events"): "dev_dashboard_readonly.py",
}

FORBIDDEN_PATTERNS = (
    re.compile(r"\bsubprocess\b"),
    re.compile(r"\bsystemctl\b"),
    re.compile(r"\bsudo\b", re.I),
    re.compile(r"build_dashboard_status"),
    re.compile(r"\blsblk\b"),
    re.compile(r"\bblkid\b"),
    re.compile(r"\bfindmnt\b"),
    re.compile(r"validate_write_target"),
    re.compile(r"write_guard"),
    re.compile(r"\bos\.walk\b"),
    re.compile(r"\.rglob\("),
)

_BASELINE_E7_LINES = 17472


def _route_table(router) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for r in router.routes:
        methods = sorted(getattr(r, "methods", None) or [])
        path = getattr(r, "path", "")
        for m in methods:
            if m != "HEAD":
                out.append((m, path))
    return out


class TestAppRouterSliceE8(unittest.TestCase):
    def test_router_imports_without_side_effects(self) -> None:
        self.assertTrue(dev_dashboard_readonly_router.routes)

    def test_public_paths_and_methods_unchanged(self) -> None:
        tbl = _route_table(dev_dashboard_readonly_router)
        for key in E8_ROUTES:
            self.assertIn(key, tbl, f"missing route {key}")

    def test_no_subprocess_or_dashboard_aggregation(self) -> None:
        text = (_backend / "api/routes/dev_dashboard_readonly.py").read_text(encoding="utf-8")
        for rx in FORBIDDEN_PATTERNS:
            self.assertIsNone(rx.search(text), f"router must not match {rx.pattern}")

    def test_delegates_to_facade_for_e8_routes(self) -> None:
        text = (_backend / "api/routes/dev_dashboard_readonly.py").read_text(encoding="utf-8")
        self.assertIn("build_dcc_backend_health_api", text)
        self.assertIn("build_dcc_notifications_status_api", text)
        self.assertIn("build_dcc_notifications_events_api", text)
        self.assertIn("dcc_status_facade", text)
        self.assertNotIn("load_backend_health_snapshot", text)
        self.assertNotIn("build_notification_summary", text)
        self.assertNotIn("list_notification_events", text)
        self.assertNotIn("def build_notification_summary", text)
        self.assertNotIn("def list_notification_events", text)

    def test_app_py_includes_router_and_no_duplicate_handlers(self) -> None:
        app_text = (_backend / "app.py").read_text(encoding="utf-8")
        self.assertIn("include_router(dev_dashboard_readonly_router)", app_text)
        for dup in (
            '@app.get("/api/dev-dashboard/backend-health")',
            '@app.get("/api/dev-dashboard/notifications/status")',
            '@app.get("/api/dev-dashboard/notifications/events")',
        ):
            self.assertNotIn(dup, app_text, f"duplicate handler still in app.py: {dup}")

    def test_app_py_line_count_reduced_after_e8(self) -> None:
        lines = (_backend / "app.py").read_text(encoding="utf-8").count("\n") + 1
        self.assertLess(lines, _BASELINE_E7_LINES, "app.py should be smaller after E.8 extraction")

    def test_handlers_are_get_only_for_e8(self) -> None:
        text = (_backend / "api/routes/dev_dashboard_readonly.py").read_text(encoding="utf-8")
        self.assertEqual(text.count("@router.get"), 8)
        self.assertNotIn("@router.post", text)

    def test_readonly_router_has_eight_get_handlers_total(self) -> None:
        tbl = _route_table(dev_dashboard_readonly_router)
        get_routes = [p for m, p in tbl if m == "GET"]
        self.assertEqual(len(get_routes), 8)
