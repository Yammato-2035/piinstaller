"""PI-RS-TEL-003 findings preview integration tests."""

from __future__ import annotations

import unittest

from core.rescue_lab_telemetry_cross_repo_preview import (
    build_diagnostics_cloudserver_payload_from_rescue,
    build_rescue_cross_repo_telemetry_payload,
)
from tests.support.pi_rs_tel003_cross_repo_harness import (
    diagnostics_repo_available,
    local_diagnostics_server,
    verify_diagnostics_findings_preview,
)

EXPECTED_CATEGORIES = {
    "diag_plesk_version_unknown",
    "diag_dns_records_missing_or_unknown",
    "diag_mail_service_status_unknown",
    "diag_ssl_certificate_missing_or_unknown",
    "diag_backup_status_unknown",
}


@unittest.skipUnless(diagnostics_repo_available(), "diagnostics monorepo venv missing")
class FindingsPreviewTests(unittest.TestCase):
    def test_findings_preview_generated(self) -> None:
        rescue = build_rescue_cross_repo_telemetry_payload()
        cloudserver = build_diagnostics_cloudserver_payload_from_rescue(rescue)
        with local_diagnostics_server() as base_url:
            result = verify_diagnostics_findings_preview(base_url=base_url, cloudserver_payload=cloudserver)
        self.assertTrue(result.get("accepted_for_diagnostics"))
        self.assertGreater(result.get("finding_count", 0), 0)
        self.assertTrue(result.get("preview_only"))
        finding_ids = {f.get("finding_id") for f in result.get("findings", [])}
        self.assertTrue(EXPECTED_CATEGORIES.intersection(finding_ids))

    def test_findings_production_ready_false(self) -> None:
        rescue = build_rescue_cross_repo_telemetry_payload()
        cloudserver = build_diagnostics_cloudserver_payload_from_rescue(rescue)
        with local_diagnostics_server() as base_url:
            result = verify_diagnostics_findings_preview(base_url=base_url, cloudserver_payload=cloudserver)
        for finding in result.get("findings", []):
            self.assertFalse(finding.get("production_ready"))
