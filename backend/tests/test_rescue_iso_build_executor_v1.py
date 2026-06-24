"""Tests fuer den kontrollierten Rescue-ISO-Executor."""

from __future__ import annotations

import shutil
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

from core import rescue_iso_build_executor as executor  # noqa: E402
from core import rescue_iso_build_state as build_state  # noqa: E402
from core import rescue_iso_operator_commands as operator_commands  # noqa: E402
from core.rescue_iso_operator_commands import build_sudo_clean_commands  # noqa: E402


class RescueIsoBuildExecutorTests(unittest.TestCase):
    def _make_repo(self, td: str) -> Path:
        repo = Path(td)
        (repo / "scripts/rescue-live").mkdir(parents=True, exist_ok=True)
        (repo / "build/rescue/live-build/setuphelfer-rescue-live").mkdir(parents=True, exist_ok=True)
        subprocess.run(["git", "-C", str(repo), "init", "-q"], check=True)
        return repo

    def _runtime_root(self) -> Path:
        return Path("/opt/setuphelfer")

    def _paths(self, repo: Path, *, status: str = "ok", errors: list[str] | None = None, warnings: list[str] | None = None) -> dict[str, object]:
        return {
            "runtime_path": str(self._runtime_root()),
            "workspace_path": str(repo),
            "build_tree_path": str(repo / "build/rescue/live-build/setuphelfer-rescue-live"),
            "temp_runtime_bundle_path": str(repo / "build/rescue/temp-runtime/setuphelfer-rescue-runtime"),
            "logs_path": str(repo / "build/rescue/logs/controlled-iso-build"),
            "summary_path": str(repo / "docs/evidence/runtime-results/rescue/controlled_iso_build_latest_summary.json"),
            "path_mode": "workspace_build_runtime_opt",
            "path_status": status,
            "errors": errors or [],
            "warnings": warnings or [],
            "workspace_head": "653d41a",
            "workspace_branch": "main",
        }

    def _script(self, repo: Path, rel: str, body: str) -> None:
        path = repo / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")
        path.chmod(0o755)

    def _write_dpkg_preflight_json(self, repo: Path, *, status: str, exit_code: int, summary: str) -> None:
        path = repo / "docs/evidence/runtime-results/rescue/live_build_dpkg_preflight_latest.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            (
                "{\n"
                f'  "status": "{status}",\n'
                f'  "exit_code": {exit_code},\n'
                f'  "summary": "{summary}",\n'
                '  "chroot_status": "missing",\n'
                '  "issues": []\n'
                "}\n"
            ),
            encoding="utf-8",
        )

    def test_toolcheck_is_read_only(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = self._make_repo(td)
            sentinel = repo / "outside.txt"
            sentinel.write_text("keep", encoding="utf-8")
            with patch.object(executor, "_repo_root", return_value=self._runtime_root()):
                with patch.object(executor, "resolve_rescue_iso_paths", return_value=self._paths(repo)):
                    with patch.object(executor.shutil, "which", return_value="/usr/bin/tool"):
                        result = executor.run_rescue_iso_step("toolcheck")
            self.assertEqual(result["status"], "ok")
            self.assertEqual(sentinel.read_text(encoding="utf-8"), "keep")

    def test_forbidden_usb_write_step_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = self._make_repo(td)
            with patch.object(executor, "_repo_root", return_value=self._runtime_root()):
                with patch.object(executor, "resolve_rescue_iso_paths", return_value=self._paths(repo)):
                    result = executor.run_rescue_iso_step("usb_write")
            self.assertEqual(result["status"], "forbidden")
            self.assertEqual(result["exit_code"], 13)

    def test_forbidden_dd_step_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = self._make_repo(td)
            with patch.object(executor, "_repo_root", return_value=self._runtime_root()):
                with patch.object(executor, "resolve_rescue_iso_paths", return_value=self._paths(repo)):
                    result = executor.run_rescue_iso_step("dd")
            self.assertEqual(result["status"], "forbidden")
            self.assertEqual(result["exit_code"], 13)

    def test_clean_user_state_does_not_touch_outside_tree(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = self._make_repo(td)
            build_root = repo / "build/rescue/live-build/setuphelfer-rescue-live"
            outside = repo / "outside-keep.txt"
            outside.write_text("keep", encoding="utf-8")
            (build_root / ".build").mkdir(parents=True, exist_ok=True)
            (build_root / ".build/temp.txt").write_text("remove", encoding="utf-8")
            with patch.object(executor, "_repo_root", return_value=self._runtime_root()):
                with patch.object(executor, "resolve_rescue_iso_paths", return_value=self._paths(repo)):
                    result = executor.run_rescue_iso_step("clean_user_state")
            self.assertEqual(result["status"], "ok")
            self.assertTrue(outside.exists())
            self.assertFalse((build_root / ".build").exists())

    def test_root_owned_state_is_not_deleted_as_user_state(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = self._make_repo(td)
            build_root = repo / "build/rescue/live-build/setuphelfer-rescue-live"
            target = build_root / ".build"
            target.mkdir(parents=True, exist_ok=True)
            (target / "root-owned").write_text("x", encoding="utf-8")
            with patch.object(executor, "_repo_root", return_value=self._runtime_root()):
                with patch.object(executor, "resolve_rescue_iso_paths", return_value=self._paths(repo)):
                    with patch.object(executor, "_root_owned_under", return_value=[target / "root-owned"]):
                        result = executor.run_rescue_iso_step("clean_user_state")
            self.assertEqual(result["status"], "operator_required")
            self.assertTrue((target / "root-owned").exists())
            commands = result["details"]["commands"]
            self.assertTrue(commands)
            self.assertNotIn("lb clean", "\n".join(commands))

    def test_prepare_bundle_runs_only_allowed_script(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = self._make_repo(td)
            marker = repo / "bundle.marker"
            self._script(
                repo,
                "scripts/rescue-live/create-temp-runtime-bundle.sh",
                f"#!/bin/sh\necho bundle\nprintf ok > \"{marker}\"\n",
            )
            with patch.object(executor, "_repo_root", return_value=self._runtime_root()):
                with patch.object(executor, "resolve_rescue_iso_paths", return_value=self._paths(repo)):
                    result = executor.run_rescue_iso_step("prepare_bundle")
            self.assertEqual(result["status"], "ok")
            self.assertTrue(marker.exists())
            self.assertEqual(result["details"]["cwd"], str(repo))
            self.assertEqual(result["details"]["command"][0], "scripts/rescue-live/create-temp-runtime-bundle.sh")

    def test_validate_tree_runs_only_allowed_script(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = self._make_repo(td)
            marker = repo / "validate-tree.marker"
            self._script(
                repo,
                "scripts/rescue-live/validate-controlled-live-build-tree.sh",
                f"#!/bin/sh\necho validate-tree \"$1\"\nprintf ok > \"{marker}\"\n",
            )
            with patch.object(executor, "_repo_root", return_value=self._runtime_root()):
                with patch.object(executor, "resolve_rescue_iso_paths", return_value=self._paths(repo)):
                    result = executor.run_rescue_iso_step("validate_tree")
            self.assertEqual(result["status"], "ok")
            self.assertTrue(marker.exists())
            self.assertEqual(result["details"]["cwd"], str(repo))
            self.assertEqual(result["details"]["command"][1], "build/rescue/live-build/setuphelfer-rescue-live")

    def test_dpkg_preflight_step_exists_and_is_read_only(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = self._make_repo(td)
            marker = repo / "dpkg-preflight.marker"
            self._script(
                repo,
                "scripts/rescue-live/validate-live-build-dpkg-preflight.sh",
                (
                    "#!/bin/sh\n"
                    "mkdir -p docs/evidence/runtime-results/rescue\n"
                    "cat > docs/evidence/runtime-results/rescue/live_build_dpkg_preflight_latest.json <<'EOF'\n"
                    '{\n'
                    '  "status": "pre_chroot_ok",\n'
                    '  "exit_code": 0,\n'
                    '  "summary": "Preflight ok vor chroot-Erzeugung",\n'
                    '  "chroot_status": "missing",\n'
                    '  "issues": []\n'
                    '}\n'
                    "EOF\n"
                    f"printf ok > \"{marker}\"\n"
                ),
            )
            with patch.object(executor, "_repo_root", return_value=self._runtime_root()):
                with patch.object(executor, "resolve_rescue_iso_paths", return_value=self._paths(repo)):
                    result = executor.run_rescue_iso_step("dpkg_preflight")
            self.assertEqual(result["status"], "ok")
            self.assertTrue(marker.exists())
            self.assertEqual(result["details"]["cwd"], str(repo))
            self.assertEqual(result["details"]["command"][0], "scripts/rescue-live/validate-live-build-dpkg-preflight.sh")
            self.assertIn("result", result["details"])

    def test_dpkg_preflight_does_not_execute_lb_build_or_apt(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = self._make_repo(td)
            commands: list[list[str]] = []

            def fake_run_command(
                repo_root: Path,
                action: dict[str, object],
                command: list[str],
                *,
                cwd: Path,
                extra_env: dict[str, str] | None = None,
            ) -> tuple[int, list[str]]:
                del repo_root, action, cwd, extra_env
                commands.append(command)
                self._write_dpkg_preflight_json(repo, status="pre_chroot_ok", exit_code=0, summary="Preflight ok vor chroot-Erzeugung")
                return 0, ["ok"]

            with patch.object(executor, "_repo_root", return_value=self._runtime_root()):
                with patch.object(executor, "resolve_rescue_iso_paths", return_value=self._paths(repo)):
                    with patch.object(executor, "_run_command", side_effect=fake_run_command):
                        result = executor.run_rescue_iso_step("dpkg_preflight")
            self.assertEqual(result["status"], "ok")
            self.assertEqual(commands, [["scripts/rescue-live/validate-live-build-dpkg-preflight.sh"]])
            joined = "\n".join(" ".join(cmd) for cmd in commands)
            self.assertNotIn("lb build", joined)
            self.assertNotIn("apt", joined)

    def test_dpkg_preflight_blocks_when_start_stop_daemon_missing(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = self._make_repo(td)

            def fake_run_command(
                repo_root: Path,
                action: dict[str, object],
                command: list[str],
                *,
                cwd: Path,
                extra_env: dict[str, str] | None = None,
            ) -> tuple[int, list[str]]:
                del repo_root, action, command, cwd, extra_env
                self._write_dpkg_preflight_json(
                    repo,
                    status="chroot_start_stop_daemon_missing",
                    exit_code=16,
                    summary="start-stop-daemon im chroot fehlt",
                )
                return 16, ["missing start-stop-daemon"]

            with patch.object(executor, "_repo_root", return_value=self._runtime_root()):
                with patch.object(executor, "resolve_rescue_iso_paths", return_value=self._paths(repo)):
                    with patch.object(executor, "_run_command", side_effect=fake_run_command):
                        result = executor.run_rescue_iso_step("dpkg_preflight")
            self.assertEqual(result["status"], "blocked")
            self.assertEqual(result["exit_code"], 16)

    def test_dpkg_preflight_ok_when_chroot_missing_and_tree_ready(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = self._make_repo(td)

            def fake_run_command(
                repo_root: Path,
                action: dict[str, object],
                command: list[str],
                *,
                cwd: Path,
                extra_env: dict[str, str] | None = None,
            ) -> tuple[int, list[str]]:
                del repo_root, action, command, cwd, extra_env
                self._write_dpkg_preflight_json(repo, status="pre_chroot_ok", exit_code=0, summary="Preflight ok vor chroot-Erzeugung")
                return 0, ["pre_chroot_ok"]

            with patch.object(executor, "_repo_root", return_value=self._runtime_root()):
                with patch.object(executor, "resolve_rescue_iso_paths", return_value=self._paths(repo)):
                    with patch.object(executor, "_run_command", side_effect=fake_run_command):
                        result = executor.run_rescue_iso_step("dpkg_preflight")
            self.assertEqual(result["status"], "ok")
            self.assertEqual(result["exit_code"], 0)

    def test_dpkg_preflight_summary_json_is_written(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = self._make_repo(td)

            def fake_run_command(
                repo_root: Path,
                action: dict[str, object],
                command: list[str],
                *,
                cwd: Path,
                extra_env: dict[str, str] | None = None,
            ) -> tuple[int, list[str]]:
                del repo_root, action, command, cwd, extra_env
                self._write_dpkg_preflight_json(repo, status="pre_chroot_ok", exit_code=0, summary="Preflight ok vor chroot-Erzeugung")
                return 0, ["pre_chroot_ok"]

            with patch.object(executor, "_repo_root", return_value=self._runtime_root()):
                with patch.object(executor, "resolve_rescue_iso_paths", return_value=self._paths(repo)):
                    with patch.object(executor, "_run_command", side_effect=fake_run_command):
                        executor.run_rescue_iso_step("dpkg_preflight")
            summary = repo / "docs/evidence/runtime-results/rescue/live_build_dpkg_preflight_latest.json"
            self.assertTrue(summary.is_file())

    def test_build_iso_operator_required_does_not_execute_build(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = self._make_repo(td)
            with patch.object(executor, "_repo_root", return_value=self._runtime_root()):
                with patch.object(executor, "resolve_rescue_iso_paths", return_value=self._paths(repo)):
                    with patch.object(operator_commands, "resolve_rescue_iso_paths", return_value=self._paths(repo)):
                        result = executor.run_rescue_iso_step("build_iso_operator_required")
            self.assertEqual(result["status"], "operator_required")
            commands = result["details"]["commands"]
            self.assertIn("sudo lb build noauto", commands[-1])
            self.assertIn(str(repo / "build/rescue/live-build/setuphelfer-rescue-live"), commands[0])
            self.assertNotIn("/opt/setuphelfer/build", commands[0])

    def test_build_iso_with_sudo_without_confirm_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = self._make_repo(td)
            with patch.object(executor, "_repo_root", return_value=self._runtime_root()):
                with patch.object(executor, "resolve_rescue_iso_paths", return_value=self._paths(repo)):
                    result = executor.run_rescue_iso_step("build_iso_with_sudo", operator_confirm=False)
            self.assertEqual(result["status"], "blocked")
            self.assertEqual(result["exit_code"], 40)

    def test_scan_iso_generates_sha256_only_when_iso_exists(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = self._make_repo(td)
            iso = repo / "build/rescue/live-build/setuphelfer-rescue-live/live-image-amd64.hybrid.iso"
            iso.write_bytes(b"iso")
            with patch.object(executor, "_repo_root", return_value=self._runtime_root()):
                with patch.object(executor, "resolve_rescue_iso_paths", return_value=self._paths(repo)):
                    with patch.object(build_state, "resolve_rescue_iso_paths", return_value=self._paths(repo)):
                        result = executor.run_rescue_iso_step("scan_iso")
            self.assertEqual(result["status"], "ok")
            artifacts = result["details"]["artifacts"]
            self.assertTrue(artifacts["iso_found"])
            self.assertTrue(artifacts["iso_sha256"])

    def test_summary_json_is_written(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = self._make_repo(td)
            with patch.object(executor, "_repo_root", return_value=self._runtime_root()):
                with patch.object(executor, "resolve_rescue_iso_paths", return_value=self._paths(repo)):
                    executor.run_rescue_iso_step("summarize")
            summary = repo / "docs/evidence/runtime-results/rescue/controlled_iso_build_latest_summary.json"
            self.assertTrue(summary.is_file())

    def test_sudo_clean_commands_avoid_recursive_lb_clean(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = self._make_repo(td)
            payload = build_sudo_clean_commands(repo_root=repo)
            joined = "\n".join(payload["commands"])
            self.assertNotIn("lb clean", joined)
            self.assertIn("sudo rm -rf .build chroot cache binary local", joined)
            self.assertIn("config/includes.chroot/opt/setuphelfer-rescue", joined)

    def test_validate_bundle_uses_workspace_manifest_path(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = self._make_repo(td)
            marker = repo / "validate-bundle.marker"
            self._script(
                repo,
                "scripts/rescue-live/validate-temp-runtime-bundle.sh",
                f"#!/bin/sh\nprintf '%s' \"$1\" > \"{marker}\"\n",
            )
            with patch.object(executor, "_repo_root", return_value=self._runtime_root()):
                with patch.object(executor, "resolve_rescue_iso_paths", return_value=self._paths(repo)):
                    result = executor.run_rescue_iso_step("validate_bundle")
            self.assertEqual(result["status"], "ok")
            self.assertEqual(marker.read_text(encoding="utf-8"), "build/rescue/temp-runtime/setuphelfer-rescue-runtime")
            self.assertEqual(result["details"]["cwd"], str(repo))

    def test_opt_runtime_build_workspace_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = self._make_repo(td)
            blocked_paths = self._paths(
                Path("/opt/setuphelfer"),
                status="blocked",
                errors=["WORKSPACE_NOT_ALLOWLISTED"],
                warnings=["WORKSPACE_PATH_POINTS_TO_RUNTIME_OPT"],
            )
            with patch.object(executor, "_repo_root", return_value=repo):
                with patch.object(executor, "resolve_rescue_iso_paths", return_value=blocked_paths):
                    result = executor.run_rescue_iso_step("prepare_bundle")
            self.assertEqual(result["status"], "blocked")
            self.assertIn("WORKSPACE_NOT_ALLOWLISTED", result["errors"])

    def test_path_traversal_symlink_escape_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            with tempfile.TemporaryDirectory() as outside_td:
                repo = self._make_repo(td)
                outside = Path(outside_td)
                live_build = repo / "build/rescue/live-build"
                shutil.rmtree(live_build)
                live_build.parent.mkdir(parents=True, exist_ok=True)
                live_build.symlink_to(outside, target_is_directory=True)
                payload = build_sudo_clean_commands(repo_root=repo)
                self.assertEqual(payload["status"], "blocked")
                self.assertIn("BUILD_TREE_PARENT_OUTSIDE_WORKSPACE", payload["errors"])

    def test_source_contains_no_forbidden_runtime_commands(self) -> None:
        src = (_backend / "core/rescue_iso_build_executor.py").read_text(encoding="utf-8")
        self.assertNotIn("apt install", src)
        self.assertNotIn("apt upgrade", src)
        self.assertNotIn("mount ", src)
        self.assertNotIn("restore --execute", src)
        self.assertNotIn("dd if=", src)

    def test_missing_workspace_is_blocked_not_crash(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = self._make_repo(td)
            missing = Path("/tmp/definitely-missing-rescue-workspace")
            paths = {
                "runtime_path": str(self._runtime_root()),
                "workspace_path": str(missing),
                "build_tree_path": str(missing / "build/rescue/live-build/setuphelfer-rescue-live"),
                "temp_runtime_bundle_path": str(missing / "build/rescue/temp-runtime/setuphelfer-rescue-runtime"),
                "logs_path": str(missing / "build/rescue/logs/controlled-iso-build"),
                "summary_path": str(missing / "docs/evidence/runtime-results/rescue/controlled_iso_build_latest_summary.json"),
                "path_mode": "workspace_build_runtime_opt",
                "path_status": "blocked",
                "errors": ["WORKSPACE_MISSING"],
                "warnings": [],
                "workspace_head": None,
                "workspace_branch": None,
            }
            with patch.object(executor, "_repo_root", return_value=repo):
                with patch.object(executor, "resolve_rescue_iso_paths", return_value=paths):
                    result = executor.run_rescue_iso_step("prepare_tree")
            self.assertEqual(result["status"], "blocked")
            self.assertIn("WORKSPACE_MISSING", result["errors"])

    def test_path_resolution_uses_safe_directory_for_git_workspace(self) -> None:
        repo = Path(__file__).resolve().parents[2]

        def fake_run(cmd: list[str], **_: object) -> SimpleNamespace:
            self.assertIn("-c", cmd)
            self.assertIn(f"safe.directory={repo}", cmd)
            if "--show-toplevel" in cmd:
                return SimpleNamespace(returncode=0, stdout=f"{repo}\n")
            if "--short" in cmd:
                return SimpleNamespace(returncode=0, stdout="751e2cf\n")
            return SimpleNamespace(returncode=0, stdout="main\n")

        with patch.object(operator_commands, "_configured_workspace_root", return_value=repo):
            with patch.object(operator_commands, "_allowed_workspace_roots", return_value=(repo,)):
                with patch.object(operator_commands.subprocess, "run", side_effect=fake_run):
                    payload = operator_commands.resolve_rescue_iso_paths(repo_root=Path("/opt/setuphelfer"))
        self.assertEqual(payload["path_status"], "ok")
        self.assertEqual(payload["workspace_head"], "751e2cf")


if __name__ == "__main__":
    unittest.main()
