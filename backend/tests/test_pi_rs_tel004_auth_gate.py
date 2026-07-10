"""PI-RS-TEL-004 auth/HMAC gate tests (dummy secrets only)."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from core.rescue_telemetry_auth_gate import (
    ENV_CLOUD_SEND_ENABLED,
    ENV_KEY_ID,
    ENV_OPERATOR_CONSENT,
    ENV_SECRET_FILE,
    build_hmac_signature_preview,
    evaluate_cloud_send_gate,
    load_rescue_telemetry_auth_config,
)
from core.rescue_telemetry_payload_v2 import build_rescue_telemetry_preview_payload_v2


class Tel004AuthGateTests(unittest.TestCase):
    def test_missing_operator_env_blocks_send(self) -> None:
        gate = evaluate_cloud_send_gate(
            auth=load_rescue_telemetry_auth_config({}),
            payload=build_rescue_telemetry_preview_payload_v2(workspace_version="1.9.19.5"),
        )
        self.assertFalse(gate["allowed"])
        self.assertIn("cloud_send_disabled", gate["reasons"])

    def test_explicit_consent_and_secret_required(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            secret_path = Path(tmp) / "telemetry_secret"
            secret_path.write_text("test-secret-for-preview-only\n", encoding="utf-8")
            env = {
                ENV_OPERATOR_CONSENT: "explicit",
                ENV_CLOUD_SEND_ENABLED: "1",
                ENV_KEY_ID: "preview-key",
                "SETUPHELFER_RESCUE_TELEMETRY_AUTH_MODE": "hmac",
                ENV_SECRET_FILE: str(secret_path),
            }
            auth = load_rescue_telemetry_auth_config(env)
            self.assertTrue(auth.secret_configured)
            gate = evaluate_cloud_send_gate(
                auth=auth,
                payload=build_rescue_telemetry_preview_payload_v2(workspace_version="1.9.19.5"),
            )
            self.assertTrue(gate["allowed"])

    def test_hmac_preview_uses_dummy_key(self) -> None:
        payload = build_rescue_telemetry_preview_payload_v2(workspace_version="1.9.19.5")
        sig = build_hmac_signature_preview(payload, secret="test-secret-for-preview-only", key_id="preview")
        self.assertEqual(sig["attestation_mode"], "hmac")
        self.assertTrue(sig["signature"])


if __name__ == "__main__":
    unittest.main()
