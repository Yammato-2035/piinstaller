"""Phase F.2: DCC aggregation routes migrated to dcc_status_facade."""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path
from unittest import mock

_BACKEND = Path(__file__).resolve().parent.parent
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

APP_PY = _BACKEND / "app.py"
STATUS_SERVICE = _BACKEND / "core" / "dev_dashboard_status_service.py"

MIGRATED_HANDLERS = (
    "dev_dashboard_status",
    "dev_dashboard_control_center_summary",
    "dev_dashboard_roadmap",
    "dev_dashboard_project_overview",
    "dev_dashboard_prompt_findings",
    "dev_dashboard_cursor_meta_prompt",
)

FACADE_IMPORTS = (
    "build_dcc_control_center_summary_api",
    "build_dcc_roadmap_api_bundle",
    "build_dcc_project_overview_body",
    "build_dcc_prompt_findings_api",
    "build_dcc_cursor_meta_prompt_api",
)


class TestDccStatusFacadeRouterMigrationV1(unittest.TestCase):
    def test_app_py_migrated_handlers_use_facade(self) -> None:
        text = APP_PY.read_text(encoding="utf-8")
        for fn in MIGRATED_HANDLERS:
            self.assertIn(f"async def {fn}", text)
        for imp in FACADE_IMPORTS:
            self.assertIn(imp, text, f"missing facade import {imp}")
        self.assertIn("build_dev_dashboard_status", text)

    def test_app_py_no_direct_dashboard_aggregation_in_migrated_handlers(self) -> None:
        text = APP_PY.read_text(encoding="utf-8")
        for pattern in (
            r"dev_dashboard_roadmap[\s\S]{0,400}build_dashboard_status",
            r"dev_dashboard_control_center_summary[\s\S]{0,400}build_dashboard_status",
            r"dev_dashboard_prompt_findings[\s\S]{0,400}build_dashboard_status",
            r"dev_dashboard_cursor_meta_prompt[\s\S]{0,400}build_dashboard_status",
        ):
            self.assertIsNone(re.search(pattern, text), f"direct aggregation still present: {pattern}")

    def test_status_service_uses_facade(self) -> None:
        text = STATUS_SERVICE.read_text(encoding="utf-8")
        self.assertIn("build_dashboard_status_body", text)
        self.assertIn("dcc_status_facade", text)
        self.assertNotIn("dev_dashboard_core.build_dashboard_status", text)

    def test_profile_gate_preserved_in_status_service(self) -> None:
        text = STATUS_SERVICE.read_text(encoding="utf-8")
        self.assertIn("build_dcc_profile_block_response", text)

    def test_roadmap_api_bundle_returns_legacy_shape(self) -> None:
        from core.dcc_status_facade import build_dcc_roadmap_api_bundle

        fake_bundle = {"status": "success", "areas": [], "read_only": True}
        with mock.patch(
            "core.dcc_status_facade.build_dcc_roadmap_overview",
            return_value={"sections": [{"data": {"bundle": fake_bundle}}]},
        ):
            out = build_dcc_roadmap_api_bundle(include_dashboard_context=True)
        self.assertEqual(out, fake_bundle)

    def test_prompt_findings_api_response_shape(self) -> None:
        from core.dcc_status_facade import build_dcc_prompt_findings_api

        with mock.patch(
            "core.dcc_status_facade.build_dashboard_status_body",
            return_value={"generated_at": "t"},
        ), mock.patch(
            "core.dev_dashboard._repo_root",
            return_value=Path("/tmp/repo"),
        ), mock.patch(
            "core.dev_dashboard_cockpit.build_prompt_findings",
            return_value=[{"id": "x"}],
        ):
            out = build_dcc_prompt_findings_api()
        self.assertEqual(out, {"status": "success", "findings": [{"id": "x"}]})

    def test_control_center_summary_api_response_shape(self) -> None:
        from core.dcc_status_facade import build_dcc_control_center_summary_api

        with mock.patch(
            "core.dcc_status_facade.build_dashboard_status_body",
            return_value={},
        ), mock.patch(
            "core.dev_control_center_summary.build_control_center_summary",
            return_value={"runtime": "ok"},
        ):
            out = build_dcc_control_center_summary_api()
        self.assertEqual(out, {"status": "success", "summary": {"runtime": "ok"}})
