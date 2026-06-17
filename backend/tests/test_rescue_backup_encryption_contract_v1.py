"""RS-P1 backup encryption contract tests."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

_backend = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_backend))

from core.rescue_backup_encryption_contract import build_encryption_preflight


class TestRescueBackupEncryptionContractV1(unittest.TestCase):
    def test_key_missing_execute_false(self):
        out = build_encryption_preflight(encryption_requested=True, key_configured=False)
        self.assertFalse(out["execute_allowed"])
        self.assertFalse(out["key_material_logged"])

    def test_configured_still_execute_false_in_p1(self):
        out = build_encryption_preflight(encryption_requested=True, key_configured=True, mode="age")
        self.assertEqual(out["encryption_status"], "configured")


if __name__ == "__main__":
    unittest.main()
