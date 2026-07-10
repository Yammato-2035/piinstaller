"""PI-RS-TEL-004 security negative cases."""

from __future__ import annotations

import unittest
from pathlib import Path

from core.rescue_telemetry_auth_gate import evaluate_cloud_send_gate, load_rescue_telemetry_auth_config
from core.rescue_telemetry_payload_v2 import (
    build_rescue_telemetry_preview_payload_v2,
    validate_preview_payload_security,
)


class Tel004SecurityNegativeTests(unittest.TestCase):
    def test_payload_rejects_secret_like_tokens(self) -> None:
        payload = build_rescue_telemetry_preview_payload_v2(workspace_version="1.9.19.5")
        payload["system_assessment"]["note"] = "Authorization: Bearer deadbeef"
        errors = validate_preview_payload_security(payload)
        self.assertTrue(any("forbidden_secret_like_token" in e for e in errors))

    def test_production_ready_payload_blocked(self) -> None:
        payload = build_rescue_telemetry_preview_payload_v2(workspace_version="1.9.19.5")
        payload["production_ready"] = True
        gate = evaluate_cloud_send_gate(
            auth=load_rescue_telemetry_auth_config({}),
            payload=payload,
        )
        self.assertFalse(gate["allowed"])
        self.assertIn("production_ready_forbidden", gate["reasons"])

    def test_network_env_documented_not_committed(self) -> None:
        root = Path(__file__).resolve().parents[2]
        doc = root / "docs/config/RESCUE_TELEMETRY_NETWORK_ENV.md"
        self.assertTrue(doc.is_file())
        text = doc.read_text(encoding="utf-8")
        self.assertIn("Do not commit", text)
        self.assertIn("network.env", text)


if __name__ == "__main__":
    unittest.main()
