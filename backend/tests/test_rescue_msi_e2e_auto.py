"""Tests for MSI unattended physical E2E automation."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from core.rescue_msi_e2e_auto import (
    prepare_msi_e2e_paths,
    run_msi_physical_e2e_auto,
    write_msi_e2e_auto_result,
)


class TestMsiE2EAuto(unittest.TestCase):
    def test_prepare_synthetic_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "e2e-auto"
            paths = prepare_msi_e2e_paths(state_root=root)
            self.assertEqual(paths["layout_mode"], "msi_lab_synthetic")
            self.assertTrue(paths["lab_tmpfs_mode"])
            self.assertTrue(paths["source"].is_dir())
            self.assertTrue(paths["restore_dir"].is_dir())

    def test_write_msi_e2e_auto_result(self):
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp) / "e2e"
            path = write_msi_e2e_auto_result({"status": "msi_e2e_auto_passed"}, evidence_dir=out_dir)
            self.assertTrue(path.is_file())

    @patch("core.rescue_msi_e2e_auto.run_physical_e2e_workflow")
    @patch("core.rescue_msi_e2e_auto.create_test_data")
    @patch("core.rescue_msi_e2e_auto.resolve_msi_e2e_token_file", return_value=None)
    @patch("core.rescue_msi_e2e_auto.pick_external_e2e_candidate", return_value=None)
    def test_run_msi_auto_local_only(self, _ext, _token, _create, workflow):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "scripts").mkdir()
            script = repo / "scripts" / "create-e2e-backup-test-data.sh"
            script.write_text("#!/bin/bash\nexit 0\n", encoding="utf-8")
            workflow.return_value = {"success": True, "e2e_run_id": "run-test", "status": "passed"}
            result = run_msi_physical_e2e_auto(
                repo_root=repo,
                setup_logs_base=Path(tmp) / "logs",
                create_data_script=script,
                state_root=Path(tmp) / "state",
                use_legacy_path=True,
            )
            self.assertEqual(result["status"], "msi_e2e_auto_passed")
            self.assertEqual(result["consent_effective"], "local_only")
            self.assertEqual(result["layout_mode"], "msi_lab_synthetic")


if __name__ == "__main__":
    unittest.main()
