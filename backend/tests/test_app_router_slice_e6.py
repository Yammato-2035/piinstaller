"""Phase E.6: roadmap next-prompts read-only routes in dev_dashboard_roadmap.py."""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from api.routes.dev_dashboard_roadmap import router as dev_dashboard_roadmap_router

E6_ROUTES = {
    ("GET", "/api/dev-dashboard/roadmap/next-prompts"): "dev_dashboard_roadmap.py",
    ("GET", "/api/dev-dashboard/roadmap/export-next-prompt/{prompt_id}"): "dev_dashboard_roadmap.py",
}

FORBIDDEN_PATTERNS = (
    re.compile(r"\bsubprocess\b"),
    re.compile(r"\bsystemctl\b"),
    re.compile(r"\bsudo\b", re.I),
    re.compile(r"build_dashboard_status"),
    re.compile(r"\bos\.walk\b"),
    re.compile(r"\.rglob\("),
)

_BASELINE_E5_LINES = 17499


def _route_table(router) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for r in router.routes:
        methods = sorted(getattr(r, "methods", None) or [])
        path = getattr(r, "path", "")
        for m in methods:
            if m != "HEAD":
                out.append((m, path))
    return out


class TestAppRouterSliceE6(unittest.TestCase):
    def test_e6_routes_present_on_roadmap_router(self) -> None:
        tbl = _route_table(dev_dashboard_roadmap_router)
        for key in E6_ROUTES:
            self.assertIn(key, tbl, f"missing route {key}")

    def test_uses_core_roadmap_functions_only(self) -> None:
        text = (_backend / "api/routes/dev_dashboard_roadmap.py").read_text(encoding="utf-8")
        self.assertIn("export_next_prompt_text", text)
        self.assertIn("load_roadmap_registry_bundle", text)
        for rx in FORBIDDEN_PATTERNS:
            self.assertIsNone(rx.search(text), f"router must not match {rx.pattern}")

    def test_app_py_no_duplicate_e6_handlers(self) -> None:
        app_text = (_backend / "app.py").read_text(encoding="utf-8")
        cc_ro_text = (_backend / "api/routes/control_center_readonly.py").read_text(encoding="utf-8")
        self.assertIn("include_router(dev_dashboard_roadmap_router)", app_text)
        self.assertIn("include_router(control_center_readonly_router)", app_text)
        self.assertIn('@router.get("/api/dev-dashboard/roadmap")', cc_ro_text)
        self.assertNotIn('@app.get("/api/dev-dashboard/roadmap")', app_text)
        for dup in (
            '@app.get("/api/dev-dashboard/roadmap/next-prompts")',
            '@app.get("/api/dev-dashboard/roadmap/export-next-prompt/{prompt_id}")',
        ):
            self.assertNotIn(dup, app_text, f"duplicate handler still in app.py: {dup}")

    def test_app_py_line_count_reduced_after_e6(self) -> None:
        lines = (_backend / "app.py").read_text(encoding="utf-8").count("\n") + 1
        self.assertLess(lines, _BASELINE_E5_LINES, "app.py should be smaller after E.6 extraction")

    def test_roadmap_router_has_seven_get_handlers(self) -> None:
        text = (_backend / "api/routes/dev_dashboard_roadmap.py").read_text(encoding="utf-8")
        self.assertEqual(text.count("@router.get"), 7)
        self.assertNotIn("@router.post", text)
