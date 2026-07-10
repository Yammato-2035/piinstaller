"""PI-RS-TEL-003 security negative cases."""

from __future__ import annotations

import json
import unittest

from core.rescue_lab_telemetry_cross_repo_preview import (
    assert_diagnostics_base_url_allowed,
    build_rescue_cross_repo_telemetry_payload,
    validate_cross_repo_preview_contract,
)


class SecurityNegativeTests(unittest.TestCase):
    def test_sensitive_payload_rejected(self) -> None:
        payload = build_rescue_cross_repo_telemetry_payload()
        payload["warnings"] = ["Bearer abcdefghijklmnopqrstuvwxyz"]
        ok, errors = validate_cross_repo_preview_contract(payload)
        self.assertFalse(ok)
        self.assertTrue(any("forbidden" in e for e in errors))

    def test_production_ready_flag_rejected(self) -> None:
        payload = build_rescue_cross_repo_telemetry_payload()
        payload["cross_repo"]["production_ready"] = True
        ok, errors = validate_cross_repo_preview_contract(payload)
        self.assertFalse(ok)
        self.assertIn("production_ready_must_be_false", errors)

    def test_external_calls_default_false(self) -> None:
        payload = build_rescue_cross_repo_telemetry_payload()
        self.assertFalse(payload["cross_repo"]["external_calls"])

    def test_non_localhost_endpoint_rejected(self) -> None:
        with self.assertRaises(ValueError):
            assert_diagnostics_base_url_allowed("https://diagnostics.example.invalid")

    def test_no_authorization_in_harness(self) -> None:
        payload = build_rescue_cross_repo_telemetry_payload()
        serialized = json.dumps(payload)
        self.assertNotIn("Bearer", serialized)
        assert_diagnostics_base_url_allowed("http://127.0.0.1:18000")
