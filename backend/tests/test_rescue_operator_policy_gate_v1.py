from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from core import rescue_iso_build_state as state  # noqa: E402


class RescueOperatorPolicyGateTests(unittest.TestCase):
    def _init_git_repo(self, repo: Path) -> None:
        subprocess.run(["git", "-C", str(repo), "init", "-q"], check=True)

    def test_operator_policy_gate_exposes_sudo_blocker_without_greenwashing(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            self._init_git_repo(repo)
            base = repo / "docs/evidence/runtime-results/rescue"
            (base / "build-logs").mkdir(parents=True, exist_ok=True)
            (base / "rescue_iso_controlled_amd64_build_run_latest.json").write_text(
                (
                    "{"
                    '"command":"scripts/rescue-live/run-controlled-iso-build-with-logging.sh --operator-confirm-build",'
                    '"started_at":"2026-05-26T20:15:26+00:00",'
                    '"exit_code":1'
                    "}"
                ),
                encoding="utf-8",
            )
            (base / "rescue_iso_controlled_amd64_build_result_latest.json").write_text(
                (
                    "{"
                    '"result_status":"blocked",'
                    '"error_code":"blocked_requires_operator_sudo_policy",'
                    '"exit_code":1,'
                    '"iso_created":false,'
                    '"usb_write_performed":false'
                    "}"
                ),
                encoding="utf-8",
            )
            (base / "build-logs/rescue_iso_controlled_amd64_build_combined_latest.log").write_text(
                "sudo: ein Terminal ist erforderlich\nsudo: Ein Passwort ist notwendig\n",
                encoding="utf-8",
            )
            paths = {
                "runtime_path": "/opt/setuphelfer",
                "workspace_path": str(repo),
                "build_tree_path": str(repo / "build/rescue/live-build/setuphelfer-rescue-live"),
                "temp_runtime_bundle_path": str(repo / "build/rescue/temp-runtime/setuphelfer-rescue-runtime"),
                "logs_path": str(repo / "build/rescue/logs/controlled-iso-build"),
                "summary_path": str(repo / "docs/evidence/runtime-results/rescue/controlled_iso_build_latest_summary.json"),
                "path_mode": "workspace_build_runtime_opt",
                "path_status": "ok",
                "errors": [],
                "warnings": [],
                "workspace_head": "db05447",
                "workspace_branch": "main",
            }
            with (
                patch.object(state, "resolve_rescue_iso_paths", return_value=paths),
                patch.object(state, "_runtime_gate", return_value={"status": "green", "exit_code": 0, "summary": "ok"}),
                patch.object(state, "_tool_presence", return_value={"present": True, "path": "/usr/bin/tool"}),
                patch.object(
                    state,
                    "inspect_rsvg_build_dependency",
                    return_value={
                        "required": True,
                        "status": "ok",
                        "summary": "legacy wrapper ready",
                        "legacy_path": str(repo / "build/rescue/tool-compat/bin/rsvg"),
                        "compat_path": "/usr/bin/rsvg-convert",
                        "legacy_source": "project_local_wrapper",
                        "error_code": None,
                        "hint_package": "librsvg2-bin",
                    },
                ),
                patch.object(state, "detect_live_build_stale_state", return_value={"present": False, "needs_sudo_clean": False}),
                patch.object(state, "_temp_runtime_bundle", return_value={"status": "ok", "files_count": 1, "manifest_sha256": "abc"}),
                patch.object(
                    state,
                    "_build_tree",
                    return_value={"validator_status": "ok", "auto_config_noauto": True, "auto_build_blocked": True, "source_head": "db05447"},
                ),
                patch.object(state, "_dpkg_preflight", return_value={"status": "pre_chroot_ok", "summary": "ok"}),
                patch.object(state, "read_rescue_iso_latest_logs", return_value={"latest_log_path": "x", "last_80_lines": [], "last_error": None}),
                patch.object(
                    state,
                    "summarize_rescue_iso_artifacts",
                    return_value={"iso_found": False, "iso_path": None, "iso_abs_path": None, "iso_size_bytes": None, "iso_sha256": None},
                ),
                patch.object(state, "_summary_payload", return_value={}),
            ):
                payload = state.build_rescue_iso_dashboard_state(repo_root=Path("/opt/setuphelfer"))

        self.assertEqual(payload["status"], "yellow")
        self.assertEqual(payload["operator_policy_gate"]["status"], "review_required")
        self.assertEqual(payload["operator_policy_gate"]["error_code"], "blocked_requires_operator_sudo_policy")
        self.assertEqual(payload["operator_policy_gate"]["next_action"], "manual_operator_terminal_required")
        self.assertIn("password_stdin", payload["operator_policy_gate"]["forbidden_execution_modes"])
        self.assertIn("broad_nopasswd", payload["operator_policy_gate"]["forbidden_execution_modes"])
        self.assertEqual(payload["rescue_build_progress"]["target_architecture"], "amd64")
        self.assertEqual(payload["rescue_build_progress"]["iso_artifact"], "not_started")
        self.assertEqual(payload["rescue_build_progress"]["usb_write"], "blocked")
        self.assertEqual(payload["rescue_build_progress"]["restore_test"], "deferred")
        self.assertEqual(payload["next_operator_action"]["type"], "operator_policy_required")


if __name__ == "__main__":
    unittest.main()
