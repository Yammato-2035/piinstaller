from __future__ import annotations

import json
import unittest
from pathlib import Path

from deploy.runner_rescue_iso_build_execution_plan import build_rescue_iso_execution_plan

_REPO = Path(__file__).resolve().parents[2]
_OUT = _REPO / "docs/evidence/runtime-results/handoff/rescue_iso_execution_plan.json"


class DeployRunnerRescueIsoBuildExecutionPlanV1Tests(unittest.TestCase):
    def setUp(self) -> None:
        _OUT.parent.mkdir(parents=True, exist_ok=True)
        self._bak = _OUT.read_bytes() if _OUT.exists() else None
        _OUT.unlink(missing_ok=True)

    def tearDown(self) -> None:
        if self._bak is None:
            _OUT.unlink(missing_ok=True)
        else:
            _OUT.write_bytes(self._bak)

    def test_forbidden_commands_listed(self) -> None:
        res = build_rescue_iso_execution_plan(explicit_overwrite=True)
        self.assertEqual(res.get("rescue_iso_execution_plan_status"), "ok")
        fb = (res.get("rescue_iso_execution_plan") or {}).get("forbidden_commands") or []
        self.assertIn("dd", fb)
        self.assertIn("mkfs", fb)
        self.assertTrue(any("build/rescue/" in str(x) for x in (res.get("rescue_iso_execution_plan") or {}).get("allowed_workdirs") or []))
