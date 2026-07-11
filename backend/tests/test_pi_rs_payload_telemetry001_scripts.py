"""PI-RS-PAYLOAD-TELEMETRY-001 lab script tests."""

from __future__ import annotations

import os
import unittest
from pathlib import Path

from core.rescue_stick_cloud_lab_models import RescueStickLabSendConfig
from core.rescue_stick_cloud_lab_send import preview_rescue_stick_lab_send


class PayloadTelemetry001ScriptsTests(unittest.TestCase):
    def test_workspace_scripts_executable(self) -> None:
        root = Path(__file__).resolve().parents[2]
        for name in ("lab-rs-tel-send001-preview.sh", "lab-rs-tel-send001-send.sh"):
            path = root / "scripts" / name
            self.assertTrue(path.is_file(), name)
            self.assertTrue(os.access(path, os.X_OK), name)

    def test_lab_modules_importable(self) -> None:
        from core.rescue_stick_cloud_lab_payload import build_rescue_stick_lab_payload

        payload = build_rescue_stick_lab_payload(stick_version="1.10.0.13")
        self.assertEqual(payload["source"], "rescue_stick")
        self.assertFalse(payload["production_ready"])

    def test_preview_remains_gate_protected_without_token(self) -> None:
        config = RescueStickLabSendConfig(
            lab_send_enabled=True,
            operator_approval="explicit",
            consent_status="granted_lab",
            token_file="/nonexistent/token",
            stick_version="1.10.0.13",
        )
        result = preview_rescue_stick_lab_send(
            config,
            health_check=lambda _url, _timeout: "health_ok",
        )
        self.assertFalse(result.real_send_executed)
        self.assertNotEqual(result.send_status.value, "lab_send_accepted")


if __name__ == "__main__":
    unittest.main()
