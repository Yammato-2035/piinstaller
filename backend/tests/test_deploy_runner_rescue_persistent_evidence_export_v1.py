from __future__ import annotations

import json
import unittest
from pathlib import Path

from deploy.runner_rescue_persistent_evidence_export import (
    build_rescue_evidence_export_plan,
    build_rescue_evidence_export_result,
    execute_rescue_evidence_export,
)

_REPO = Path(__file__).resolve().parents[2]
_H = _REPO / "docs/evidence/runtime-results/handoff"
_PLAN = _H / "rescue_evidence_export_plan.json"
_RES = _H / "rescue_evidence_export_result.json"
_EXPORT_ROOT = _REPO / "build/rescue/evidence/export/pytest_rescue_evidence"


class DeployRunnerRescuePersistentEvidenceExportV1Tests(unittest.TestCase):
    def setUp(self) -> None:
        _H.mkdir(parents=True, exist_ok=True)
        self._backs = {p: p.read_bytes() if p.exists() else None for p in (_PLAN, _RES)}
        for p in (_PLAN, _RES):
            p.unlink(missing_ok=True)
        (_H / "rescue_dummy_evidence_marker.json").write_text('{"x":1}', encoding="utf-8")

    def tearDown(self) -> None:
        for p, bak in self._backs.items():
            if bak is None:
                p.unlink(missing_ok=True)
            else:
                p.write_bytes(bak)
        (_H / "rescue_dummy_evidence_marker.json").unlink(missing_ok=True)
        import shutil

        shutil.rmtree(_EXPORT_ROOT, ignore_errors=True)

    def test_internal_target_blocked(self) -> None:
        r = execute_rescue_evidence_export(
            explicit_overwrite=True,
            explicit_execute_evidence_export=True,
            export_target="/home",
        )
        self.assertEqual(r.get("rescue_evidence_export_result_status"), "blocked")

    def test_repo_export_allowed(self) -> None:
        tgt = "build/rescue/evidence/export/pytest_rescue_evidence"
        r = execute_rescue_evidence_export(
            explicit_overwrite=True,
            explicit_execute_evidence_export=True,
            export_target=tgt,
        )
        self.assertEqual(r.get("rescue_evidence_export_result_status"), "ok")
        rr = build_rescue_evidence_export_result(explicit_overwrite=True)
        ev = (rr.get("rescue_evidence_export_result") or {}).get("evaluation") or {}
        self.assertEqual(ev.get("rescue_evidence_export_eval_status"), "ok")

    def test_plan(self) -> None:
        p = build_rescue_evidence_export_plan(explicit_overwrite=True)
        self.assertEqual(p.get("rescue_evidence_export_plan_status"), "ok")
        body = p.get("rescue_evidence_export_plan") or {}
        self.assertTrue(body.get("no_auto_target_selection"))
