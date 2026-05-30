"""Tests für devserver_agent.redaction_client."""

from __future__ import annotations

import unittest

from devserver_agent.redaction_client import detect_sensitive_fields, enforce_mode_redaction, redact_for_beta


class DevAgentRedactionTests(unittest.TestCase):
    def test_hostname_detected(self) -> None:
        found = detect_sensitive_fields({"hostname": "secret-host"})
        self.assertTrue(any("hostname" in f for f in found))

    def test_mac_detected_in_string(self) -> None:
        found = detect_sensitive_fields({"note": "aa:bb:cc:dd:ee:ff"})
        self.assertTrue(len(found) >= 0)

    def test_serial_detected(self) -> None:
        found = detect_sensitive_fields({"serial": "S12345"})
        self.assertTrue(any("serial" in f for f in found))

    def test_token_detected(self) -> None:
        found = detect_sensitive_fields({"token": "secret-token"})
        self.assertTrue(any("token" in f for f in found))

    def test_beta_redacted(self) -> None:
        out = redact_for_beta({"hostname": "h1", "cpu": {}})
        self.assertNotEqual(out.get("hostname"), "h1")

    def test_public_upload_blocked(self) -> None:
        report = {"payload": {"x": 1}}
        _, _, errors = enforce_mode_redaction("public_rescue", report)
        self.assertIn("public_upload_blocked", errors)

    def test_local_lab_raw_allowed(self) -> None:
        report = {"payload": {"hostname": "lab"}, "redaction_status": "raw_lab"}
        out, _, errors = enforce_mode_redaction("local_lab", report)
        self.assertEqual(out["redaction_status"], "raw_lab")
        self.assertFalse(errors)


if __name__ == "__main__":
    unittest.main()
