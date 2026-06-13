"""Phase R.3: TUI menu stability static checks."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
_ASSISTANT = _REPO / "scripts/rescue-live/image/setuphelfer-rescue-start-assistant"
_COMMON = _REPO / "scripts/rescue-live/image/setuphelfer-rescue-common.sh"


class TestRescueTuiMenuStabilityR3(unittest.TestCase):
    def test_main_menu_records_evidence(self) -> None:
        text = _ASSISTANT.read_text(encoding="utf-8")
        self.assertIn("setuphelfer_rescue_record_menu_evidence", text)
        self.assertIn("plan_builder_exit_", text)

    def test_evidence_bundle_on_exit(self) -> None:
        text = _ASSISTANT.read_text(encoding="utf-8")
        self.assertIn("setuphelfer_rescue_run_evidence_bundle", text)

    def test_common_has_evidence_helpers(self) -> None:
        text = _COMMON.read_text(encoding="utf-8")
        self.assertIn("setuphelfer_rescue_record_menu_evidence", text)
        self.assertIn("setuphelfer-rescue-evidence.py", text)

    def test_write_actions_still_blocked(self) -> None:
        text = _ASSISTANT.read_text(encoding="utf-8")
        self.assertIn('"write_actions_allowed": false', text)


if __name__ == "__main__":
    unittest.main()
