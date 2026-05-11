from __future__ import annotations

import json
import unittest
from pathlib import Path

from deploy.runner_manual_runtime_failure_readiness_gate import evaluate_manual_runtime_failure_readiness

_REPO_ROOT = Path(__file__).resolve().parents[2]
_HANDOFF = _REPO_ROOT / "docs/evidence/runtime-results/handoff"
_MATRIX = _HANDOFF / "failure_injection_matrix.json"
_PREVIEW = _HANDOFF / "failure_execution_preview.json"
_CHECK = _HANDOFF / "failure_operator_checklists.json"
_SESS = _HANDOFF / "failure_test_sessions.json"
_RES = _HANDOFF / "failure_test_results.json"
_EVAL = _HANDOFF / "failure_result_evaluation.json"
_RD = _HANDOFF / "failure_test_readiness.json"

_FT = "sha256_mismatch"
_SID = f"manual_failure_ts_v1_{_FT}"


class DeployRunnerManualRuntimeFailureReadinessGateV1Tests(unittest.TestCase):
    def setUp(self) -> None:
        _HANDOFF.mkdir(parents=True, exist_ok=True)
        for p in (_MATRIX, _PREVIEW, _CHECK, _SESS, _RES, _EVAL, _RD):
            p.unlink(missing_ok=True)
        for tmp in _HANDOFF.glob("*.tmp"):
            tmp.unlink(missing_ok=True)

    def tearDown(self) -> None:
        self.setUp()

    def _write_pipeline(self, *, eval_findings: list | None = None, matrix_warnings: list | None = None, destructive_matrix: bool = False) -> None:
        fc = {
            "failure_type": _FT,
            "expected_detection_layer": "integrity_hash_validation",
            "expected_status": "blocked",
            "rollback_required": False,
            "destructive": destructive_matrix,
        }
        _MATRIX.write_text(
            json.dumps({"failure_cases": [fc], "warnings": matrix_warnings or []}),
            encoding="utf-8",
        )
        _PREVIEW.write_text(
            json.dumps({"preview_cases": [{"failure_type": _FT, "expected_runtime_status": "blocked"}], "warnings": []}),
            encoding="utf-8",
        )
        _CHECK.write_text(
            json.dumps(
                {
                    "checklists": [
                        {
                            "failure_type": _FT,
                            "abort_conditions": ["abort_unknown_target"],
                            "required_evidence": ["operator_log"],
                            "destructive": False,
                        }
                    ],
                    "warnings": [],
                }
            ),
            encoding="utf-8",
        )
        _SESS.write_text(
            json.dumps(
                {
                    "test_sessions": [
                        {
                            "session_id": _SID,
                            "failure_type": _FT,
                            "evidence_to_capture": ["log"],
                            "abort_conditions": ["stop_if_wrong_media"],
                        }
                    ],
                    "warnings": [],
                }
            ),
            encoding="utf-8",
        )
        _RES.write_text(
            json.dumps(
                {
                    "session_results": [
                        {
                            "session_id": _SID,
                            "failure_type": _FT,
                            "evidence_collected": ["log"],
                        }
                    ],
                    "warnings": [],
                }
            ),
            encoding="utf-8",
        )
        _EVAL.write_text(
            json.dumps(
                {
                    "mismatching_sessions": 0,
                    "review_required_sessions": 0,
                    "findings": eval_findings if eval_findings is not None else [],
                }
            ),
            encoding="utf-8",
        )

    def test_pipeline_ready(self) -> None:
        self._write_pipeline()
        out = evaluate_manual_runtime_failure_readiness(explicit_overwrite=True)
        self.assertEqual(out["readiness_status"], "ready")
        data = json.loads(_RD.read_text(encoding="utf-8"))
        self.assertEqual(data["readiness_status"], "ready")
        self.assertEqual(data["checked_failure_types"], 1)
        self.assertEqual(data["checked_sessions"], 1)

    def test_evaluation_review_required(self) -> None:
        self._write_pipeline(eval_findings=[{"session_id": _SID, "finding": "x"}])
        out = evaluate_manual_runtime_failure_readiness(explicit_overwrite=True)
        self.assertEqual(out["readiness_status"], "review_required")

    def test_destructive_blocked(self) -> None:
        self._write_pipeline(destructive_matrix=True)
        out = evaluate_manual_runtime_failure_readiness(explicit_overwrite=True)
        self.assertEqual(out["readiness_status"], "blocked")

    def test_fehlende_arteakte_blocked(self) -> None:
        self._write_pipeline()
        _EVAL.unlink(missing_ok=True)
        out = evaluate_manual_runtime_failure_readiness(explicit_overwrite=True)
        self.assertEqual(out["readiness_status"], "blocked")

    def test_duplicate_session_ids_blocked(self) -> None:
        self._write_pipeline()
        _SESS.write_text(
            json.dumps(
                {
                    "test_sessions": [
                        {
                            "session_id": "dup",
                            "failure_type": _FT,
                            "evidence_to_capture": ["a"],
                            "abort_conditions": ["b"],
                        },
                        {
                            "session_id": "dup",
                            "failure_type": _FT,
                            "evidence_to_capture": ["a"],
                            "abort_conditions": ["b"],
                        },
                    ],
                    "warnings": [],
                }
            ),
            encoding="utf-8",
        )
        _RES.write_text(
            json.dumps(
                {
                    "session_results": [
                        {"session_id": "dup", "failure_type": _FT, "evidence_collected": ["x"]},
                        {"session_id": "dup", "failure_type": _FT, "evidence_collected": ["y"]},
                    ],
                    "warnings": [],
                }
            ),
            encoding="utf-8",
        )
        out = evaluate_manual_runtime_failure_readiness(explicit_overwrite=True)
        self.assertEqual(out["readiness_status"], "blocked")

    def test_abort_checklist_blocked(self) -> None:
        self._write_pipeline()
        _CHECK.write_text(
            json.dumps(
                {
                    "checklists": [
                        {
                            "failure_type": _FT,
                            "abort_conditions": [],
                            "required_evidence": ["e"],
                            "destructive": False,
                        }
                    ],
                    "warnings": [],
                }
            ),
            encoding="utf-8",
        )
        out = evaluate_manual_runtime_failure_readiness(explicit_overwrite=True)
        self.assertEqual(out["readiness_status"], "blocked")

    def test_atomisches_schreiben(self) -> None:
        self._write_pipeline()
        evaluate_manual_runtime_failure_readiness(explicit_overwrite=True)
        self.assertFalse(any(p.name.endswith(".tmp") for p in _HANDOFF.iterdir()))

    def test_no_forbidden_systemcalls(self) -> None:
        src = (_REPO_ROOT / "backend/deploy/runner_manual_runtime_failure_readiness_gate.py").read_text(encoding="utf-8").lower()
        for token in ["subprocess", "os.system", "mkfs", " dd ", "wipefs", "restore ", "rm -rf"]:
            self.assertNotIn(token, src)

    def test_no_execute_subroutes(self) -> None:
        routes = (_REPO_ROOT / "backend/deploy/routes.py").read_text(encoding="utf-8")
        self.assertIn("/runner/manual-runtime/failure-readiness-gate", routes)
        for forbidden in [
            "/runner/manual-runtime/failure-readiness-gate/execute",
            "/runner/manual-runtime/failure-readiness-gate/apply",
            "/runner/manual-runtime/failure-readiness-gate/install",
            "/runner/manual-runtime/failure-readiness-gate/delete",
            "/runner/manual-runtime/failure-readiness-gate/release",
        ]:
            self.assertNotIn(forbidden, routes)


if __name__ == "__main__":
    unittest.main()
