"""Tests for DCC recent evidence report feed."""

from __future__ import annotations

import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from core.dev_dashboard_recent_evidence import (  # noqa: E402
    build_recent_evidence_feed,
    build_recent_evidence_for_summary,
)


class DevDashboardRecentEvidenceTests(unittest.TestCase):
    def test_june_reports_sorted_before_may(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            rescue = repo / "docs/evidence/rescue"
            rescue.mkdir(parents=True)
            old = rescue / "OLD_MAY_RESULT.md"
            old.write_text("**Datum:** 2026-05-30\nStatus: ok\n", encoding="utf-8")
            new = rescue / "QEMU_GUEST_AGENT_SMOKE_AFTER_PREFLIGHT_RESULT.md"
            new.write_text("**Datum:** 2026-06-03\nStatus: blocked\n", encoding="utf-8")
            feed = build_recent_evidence_feed(repo_root=repo, limit=5)
            items = feed.get("recent_reports") or []
            self.assertGreaterEqual(len(items), 2)
            self.assertIn("2026-06-03", str(items[0].get("timestamp") or ""))
            self.assertIn("QEMU_GUEST", str(items[0].get("path") or ""))

    def test_default_limit_five(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            base = repo / "docs/evidence/rescue"
            base.mkdir(parents=True)
            for i in range(8):
                (base / f"REPORT_{i}_RESULT.md").write_text(
                    f"**Datum:** 2026-06-0{(i % 3) + 2}\n",
                    encoding="utf-8",
                )
            feed = build_recent_evidence_feed(repo_root=repo)
            self.assertEqual(feed.get("default_limit"), 5)
            self.assertLessEqual(len(feed.get("recent_reports") or []), 5)

    def test_category_filter_rescue(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            (repo / "docs/evidence/rescue").mkdir(parents=True)
            (repo / "docs/evidence/diagnostics").mkdir(parents=True)
            (repo / "docs/evidence/rescue/R1_RESULT.md").write_text(
                "**Datum:** 2026-06-02\n", encoding="utf-8"
            )
            (repo / "docs/evidence/diagnostics/D1_RESULT.md").write_text(
                "**Datum:** 2026-06-02\n", encoding="utf-8"
            )
            feed = build_recent_evidence_feed(repo_root=repo, category="rescue", limit=10)
            paths = [str(x.get("path")) for x in feed.get("items") or []]
            self.assertTrue(all("rescue" in p for p in paths))

    def test_large_log_not_included(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            base = repo / "docs/evidence/rescue"
            base.mkdir(parents=True)
            (base / "big.log").write_text("x" * 100, encoding="utf-8")
            (base / "SMALL_RESULT.md").write_text("**Datum:** 2026-06-03\n", encoding="utf-8")
            feed = build_recent_evidence_feed(repo_root=repo, limit=10)
            paths = [str(x.get("path")) for x in feed.get("recent_reports") or []]
            self.assertNotIn("big.log", " ".join(paths))

    def test_summary_helper_returns_reports_and_tests(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            (repo / "docs/evidence/dev-dashboard").mkdir(parents=True)
            (repo / "docs/evidence/dev-dashboard/DCC_TEST_RESULT.md").write_text(
                "**Datum:** 2026-06-03\n", encoding="utf-8"
            )
            out = build_recent_evidence_for_summary(repo_root=repo)
            self.assertIn("recent_reports", out)
            self.assertIn("recent_tests", out)


if __name__ == "__main__":
    unittest.main()
