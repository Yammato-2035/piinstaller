from __future__ import annotations

import unittest
from unittest.mock import patch

from core import update_check


class UpdateCheckTests(unittest.TestCase):
    def test_deploy_required_when_drift_present(self) -> None:
        deploy_state = {
            "runtime_gate": {"exit_code": 14, "status": "yellow"},
            "deploy_drift": {"status": "yellow", "manifest_match": True},
        }
        with (
            patch.object(update_check, "build_deploy_job_state", return_value=deploy_state),
            patch.object(update_check, "_git_head", return_value="abc123"),
            patch.object(update_check, "_workspace_version", return_value="1.7.1"),
            patch.object(update_check, "_runtime_manifest", return_value={"git_commit": "def456", "project_version": "1.7.0"}),
        ):
            result = update_check.build_update_status()
        self.assertEqual(result["status"], "deploy_required")
        self.assertTrue(result["deploy_required"])

    def test_automatic_update_allowed_is_false(self) -> None:
        with (
            patch.object(update_check, "build_deploy_job_state", return_value={"runtime_gate": {"exit_code": 0}, "deploy_drift": {"status": "green", "manifest_match": True}}),
            patch.object(update_check, "_git_head", return_value="abc123"),
            patch.object(update_check, "_workspace_version", return_value="1.7.1"),
            patch.object(update_check, "_runtime_manifest", return_value=None),
        ):
            result = update_check.build_update_status()
        self.assertFalse(result["automatic_update_allowed"])

    def test_package_manager_update_allowed_is_false(self) -> None:
        with (
            patch.object(update_check, "build_deploy_job_state", return_value={"runtime_gate": {"exit_code": 0}, "deploy_drift": {"status": "green", "manifest_match": True}}),
            patch.object(update_check, "_git_head", return_value="abc123"),
            patch.object(update_check, "_workspace_version", return_value="1.7.1"),
            patch.object(update_check, "_runtime_manifest", return_value=None),
        ):
            result = update_check.build_update_status()
        self.assertFalse(result["package_manager_update_allowed"])

    def test_update_available_stays_unknown_without_remote(self) -> None:
        with (
            patch.object(update_check, "build_deploy_job_state", return_value={"runtime_gate": {"exit_code": 0}, "deploy_drift": {"status": "green", "manifest_match": True}}),
            patch.object(update_check, "_git_head", return_value="abc123"),
            patch.object(update_check, "_workspace_version", return_value="1.7.1"),
            patch.object(update_check, "_runtime_manifest", return_value=None),
        ):
            result = update_check.build_update_status()
        self.assertEqual(result["update_available"], "unknown")

    def test_no_network_required(self) -> None:
        with (
            patch.object(update_check, "build_deploy_job_state", return_value={"runtime_gate": {"exit_code": 0}, "deploy_drift": {"status": "green", "manifest_match": True}}),
            patch.object(update_check, "_git_head", return_value=None),
            patch.object(update_check, "_workspace_version", return_value="1.7.1"),
            patch.object(update_check, "_runtime_manifest", return_value=None),
        ):
            result = update_check.build_update_status()
        self.assertIn(result["status"], ("ok", "blocked", "deploy_required"))
        self.assertEqual(result["update_available"], "unknown")


if __name__ == "__main__":
    unittest.main()
