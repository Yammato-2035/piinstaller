"""DCC rescue BVR status + version drift tests (PI-RS-BVR-GUI-DCC-001)."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from core.rescue_bvr_dcc_status import build_rescue_bvr_dcc_status, map_overall_status
from core.version_commit_drift import build_version_drift_matrix, classify_identity_pair

REPO = Path(__file__).resolve().parents[2]


class RescueBvrDccStatusTests(unittest.TestCase):
    def test_baseline_shows_passed_with_gui_fallback(self) -> None:
        status = build_rescue_bvr_dcc_status(repo_root=REPO)
        self.assertEqual(status["last_physical_run_status"], "passed_with_gui_fallback")
        self.assertEqual(status["bvr_core_status"], "passed")
        self.assertEqual(status["gui_status"], "fallback")
        # Prefer latest physical result; baseline used http_server_failed historically.
        self.assertIn(
            status["gui_failure_code"],
            {"http_server_failed", "openvt_console_2_not_released", "rescue.gui.vt.in_use"},
        )
        self.assertEqual(status["traffic_lights"]["bvr_core"], "green")
        self.assertEqual(status["traffic_lights"]["gui"], "yellow")
        self.assertNotEqual(status["traffic_lights"]["gui"], "green")

    def test_unknown_evidence_not_green(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "scripts/rescue-live/image/locales").mkdir(parents=True)
            status = build_rescue_bvr_dcc_status(repo_root=root)
            self.assertEqual(status["evidence_status"], "missing")
            self.assertEqual(status["traffic_lights"]["evidence"], "gray")
            self.assertNotEqual(status["traffic_lights"]["bvr_core"], "green")

    def test_physical_visible_sets_gui_visible(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            ev = root / "docs/evidence/rescue/bvr-gui-dcc-001"
            ev.mkdir(parents=True)
            (ev / "physical_msi_result.json").write_text(
                json.dumps(
                    {
                        "run_id": "run-xyz",
                        "overall_status": "passed",
                        "gui_visible": True,
                        "watchdog_fallback": False,
                        "evidence_imported": True,
                    }
                ),
                encoding="utf-8",
            )
            loc = root / "scripts/rescue-live/image/locales"
            loc.mkdir(parents=True)
            for name in ("de-DE", "en-US", "fr-FR", "nl-NL"):
                (loc / f"{name}.json").write_text("{}", encoding="utf-8")
            status = build_rescue_bvr_dcc_status(repo_root=root)
            self.assertEqual(status["gui_status"], "visible")
            self.assertEqual(status["last_physical_run_status"], "passed")

    def test_map_overall(self) -> None:
        self.assertEqual(
            map_overall_status(
                bvr_core_status="passed",
                gui_status="fallback",
                evidence_status="complete",
            ),
            "passed_with_gui_fallback",
        )


class VersionCommitDriftTests(unittest.TestCase):
    def test_all_equal_green(self) -> None:
        matrix = build_version_drift_matrix(
            workspace_version="1.10.1.1",
            workspace_commit="abc",
            runtime_version="1.10.1.1",
            runtime_commit="abc",
            api_version="1.10.1.1",
            frontend_version="1.10.1.1",
            payload_version="1.10.1.1",
            payload_commit="abc",
            payload_sha256="sha1",
            usb_payload_version="1.10.1.1",
            usb_payload_sha256="sha1",
            feature_commit="abc",
        )
        self.assertEqual(matrix["overall_status"], "green")

    def test_runtime_commit_red(self) -> None:
        matrix = build_version_drift_matrix(
            workspace_version="1.10.1.1",
            workspace_commit="abc",
            runtime_version="1.10.1.1",
            runtime_commit="old",
            api_version="1.10.1.1",
            frontend_version="1.10.1.1",
            payload_version="1.10.1.1",
            payload_commit="abc",
            payload_sha256="sha1",
            usb_payload_version="1.10.1.1",
            usb_payload_sha256="sha1",
            feature_commit="abc",
        )
        self.assertEqual(matrix["overall_status"], "red")
        self.assertIn("workspace_runtime_commit_drift", matrix["drifts"])

    def test_unknown_runtime_gray_or_flag(self) -> None:
        self.assertEqual(classify_identity_pair(left="", right="abc"), "gray")
        matrix = build_version_drift_matrix(
            workspace_version="1.10.1.1",
            workspace_commit="abc",
            runtime_version="",
            runtime_commit="",
            api_version="1.10.1.1",
            frontend_version="1.10.1.1",
            payload_version="1.10.1.1",
            payload_commit="abc",
            payload_sha256="",
            usb_payload_version="",
            usb_payload_sha256="",
            feature_commit="abc",
        )
        self.assertIn(matrix["overall_status"], {"gray", "yellow"})
        self.assertIn("unknown_runtime_identity", matrix["drifts"])

    def test_origin_main_lag_not_auto_red(self) -> None:
        matrix = build_version_drift_matrix(
            workspace_version="1.10.1.1",
            workspace_commit="feature",
            runtime_version="1.10.1.1",
            runtime_commit="feature",
            api_version="1.10.1.1",
            frontend_version="1.10.1.1",
            payload_version="1.10.1.1",
            payload_commit="feature",
            payload_sha256="sha1",
            usb_payload_version="1.10.1.1",
            usb_payload_sha256="sha1",
            origin_main_commit="mainold",
            feature_commit="feature",
        )
        self.assertEqual(matrix["origin_main_status"], "yellow")
        self.assertNotEqual(matrix["overall_status"], "red")


if __name__ == "__main__":
    unittest.main()
