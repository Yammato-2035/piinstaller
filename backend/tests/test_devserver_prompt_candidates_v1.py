"""Tests für devserver.prompt_candidates."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from devserver.models import default_dev_report, new_id
from devserver.prompt_candidates import build_prompt_candidate_from_reports
from devserver.storage import DevServerStorage


class DevServerPromptCandidatesTests(unittest.TestCase):
    def setUp(self) -> None:
        self._td = tempfile.TemporaryDirectory()
        self.storage = DevServerStorage(Path(self._td.name))

    def tearDown(self) -> None:
        self._td.cleanup()

    def test_report_group_creates_draft(self) -> None:
        rid = new_id("report")
        self.storage.save_report(
            default_dev_report(
                report_id=rid,
                node_id="n1",
                report_type="storage",
                payload={},
            ),
        )
        candidate = build_prompt_candidate_from_reports([rid], storage=self.storage)
        self.assertEqual(candidate["status"], "draft")
        self.assertIn(rid, candidate["source_report_ids"])
        self.assertTrue(candidate["candidate_id"])

    def test_no_automatic_execution(self) -> None:
        rid = new_id("report")
        self.storage.save_report(default_dev_report(report_id=rid, node_id="n1"))
        candidate = build_prompt_candidate_from_reports([rid], storage=self.storage)
        self.assertNotIn("execute", candidate.get("suggested_cursor_task", "").lower())

    def test_safety_rules_contain_no_write(self) -> None:
        candidate = build_prompt_candidate_from_reports([], storage=self.storage)
        rules = " ".join(candidate.get("safety_rules") or [])
        self.assertIn("no write", rules)
        self.assertIn("no backup", rules)
        self.assertIn("no restore", rules)


if __name__ == "__main__":
    unittest.main()
