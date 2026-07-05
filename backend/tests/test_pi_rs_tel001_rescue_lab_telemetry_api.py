"""PI-RS-TEL-001 API route tests."""

from __future__ import annotations

import asyncio
import json
import os
import unittest
from unittest.mock import patch

from core.rescue_lab_telemetry_evidence import export_pi_rs_tel_001_evidence
from core.rescue_lab_telemetry_status import reset_last_send_status_for_tests


class RescueLabTelemetryApiTests(unittest.TestCase):
    def tearDown(self) -> None:
        reset_last_send_status_for_tests()

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
            with patch("api.routes.rescue_lab_telemetry.send_rescue_lab_telemetry") as mock_send:
                from core.rescue_lab_telemetry_model import RescueLabTelemetryResult

                mock_send.return_value = RescueLabTelemetryResult(
                    status="blocked_missing_secret",
                    client_id="fake-rescue-stick-lab-client",
                    product="setuphelfer-rescue-stick",
                    source="rescue_stick_lab_preview",
                    environment="lab",
                    payload_kind="rescue_preview",
                    http_status=None,
                    server_status=None,
                    nonce_status="unknown",
                    sent_at="2026-07-05T12:00:00Z",
                    errors=["secret missing"],
                )
                resp = self._run(rescue_lab_telemetry_send_preview())
        self.assertEqual(resp.status_code, 200)
        body = json.loads(resp.body.decode())
        self.assertEqual(body["code"], "RESCUE_LAB_TELEMETRY_BLOCKED")
        self.assertFalse(body["result"]["production_ready"])
        sent_payload = mock_send.call_args[0][1]
        self.assertIs(sent_payload.get("safety", {}).get("contains_real_host_data"), False)
        self.assertNotIn("hostname", sent_payload)
        self.assertNotIn("mac_address", sent_payload)

    def test_status_shows_production_ready_false(self) -> None:
        from api.routes.rescue_lab_telemetry import rescue_lab_telemetry_status

        with patch("api.routes.rescue_lab_telemetry._lab_profile_allowed", return_value=True):
            body = self._run(rescue_lab_telemetry_status())
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
