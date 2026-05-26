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

from core import rescue_iso_build_executor as executor  # noqa: E402
from core import rescue_iso_build_state as state  # noqa: E402
from core import rescue_iso_operator_commands as operator_commands  # noqa: E402


class RescueIsoRsvgPreflightTests(unittest.TestCase):
    def _make_repo(self, td: str) -> Path:
        repo = Path(td)
        subprocess.run(["git", "-C", str(repo), "init", "-q"], check=True)
        return repo

    def _paths(self, repo: Path) -> dict[str, object]:
        return {
            "runtime_path": str(Path("/opt/setuphelfer")),
            "workspace_path": str(repo),
            "build_tree_path": str(repo / "build/rescue/live-build/setuphelfer-rescue-live"),
            "temp_runtime_bundle_path": str(repo / "build/rescue/temp-runtime/setuphelfer-rescue-runtime"),
            "logs_path": str(repo / "build/rescue/logs/controlled-iso-build"),
            "summary_path": str(repo / "docs/evidence/runtime-results/rescue/controlled_iso_build_latest_summary.json"),
            "path_mode": "workspace_build_runtime_opt",
            "path_status": "ok",
            "errors": [],
            "warnings": [],
            "workspace_head": "3adfc13",
            "workspace_branch": "main",
        }

    def _write_live_build_script(self, repo: Path, *, uses_legacy_rsvg: bool) -> Path:
        script = repo / "lb_binary_syslinux"
        script.write_text(
            (
                "#!/bin/sh\n"
                "if [ ! -e /usr/bin/rsvg ]; then\n"
                "  Echo_error '/usr/bin/rsvg - no such file'\n"
                "  exit 1\n"
                "fi\n"
                "rsvg --format png --height 480 --width 640 splash.svg splash.png\n"
            )
            if uses_legacy_rsvg
            else "#!/bin/sh\nexit 0\n",
            encoding="utf-8",
        )
        return script

    def test_missing_rsvg_and_rsvg_convert_blocks_with_build_tools_missing(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = self._make_repo(td)
            splash = repo / "build/rescue/live-build/setuphelfer-rescue-live/config/bootloaders/isolinux/splash.svg.in"
            splash.parent.mkdir(parents=True, exist_ok=True)
            splash.write_text("<svg/>", encoding="utf-8")
            script = self._write_live_build_script(repo, uses_legacy_rsvg=True)

            def _which(name: str) -> str | None:
                if name in {"rsvg", "rsvg-convert"}:
                    return None
                return "/usr/bin/" + name

            with (
                patch.object(operator_commands.shutil, "which", side_effect=_which),
                patch.object(operator_commands, "_LIVE_BUILD_SYSLINUX", script),
                patch.object(operator_commands, "_package_installed", return_value=False),
            ):
                payload = operator_commands.inspect_rsvg_build_dependency(repo_root=repo)

        self.assertTrue(payload["required"])
        self.assertEqual(payload["status"], "blocked")
        self.assertEqual(payload["error_code"], "blocked_build_tools_missing")
        self.assertEqual(payload["hint_package"], "librsvg2-bin")
        self.assertEqual(payload["install_command"], "sudo apt install librsvg2-bin")

    def test_rsvg_convert_is_ready_when_live_build_does_not_need_legacy_rsvg(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = self._make_repo(td)
            splash = repo / "build/rescue/live-build/setuphelfer-rescue-live/config/bootloaders/isolinux/splash.svg.in"
            splash.parent.mkdir(parents=True, exist_ok=True)
            splash.write_text("<svg/>", encoding="utf-8")
            script = self._write_live_build_script(repo, uses_legacy_rsvg=False)

            def _which(name: str) -> str | None:
                if name == "rsvg-convert":
                    return "/usr/bin/rsvg-convert"
                if name == "rsvg":
                    return None
                return "/usr/bin/" + name

            with (
                patch.object(operator_commands.shutil, "which", side_effect=_which),
                patch.object(operator_commands, "_LIVE_BUILD_SYSLINUX", script),
            ):
                payload = operator_commands.inspect_rsvg_build_dependency(repo_root=repo)

        self.assertFalse(payload["required"])
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["compat_path"], "/usr/bin/rsvg-convert")

    def test_rsvg_convert_only_becomes_legacy_review_required_when_live_build_needs_rsvg(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = self._make_repo(td)
            splash = repo / "build/rescue/live-build/setuphelfer-rescue-live/config/bootloaders/isolinux/splash.svg.in"
            splash.parent.mkdir(parents=True, exist_ok=True)
            splash.write_text("<svg/>", encoding="utf-8")
            script = self._write_live_build_script(repo, uses_legacy_rsvg=True)

            def _which(name: str) -> str | None:
                if name == "rsvg-convert":
                    return "/usr/bin/rsvg-convert"
                if name == "rsvg":
                    return None
                return "/usr/bin/" + name

            with (
                patch.object(operator_commands.shutil, "which", side_effect=_which),
                patch.object(operator_commands, "_LIVE_BUILD_SYSLINUX", script),
            ):
                payload = operator_commands.inspect_rsvg_build_dependency(repo_root=repo)

        self.assertTrue(payload["required"])
        self.assertEqual(payload["status"], "review_required")
        self.assertEqual(payload["error_code"], "blocked_legacy_rsvg_command_missing")
        self.assertEqual(payload["compat_path"], "/usr/bin/rsvg-convert")
        self.assertFalse(payload["commands"])

    def test_project_local_wrapper_makes_legacy_rsvg_requirement_ready(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = self._make_repo(td)
            splash = repo / "build/rescue/live-build/setuphelfer-rescue-live/config/bootloaders/isolinux/splash.svg.in"
            splash.parent.mkdir(parents=True, exist_ok=True)
            splash.write_text("<svg/>", encoding="utf-8")
            script = self._write_live_build_script(repo, uses_legacy_rsvg=True)
            wrapper = repo / "build/rescue/tool-compat/bin/rsvg"
            wrapper.parent.mkdir(parents=True, exist_ok=True)
            wrapper.write_text("#!/bin/sh\nexec rsvg-convert \"$@\"\n", encoding="utf-8")

            def _which(name: str) -> str | None:
                if name == "rsvg-convert":
                    return "/usr/bin/rsvg-convert"
                if name == "rsvg":
                    return None
                return "/usr/bin/" + name

            with (
                patch.object(operator_commands.shutil, "which", side_effect=_which),
                patch.object(operator_commands, "_LIVE_BUILD_SYSLINUX", script),
            ):
                payload = operator_commands.inspect_rsvg_build_dependency(repo_root=repo)

        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["legacy_source"], "project_local_wrapper")
        self.assertEqual(payload["legacy_path"], str(wrapper.resolve(strict=False)))

    def test_system_rsvg_makes_preflight_ready(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = self._make_repo(td)
            splash = repo / "build/rescue/live-build/setuphelfer-rescue-live/config/bootloaders/isolinux/splash.svg.in"
            splash.parent.mkdir(parents=True, exist_ok=True)
            splash.write_text("<svg/>", encoding="utf-8")
            script = self._write_live_build_script(repo, uses_legacy_rsvg=True)

            def _which(name: str) -> str | None:
                if name == "rsvg":
                    return "/usr/bin/rsvg"
                if name == "rsvg-convert":
                    return "/usr/bin/rsvg-convert"
                return "/usr/bin/" + name

            with (
                patch.object(operator_commands.shutil, "which", side_effect=_which),
                patch.object(operator_commands, "_LIVE_BUILD_SYSLINUX", script),
            ):
                payload = operator_commands.inspect_rsvg_build_dependency(repo_root=repo)

        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["legacy_source"], "system")
        self.assertEqual(payload["legacy_path"], "/usr/bin/rsvg")

    def test_installed_package_without_rsvg_convert_in_path_is_review_required(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = self._make_repo(td)
            splash = repo / "build/rescue/live-build/setuphelfer-rescue-live/config/bootloaders/isolinux/splash.svg.in"
            splash.parent.mkdir(parents=True, exist_ok=True)
            splash.write_text("<svg/>", encoding="utf-8")
            script = self._write_live_build_script(repo, uses_legacy_rsvg=True)

            def _which(name: str) -> str | None:
                if name in {"rsvg", "rsvg-convert"}:
                    return None
                return "/usr/bin/" + name

            with (
                patch.object(operator_commands.shutil, "which", side_effect=_which),
                patch.object(operator_commands, "_LIVE_BUILD_SYSLINUX", script),
                patch.object(operator_commands, "_package_installed", return_value=True),
            ):
                payload = operator_commands.inspect_rsvg_build_dependency(repo_root=repo)

        self.assertEqual(payload["status"], "review_required")
        self.assertEqual(payload["error_code"], "review_required_rsvg_convert_not_in_path")

    def test_dashboard_state_uses_wrapper_preparation_action_for_legacy_missing(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = self._make_repo(td)
            paths = self._paths(repo)
            with (
                patch.object(state, "resolve_rescue_iso_paths", return_value=paths),
                patch.object(state, "_runtime_gate", return_value={"status": "green", "exit_code": 0, "summary": "ok"}),
                patch.object(state, "_tool_presence", return_value={"present": True, "path": "/usr/bin/tool"}),
                patch.object(
                    state,
                    "inspect_rsvg_build_dependency",
                    return_value={
                        "required": True,
                        "status": "review_required",
                        "summary": "live-build erwartet den Legacy-Befehl 'rsvg'; rsvg-convert ist vorhanden, aber kein Wrapper.",
                        "error_code": "blocked_legacy_rsvg_command_missing",
                        "legacy_path": None,
                        "compat_path": "/usr/bin/rsvg-convert",
                        "hint_package": "librsvg2-bin",
                        "install_command": "sudo apt install librsvg2-bin",
                        "commands": [],
                    },
                ),
                patch.object(state, "detect_live_build_stale_state", return_value={"present": False, "needs_sudo_clean": False}),
                patch.object(state, "_temp_runtime_bundle", return_value={"status": "ok"}),
                patch.object(
                    state,
                    "_build_tree",
                    return_value={"validator_status": "ok", "auto_config_noauto": True, "auto_build_blocked": True, "source_head": "3adfc13"},
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

        self.assertEqual(payload["status"], "red")
        self.assertEqual(payload["next_operator_action"]["type"], "prepare_project_local_rsvg_wrapper")
        self.assertFalse(payload["usb_write"]["allowed"])

    def test_prebuild_check_reports_legacy_rsvg_missing_without_usb_write(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = self._make_repo(td)
            state_payload = {
                "repo": {"runtime_gate": "green"},
                "stale_state": {"needs_sudo_clean": False, "present": False},
                "tools": {
                    "lb": {"present": True},
                    "xorriso": {"present": True},
                    "mksquashfs": {"present": True},
                    "rsvg": {"present": True},
                },
                "rsvg_preflight": {
                    "status": "review_required",
                    "error_code": "blocked_legacy_rsvg_command_missing",
                    "summary": "live-build erwartet den Legacy-Befehl 'rsvg'; rsvg-convert ist vorhanden, aber kein Wrapper.",
                    "commands": [],
                },
                "temp_runtime_bundle": {"status": "ok"},
                "build_tree": {"validator_status": "ok", "auto_config_noauto": True, "auto_build_blocked": True},
                "dpkg_preflight": {"status": "pre_chroot_ok"},
                "usb_write": {"allowed": False},
            }
            with (
                patch.object(executor, "_repo_root", return_value=Path("/opt/setuphelfer")),
                patch.object(executor, "resolve_rescue_iso_paths", return_value=self._paths(repo)),
                patch.object(executor, "build_rescue_iso_dashboard_state", return_value=state_payload),
            ):
                result = executor.run_rescue_iso_step("prebuild_check")

        self.assertEqual(result["status"], "review_required")
        self.assertEqual(result["exit_code"], 18)
        self.assertIn("blocked_legacy_rsvg_command_missing", result["errors"])
        self.assertFalse(state_payload["usb_write"]["allowed"])

    def test_operator_hint_names_librsvg2_bin_without_global_symlink(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = self._make_repo(td)
            splash = repo / "build/rescue/live-build/setuphelfer-rescue-live/config/bootloaders/isolinux/splash.svg.in"
            splash.parent.mkdir(parents=True, exist_ok=True)
            splash.write_text("<svg/>", encoding="utf-8")
            script = self._write_live_build_script(repo, uses_legacy_rsvg=True)

            def _which(name: str) -> str | None:
                if name in {"rsvg", "rsvg-convert"}:
                    return None
                return "/usr/bin/" + name

            with (
                patch.object(operator_commands.shutil, "which", side_effect=_which),
                patch.object(operator_commands, "_LIVE_BUILD_SYSLINUX", script),
                patch.object(operator_commands, "_package_installed", return_value=False),
            ):
                payload = operator_commands.build_operator_build_commands(repo_root=repo)

        joined = "\n".join(payload["commands"])
        self.assertEqual(payload["status"], "blocked")
        self.assertIn("librsvg2-bin", joined)
        self.assertNotIn("/usr/bin/rsvg", joined)
        self.assertNotIn("ln -s", joined)
        self.assertNotIn("dd", joined)
        self.assertNotIn("mkfs", joined)
        self.assertNotIn("parted", joined)


if __name__ == "__main__":
    unittest.main()
