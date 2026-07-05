"""PI-RS-TEL-001 API route tests."""

from __future__ import annotations

import asyncio
import json
import unittest
from unittest.mock import patch

from core.rescue_lab_telemetry_evidence import export_pi_rs_tel_001_evidence
from core.rescue_lab_telemetry_status import reset_last_send_status_for_tests
from core.rescue_lab_telemetry_send_preview_gate import reset_send_preview_for_tests


class RescueLabTelemetryApiTests(unittest.TestCase):
    def tearDown(self) -> None:
        reset_last_send_status_for_tests()
        reset_send_preview_for_tests()

    def _run(self, coro):  # noqa: ANN001
        return asyncio.run(coro)

    def test_release_profile_disabled(self) -> None:
        from api.routes.rescue_lab_telemetry import rescue_lab_telemetry_send_preview

        with patch("api.routes.rescue_lab_telemetry._lab_profile_allowed", return_value=False):
            resp = self._run(rescue_lab_telemetry_send_preview())
        self.assertEqual(resp.status_code, 403)
        body = json.loads(resp.body.decode())
        self.assertEqual(body["code"], "RESCUE_LAB_TELEMETRY_BLOCKED")

    def test_local_lab_send_preview_synthetic_only(self) -> None:
        from api.routes.rescue_lab_telemetry import rescue_lab_telemetry_send_preview

        with patch("api.routes.rescue_lab_telemetry._lab_profile_allowed", return_value=True):
            with patch("api.routes.rescue_lab_telemetry.execute_send_preview") as mock_exec:
                mock_exec.return_value = {
                    "code": "RESCUE_LAB_TELEMETRY_BLOCKED",
                    "result": {
                        "send_mode": "dry_run",
                        "send_executed": False,
                        "production_ready": False,
                    },
                    "warnings": [],
                    "errors": [],
                }
                resp = self._run(rescue_lab_telemetry_send_preview())
        self.assertEqual(resp.status_code, 200)
        body = json.loads(resp.body.decode())
        self.assertFalse(body["result"]["production_ready"])
        self.assertFalse(body["result"]["send_executed"])

    def test_status_shows_production_ready_false(self) -> None:
        from api.routes.rescue_lab_telemetry import rescue_lab_telemetry_status

        with patch("api.routes.rescue_lab_telemetry._lab_profile_allowed", return_value=True):
            with patch("api.routes.rescue_lab_telemetry.build_rescue_lab_telemetry_dashboard_status") as mock_dash:
                mock_dash.return_value = {"production_ready": False, "client_id": "fake-rescue-stick-lab-client"}
                resp = self._run(rescue_lab_telemetry_status())
        body = json.loads(resp.body.decode())
        self.assertFalse(body["production_ready"])

    def test_evidence_export_no_secrets(self) -> None:
        out = export_pi_rs_tel_001_evidence()
        for path in out.glob("*.json"):
            text = path.read_text(encoding="utf-8")
            self.assertNotIn("BEGIN PRIVATE KEY", text)
            self.assertNotIn("unit-test-secret", text)
            self.assertNotIn("test-secret-for-unit-tests-only", text)

    def test_no_auto_send_on_import(self) -> None:
        import importlib

        mod = importlib.import_module("core.rescue_lab_telemetry_client")
        self.assertTrue(callable(mod.send_rescue_lab_telemetry))
        self.assertFalse(hasattr(mod, "_startup_send_executed"))

    def test_no_backup_restore_usb_paths_in_new_modules(self) -> None:
        from pathlib import Path

        root = Path(__file__).resolve().parents[1] / "core"
        names = [
            "rescue_lab_telemetry_model.py",
            "rescue_lab_telemetry_client.py",
            "rescue_lab_telemetry_signing.py",
        ]
        forbidden = ("backup_execute", "restore_usb", "dd ", "mkfs", "mount(")
        for name in names:
            text = (root / name).read_text(encoding="utf-8")
            for token in forbidden:
                self.assertNotIn(token, text)


if __name__ == "__main__":
    unittest.main()
