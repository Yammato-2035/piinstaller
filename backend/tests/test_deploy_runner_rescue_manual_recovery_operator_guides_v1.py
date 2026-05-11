from __future__ import annotations

import unittest
from pathlib import Path

from deploy.runner_rescue_manual_recovery_operator_guides import build_rescue_manual_recovery_operator_guides

_REPO = Path(__file__).resolve().parents[2]
_OUT = _REPO / "docs/evidence/runtime-results/handoff/rescue_manual_recovery_operator_guides.json"


class DeployRunnerRescueManualRecoveryOperatorGuidesV1Tests(unittest.TestCase):
    def setUp(self) -> None:
        _OUT.parent.mkdir(parents=True, exist_ok=True)
        self._bak = _OUT.read_bytes() if _OUT.exists() else None
        _OUT.unlink(missing_ok=True)

    def tearDown(self) -> None:
        if self._bak is None:
            _OUT.unlink(missing_ok=True)
        else:
            _OUT.write_bytes(self._bak)

    def test_guides_no_auto_repair(self) -> None:
        r = build_rescue_manual_recovery_operator_guides(explicit_overwrite=True)
        self.assertEqual(r.get("rescue_manual_recovery_operator_guides_status"), "ok")
        body = r.get("rescue_manual_recovery_operator_guides") or {}
        self.assertTrue(body.get("no_auto_repair"))
        self.assertGreaterEqual(len(body.get("guides") or []), 4)
