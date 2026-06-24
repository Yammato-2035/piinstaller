"""Development Dashboard — Rescue build status aggregation tests."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from core import rescue_build_dashboard_state as rbd  # noqa: E402


class TestRescueBuildDashboardState(unittest.TestCase):
    def test_builds_with_missing_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            state = rbd.build_rescue_build_dashboard_state(repo_root=repo)
            self.assertIn(state["status"], ("gray", "yellow", "red", "green"))
            self.assertFalse(state["forbidden_actions"]["usb_write_allowed"])
            self.assertFalse(state["forbidden_actions"]["dd_allowed"])
            self.assertIsInstance(state["evidence_missing"], list)

    def test_iso_build_failed_not_green(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            ev = repo / "docs/evidence/rescue"
            ev.mkdir(parents=True)
            (ev / "RESCUE_CONTROLLED_ISO_BUILD_RESULT.md").write_text(
                "# Result\n**Gesamtstatus:** **ISO_BUILD_FAILED**\nE: Tried to extract package\n",
                encoding="utf-8",
            )
            state = rbd.build_rescue_build_dashboard_state(repo_root=repo)
            self.assertIn(state["controlled_iso_build"]["status"], ("red", "yellow"))
            self.assertNotEqual(state["controlled_iso_build"]["status"], "green")
            self.assertNotEqual(state["status"], "green")

    def test_usb_write_stays_false(self) -> None:
        with patch("core.rescue_usb_operator_selection.load_operator_selection_evidence", return_value=None):
            state = rbd.build_rescue_build_dashboard_state()
        self.assertFalse(state["usb_write_gate"]["usb_write_allowed"])
        self.assertFalse(state["forbidden_actions"]["usb_write_allowed"])

    def test_log_lines_capped(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            log_dir = repo / "build/rescue/logs/controlled-iso-build"
            log_dir.mkdir(parents=True)
            lines = [f"line {i}" for i in range(200)]
            (log_dir / "latest.log").write_text("\n".join(lines), encoding="utf-8")
            state = rbd.build_rescue_build_dashboard_state(repo_root=repo)
            self.assertLessEqual(len(state["latest_logs"]["lines"]), 40)

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
        red = rbd._redact_line(raw)
        self.assertNotIn("supersecret", red)
        self.assertIn("[REDACTED]", red)

    def test_final_gate_ready_read(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            handoff = repo / "docs/evidence/runtime-results/handoff"
            handoff.mkdir(parents=True)
            (handoff / "rescue_stick_readonly_build_final_gate.json").write_text(
                json.dumps({"gate_status": "ready", "real_iso_build_allowed": False}),
                encoding="utf-8",
            )
            state = rbd.build_rescue_build_dashboard_state(repo_root=repo)
            self.assertEqual(state["readonly_build_emulation_gate"]["gate_status"], "ready")

    def test_missing_iso_review_required(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            ev = repo / "docs/evidence/rescue"
            ev.mkdir(parents=True)
            (ev / "RESCUE_CONTROLLED_ISO_BUILD_RESULT.md").write_text(
                "review_required\nno ISO\n", encoding="utf-8"
            )
            state = rbd.build_rescue_build_dashboard_state(repo_root=repo)
            self.assertIn(state["controlled_iso_build"]["status"], ("yellow", "red", "gray"))
            self.assertFalse(state["latest_artifacts"]["iso"]["found"])

    def test_api_code_not_ok_when_failed(self) -> None:
        state = {"status": "red"}
        self.assertEqual(rbd.rescue_build_status_api_code(state), "DEV_DASHBOARD_RESCUE_BUILD_STATUS_BLOCKED")

    @patch.object(rbd, "subprocess")
    def test_no_forbidden_subprocess_in_state_build(self, mock_sp: unittest.mock.MagicMock) -> None:
        mock_sp.run.return_value = unittest.mock.Mock(returncode=0, stdout="ok", stderr="")
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td)
            (repo / "scripts").mkdir()
            (repo / "scripts/check-runtime-deploy-gate.sh").write_text("#!/bin/sh\nexit 0\n")
            rbd.build_rescue_build_dashboard_state(repo_root=repo)
        for call in mock_sp.run.call_args_list:
            cmd = call[0][0] if call[0] else call.kwargs.get("args")
            if isinstance(cmd, list):
                joined = " ".join(cmd)
                self.assertNotIn("dd", joined)
                self.assertNotIn("mkfs", joined)
                self.assertNotIn("parted", joined)


class TestRescueBuildDashboardEndpoint(unittest.TestCase):
    def test_endpoint_registered_read_only_get(self) -> None:
        app_path = _backend.parent / "backend" / "app.py"
        if not app_path.is_file():
            app_path = Path(__file__).resolve().parents[2] / "backend" / "app.py"
        text = app_path.read_text(encoding="utf-8")
        self.assertIn("/api/dev-dashboard/rescue-build/status", text)
        self.assertIn("build_rescue_build_dashboard_state", text)


if __name__ == "__main__":
    unittest.main()
