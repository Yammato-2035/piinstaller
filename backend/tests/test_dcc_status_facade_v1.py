"""DCC Status Facade Phase F.1 — read-only delegation contract."""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path
from unittest import mock

_BACKEND = Path(__file__).resolve().parent.parent
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

from core.dcc_status_facade import (
    FACADE_VERSION,
    build_dcc_backend_health_section,
    build_dcc_evidence_section,
    build_dcc_facade_diagnostics,
    build_dcc_notification_section,
    build_dcc_roadmap_overview,
    build_dcc_status_overview,
    build_section_status,
    normalize_legacy_dcc_status,
    normalize_legacy_notification_summary,
    normalize_legacy_roadmap_bundle,
)

FORBIDDEN = (
    re.compile(r"\bsubprocess\b"),
    re.compile(r"\bsystemctl\b"),
    re.compile(r"\bsudo\b", re.I),
    re.compile(r"\bos\.walk\b"),
    re.compile(r"emit_notification_event"),
)


class DccStatusFacadeV1Tests(unittest.TestCase):
    def test_import_without_side_effects(self) -> None:
        self.assertEqual(FACADE_VERSION, 1)

    def test_public_functions_exist(self) -> None:
        diag = build_dcc_facade_diagnostics()
        for name in (
            "build_dcc_status_overview",
            "build_dcc_roadmap_overview",
            "build_dcc_backend_health_section",
            "build_dcc_notification_section",
            "build_dcc_evidence_section",
            "build_dcc_facade_diagnostics",
        ):
            self.assertIn(name, diag["public_functions"])

    def test_no_subprocess_or_writes_in_facade_module(self) -> None:
        src = (_BACKEND / "core" / "dcc_status_facade.py").read_text(encoding="utf-8")
        for rx in FORBIDDEN:
            self.assertIsNone(rx.search(src), f"facade must not contain {rx.pattern}")

    def test_status_values_valid(self) -> None:
        self.assertEqual(build_section_status("green"), "ok")
        self.assertEqual(build_section_status("red"), "blocked")
        self.assertEqual(build_section_status("degraded"), "degraded")
        self.assertEqual(build_section_status("gray"), "unavailable")
        self.assertEqual(build_section_status(None), "unknown")

    def test_normalize_legacy_dcc_status(self) -> None:
        norm = normalize_legacy_dcc_status(
            {
                "deploy_drift": {"status": "green"},
                "consistency": {"status": "yellow"},
                "warnings": ["a"],
            }
        )
        self.assertIn(norm["status"], ("ok", "warning", "unknown"))

    def test_build_dcc_status_overview_delegates_and_structures_result(self) -> None:
        fake_dashboard = {
            "generated_at": "2026-01-01T00:00:00+00:00",
            "deploy_drift": {"status": "green"},
            "consistency": {"status": "green"},
            "warnings": [],
            "errors": [],
        }
        with mock.patch(
            "core.dev_dashboard.build_dashboard_status",
            return_value=fake_dashboard,
        ) as m:
            result = build_dcc_status_overview()
        m.assert_called_once()
        self.assertEqual(result["facade_version"], FACADE_VERSION)
        self.assertEqual(len(result["sections"]), 1)
        self.assertEqual(result["sections"][0]["section_id"], "dashboard")
        self.assertIn("normalized", result["sections"][0]["data"])

    def test_section_failure_does_not_crash_overview(self) -> None:
        with mock.patch(
            "core.dev_dashboard.build_dashboard_status",
            side_effect=RuntimeError("boom"),
        ):
            result = build_dcc_status_overview()
        self.assertEqual(result["sections"][0]["status"], "unavailable")
        self.assertTrue(result["errors"])
        self.assertTrue(result["warnings"])

    def test_build_dcc_roadmap_overview_delegates(self) -> None:
        bundle = {
            "status": "success",
            "schema_valid": True,
            "areas": [],
            "warnings": [],
            "summary": {"status": "green"},
        }
        with mock.patch(
            "core.dev_dashboard_roadmap.load_roadmap_registry_bundle",
            return_value=bundle,
        ) as m:
            result = build_dcc_roadmap_overview()
        m.assert_called_once()
        self.assertEqual(result["sections"][0]["section_id"], "roadmap")

    def test_build_dcc_backend_health_section_mockable(self) -> None:
        with mock.patch(
            "core.dev_dashboard_backend_health.load_backend_health_snapshot",
            return_value={"status": "ok", "stale": False},
        ):
            section = build_dcc_backend_health_section()
        self.assertEqual(section["section_id"], "backend_health")
        self.assertEqual(section["status"], "ok")

    def test_build_dcc_notification_section_mockable(self) -> None:
        with mock.patch(
            "core.notification_state.build_notification_summary",
            return_value={"status": "green", "event_count": 0, "email": {"status": "ready"}},
        ):
            section = build_dcc_notification_section()
        self.assertEqual(section["section_id"], "notifications")
        self.assertEqual(normalize_legacy_notification_summary(section["data"]["summary"])["status"], "ok")

    def test_build_dcc_evidence_section_mockable(self) -> None:
        with mock.patch(
            "core.dev_dashboard.build_evidence_index",
            return_value={"status": "success", "buckets": [], "warnings": []},
        ):
            section = build_dcc_evidence_section()
        self.assertEqual(section["section_id"], "evidence")

    def test_build_dcc_facade_diagnostics(self) -> None:
        diag = build_dcc_facade_diagnostics()
        self.assertEqual(diag["facade_version"], FACADE_VERSION)
        self.assertIn("delegates_to", diag)
        self.assertIn("GET /api/dev-dashboard/status", diag["routes_pending_facade_migration"])
        self.assertFalse(diag["writes_allowed"])

    def test_normalize_roadmap_bundle(self) -> None:
        norm = normalize_legacy_roadmap_bundle({"status": "review_required", "areas": [1, 2]})
        self.assertEqual(norm["area_count"], 2)
        self.assertEqual(norm["status"], "warning")
