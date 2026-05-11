from __future__ import annotations

import unittest
from pathlib import Path

from deploy.runner_rescue_recovery_scenario_matrix import build_rescue_recovery_scenario_matrix

_REPO = Path(__file__).resolve().parents[2]
_OUT = _REPO / "docs/evidence/runtime-results/handoff/rescue_recovery_scenario_matrix.json"


class DeployRunnerRescueRecoveryScenarioMatrixV1Tests(unittest.TestCase):
    def setUp(self) -> None:
        _OUT.parent.mkdir(parents=True, exist_ok=True)
        self._bak = _OUT.read_bytes() if _OUT.exists() else None
        _OUT.unlink(missing_ok=True)

    def tearDown(self) -> None:
        if self._bak is None:
            _OUT.unlink(missing_ok=True)
        else:
            _OUT.write_bytes(self._bak)

    def test_twelve_scenarios_all_manual_only(self) -> None:
        r = build_rescue_recovery_scenario_matrix(explicit_overwrite=True)
        self.assertEqual(r.get("rescue_recovery_scenario_matrix_status"), "ok")
        body = r.get("rescue_recovery_scenario_matrix") or {}
        scenarios = body.get("scenarios") or []
        self.assertEqual(len(scenarios), 12)
        self.assertTrue(all(s.get("manual_only") is True for s in scenarios))
        self.assertTrue(all(s.get("destructive") is False for s in scenarios))
        ids = {s.get("scenario_id") for s in scenarios}
        self.assertIn("missing_grub", ids)
        self.assertIn("damaged_backup", ids)
