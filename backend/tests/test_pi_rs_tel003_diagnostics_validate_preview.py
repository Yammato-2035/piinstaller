"""PI-RS-TEL-003 diagnostics validate preview integration tests."""

from __future__ import annotations

import unittest

from core.rescue_lab_telemetry_cross_repo_preview import (
    assert_diagnostics_base_url_allowed,
    build_diagnostics_cloudserver_payload_from_rescue,
    build_rescue_cross_repo_telemetry_payload,
)
from tests.support.pi_rs_tel003_cross_repo_harness import (
    diagnostics_repo_available,
    local_diagnostics_server,
    verify_diagnostics_validate_preview,
)


@unittest.skipUnless(diagnostics_repo_available(), "diagnostics monorepo venv missing")
class DiagnosticsValidatePreviewTests(unittest.TestCase):
    def test_validate_accepted_localhost(self) -> None:
        rescue = build_rescue_cross_repo_telemetry_payload()
        cloudserver = build_diagnostics_cloudserver_payload_from_rescue(rescue)
        with local_diagnostics_server() as base_url:
            result = verify_diagnostics_validate_preview(base_url=base_url, cloudserver_payload=cloudserver)
        self.assertTrue(result.get("accepted_for_diagnostics"))
        self.assertFalse(result.get("production_ready"))
        self.assertIn("finding_rules_preview", result)

    def test_non_localhost_rejected(self) -> None:
        with self.assertRaises(ValueError):
            assert_diagnostics_base_url_allowed("https://example.invalid")
