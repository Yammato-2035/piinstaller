from __future__ import annotations

import json
import unittest
from pathlib import Path

from deploy.runner_rescue_recovery_evidence_timeline import build_rescue_recovery_evidence_timeline

_REPO = Path(__file__).resolve().parents[2]
_H = _REPO / "docs/evidence/runtime-results/handoff"
_OUT = _H / "rescue_recovery_evidence_timeline.json"


class DeployRunnerRescueRecoveryEvidenceTimelineV1Tests(unittest.TestCase):
    def setUp(self) -> None:
        _H.mkdir(parents=True, exist_ok=True)
        self._backs = {p: p.read_bytes() if p.exists() else None for p in (_OUT, _H / "rescue_iso_readiness_gate.json")}
        _OUT.unlink(missing_ok=True)
        (_H / "rescue_iso_readiness_gate.json").write_text(json.dumps({"gate_status": "ready"}), encoding="utf-8")

    def tearDown(self) -> None:
        for p, bak in self._backs.items():
            if bak is None:
                p.unlink(missing_ok=True)
            else:
                p.write_bytes(bak)

    def test_iso_step_has_sha256(self) -> None:
        r = build_rescue_recovery_evidence_timeline(explicit_overwrite=True)
        body = r.get("rescue_recovery_evidence_timeline") or {}
        entries = body.get("entries") or []
        iso = next((e for e in entries if e.get("step_id") == "iso_boot"), {})
        self.assertTrue(iso.get("present"))
        self.assertEqual(len(str(iso.get("sha256") or "")), 64)
