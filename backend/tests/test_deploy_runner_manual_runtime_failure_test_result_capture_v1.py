from __future__ import annotations

import json
import unittest
from pathlib import Path

from deploy.runner_manual_runtime_failure_injection_matrix import _FAILURE_CASES
from deploy.runner_manual_runtime_failure_test_result_capture import capture_manual_runtime_failure_test_results

_REPO_ROOT = Path(__file__).resolve().parents[2]
_HANDOFF = _REPO_ROOT / "docs/evidence/runtime-results/handoff"
_SESS = _HANDOFF / "failure_test_sessions.json"
_OUT = _HANDOFF / "failure_test_results.json"


class DeployRunnerManualRuntimeFailureTestResultCaptureV1Tests(unittest.TestCase):
    def setUp(self) -> None:
        _HANDOFF.mkdir(parents=True, exist_ok=True)
        _SESS.unlink(missing_ok=True)
        _OUT.unlink(missing_ok=True)
        for tmp in _HANDOFF.glob("*.tmp"):
            tmp.unlink(missing_ok=True)

    def tearDown(self) -> None:
        self.setUp()

    def _write_sessions(self) -> None:
        sessions = []
        for c in _FAILURE_CASES:
            ft = str(c["failure_type"])
            sessions.append(
                {
                    "session_id": f"manual_failure_ts_v1_{ft}",
                    "failure_type": ft,
                    "execution_mode": "manual_only",
                    "risk_level": "low",
                    "destructive": False,
                    "rollback_required": False,
                    "required_media": ["external_usb_test_drive"],
                    "operator_steps": ["step"],
                    "evidence_to_capture": ["log"],
                    "abort_conditions": ["abort"],
                    "expected_final_state": ["ok"],
                }
            )
        _SESS.write_text(
            json.dumps(
                {
                    "sessions_schema_version": 1,
                    "strict_mode": "manual_failure_test_sessions",
                    "generated_at": "2026-05-08T12:00:00Z",
                    "test_sessions": sessions,
                    "warnings": [],
                    "blocked_reasons": [],
                }
            ),
            encoding="utf-8",
        )

    def test_resultate_erzeugbar(self) -> None:
        self._write_sessions()
        out = capture_manual_runtime_failure_test_results(explicit_overwrite=True)
        self.assertEqual(out["capture_status"], "ok")
        self.assertTrue(_OUT.is_file())

    def test_alle_sessions_enthalten(self) -> None:
        self._write_sessions()
        capture_manual_runtime_failure_test_results(explicit_overwrite=True)
        data = json.loads(_OUT.read_text(encoding="utf-8"))
        exp = {str(c["failure_type"]) for c in _FAILURE_CASES}
        got = {str(r.get("failure_type")) for r in data["session_results"]}
        self.assertEqual(got, exp)

    def test_destructive_immer_false(self) -> None:
        self._write_sessions()
        capture_manual_runtime_failure_test_results(explicit_overwrite=True)
        data = json.loads(_OUT.read_text(encoding="utf-8"))
        self.assertTrue(all(bool(r.get("destructive")) is False for r in data["session_results"]))

    def test_rollback_performed_vorhanden(self) -> None:
        self._write_sessions()
        capture_manual_runtime_failure_test_results(explicit_overwrite=True)
        data = json.loads(_OUT.read_text(encoding="utf-8"))
        self.assertTrue(all("rollback_performed" in r for r in data["session_results"]))

    def test_evidence_collected_vorhanden(self) -> None:
        self._write_sessions()
        capture_manual_runtime_failure_test_results(explicit_overwrite=True)
        data = json.loads(_OUT.read_text(encoding="utf-8"))
        self.assertTrue(all(isinstance(r.get("evidence_collected"), list) for r in data["session_results"]))

    def test_deviations_vorhanden(self) -> None:
        self._write_sessions()
        capture_manual_runtime_failure_test_results(explicit_overwrite=True)
        data = json.loads(_OUT.read_text(encoding="utf-8"))
        self.assertTrue(all(isinstance(r.get("deviations"), list) for r in data["session_results"]))

    def test_keine_produktiven_targets(self) -> None:
        self._write_sessions()
        capture_manual_runtime_failure_test_results(explicit_overwrite=True)
        payload = _OUT.read_text(encoding="utf-8").lower()
        self.assertNotIn("/dev/sda", payload)
        self.assertNotIn("productive_os_volume", payload)

    def test_atomisches_schreiben(self) -> None:
        self._write_sessions()
        capture_manual_runtime_failure_test_results(explicit_overwrite=True)
        self.assertFalse(any(p.name.endswith(".tmp") for p in _HANDOFF.iterdir()))

    def test_no_forbidden_systemcalls(self) -> None:
        src = (_REPO_ROOT / "backend/deploy/runner_manual_runtime_failure_test_result_capture.py").read_text(
            encoding="utf-8"
        ).lower()
        for token in ["subprocess", "os.system", "mkfs", " dd ", "wipefs", "restore ", "rm -rf"]:
            self.assertNotIn(token, src)

    def test_no_execute_subroutes(self) -> None:
        routes = (_REPO_ROOT / "backend/deploy/routes.py").read_text(encoding="utf-8")
        self.assertIn("/runner/manual-runtime/failure-test-results", routes)
        for forbidden in [
            "/runner/manual-runtime/failure-test-results/execute",
            "/runner/manual-runtime/failure-test-results/apply",
            "/runner/manual-runtime/failure-test-results/install",
            "/runner/manual-runtime/failure-test-results/delete",
            "/runner/manual-runtime/failure-test-results/release",
        ]:
            self.assertNotIn(forbidden, routes)


if __name__ == "__main__":
    unittest.main()
