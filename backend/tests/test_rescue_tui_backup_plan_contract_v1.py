"""RS-P2C TUI backup plan contract — workspace script checks."""

from __future__ import annotations

import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
TUI = REPO / "scripts/rescue-live/image/setuphelfer-rescue-tui.sh"


class TestRescueTuiBackupPlanContractV1(unittest.TestCase):
    def setUp(self) -> None:
        self.tui = TUI.read_text(encoding="utf-8")

    def test_backup_plan_menu_present(self):
        self.assertIn("Backup-Plan erstellen", self.tui)

    def test_dry_run_only(self):
        self.assertIn("dry-run", self.tui)
        self.assertNotIn("backup_execute", self.tui.lower())

    def test_uses_contract(self):
        self.assertIn("build_rescue_backup_plan", self.tui)

    def test_evidence_mirror(self):
        self.assertIn("backup-plan-dry-run.json", self.tui)


if __name__ == "__main__":
    unittest.main()
