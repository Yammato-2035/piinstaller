from __future__ import annotations

import json
import unittest
from pathlib import Path


class DiagnosticsTestTrackTests(unittest.TestCase):
    def test_test_track_contains_required_sections_and_cases(self) -> None:
        root = Path(__file__).resolve().parent.parent.parent
        path = root / "docs/evidence/diagnostics/DIAGNOSTICS_TEST_TRACK_LATEST.json"
        data = json.loads(path.read_text(encoding="utf-8"))

        tracks = data.get("tracks") or []
        track_ids = {str(item.get("id") or "") for item in tracks if isinstance(item, dict)}
        self.assertTrue(
            {
                "rescue_build_diagnostics",
                "backup_diagnostics",
                "restore_diagnostics",
                "runtime_deploy_diagnostics",
                "notification_diagnostics",
                "architecture_diagnostics",
            }.issubset(track_ids)
        )

        expected_codes = {
            str(case.get("expected_diagnostic_code") or "")
            for track in tracks
            if isinstance(track, dict)
            for case in (track.get("cases") or [])
            if isinstance(case, dict)
        }
        self.assertIn("RESCUE-BUILD-ROOT-001", expected_codes)
        self.assertIn("RESCUE-BUILD-GATE-001", expected_codes)
        self.assertIn("RESCUE-BUILD-TOOL-001", expected_codes)
        self.assertIn("RESCUE-BUILD-RSVG-001", expected_codes)
        self.assertIn("RESCUE-BUILD-ARCH-001", expected_codes)
        self.assertIn("NOTIFICATION-EMAIL-PROVIDER-001", expected_codes)

    def test_test_track_keeps_diagnostics_non_green_and_updates_next_prompt(self) -> None:
        root = Path(__file__).resolve().parent.parent.parent
        path = root / "docs/evidence/diagnostics/DIAGNOSTICS_TEST_TRACK_LATEST.json"
        data = json.loads(path.read_text(encoding="utf-8"))

        self.assertIn(data.get("overall_status"), ("yellow", "partial_green"))
        self.assertNotEqual(data.get("overall_status"), "green")
        self.assertEqual(data.get("next_prompt_id"), "RESCUE_ISO_MANUAL_OPERATOR_TERMINAL_BUILD")


if __name__ == "__main__":
    unittest.main()
