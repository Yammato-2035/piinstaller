"""Quarantine retention policy tests."""

from __future__ import annotations

import unittest

from core.beta_agreement_gate_v1 import QUARANTINE_RETENTION_DAYS_MISSING_AGREEMENT


class TelemetryQuarantineRetentionV1Tests(unittest.TestCase):
    def test_max_14_days_missing_agreement(self) -> None:
        self.assertLessEqual(QUARANTINE_RETENTION_DAYS_MISSING_AGREEMENT, 14)
        self.assertEqual(QUARANTINE_RETENTION_DAYS_MISSING_AGREEMENT, 14)


if __name__ == "__main__":
    unittest.main()
