from __future__ import annotations

import json
import unittest
from pathlib import Path

from deploy.runner_manual_runtime_failure_result_evaluation import evaluate_manual_runtime_failure_results

_REPO_ROOT = Path(__file__).resolve().parents[2]
_HANDOFF = _REPO_ROOT / "docs/evidence/runtime-results/handoff"
_RES = _HANDOFF / "failure_test_results.json"
_SESS = _HANDOFF / "failure_test_sessions.json"
_PREV = _HANDOFF / "failure_execution_preview.json"
_EVAL = _HANDOFF / "failure_result_evaluation.json"

_FT = "sha256_mismatch"
_SID = f"manual_failure_ts_v1_{_FT}"


class DeployRunnerManualRuntimeFailureResultEvaluationV1Tests(unittest.TestCase):
    def setUp(self) -> None:
        _HANDOFF.mkdir(parents=True, exist_ok=True)
        for p in (_RES, _SESS, _PREV, _EVAL):
            p.unlink(missing_ok=True)
        for tmp in _HANDOFF.glob("*.tmp"):
            tmp.unlink(missing_ok=True)

    def tearDown(self) -> None:
        self.setUp()

    def _write_preview(self) -> None:
        _PREV.write_text(
            json.dumps(
                {
                    "preview_schema_version": 1,
                    "preview_cases": [
                        {
                            "failure_type": _FT,
                            "expected_runtime_status": "blocked",
                            "execution_mode": "manual_preview_only",
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )

    def _write_session(self, *, rollback_required: bool = False) -> None:
        _SESS.write_text(
            json.dumps(
                {
                    "sessions_schema_version": 1,
                    "test_sessions": [
                        {
                            "session_id": _SID,
                            "failure_type": _FT,
                            "execution_mode": "manual_only",
                            "rollback_required": rollback_required,
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )

    def _write_result(
        self,
        *,
        observed: str = "blocked",
        expected: str = "blocked",
        deviations: list | None = None,
        destructive: bool = False,
        evidence: list | None = None,
        rollback_performed: bool = False,
    ) -> None:
        _RES.write_text(
            json.dumps(
                {
                    "results_schema_version": 1,
                    "session_results": [
                        {
                            "session_id": _SID,
                            "failure_type": _FT,
                            "execution_mode": "manual_only",
                            "operator": "op",
                            "executed_at": "2026-05-08T12:00:00Z",
                            "observed_status": observed,
                            "expected_status": expected,
                            "rollback_performed": rollback_performed,
                            "evidence_collected": evidence if evidence is not None else ["log"],
                            "deviations": deviations if deviations is not None else [],
                            "notes": [],
                            "destructive": destructive,
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )

    def test_vollstaendige_evaluation_ok(self) -> None:
        self._write_preview()
        self._write_session()
        self._write_result()
        out = evaluate_manual_runtime_failure_results(explicit_overwrite=True)
        self.assertEqual(out["evaluation_status"], "ok")
        data = json.loads(_EVAL.read_text(encoding="utf-8"))
        self.assertEqual(data["matching_sessions"], 1)
        self.assertEqual(data["mismatching_sessions"], 0)
        self.assertEqual(data["review_required_sessions"], 0)

    def test_mismatches_review_required(self) -> None:
        self._write_preview()
        self._write_session()
        self._write_result(observed="ok", expected="blocked")
        out = evaluate_manual_runtime_failure_results(explicit_overwrite=True)
        self.assertEqual(out["evaluation_status"], "review_required")
        data = json.loads(_EVAL.read_text(encoding="utf-8"))
        self.assertEqual(data["mismatching_sessions"], 1)
        self.assertTrue(any(f.get("finding") == "observed_status_mismatch" for f in data["findings"]))

    def test_deviations_review_required(self) -> None:
        self._write_preview()
        self._write_session()
        self._write_result(deviations=["unexpected_timing"])
        out = evaluate_manual_runtime_failure_results(explicit_overwrite=True)
        self.assertEqual(out["evaluation_status"], "review_required")
        data = json.loads(_EVAL.read_text(encoding="utf-8"))
        self.assertTrue(any(f.get("finding") == "deviations_present" for f in data["findings"]))

    def test_destructive_blocked(self) -> None:
        self._write_preview()
        self._write_session()
        self._write_result(destructive=True)
        out = evaluate_manual_runtime_failure_results(explicit_overwrite=True)
        self.assertEqual(out["evaluation_status"], "blocked")
        self.assertFalse(_EVAL.exists())

    def test_fehlende_pflichtfelder_blocked(self) -> None:
        self._write_preview()
        self._write_session()
        self._write_result(observed="", expected="blocked")
        out = evaluate_manual_runtime_failure_results(explicit_overwrite=True)
        self.assertEqual(out["evaluation_status"], "blocked")
        self.assertFalse(_EVAL.exists())

    def test_atomisches_schreiben(self) -> None:
        self._write_preview()
        self._write_session()
        self._write_result()
        evaluate_manual_runtime_failure_results(explicit_overwrite=True)
        self.assertFalse(any(p.name.endswith(".tmp") for p in _HANDOFF.iterdir()))

    def test_no_forbidden_systemcalls(self) -> None:
        src = (_REPO_ROOT / "backend/deploy/runner_manual_runtime_failure_result_evaluation.py").read_text(
            encoding="utf-8"
        ).lower()
        for token in ["subprocess", "os.system", "mkfs", " dd ", "wipefs", "restore ", "rm -rf"]:
            self.assertNotIn(token, src)

    def test_no_execute_subroutes(self) -> None:
        routes = (_REPO_ROOT / "backend/deploy/routes.py").read_text(encoding="utf-8")
        self.assertIn("/runner/manual-runtime/failure-result-evaluation", routes)
        for forbidden in [
            "/runner/manual-runtime/failure-result-evaluation/execute",
            "/runner/manual-runtime/failure-result-evaluation/apply",
            "/runner/manual-runtime/failure-result-evaluation/install",
            "/runner/manual-runtime/failure-result-evaluation/delete",
            "/runner/manual-runtime/failure-result-evaluation/release",
        ]:
            self.assertNotIn(forbidden, routes)


if __name__ == "__main__":
    unittest.main()
