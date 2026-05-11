from __future__ import annotations

import json
import unittest
from pathlib import Path

from deploy.runner_rescue_iso_readiness_gate import build_rescue_iso_readiness_gate

_REPO = Path(__file__).resolve().parents[2]
_H = _REPO / "docs/evidence/runtime-results/handoff"
_BUILD = _H / "rescue_iso_build_result.json"
_VM = _H / "rescue_vm_test_result.json"
_PROBE = _H / "rescue_iso_live_runtime_probe_result.json"
_GATE = _H / "rescue_iso_readiness_gate.json"


class DeployRunnerRescueIsoReadinessGateV1Tests(unittest.TestCase):
    def setUp(self) -> None:
        _H.mkdir(parents=True, exist_ok=True)
        self._backs: dict[Path, bytes | None] = {}
        for p in (_BUILD, _VM, _PROBE, _GATE):
            self._backs[p] = p.read_bytes() if p.exists() else None
            p.unlink(missing_ok=True)

    def tearDown(self) -> None:
        for p, bak in self._backs.items():
            if bak is None:
                p.unlink(missing_ok=True)
            else:
                p.write_bytes(bak)

    def _write_ok_chain(self) -> None:
        _BUILD.write_text(
            json.dumps(
                {
                    "build_success": True,
                    "iso_found": True,
                    "forbidden_commands_detected": [],
                }
            ),
            encoding="utf-8",
        )
        _VM.write_text(
            json.dumps(
                {
                    "vm_boot_simulated": True,
                    "iso_verified": True,
                    "qemu_available": True,
                }
            ),
            encoding="utf-8",
        )
        _PROBE.write_text(
            json.dumps(
                {
                    "executions": [],
                    "evaluation": {
                        "iso_live_runtime_probe_status": "ok",
                        "legacy_runtime_detected": False,
                    },
                }
            ),
            encoding="utf-8",
        )

    def test_ready_when_all_ok(self) -> None:
        self._write_ok_chain()
        r = build_rescue_iso_readiness_gate(explicit_overwrite=True)
        self.assertEqual(r.get("rescue_iso_readiness_gate_status"), "ready")

    def test_blocked_when_legacy(self) -> None:
        self._write_ok_chain()
        d = json.loads(_PROBE.read_text(encoding="utf-8"))
        d["evaluation"]["legacy_runtime_detected"] = True
        d["evaluation"]["legacy_markers_hit"] = ["pi-installer"]
        _PROBE.write_text(json.dumps(d), encoding="utf-8")
        r = build_rescue_iso_readiness_gate(explicit_overwrite=True)
        self.assertEqual(r.get("rescue_iso_readiness_gate_status"), "blocked")
