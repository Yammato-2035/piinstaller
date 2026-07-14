"""Tests for E2E evidence import and dev automation helpers."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from core.rescue_physical_e2e_dev_automation import prepare_lab_workspace, resolve_token_file
from core.rescue_physical_e2e_evidence_import import import_e2e_run_evidence, redact_text


class TestE2EEvidenceImport(unittest.TestCase):
    def test_redact_text_strips_bearer(self):
        raw = "Authorization: Bearer secret-token-123"
        self.assertIn("[redacted]", redact_text(raw))

    def test_import_e2e_run_evidence_copies_required_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = root / "repo"
            run_dir = root / "run" / "e2e-rescue-physical-test"
            run_dir.mkdir(parents=True)
            required = (
                "event-journal.jsonl",
                "e2e-result.json",
                "backup-result.json",
                "verify-result.json",
                "restore-result.json",
                "manifest-comparison.json",
            )
            for name in required:
                (run_dir / name).write_text(json.dumps({"file": name}) + "\n", encoding="utf-8")

            manifest = import_e2e_run_evidence(run_dir, repo_root=repo)
            self.assertTrue(manifest["import_ok"])
            dest = repo / "docs" / "evidence" / "e2e_live_001d" / "physical_run" / run_dir.name
            for name in required:
                self.assertTrue((dest / name).is_file())
            self.assertTrue((dest / "import-manifest.json").is_file())
            latest = repo / "docs" / "evidence" / "e2e_live_001d" / "physical_run_latest.json"
            self.assertTrue(latest.is_file())


class TestDevAutomationHelpers(unittest.TestCase):
    def test_prepare_lab_workspace_creates_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp) / "lab"
            paths = prepare_lab_workspace(work)
            self.assertTrue(paths["source"].is_dir())
            self.assertTrue(paths["backup_archive"].parent.is_dir())
            self.assertTrue(paths["restore_dir"].is_dir())

    def test_resolve_token_file_missing_returns_none(self):
        self.assertIsNone(resolve_token_file("/nonexistent/token-file"))


if __name__ == "__main__":
    unittest.main()
