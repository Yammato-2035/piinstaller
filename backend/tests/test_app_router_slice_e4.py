"""Phase E.4: fourth read-only router slice — dev-dashboard indexes via core modules."""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from api.routes.dev_dashboard_readonly import router as dev_dashboard_readonly_router

E4_ROUTES = {
    ("GET", "/api/dev-dashboard/modules"): "dev_dashboard_readonly.py",
    ("GET", "/api/dev-dashboard/modules/{module_id}"): "dev_dashboard_readonly.py",
    ("GET", "/api/dev-dashboard/evidence-index"): "dev_dashboard_readonly.py",
    ("GET", "/api/dev-dashboard/manual-command-runs"): "dev_dashboard_readonly.py",
    ("GET", "/api/dev-dashboard/recent-evidence"): "dev_dashboard_readonly.py",
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
    re.compile(r"\bos\.walk\b"),
    re.compile(r"\.rglob\("),
)

_BASELINE_E3_LINES = 17617


def _route_table(router) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for r in router.routes:
        methods = sorted(getattr(r, "methods", None) or [])
        path = getattr(r, "path", "")
        for m in methods:
            if m != "HEAD":
                out.append((m, path))
    return out


class TestAppRouterSliceE4(unittest.TestCase):
    def test_router_imports_without_side_effects(self) -> None:
        self.assertTrue(dev_dashboard_readonly_router.routes)

    def test_public_paths_and_methods_unchanged(self) -> None:
        tbl = _route_table(dev_dashboard_readonly_router)
        for key in E4_ROUTES:
            self.assertIn(key, tbl, f"missing route {key}")

    def test_no_subprocess_or_local_file_scanners(self) -> None:
        text = (_backend / "api/routes/dev_dashboard_readonly.py").read_text(encoding="utf-8")
        for rx in FORBIDDEN_PATTERNS:
            self.assertIsNone(rx.search(text), f"router must not match {rx.pattern}")
        self.assertIn("dev_dashboard", text)
        self.assertIn("build_modules_list", text)
        self.assertIn("build_dcc_evidence_index_api", text)
        self.assertIn("dcc_status_facade", text)

    def test_app_py_includes_router_and_no_duplicate_handlers(self) -> None:
        app_text = (_backend / "app.py").read_text(encoding="utf-8")
        self.assertIn("include_router(dev_dashboard_readonly_router)", app_text)
        for dup in (
            '@app.get("/api/dev-dashboard/modules")',
            '@app.get("/api/dev-dashboard/modules/{module_id}")',
            '@app.get("/api/dev-dashboard/evidence-index")',
            '@app.get("/api/dev-dashboard/manual-command-runs")',
            '@app.get("/api/dev-dashboard/recent-evidence")',
        ):
            self.assertNotIn(dup, app_text, f"duplicate handler still in app.py: {dup}")

    def test_app_py_line_count_reduced_after_e4(self) -> None:
        lines = (_backend / "app.py").read_text(encoding="utf-8").count("\n") + 1
        self.assertLess(lines, _BASELINE_E3_LINES, "app.py should be smaller after E.4 extraction")

    def test_handlers_are_get_only(self) -> None:
        text = (_backend / "api/routes/dev_dashboard_readonly.py").read_text(encoding="utf-8")
        self.assertNotIn("@router.post", text)
        self.assertGreaterEqual(text.count("@router.get"), 5)
