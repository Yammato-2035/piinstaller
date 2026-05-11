from __future__ import annotations

import json
import unittest
from pathlib import Path

from deploy.runner_rescue_debian_live_build_plan import build_rescue_debian_live_build_plan

_REPO = Path(__file__).resolve().parents[2]
_OUT = _REPO / "docs/evidence/runtime-results/handoff/rescue_debian_live_build_plan.json"


class DeployRunnerRescueDebianLiveBuildPlanV1Tests(unittest.TestCase):
    def setUp(self) -> None:
        _OUT.parent.mkdir(parents=True, exist_ok=True)
        self._bak = _OUT.read_bytes() if _OUT.exists() else None
        _OUT.unlink(missing_ok=True)

    def tearDown(self) -> None:
        if self._bak is None:
            _OUT.unlink(missing_ok=True)
        else:
            _OUT.write_bytes(self._bak)

    def test_outputs_only_build_rescue(self) -> None:
        res = build_rescue_debian_live_build_plan(explicit_overwrite=True)
        self.assertEqual(res.get("rescue_debian_live_build_plan_status"), "ok")
        body = res.get("rescue_debian_live_build_plan") or {}
        self.assertTrue(str(body.get("artifact_output_root") or "").startswith("build/rescue"))
        for p in body.get("output_paths") or []:
            self.assertTrue(str(p).startswith("build/rescue/"), p)
        parsed = json.loads(_OUT.read_text(encoding="utf-8"))
        self.assertEqual(parsed.get("tooling"), "live-build")
