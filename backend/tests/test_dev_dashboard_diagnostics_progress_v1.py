from __future__ import annotations

import sys
import unittest
from pathlib import Path

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from core.dev_dashboard_roadmap import load_roadmap_registry_bundle  # noqa: E402


class DevDashboardDiagnosticsProgressTests(unittest.TestCase):
    def test_roadmap_bundle_exposes_diagnostics_progress(self) -> None:
        repo = Path(__file__).resolve().parent.parent.parent
        bundle = load_roadmap_registry_bundle(repo)
        roadmap = bundle.get("roadmap") or {}
        progress = roadmap.get("diagnostics_progress") or {}

        required_keys = {
            "catalog_status",
            "matcher_status",
            "api_status",
            "ui_status",
            "evidence_status",
            "test_track_status",
            "rescue_build_diagnostics_status",
            "backup_diagnostics_status",
            "restore_diagnostics_status",
            "runtime_diagnostics_status",
            "notification_diagnostics_status",
            "architecture_diagnostics_status",
        }
        self.assertTrue(required_keys.issubset(set(progress.keys())))
        self.assertIn(progress.get("rescue_build_diagnostics_status"), ("yellow", "partial_green"))
        self.assertIn(progress.get("notification_diagnostics_status"), ("yellow", "partial_green"))
        self.assertIn(progress.get("restore_diagnostics_status"), ("deferred", "yellow"))

    def test_diagnostics_area_stays_non_green_and_restore_stays_deferred(self) -> None:
        repo = Path(__file__).resolve().parent.parent.parent
        bundle = load_roadmap_registry_bundle(repo)
        areas = bundle.get("areas") or []

        diagnostics = next(area for area in areas if area.get("id") == "diagnostics")
        restore = next(area for area in areas if area.get("id") == "restore")

        self.assertIn(diagnostics.get("status"), ("yellow", "partial_green"))
        self.assertNotEqual(diagnostics.get("status"), "green")
        self.assertEqual(restore.get("status"), "deferred")

    def test_next_prompt_moves_to_operator_terminal_build(self) -> None:
        repo = Path(__file__).resolve().parent.parent.parent
        bundle = load_roadmap_registry_bundle(repo)
        recommended = bundle.get("recommended_prompt") or {}
        self.assertEqual(recommended.get("id"), "RESCUE_ISO_MANUAL_OPERATOR_TERMINAL_BUILD")


if __name__ == "__main__":
    unittest.main()
