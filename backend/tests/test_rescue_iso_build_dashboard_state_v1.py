"""Tests fuer den read-only Rescue-ISO-Dashboard-State."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from core import rescue_iso_build_state as state  # noqa: E402


class RescueIsoBuildDashboardStateTests(unittest.TestCase):
    def _repo(self) -> tempfile.TemporaryDirectory[str]:
        return tempfile.TemporaryDirectory()

    def test_missing_evidence_does_not_crash(self) -> None:
        with self._repo() as td:
            repo = Path(td)
            payload = state.build_rescue_iso_dashboard_state(repo_root=repo)
            self.assertIn(payload["status"], ("gray", "yellow", "red", "green"))
            self.assertFalse(payload["usb_write"]["allowed"])

    def test_tar_failed_is_detected_from_debootstrap_log(self) -> None:
        with self._repo() as td:
            repo = Path(td)
            log = repo / "build/rescue/live-build/setuphelfer-rescue-live/chroot/debootstrap/debootstrap.log"
            log.parent.mkdir(parents=True, exist_ok=True)
            log.write_text("E: Tried to extract package, but tar failed. Exit...\n", encoding="utf-8")
            stale = state.detect_live_build_stale_state(repo_root=repo)
            self.assertIn("debootstrap_tar_failed", stale["indicators"])

    def test_chroot_package_lists_install_stale_is_detected(self) -> None:
        with self._repo() as td:
            repo = Path(td)
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
            fake = repo / "build/rescue/live-build/setuphelfer-rescue-live/.build/root-owned"
            fake.parent.mkdir(parents=True, exist_ok=True)
            fake.write_text("x", encoding="utf-8")
            with patch.object(state, "_list_root_owned_entries", return_value=[fake]):
                payload = state.build_rescue_iso_dashboard_state(repo_root=repo)
            self.assertTrue(payload["stale_state"]["needs_sudo_clean"])
            self.assertEqual(payload["next_operator_action"]["type"], "sudo_clean_required")

    def test_auto_config_without_noauto_is_review_required(self) -> None:
        with self._repo() as td:
            repo = Path(td)
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
            payload = state.build_rescue_iso_dashboard_state(repo_root=repo)
            self.assertFalse(payload["iso_build"]["iso_found"])
            self.assertNotEqual(payload["status"], "green")

    def test_usb_write_stays_false(self) -> None:
        payload = state.build_rescue_iso_dashboard_state()
        self.assertFalse(payload["usb_write"]["allowed"])
        self.assertFalse(payload["forbidden_actions"]["usb_write_allowed"])

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
            latest = repo / "build/rescue/logs/controlled-iso-build/latest.log"
            latest.parent.mkdir(parents=True, exist_ok=True)
            latest.write_text("\n".join(f"line {idx}" for idx in range(250)), encoding="utf-8")
            logs = state.read_rescue_iso_latest_logs(repo_root=repo)
            self.assertLessEqual(len(logs["last_80_lines"]), 80)


class RescueIsoDashboardRouteRegistrationTests(unittest.TestCase):
    def test_routes_are_registered_in_app(self) -> None:
        app_py = _backend / "app.py"
        text = app_py.read_text(encoding="utf-8")
        self.assertIn("/api/dev-dashboard/rescue-iso/status", text)
        self.assertIn("/api/dev-dashboard/rescue-iso/step", text)
        self.assertIn("/api/dev-dashboard/rescue-iso/operator-commands/sudo-clean", text)


if __name__ == "__main__":
    unittest.main()
