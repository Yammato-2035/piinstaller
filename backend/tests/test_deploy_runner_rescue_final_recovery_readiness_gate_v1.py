from __future__ import annotations

import json
import unittest
from pathlib import Path

from deploy.runner_rescue_final_recovery_readiness_gate import build_rescue_final_recovery_readiness_gate

_REPO = Path(__file__).resolve().parents[2]
_H = _REPO / "docs/evidence/runtime-results/handoff"
_FILES = (
    _H / "rescue_recovery_target_validation_result.json",
    _H / "rescue_backup_verify_result.json",
    _H / "rescue_restore_preview_result.json",
    _H / "rescue_hardware_recovery_test_chain.json",
    _H / "rescue_live_runtime_safety_gate.json",
    _H / "rescue_final_recovery_readiness_gate.json",
)


class DeployRunnerRescueFinalRecoveryReadinessGateV1Tests(unittest.TestCase):
    def setUp(self) -> None:
        _H.mkdir(parents=True, exist_ok=True)
        self._backs = {p: p.read_bytes() if p.exists() else None for p in _FILES}
        for p in _FILES:
            p.unlink(missing_ok=True)

    def tearDown(self) -> None:
        for p, bak in self._backs.items():
            if bak is None:
                p.unlink(missing_ok=True)
            else:
                p.write_bytes(bak)

    def test_ready_all_inputs_clean(self) -> None:
        (_H / "rescue_recovery_target_validation_result.json").write_text(
            json.dumps({"evaluation": {"rescue_recovery_target_validation_eval_status": "ok"}}),
            encoding="utf-8",
        )
        (_H / "rescue_backup_verify_result.json").write_text(
            json.dumps(
                {
                    "evaluation": {"rescue_backup_verify_eval_status": "ok", "restore_preview_possible": True},
                    "discovery": {"manifest_present": True},
                }
            ),
            encoding="utf-8",
        )
        (_H / "rescue_restore_preview_result.json").write_text(
            json.dumps({"evaluation": {"rescue_restore_preview_eval_status": "ok", "writes_performed": False}}),
            encoding="utf-8",
        )
        (_H / "rescue_hardware_recovery_test_chain.json").write_text(
            json.dumps({"chain_summary_status": "ok"}),
            encoding="utf-8",
        )
        (_H / "rescue_live_runtime_safety_gate.json").write_text(json.dumps({"gate_status": "ready"}), encoding="utf-8")
        r = build_rescue_final_recovery_readiness_gate(explicit_overwrite=True)
        self.assertEqual(r.get("rescue_final_recovery_readiness_gate_status"), "ready")
        gate = r.get("rescue_final_recovery_readiness_gate") or {}
        self.assertEqual(gate.get("gate_status"), "ready")
