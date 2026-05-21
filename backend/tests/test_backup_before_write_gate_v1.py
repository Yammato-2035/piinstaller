"""Backup-before-overwrite gate — decision only."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from core.backup_before_write_gate import evaluate_backup_before_write_requirement  # noqa: E402


class BackupBeforeWriteGateTests(unittest.TestCase):
    def test_empty_target_satisfied(self) -> None:
        r = evaluate_backup_before_write_requirement()
        self.assertEqual(r["status"], "satisfied")
        self.assertFalse(r["backup_required"])

    def test_existing_filesystem_requires_backup(self) -> None:
        r = evaluate_backup_before_write_requirement(existing_filesystems=True)
        self.assertTrue(r["backup_required"])
        self.assertEqual(r["status"], "required")

    def test_existing_os_requires_backup(self) -> None:
        r = evaluate_backup_before_write_requirement(existing_os_indicators=True)
        self.assertTrue(r["backup_required"])
        self.assertIn(r["status"], ("required", "blocked"))

    def test_user_data_requires_backup(self) -> None:
        r = evaluate_backup_before_write_requirement(user_data_indicators=True)
        self.assertTrue(r["backup_required"])

    def test_missing_evidence_required(self) -> None:
        r = evaluate_backup_before_write_requirement(
            existing_filesystems=True,
            backup_evidence=None,
        )
        self.assertEqual(r["status"], "required")

    def test_evidence_satisfied(self) -> None:
        r = evaluate_backup_before_write_requirement(
            existing_os_indicators=True,
            backup_evidence={"status": "ok", "backup_completed": True},
        )
        self.assertEqual(r["status"], "satisfied")
        self.assertTrue(r["backup_required"])

    def test_operator_override_not_satisfied(self) -> None:
        r = evaluate_backup_before_write_requirement(
            user_data_indicators=True,
            operator_override=True,
        )
        self.assertNotEqual(r["status"], "satisfied")
        self.assertEqual(r["status"], "review_required")

    def test_no_subprocess_in_module(self) -> None:
        import core.backup_before_write_gate as mod

        src = Path(mod.__file__).read_text(encoding="utf-8")
        self.assertNotIn("subprocess", src)
        self.assertNotIn("tar ", src)


if __name__ == "__main__":
    unittest.main()
