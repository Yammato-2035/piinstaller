from __future__ import annotations

import json
import unittest
from pathlib import Path

from deploy.runner_rescue_build_readiness_gate import build_rescue_build_readiness_gate
from deploy.runner_rescue_debian_live_build_plan import build_rescue_debian_live_build_plan
from deploy.runner_rescue_iso_test_matrix import build_rescue_iso_test_matrix
from deploy.runner_rescue_live_os_base_decision import build_rescue_live_os_base_decision
from deploy.runner_rescue_mvp_scope_gate import build_rescue_mvp_scope_gate
from deploy.runner_rescue_stick_component_inventory import build_rescue_stick_component_inventory

_REPO = Path(__file__).resolve().parents[2]
_H = _REPO / "docs/evidence/runtime-results/handoff"
_FILES = (
    _H / "rescue_live_os_base_decision.json",
    _H / "rescue_stick_component_inventory.json",
    _H / "rescue_mvp_scope_gate.json",
    _H / "rescue_debian_live_build_plan.json",
    _H / "rescue_iso_test_matrix.json",
    _H / "rescue_build_readiness_gate.json",
)


class DeployRunnerRescueBuildReadinessGateV1Tests(unittest.TestCase):
    def setUp(self) -> None:
        _H.mkdir(parents=True, exist_ok=True)
        self._bak: dict[Path, bytes | None] = {}
        for p in _FILES:
            self._bak[p] = p.read_bytes() if p.exists() else None
            p.unlink(missing_ok=True)

    def tearDown(self) -> None:
        for p, bak in self._bak.items():
            if bak is None:
                p.unlink(missing_ok=True)
            else:
                p.write_bytes(bak)

    def _run_chain(self) -> None:
        build_rescue_live_os_base_decision(explicit_overwrite=True)
        build_rescue_stick_component_inventory(explicit_overwrite=True)
        build_rescue_mvp_scope_gate(explicit_overwrite=True)
        build_rescue_debian_live_build_plan(explicit_overwrite=True)
        build_rescue_iso_test_matrix(explicit_overwrite=True)

    def test_ready_after_full_chain(self) -> None:
        self._run_chain()
        res = build_rescue_build_readiness_gate(explicit_overwrite=True)
        self.assertEqual(res.get("rescue_build_readiness_gate_status"), "ready")
        body = res.get("rescue_build_readiness_gate") or {}
        self.assertEqual(body.get("gate_status"), "ready")

    def test_blocked_on_forbidden_plan_token(self) -> None:
        self._run_chain()
        plan_path = _H / "rescue_debian_live_build_plan.json"
        bad = json.loads(plan_path.read_text(encoding="utf-8"))
        bad["notes"] = list(bad.get("notes") or []) + ["forbidden example: dd if=/dev/zero"]
        plan_path.write_text(json.dumps(bad, indent=2, sort_keys=True), encoding="utf-8")
        res = build_rescue_build_readiness_gate(explicit_overwrite=True)
        self.assertEqual(res.get("rescue_build_readiness_gate_status"), "blocked")
