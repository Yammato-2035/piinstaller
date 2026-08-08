"""Unit tests for boot correlation + root-cause ranking (007 Phases 19–20)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from rescue.boot_correlation_ranking import correlate_boots, rank_root_causes


class RankRootCausesTests(unittest.TestCase):
    def test_sorts_by_confidence_desc(self) -> None:
        ranked = rank_root_causes(
            [
                {"hypothesis": "AMD DRM issue", "confidence": 0.22},
                {"hypothesis": "Xorg not invoked", "confidence": 0.93},
                {"hypothesis": "Xauth/TTY problem", "confidence": 0.71},
                {"hypothesis": "Chromium issue", "confidence": 0.05},
            ]
        )
        self.assertEqual(ranked[0]["hypothesis"], "Xorg not invoked")
        self.assertEqual(ranked[0]["rank"], 1)
        self.assertEqual(ranked[0]["confidence"], 0.93)
        self.assertEqual(ranked[1]["hypothesis"], "Xauth/TTY problem")
        self.assertEqual(ranked[-1]["hypothesis"], "Chromium issue")
        confidences = [c["confidence"] for c in ranked]
        self.assertEqual(confidences, sorted(confidences, reverse=True))

    def test_empty_candidates(self) -> None:
        self.assertEqual(rank_root_causes([]), [])
        self.assertEqual(rank_root_causes(None), [])


class CorrelateBootsTests(unittest.TestCase):
    def test_persistent_intermittent_resolved_new(self) -> None:
        boots = [
            {"boot_id": "b1", "issue_codes": ["wifi.rfkill", "gpu.drm_timeout", "usb.reset"]},
            {"boot_id": "b2", "issue_codes": ["wifi.rfkill", "gpu.drm_timeout"]},
            {"boot_id": "b3", "issue_codes": ["wifi.rfkill", "net.dhcp_timeout"]},
        ]
        out = correlate_boots(boots)
        self.assertIn("wifi.rfkill", out["persistent_problem"])
        self.assertIn("gpu.drm_timeout", out["resolved_problem"])
        self.assertIn("net.dhcp_timeout", out["new_problem"])
        # usb.reset only in first boot → resolved (previous, not current)
        self.assertIn("usb.reset", out["resolved_problem"])
        self.assertEqual(out["boot_count"], 3)

    def test_intermittent_when_present_some_not_all_and_in_current(self) -> None:
        boots = [
            {"issue_codes": ["a", "flicker"]},
            {"issue_codes": ["a"]},
            {"issue_codes": ["a", "flicker"]},
        ]
        out = correlate_boots(boots)
        self.assertIn("a", out["persistent_problem"])
        self.assertIn("flicker", out["intermittent_problem"])
        self.assertNotIn("flicker", out["persistent_problem"])
        self.assertNotIn("flicker", out["new_problem"])
        self.assertNotIn("flicker", out["resolved_problem"])

    def test_findings_mapping_issue_codes(self) -> None:
        boots = [
            {"findings": [{"issue_code": "x"}, {"issue_code": "y"}]},
            {"findings": [{"issue_code": "x"}]},
        ]
        out = correlate_boots(boots)
        self.assertIn("x", out["persistent_problem"])
        self.assertIn("y", out["resolved_problem"])

    def test_empty_boots(self) -> None:
        out = correlate_boots([])
        self.assertEqual(out["persistent_problem"], [])
        self.assertEqual(out["intermittent_problem"], [])
        self.assertEqual(out["resolved_problem"], [])
        self.assertEqual(out["new_problem"], [])


if __name__ == "__main__":
    unittest.main()
