from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from core import deploy_job_state as djs


class DeployJobStateTests(unittest.TestCase):
    def _base_drift(self, *, status: str = "green", suggested: list[str] | None = None) -> dict:
        return {
            "status": status,
            "suggested_actions": list(suggested or ["none"]),
            "manifest_match": True,
            "checked_files": [],
            "missing_runtime_files": [],
            "missing_workspace_files": [],
            "runtime_root": "/opt/setuphelfer",
            "workspace_root": "/home/volker/piinstaller",
            "warnings": [],
        }

    def test_missing_state_files_do_not_crash(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            workspace = Path(td) / "repo"
            workspace.mkdir()
            state_dir = Path(td) / "state"
            with (
                patch.dict(
                    os.environ,
                    {
                        "SETUPHELFER_DEPLOY_WORKSPACE_ROOT": str(workspace),
                        "SETUPHELFER_DEPLOY_JOB_DIR": str(state_dir),
                    },
                    clear=False,
                ),
                patch.object(djs, "_run_runtime_gate", return_value={"exit_code": 0, "status": "green", "summary": "ok"}),
                patch.object(djs, "_compute_deploy_drift", return_value=self._base_drift()),
                patch.object(djs, "_helper_state", return_value={"systemd_unit_present": True, "can_start_without_password": "unknown", "requires_operator_setup": False}),
                patch.object(djs, "_git_workspace_detail", return_value={"git_head": "abc123", "git_branch": "main", "git_dirty_count": 0, "git_unpushed_count": 0}),
            ):
                state = djs.build_deploy_job_state()
        self.assertEqual(state["status"], "idle")
        self.assertEqual(state["last_job"]["log_tail"], [])
        self.assertEqual(state["runtime_gate"]["status"], "green")

    def test_exit_14_is_deploy_required_and_yellow(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            workspace = Path(td) / "repo"
            workspace.mkdir()
            state_dir = Path(td) / "state"
            with (
                patch.dict(
                    os.environ,
                    {
                        "SETUPHELFER_DEPLOY_WORKSPACE_ROOT": str(workspace),
                        "SETUPHELFER_DEPLOY_JOB_DIR": str(state_dir),
                    },
                    clear=False,
                ),
                patch.object(djs, "_run_runtime_gate", return_value={"exit_code": 14, "status": "yellow", "summary": "deploy required"}),
                patch.object(djs, "_compute_deploy_drift", return_value=self._base_drift(status="yellow", suggested=["deploy_backend_files"])),
                patch.object(djs, "_helper_state", return_value={"systemd_unit_present": True, "can_start_without_password": "unknown", "requires_operator_setup": False}),
                patch.object(djs, "_git_workspace_detail", return_value={"git_head": "abc123", "git_branch": "main", "git_dirty_count": 0, "git_unpushed_count": 0}),
            ):
                state = djs.build_deploy_job_state()
        self.assertEqual(state["runtime_gate"]["exit_code"], 14)
        self.assertEqual(state["runtime_gate"]["status"], "yellow")
        self.assertEqual(state["next_action"]["type"], "deploy_required")
        self.assertEqual(state["status"], "ready")

    def test_logs_are_limited_and_redacted(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            workspace = Path(td) / "repo"
            workspace.mkdir()
            state_dir = Path(td) / "state"
            state_dir.mkdir()
            lines = [f"line-{idx}" for idx in range(70)]
            lines.append("API_KEY=supersecret")
            lines.append("Authorization: Bearer abcdef")
            (state_dir / "latest.log").write_text("\n".join(lines), encoding="utf-8")
            with (
                patch.dict(
                    os.environ,
                    {
                        "SETUPHELFER_DEPLOY_WORKSPACE_ROOT": str(workspace),
                        "SETUPHELFER_DEPLOY_JOB_DIR": str(state_dir),
                    },
                    clear=False,
                ),
                patch.object(djs, "_run_runtime_gate", return_value={"exit_code": 0, "status": "green", "summary": "ok"}),
                patch.object(djs, "_compute_deploy_drift", return_value=self._base_drift()),
                patch.object(djs, "_helper_state", return_value={"systemd_unit_present": True, "can_start_without_password": "unknown", "requires_operator_setup": False}),
                patch.object(djs, "_git_workspace_detail", return_value={"git_head": "abc123", "git_branch": "main", "git_dirty_count": 0, "git_unpushed_count": 0}),
            ):
                state = djs.build_deploy_job_state()
        tail = state["last_job"]["log_tail"]
        self.assertLessEqual(len(tail), djs.MAX_LOG_TAIL_LINES)
        joined = "\n".join(tail)
        self.assertNotIn("supersecret", joined)
        self.assertNotIn("Bearer abcdef", joined)
        self.assertIn("[REDACTED]", joined)

    def test_success_requires_deploy_exit_zero_and_runtime_gate_zero(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            workspace = Path(td) / "repo"
            workspace.mkdir()
            state_dir = Path(td) / "state"
            state_dir.mkdir()
            (state_dir / "latest.json").write_text(
                json.dumps(
                    {
                        "id": "job-1",
                        "status": "success",
                        "deploy_exit_code": 0,
                        "started_at": "2026-05-25T12:00:00Z",
                        "ended_at": "2026-05-25T12:10:00Z",
                    }
                ),
                encoding="utf-8",
            )
            common_patches = [
                patch.dict(
                    os.environ,
                    {
                        "SETUPHELFER_DEPLOY_WORKSPACE_ROOT": str(workspace),
                        "SETUPHELFER_DEPLOY_JOB_DIR": str(state_dir),
                    },
                    clear=False,
                ),
                patch.object(djs, "_compute_deploy_drift", return_value=self._base_drift()),
                patch.object(djs, "_helper_state", return_value={"systemd_unit_present": True, "can_start_without_password": "unknown", "requires_operator_setup": False}),
                patch.object(djs, "_git_workspace_detail", return_value={"git_head": "abc123", "git_branch": "main", "git_dirty_count": 0, "git_unpushed_count": 0}),
            ]
            with common_patches[0], common_patches[1], common_patches[2], common_patches[3], patch.object(
                djs, "_run_runtime_gate", return_value={"exit_code": 14, "status": "yellow", "summary": "deploy required"}
            ):
                blocked = djs.build_deploy_job_state()
            with common_patches[0], common_patches[1], common_patches[2], common_patches[3], patch.object(
                djs, "_run_runtime_gate", return_value={"exit_code": 0, "status": "green", "summary": "ok"}
            ):
                success = djs.build_deploy_job_state()
        self.assertNotEqual(blocked["status"], "success")
        self.assertEqual(success["status"], "success")


if __name__ == "__main__":
    unittest.main()
