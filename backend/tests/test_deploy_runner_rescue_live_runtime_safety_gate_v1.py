from __future__ import annotations

import json
import unittest
from pathlib import Path

from deploy.runner_rescue_live_runtime_safety_gate import build_rescue_live_runtime_safety_gate

_REPO = Path(__file__).resolve().parents[2]
_H = _REPO / "docs/evidence/runtime-results/handoff"
_FILES = (
    _H / "rescue_storage_discovery_result.json",
    _H / "readonly_mount_result.json",
    _H / "rescue_efi_boot_analysis.json",
    _H / "rescue_evidence_export_result.json",
    _H / "rescue_remote_help_result.json",
    _H / "rescue_live_runtime_safety_gate.json",
)


class DeployRunnerRescueLiveRuntimeSafetyGateV1Tests(unittest.TestCase):
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

    def test_ready_when_inputs_ok(self) -> None:
        (_H / "rescue_storage_discovery_result.json").write_text(
            json.dumps(
                {
                    "evaluation": {"rescue_storage_discovery_eval_status": "ok"},
                    "classification": {"row_count": 1, "flags": {}, "uuid_conflicts": []},
                }
            ),
            encoding="utf-8",
        )
        (_H / "readonly_mount_result.json").write_text(
            json.dumps({"evaluation": {"readonly_mount_eval_status": "ok", "readonly_enforced": True}}),
            encoding="utf-8",
        )
        (_H / "rescue_efi_boot_analysis.json").write_text(
            json.dumps({"efi_present": True, "rescue_efi_boot_analysis_status": "ok"}),
            encoding="utf-8",
        )
        (_H / "rescue_evidence_export_result.json").write_text(
            json.dumps({"evaluation": {"rescue_evidence_export_eval_status": "ok"}}),
            encoding="utf-8",
        )
        (_H / "rescue_remote_help_result.json").write_text(
            json.dumps({"ssh_service_auto_started": False}),
            encoding="utf-8",
        )
        r = build_rescue_live_runtime_safety_gate(explicit_overwrite=True)
        self.assertEqual(r.get("rescue_live_runtime_safety_gate_status"), "ready")
        gate = r.get("rescue_live_runtime_safety_gate") or {}
        self.assertEqual(gate.get("gate_status"), "ready")

    def test_blocked_on_rw_mount_eval(self) -> None:
        (_H / "rescue_storage_discovery_result.json").write_text(
            json.dumps({"evaluation": {"rescue_storage_discovery_eval_status": "ok"}}),
            encoding="utf-8",
        )
        (_H / "readonly_mount_result.json").write_text(
            json.dumps({"evaluation": {"readonly_mount_eval_status": "ok", "readonly_enforced": False}}),
            encoding="utf-8",
        )
        (_H / "rescue_efi_boot_analysis.json").write_text("{}", encoding="utf-8")
        (_H / "rescue_evidence_export_result.json").write_text(
            json.dumps({"evaluation": {"rescue_evidence_export_eval_status": "ok"}}),
            encoding="utf-8",
        )
        (_H / "rescue_remote_help_result.json").write_text(
            json.dumps({"ssh_service_auto_started": False}),
            encoding="utf-8",
        )
        r = build_rescue_live_runtime_safety_gate(explicit_overwrite=True)
        self.assertEqual(r.get("rescue_live_runtime_safety_gate_status"), "blocked")
