from __future__ import annotations

import unittest
from pathlib import Path

from deploy.runner_rescue_remote_help_preparation import build_rescue_remote_help_plan, build_rescue_remote_help_result

_REPO = Path(__file__).resolve().parents[2]
_H = _REPO / "docs/evidence/runtime-results/handoff"
_PLAN = _H / "rescue_remote_help_plan.json"
_RES = _H / "rescue_remote_help_result.json"


class DeployRunnerRescueRemoteHelpPreparationV1Tests(unittest.TestCase):
    def setUp(self) -> None:
        _H.mkdir(parents=True, exist_ok=True)
        self._backs = {p: p.read_bytes() if p.exists() else None for p in (_PLAN, _RES)}
        for p in (_PLAN, _RES):
            p.unlink(missing_ok=True)

    def tearDown(self) -> None:
        for p, bak in self._backs.items():
            if bak is None:
                p.unlink(missing_ok=True)
            else:
                p.write_bytes(bak)

    def test_ssh_not_auto_started(self) -> None:
        pl = build_rescue_remote_help_plan(explicit_overwrite=True)
        self.assertIs(pl.get("rescue_remote_help_plan", {}).get("ssh_auto_start"), False)
        rs = build_rescue_remote_help_result(explicit_overwrite=True)
        body = rs.get("rescue_remote_help_result") or {}
        self.assertIs(body.get("ssh_service_auto_started"), False)
        self.assertEqual(rs.get("rescue_remote_help_result_status"), "ok")
