"""Phase R.3: rescue_evidence_bundle contract tests."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest import mock

_BACKEND = Path(__file__).resolve().parent.parent
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))


class TestRescueEvidenceBundleR3(unittest.TestCase):
    def test_next_actions_from_blockers(self) -> None:
        import core.rescue_evidence_bundle as eb

        bundle = {
            "open_blockers": [{"next_action": "Fix boot"}],
            "matrix": {"document": {"entries": [{"id": "R3-NEXT-001", "next_action": "Primary"}]}},
        }
        actions = eb.build_rescue_next_actions(bundle)
        self.assertIn("Primary", actions)

    def test_build_bundle_calls_slices(self) -> None:
        import core.rescue_evidence_bundle as eb

        with (
            mock.patch.object(eb, "write_boot_evidence_bundle", return_value={"status": "ok"}),
            mock.patch.object(eb, "write_rescue_test_matrix", return_value={"status": "ok", "document": {"entries": []}}),
            mock.patch.object(eb, "build_telemetry_spool_summary", return_value={"pending_count": 0}),
            mock.patch.object(eb, "write_msi_diagnostics_evidence", return_value={"status": "ok"}),
        ):
            bundle = eb.build_rescue_evidence_bundle()
        self.assertEqual(bundle["bundle_version"], 3)
        self.assertIn("next_actions", bundle)


if __name__ == "__main__":
    unittest.main()
