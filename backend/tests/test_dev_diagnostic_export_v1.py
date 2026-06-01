"""Unit tests for dev_diagnostic_export (no QEMU)."""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from core.dev_diagnostic_export import (
    build_fleet_session_diagnostic_export,
    build_markdown_diagnostic_report,
    build_qemu_smoke_diagnostic_export,
    classify_qemu_smoke_failure,
    collect_evidence_index,
    redact_diagnostic_export,
)
from core.fleet_session_state import create_fleet_session


class DevDiagnosticExportTests(unittest.TestCase):
    def setUp(self) -> None:
        self._td = tempfile.TemporaryDirectory()
        self.repo = Path(self._td.name)
        self._env = patch.dict(
            os.environ,
            {"SETUPHELFER_FLEET_SESSIONS_ENABLED": "true", "PI_INSTALLER_DEV": "1"},
            clear=False,
        )
        self._env.start()
        self._repo_patch = patch("core.dev_diagnostic_export._repo_root", return_value=self.repo)
        self._repo_patch.start()
        self._fleet_repo = patch("core.fleet_session_state._repo_root", return_value=self.repo)
        self._fleet_repo.start()

    def tearDown(self) -> None:
        self._fleet_repo.stop()
        self._repo_patch.stop()
        self._env.stop()
        self._td.cleanup()

    def _seed_qemu_run(self, run_id: str, *, serial_text: str = "") -> Path:
        run_dir = self.repo / "docs/evidence/runtime-results/rescue/qemu" / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        autopilot = {
            "run_id": run_id,
            "status": "failed",
            "qemu_exit_code": 124,
            "dev_server_report_new": False,
            "guest_smoke_from_serial": None,
            "lab_proxy_enabled": True,
            "host_dev_server_url": "http://10.0.2.2:8001",
        }
        (run_dir / "qemu_autopilot_result.json").write_text(
            json.dumps(autopilot, indent=2), encoding="utf-8"
        )
        (run_dir / "qemu-serial.log").write_text(serial_text, encoding="utf-8")
        (run_dir / "dev_server_summary_before.json").write_text(
            json.dumps({"reports_last_24h": 0, "node_count": 2}), encoding="utf-8"
        )
        (run_dir / "dev_server_summary_after.json").write_text(
            json.dumps({"reports_last_24h": 0, "node_count": 2}), encoding="utf-8"
        )
        create_fleet_session(
            {
                "run_id": run_id,
                "session_type": "local_qemu_smoke",
                "status": "timeout",
            },
            repo_root=self.repo,
        )
        return run_dir

    def test_export_known_fleet_session(self) -> None:
        run_id = "qemu_test_export_1"
        self._seed_qemu_run(run_id)
        sid = f"fleet-{run_id}"
        export = build_fleet_session_diagnostic_export(sid, redacted=True)
        self.assertEqual(export["run_id"], run_id)
        self.assertEqual(export["session_id"], sid)
        self.assertTrue(export["redacted"])

    def test_missing_session_not_found(self) -> None:
        from core.dev_diagnostic_export import DevDiagnosticExportError

        with self.assertRaises(DevDiagnosticExportError) as ctx:
            build_fleet_session_diagnostic_export("fleet-does-not-exist", redacted=True)
        self.assertEqual(ctx.exception.code, "DEV_DIAGNOSTIC_NOT_FOUND")

    def test_serial_zero_classifies_serial_empty(self) -> None:
        run_id = "qemu_serial_empty"
        self._seed_qemu_run(run_id, serial_text="")
        export = build_qemu_smoke_diagnostic_export(run_id, redacted=True)
        self.assertEqual(export["qemu_smoke"]["serial_size_bytes"], 0)
        self.assertEqual(export["classification"]["primary"], "serial_empty_boot_unknown")
        self.assertFalse(export["devserver_ingest"]["report_new"])
        self.assertFalse(export["devserver_ingest"]["guest_found"])

    def test_missing_autopilot_does_not_crash(self) -> None:
        run_id = "qemu_no_autopilot"
        run_dir = self.repo / "docs/evidence/runtime-results/rescue/qemu" / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        export = build_qemu_smoke_diagnostic_export(run_id, redacted=True)
        self.assertEqual(export["qemu_smoke"]["autopilot_result"], {})

    def test_large_serial_truncated(self) -> None:
        run_id = "qemu_big_serial"
        lines = "\n".join(f"LINE {i}" for i in range(500))
        self._seed_qemu_run(run_id, serial_text=lines)
        export = build_qemu_smoke_diagnostic_export(run_id, redacted=True)
        head = export["qemu_smoke"]["serial_excerpt_head"]
        self.assertIn("LINE 0", head)
        self.assertNotIn("LINE 499", head)

    def test_redaction_removes_token_patterns(self) -> None:
        export = {
            "run_id": "x",
            "note": "api_key=supersecret12345",
            "redaction": {},
        }
        out = redact_diagnostic_export(export)
        self.assertNotIn("supersecret12345", json.dumps(out))
        self.assertTrue(out["redaction"]["secrets_detected"])

    def test_markdown_contains_run_id_and_classification(self) -> None:
        run_id = "qemu_md_report"
        self._seed_qemu_run(run_id)
        export = build_qemu_smoke_diagnostic_export(run_id, redacted=True)
        md = build_markdown_diagnostic_report(export)
        self.assertIn(run_id, md)
        self.assertIn("serial_size_bytes", md)
        self.assertIn("serial_empty_boot_unknown", md)

    def test_collect_evidence_index_missing_paths(self) -> None:
        run_id = "qemu_ev_idx"
        self._seed_qemu_run(run_id)
        idx = collect_evidence_index(run_id, f"fleet-{run_id}")
        self.assertTrue(any(p["exists"] for p in idx["paths"]))
        self.assertIn("qemu_gtk_pid.txt", "".join(idx["missing_paths"]))


if __name__ == "__main__":
    unittest.main()
