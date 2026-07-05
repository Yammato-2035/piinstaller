"""Beta agreement gate tests."""

from __future__ import annotations

import unittest

from core.beta_agreement_gate_v1 import (
    QUARANTINE_RETENTION_DAYS_MISSING_AGREEMENT,
    gate_upload,
    validate_no_id_documents,
)


class BetaAgreementGateV1Tests(unittest.TestCase):
    def test_missing_agreement_quarantine(self) -> None:
        result = gate_upload(
            agreement_status="missing",
            telemetry_consent=True,
            mfa_enabled=True,
            email_verified=True,
        )
        self.assertFalse(result["allowed"])
        self.assertEqual(result["mode"], "quarantine")
        self.assertEqual(result["retention_days"], QUARANTINE_RETENTION_DAYS_MISSING_AGREEMENT)

    def test_valid_agreement_ok(self) -> None:
        result = gate_upload(
            agreement_status="valid",
            telemetry_consent=True,
            mfa_enabled=True,
            email_verified=True,
        )
        self.assertTrue(result["allowed"])


if __name__ == "__main__":
    unittest.main()
