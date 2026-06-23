"""Phase E.5: roadmap read-only router slice from backend/app.py."""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from api.routes.dev_dashboard_roadmap import router as dev_dashboard_roadmap_router

E5_ROUTES = {
    ("GET", "/api/dev-dashboard/roadmap/areas"): "dev_dashboard_roadmap.py",
    ("GET", "/api/dev-dashboard/roadmap/milestones"): "dev_dashboard_roadmap.py",
    ("GET", "/api/dev-dashboard/roadmap/blockers"): "dev_dashboard_roadmap.py",
    ("GET", "/api/dev-dashboard/roadmap/decisions"): "dev_dashboard_roadmap.py",
    ("GET", "/api/dev-dashboard/roadmap/next-prompt"): "dev_dashboard_roadmap.py",
}

FORBIDDEN_PATTERNS = (
    re.compile(r"\bsubprocess\b"),
    re.compile(r"\bsystemctl\b"),
    re.compile(r"\bsudo\b", re.I),
    re.compile(r"build_dashboard_status"),
    re.compile(r"\bos\.walk\b"),
    re.compile(r"\.rglob\("),
    re.compile(r"json\.loads\([^)]*roadmap"),
)

_BASELINE_E4_LINES = 17568


def _route_table(router) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for r in router.routes:
        methods = sorted(getattr(r, "methods", None) or [])
        path = getattr(r, "path", "")
        for m in methods:
            if m != "HEAD":
                out.append((m, path))
    return out


class TestAppRouterSliceE5(unittest.TestCase):
    def test_router_imports_without_side_effects(self) -> None:
        self.assertGreaterEqual(len(dev_dashboard_roadmap_router.routes), 5)

    def test_public_paths_and_methods_unchanged(self) -> None:
        tbl = _route_table(dev_dashboard_roadmap_router)
        for key in E5_ROUTES:
            self.assertIn(key, tbl, f"missing route {key}")

    def test_uses_core_roadmap_bundle_only(self) -> None:
        text = (_backend / "api/routes/dev_dashboard_roadmap.py").read_text(encoding="utf-8")
        self.assertIn("load_roadmap_registry_bundle", text)
        self.assertIn("core.dev_dashboard_roadmap", text)
        for rx in FORBIDDEN_PATTERNS:
            self.assertIsNone(rx.search(text), f"router must not match {rx.pattern}")

    def test_app_py_includes_router_and_no_duplicate_handlers(self) -> None:
        app_text = (_backend / "app.py").read_text(encoding="utf-8")
        cc_ro_text = (_backend / "api/routes/control_center_readonly.py").read_text(encoding="utf-8")
        self.assertIn("include_router(dev_dashboard_roadmap_router)", app_text)
        self.assertIn("include_router(control_center_readonly_router)", app_text)
        self.assertIn('@router.get("/api/dev-dashboard/roadmap")', cc_ro_text)
        self.assertNotIn('@app.get("/api/dev-dashboard/roadmap")', app_text)
        for dup in (
            '@app.get("/api/dev-dashboard/roadmap/areas")',
            '@app.get("/api/dev-dashboard/roadmap/milestones")',
            '@app.get("/api/dev-dashboard/roadmap/blockers")',
            '@app.get("/api/dev-dashboard/roadmap/decisions")',
            '@app.get("/api/dev-dashboard/roadmap/next-prompt")',
        ):
            self.assertNotIn(dup, app_text, f"duplicate handler still in app.py: {dup}")

    def test_app_py_line_count_reduced_after_e5(self) -> None:
        lines = (_backend / "app.py").read_text(encoding="utf-8").count("\n") + 1
        self.assertLess(lines, _BASELINE_E4_LINES, "app.py should be smaller after E.5 extraction")

    def test_handlers_are_get_only(self) -> None:
        text = (_backend / "api/routes/dev_dashboard_roadmap.py").read_text(encoding="utf-8")
        self.assertNotIn("@router.post", text)
        self.assertGreaterEqual(text.count("@router.get"), 5)
