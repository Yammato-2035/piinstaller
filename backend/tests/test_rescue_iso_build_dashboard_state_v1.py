"""Tests fuer den read-only Rescue-ISO-Dashboard-State."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from core import rescue_iso_build_state as state  # noqa: E402


class RescueIsoBuildDashboardStateTests(unittest.TestCase):
    def _repo(self) -> tempfile.TemporaryDirectory[str]:
        return tempfile.TemporaryDirectory()

    def _init_git_repo(self, repo: Path) -> None:
        subprocess.run(["git", "-C", str(repo), "init", "-q"], check=True)

    def test_missing_evidence_does_not_crash(self) -> None:
        with self._repo() as td:
            repo = Path(td)
            self._init_git_repo(repo)
            payload = state.build_rescue_iso_dashboard_state(repo_root=repo)
            self.assertIn(payload["status"], ("gray", "yellow", "red", "green"))
            self.assertFalse(payload["usb_write"]["allowed"])

    def test_tar_failed_is_detected_from_debootstrap_log(self) -> None:
        with self._repo() as td:
            repo = Path(td)
            self._init_git_repo(repo)
            log = repo / "build/rescue/live-build/setuphelfer-rescue-live/chroot/debootstrap/debootstrap.log"
            log.parent.mkdir(parents=True, exist_ok=True)
            log.write_text("E: Tried to extract package, but tar failed. Exit...\n", encoding="utf-8")
            stale = state.detect_live_build_stale_state(repo_root=repo)
            self.assertIn("debootstrap_tar_failed", stale["indicators"])

    def test_chroot_package_lists_install_stale_is_detected(self) -> None:
        with self._repo() as td:
            repo = Path(td)
            self._init_git_repo(repo)
            marker = repo / "build/rescue/live-build/setuphelfer-rescue-live/.build/chroot_package-lists.install"
            marker.parent.mkdir(parents=True, exist_ok=True)
            marker.write_text("done\n", encoding="utf-8")
            stale = state.detect_live_build_stale_state(repo_root=repo)
            self.assertTrue(stale["present"])
            self.assertTrue(stale["stage_marker_present"])
            self.assertIn("chroot_package-lists.install stale", stale["indicators"])

    def test_root_owned_stage_files_trigger_operator_action(self) -> None:
        with self._repo() as td:
            repo = Path(td)
            self._init_git_repo(repo)
            fake = repo / "build/rescue/live-build/setuphelfer-rescue-live/.build/root-owned"
            fake.parent.mkdir(parents=True, exist_ok=True)
            fake.write_text("x", encoding="utf-8")
            with patch.object(state, "_list_root_owned_entries", return_value=[fake]):
                payload = state.build_rescue_iso_dashboard_state(repo_root=repo)
            self.assertTrue(payload["stale_state"]["needs_sudo_clean"])
            self.assertEqual(payload["next_operator_action"]["type"], "sudo_clean_required")

    def test_generated_bundle_dir_root_owned_triggers_operator_action(self) -> None:
        with self._repo() as td:
            repo = Path(td)
            self._init_git_repo(repo)
            fake = repo / "build/rescue/live-build/setuphelfer-rescue-live/config/includes.chroot/opt/setuphelfer-rescue"
            fake.parent.mkdir(parents=True, exist_ok=True)
            fake.write_text("x", encoding="utf-8")
            with patch.object(state, "_list_root_owned_entries", return_value=[fake]):
                payload = state.build_rescue_iso_dashboard_state(repo_root=repo)
            self.assertTrue(payload["stale_state"]["needs_sudo_clean"])
            self.assertEqual(payload["next_operator_action"]["type"], "sudo_clean_required")

    def test_auto_config_without_noauto_is_review_required(self) -> None:
        with self._repo() as td:
            repo = Path(td)
            self._init_git_repo(repo)
            root = repo / "build/rescue/live-build/setuphelfer-rescue-live/auto"
            root.mkdir(parents=True, exist_ok=True)
            (root / "config").write_text("#!/bin/sh\nlb config\n", encoding="utf-8")
            (root / "build").write_text("#!/bin/sh\nexit 20\n", encoding="utf-8")
            tree = state.build_rescue_iso_dashboard_state(repo_root=repo)["build_tree"]
            self.assertIn(tree["validator_status"], ("review_required", "blocked", "unknown"))
            self.assertFalse(tree["auto_config_noauto"])

    def test_auto_build_blocking_is_recognized(self) -> None:
        with self._repo() as td:
            repo = Path(td)
            self._init_git_repo(repo)
            root = repo / "build/rescue/live-build/setuphelfer-rescue-live"
            (root / "auto").mkdir(parents=True, exist_ok=True)
            (root / "config/package-lists").mkdir(parents=True, exist_ok=True)
            (root / "config/includes.chroot/opt/setuphelfer-rescue").mkdir(parents=True, exist_ok=True)
            (root / "config/archives").mkdir(parents=True, exist_ok=True)
            (root / "auto/config").write_text("#!/bin/sh\nlb config noauto\n", encoding="utf-8")
            (root / "auto/build").write_text(
                "#!/bin/sh\necho \"Use controlled gate before running lb build.\"\nexit 20\n",
                encoding="utf-8",
            )
            (root / "config/package-lists/setuphelfer.list.chroot").write_text("systemd\n", encoding="utf-8")
            (root / "config/includes.chroot/opt/setuphelfer-rescue/MANIFEST.json").write_text("{}", encoding="utf-8")
            (root / "config/archives/debian-security.list.chroot").write_text("deb x\n", encoding="utf-8")
            (root / "config/archives/debian-security.list.binary").write_text("deb x\n", encoding="utf-8")
            tree = state.build_rescue_iso_dashboard_state(repo_root=repo)["build_tree"]
            self.assertTrue(tree["auto_build_blocked"])
            self.assertEqual(tree["validator_status"], "ok")

    def test_iso_missing_is_not_green(self) -> None:
        with self._repo() as td:
            repo = Path(td)
            self._init_git_repo(repo)
            payload = state.build_rescue_iso_dashboard_state(repo_root=repo)
            self.assertFalse(payload["iso_build"]["iso_found"])
            self.assertNotEqual(payload["status"], "green")

    def test_usb_write_stays_false(self) -> None:
        payload = state.build_rescue_iso_dashboard_state()
        self.assertFalse(payload["usb_write"]["allowed"])
        self.assertFalse(payload["forbidden_actions"]["usb_write_allowed"])

    def test_target_architecture_matrix_contains_candidates_without_final_green(self) -> None:
        matrix = state.build_rescue_target_architecture_matrix()
        targets = {
            item["target"]: item["status"]
            for item in [*(matrix.get("candidate_targets") or []), *(matrix.get("deferred_targets") or [])]
        }
        self.assertEqual(targets.get("amd64"), "primary_candidate")
        self.assertEqual(targets.get("i386"), "review_required")
        self.assertEqual(targets.get("arm64"), "deferred")
        self.assertEqual(targets.get("armhf"), "deferred")
        self.assertEqual(matrix.get("supported_targets"), [])

    def test_preflight_ready_stays_yellow_until_iso_exists(self) -> None:
        with self._repo() as td:
            repo = Path(td)
            self._init_git_repo(repo)
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
                "workspace_head": "653d41a",
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
                    return_value={"validator_status": "ok", "auto_config_noauto": True, "auto_build_blocked": True, "source_head": "653d41a"},
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

        self.assertEqual(payload["preflight_readiness"], "ready_for_build_preflight")
        self.assertEqual(payload["status"], "yellow")
        self.assertFalse(payload["usb_write"]["allowed"])
        self.assertFalse(payload["real_iso_build"]["allowed"])

    def test_secret_redaction(self) -> None:
        raw = (
            "API"
            + "_KEY="
            + "supersecret "
            + "TO"
            + "KEN="
            + "abc123 "
            + "PASS"
            + "WORD="
            + "hunter2"
        )
        redacted = state.redact_rescue_log_text(raw)
        self.assertNotIn("supersecret", redacted)
        self.assertIn("[REDACTED]", redacted)

    def test_last_log_lines_are_bounded(self) -> None:
        with self._repo() as td:
            repo = Path(td)
            self._init_git_repo(repo)
            latest = repo / "build/rescue/logs/controlled-iso-build/latest.log"
            latest.parent.mkdir(parents=True, exist_ok=True)
            latest.write_text("\n".join(f"line {idx}" for idx in range(250)), encoding="utf-8")
            logs = state.read_rescue_iso_latest_logs(repo_root=repo)
            self.assertLessEqual(len(logs["last_80_lines"]), 80)

    def test_status_separates_runtime_and_workspace_paths(self) -> None:
        with self._repo() as td:
            repo = Path(td)
            self._init_git_repo(repo)
            build_tree = repo / "build/rescue/live-build/setuphelfer-rescue-live"
            bundle = repo / "build/rescue/temp-runtime/setuphelfer-rescue-runtime"
            paths = {
                "runtime_path": "/opt/setuphelfer",
                "workspace_path": str(repo),
                "build_tree_path": str(build_tree),
                "temp_runtime_bundle_path": str(bundle),
                "logs_path": str(repo / "build/rescue/logs/controlled-iso-build"),
                "summary_path": str(repo / "docs/evidence/runtime-results/rescue/controlled_iso_build_latest_summary.json"),
                "path_mode": "workspace_build_runtime_opt",
                "path_status": "ok",
                "errors": [],
                "warnings": [],
                "workspace_head": "653d41a",
                "workspace_branch": "main",
            }
            with patch.object(state, "resolve_rescue_iso_paths", return_value=paths):
                payload = state.build_rescue_iso_dashboard_state(repo_root=Path("/opt/setuphelfer"))
            self.assertEqual(payload["runtime_path"], "/opt/setuphelfer")
            self.assertEqual(payload["workspace_path"], str(repo))
            self.assertEqual(payload["build_tree_path"], str(build_tree))
            self.assertEqual(payload["temp_runtime_bundle_path"], str(bundle))
            self.assertEqual(payload["path_mode"], "workspace_build_runtime_opt")
            self.assertEqual(payload["path_status"], "ok")
            self.assertNotIn("/opt/setuphelfer/build", payload["build_tree_path"])

    def test_opt_runtime_build_workspace_is_not_accepted(self) -> None:
        payload_paths = {
            "runtime_path": "/opt/setuphelfer",
            "workspace_path": "/opt/setuphelfer",
            "build_tree_path": "/opt/setuphelfer/build/rescue/live-build/setuphelfer-rescue-live",
            "temp_runtime_bundle_path": "/opt/setuphelfer/build/rescue/temp-runtime/setuphelfer-rescue-runtime",
            "logs_path": "/opt/setuphelfer/build/rescue/logs/controlled-iso-build",
            "summary_path": "/opt/setuphelfer/docs/evidence/runtime-results/rescue/controlled_iso_build_latest_summary.json",
            "path_mode": "workspace_build_runtime_opt",
            "path_status": "blocked",
            "errors": ["WORKSPACE_NOT_ALLOWLISTED"],
            "warnings": ["WORKSPACE_PATH_POINTS_TO_RUNTIME_OPT"],
            "workspace_head": None,
            "workspace_branch": None,
        }
        with patch.object(state, "resolve_rescue_iso_paths", return_value=payload_paths):
            payload = state.build_rescue_iso_dashboard_state(repo_root=Path("/opt/setuphelfer"))
        self.assertEqual(payload["path_status"], "blocked")
        self.assertEqual(payload["next_operator_action"]["type"], "fix_required")

    def test_missing_workspace_is_blocked_not_crash(self) -> None:
        repo = Path("/tmp/does-not-exist-for-rescue-test")
        paths = {
            "runtime_path": "/opt/setuphelfer",
            "workspace_path": str(repo),
            "build_tree_path": str(repo / "build/rescue/live-build/setuphelfer-rescue-live"),
            "temp_runtime_bundle_path": str(repo / "build/rescue/temp-runtime/setuphelfer-rescue-runtime"),
            "logs_path": str(repo / "build/rescue/logs/controlled-iso-build"),
            "summary_path": str(repo / "docs/evidence/runtime-results/rescue/controlled_iso_build_latest_summary.json"),
            "path_mode": "workspace_build_runtime_opt",
            "path_status": "blocked",
            "errors": ["WORKSPACE_MISSING"],
            "warnings": [],
            "workspace_head": None,
            "workspace_branch": None,
        }
        with patch.object(state, "resolve_rescue_iso_paths", return_value=paths):
            payload = state.build_rescue_iso_dashboard_state(repo_root=Path("/opt/setuphelfer"))
        self.assertEqual(payload["path_status"], "blocked")
        self.assertEqual(payload["next_operator_action"]["type"], "fix_required")

    def test_source_head_comes_from_workspace_head(self) -> None:
        with self._repo() as td:
            repo = Path(td)
            self._init_git_repo(repo)
            root = repo / "build/rescue/live-build/setuphelfer-rescue-live/evidence"
            root.mkdir(parents=True, exist_ok=True)
            (root / "build-tree-manifest.json").write_text('{"source_head":"653d41a"}', encoding="utf-8")
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
                "workspace_head": "653d41a",
                "workspace_branch": "main",
            }
            with patch.object(state, "resolve_rescue_iso_paths", return_value=paths):
                payload = state.build_rescue_iso_dashboard_state(repo_root=Path("/opt/setuphelfer"))
            self.assertEqual(payload["repo"]["head"], "653d41a")
            self.assertEqual(payload["build_tree"]["source_head"], "653d41a")

    def test_git_value_uses_safe_directory_for_workspace_repo(self) -> None:
        repo = Path("/home/volker/piinstaller")

        def fake_run(cmd: list[str], **_: object) -> SimpleNamespace:
            self.assertIn("-c", cmd)
            self.assertIn(f"safe.directory={repo}", cmd)
            return SimpleNamespace(returncode=0, stdout="751e2cf\n")

        with patch.object(state.subprocess, "run", side_effect=fake_run):
            value = state._git_value(repo, "rev-parse", "--short", "HEAD")
        self.assertEqual(value, "751e2cf")

    def test_next_operator_action_requires_dpkg_preflight_before_build(self) -> None:
        payload = state.build_next_operator_action(
            {
                "runtime_path": "/opt/setuphelfer",
                "path_status": "ok",
                "path_errors": [],
                "repo": {"runtime_gate": "green"},
                "tools": {
                    "lb": {"present": True},
                    "xorriso": {"present": True},
                    "mksquashfs": {"present": True},
                },
                "stale_state": {"needs_sudo_clean": False, "present": False},
                "build_tree": {"validator_status": "ok"},
                "temp_runtime_bundle": {"status": "ok"},
                "dpkg_preflight": {"status": "unknown", "summary": "dpkg preflight not run yet"},
                "iso_build": {"status": "review_required"},
            }
        )
        self.assertEqual(payload["type"], "fix_required")

    def test_next_operator_action_allows_operator_build_only_after_dpkg_preflight_ok(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            self._init_git_repo(repo)
            payload = state.build_next_operator_action(
                {
                    "runtime_path": str(repo),
                    "path_status": "ok",
                    "path_errors": [],
                    "repo": {"runtime_gate": "green"},
                    "tools": {
                        "lb": {"present": True},
                        "xorriso": {"present": True},
                        "mksquashfs": {"present": True},
                    },
                    "stale_state": {"needs_sudo_clean": False, "present": False},
                    "build_tree": {"validator_status": "ok"},
                    "temp_runtime_bundle": {"status": "ok"},
                    "dpkg_preflight": {"status": "ok", "summary": "DPKG preflight ok"},
                    "iso_build": {"status": "review_required"},
                }
            )
        self.assertEqual(payload["type"], "operator_sudo_required")


class RescueIsoDashboardRouteRegistrationTests(unittest.TestCase):
    def test_routes_are_registered_in_app(self) -> None:
        app_py = _backend / "app.py"
        text = app_py.read_text(encoding="utf-8")
        self.assertIn("/api/dev-dashboard/rescue-iso/status", text)
        self.assertIn("/api/dev-dashboard/rescue-iso/step", text)
        self.assertIn("/api/dev-dashboard/rescue-iso/operator-commands/sudo-clean", text)


if __name__ == "__main__":
    unittest.main()
