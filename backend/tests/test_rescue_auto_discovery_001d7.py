"""Tests for SETUPHELFER-E2E-LIVE-001D7 auto discovery."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

# Bare relative paths below only resolve when cwd == repo root; anchor them
# explicitly since pytest is normally invoked with cwd == backend/ (see
# .github/workflows/ci.yml `working-directory: backend`).
_REPO_ROOT = Path(__file__).resolve().parents[2]

from core.rescue_evidence_completeness import validate_session_evidence
from core.rescue_privacy_redaction import build_privacy_summary, redact_mapping
from core.rescue_session_state import (
    PHASE_LABELS_DE,
    generate_session_id,
    init_session_state,
    read_session_state,
    session_state_dir,
    update_session_state,
)
from core.rescue_setup_logs_persistence import ensure_setup_logs_rw
from core.rescue_stale_artifact_guard import build_failed_stub


class SessionStateTests(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self._env = patch.dict("os.environ", {"SETUPHELFER_RESCUE_SESSION_DIR": self._tmpdir.name})
        self._env.start()

    def tearDown(self):
        self._env.stop()
        self._tmpdir.cleanup()

    def test_session_id_format(self):
        sid = generate_session_id()
        self.assertTrue(sid.startswith("rescue-session-"))

    def test_atomic_state_roundtrip(self):
        state = init_session_state(payload_version="1.10.0.25")
        update_session_state(current_phase="storage_collecting", progress_percent=40)
        loaded = read_session_state()
        self.assertEqual(loaded["current_phase"], "storage_collecting")
        self.assertEqual(loaded["progress_percent"], 40)

    def test_discovery_phase_labels(self):
        self.assertIn("storage_collecting", PHASE_LABELS_DE)
        self.assertIn("usb_collecting", PHASE_LABELS_DE)


class SetupLogsTests(unittest.TestCase):
    @patch("subprocess.run")
    @patch("core.rescue_setup_logs_persistence.detect_setup_logs_mount")
    def test_fallback_when_missing(self, detect_mock, run_mock):
        detect_mock.return_value = {"detected": False, "mount_point": None, "persistent": False}
        run_mock.return_value = None
        with tempfile.TemporaryDirectory() as tmp:
            with patch("core.rescue_setup_logs_persistence._FALLBACK_RUNTIME", Path(tmp)):
                with patch.object(Path, "exists", return_value=False):
                    result = ensure_setup_logs_rw()
        self.assertTrue(result["fallback_used"])
        self.assertEqual(result["status"], "missing")


class PrivacyTests(unittest.TestCase):
    def test_redact_mac_like_values(self):
        out = redact_mapping({"mac": "aa:bb:cc:dd:ee:ff"})
        self.assertTrue(str(out["mac"]).startswith("hash:"))

    def test_privacy_summary_no_secrets(self):
        summary = build_privacy_summary(payload={"token": "Bearer secret"})
        self.assertFalse(summary["secret_detected"])


class CompletenessTests(unittest.TestCase):
    def test_missing_files_failed(self):
        with tempfile.TemporaryDirectory() as tmp:
            gate = validate_session_evidence(Path(tmp), expected_session_id="s1")
            self.assertIn(gate["status"], {"failed", "review_required"})


class StaleArtifactTests(unittest.TestCase):
    def test_failed_stub(self):
        stub = build_failed_stub(error_code="x", errors=["y"])
        self.assertEqual(stub["status"], "failed")


class TtyGateScriptTests(unittest.TestCase):
    def test_check_script_exists(self):
        path = (_REPO_ROOT / "scripts/check-rescue-exclusive-tty-owner.sh")
        self.assertTrue(path.is_file())


class AutoMsiEvidenceUnitTests(unittest.TestCase):
    def test_no_start_assistant_dependency(self):
        unit = (_REPO_ROOT / "scripts/rescue-live/image/systemd/setuphelfer-rescue-auto-msi-evidence.service").read_text(
            encoding="utf-8"
        )
        self.assertNotIn("start-assistant", unit)

    def test_running_marker_in_script(self):
        script = (_REPO_ROOT / "scripts/rescue-live/image/setuphelfer-rescue-auto-msi-evidence").read_text(encoding="utf-8")
        self.assertIn("auto-msi-evidence.running", script)


class MissingModuleTests(unittest.TestCase):
    def test_bundle_import(self):
        from core.rescue_msi_evidence_bundle import collect_rs011d_supplement

        self.assertTrue(callable(collect_rs011d_supplement))

    def test_ensure_setup_logs_rw_export(self):
        from core.rescue_setup_logs_persistence import ensure_setup_logs_rw as fn

        self.assertTrue(callable(fn))


if __name__ == "__main__":
    unittest.main()
