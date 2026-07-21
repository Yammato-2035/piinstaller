"""Unit tests for canonical BVR progress and release status (VT-PROGRESS-002)."""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from core.rescue_bvr_release_status import build_release_rescue_bvr_status
from core.rescue_canonical_bvr_progress import (
    CANONICAL_PHASES,
    DRIFT_CODE,
    detect_progress_source_drift,
    normalize_phase,
    read_progress_for_display,
    write_canonical_progress,
)


class CanonicalProgressTests(unittest.TestCase):
    def test_normalize_legacy_phases(self) -> None:
        self.assertEqual(normalize_phase("sabrent_waiting"), "sabrent_wait")
        self.assertEqual(normalize_phase("backup_create"), "backup")
        self.assertEqual(normalize_phase("shutdown"), "shutdown")

    def test_sequence_monotonic_and_no_phase_regression(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            state_dir = Path(tmp)
            with mock.patch.dict(os.environ, {"SETUPHELFER_RESCUE_STATE_DIR": str(state_dir)}):
                a = write_canonical_progress(phase="sabrent_wait", status="running", message="wait")
                b = write_canonical_progress(phase="backup", status="running", message="backup")
                c = write_canonical_progress(phase="sabrent_wait", status="running", message="old")
                self.assertEqual(a["sequence"], 1)
                self.assertEqual(b["sequence"], 2)
                self.assertEqual(c["sequence"], 3)
                self.assertEqual(c["phase"], "backup")
                self.assertGreaterEqual(b["phase_index"], a["phase_index"])
                self.assertEqual(c["phase_index"], b["phase_index"])

    def test_terminal_stays_terminal(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            state_dir = Path(tmp)
            with mock.patch.dict(os.environ, {"SETUPHELFER_RESCUE_STATE_DIR": str(state_dir)}):
                write_canonical_progress(phase="shutdown", status="passed", message="done", terminal=True)
                again = write_canonical_progress(phase="sabrent_wait", status="running", message="nope")
                self.assertTrue(again["terminal"])
                self.assertEqual(again["phase"], "shutdown")

    def test_drift_detection_sabrent_vs_shutdown(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            state_dir = Path(tmp)
            with mock.patch.dict(os.environ, {"SETUPHELFER_RESCUE_STATE_DIR": str(state_dir)}):
                canon = write_canonical_progress(
                    phase="shutdown", status="passed", message="done", terminal=True
                )
                drift = detect_progress_source_drift(
                    canonical=canon,
                    auto_e2e_state={"phase": "sabrent_waiting", "status": "running"},
                )
                self.assertTrue(drift["drift"])
                self.assertEqual(drift["code"], DRIFT_CODE)

    def test_display_prefers_canonical(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            state_dir = Path(tmp)
            with mock.patch.dict(os.environ, {"SETUPHELFER_RESCUE_STATE_DIR": str(state_dir)}):
                write_canonical_progress(phase="verify", status="running", message="verify")
                snap = read_progress_for_display()
                self.assertEqual(snap["phase"], "verify")
                self.assertEqual(len(CANONICAL_PHASES), snap["phase_count"])


class ReleaseStatusTests(unittest.TestCase):
    def test_release_status_has_no_home_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "config").mkdir()
            (root / "config/version.json").write_text(
                json.dumps({"project_version": "1.9.20.0"}), encoding="utf-8"
            )
            (root / "config/rescue_payload_version.json").write_text(
                json.dumps({"rescue_payload_version": "1.10.1.2"}), encoding="utf-8"
            )
            locales = root / "scripts/rescue-live/image/locales"
            locales.mkdir(parents=True)
            keys = {"title": "x"}
            for loc in ("de-DE", "en-US", "fr-FR", "nl-NL"):
                (locales / f"{loc}.json").write_text(json.dumps(keys), encoding="utf-8")
            status = build_release_rescue_bvr_status(repo_root=root)
            blob = json.dumps(status)
            self.assertNotIn("/home/", blob)
            self.assertTrue(status["read_only"])
            self.assertFalse(status["developer_capability_required"])
            self.assertIn("progress", status)
            self.assertIn("bvr", status)

    def test_route_exists_in_status_module(self) -> None:
        text = Path("backend/api/routes/status.py").read_text(encoding="utf-8")
        self.assertIn('/api/status/rescue-bvr', text)
        self.assertIn("build_release_rescue_bvr_status", text)


class WatchdogHealthPatternTests(unittest.TestCase):
    def test_chromium_pattern_includes_auto_e2e(self) -> None:
        common = Path("scripts/rescue-live/image/setuphelfer-rescue-common.sh").read_text(
            encoding="utf-8"
        )
        self.assertIn("auto-e2e-progress", common)
        self.assertIn("setuphelfer_rescue_select_gui_vt", common)
        self.assertNotIn("fuser -k", common)
        self.assertIn("rescue.gui.vt.none_available", common)

    def test_watchdog_uses_select_gui_vt(self) -> None:
        wd = Path("scripts/rescue-live/image/setuphelfer-rescue-gui-watchdog.sh").read_text(
            encoding="utf-8"
        )
        self.assertIn("setuphelfer_rescue_select_gui_vt", wd)
        self.assertIn("auto-e2e-progress", wd)


if __name__ == "__main__":
    unittest.main()
