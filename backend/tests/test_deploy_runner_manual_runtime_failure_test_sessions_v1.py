from __future__ import annotations

import json
import unittest
from pathlib import Path

from deploy.runner_manual_runtime_failure_injection_matrix import _FAILURE_CASES, _ROLLBACK_REQUIRED_TYPES
from deploy.runner_manual_runtime_failure_test_sessions import build_manual_runtime_failure_test_sessions
from deploy.routes_source_aggregate import read_deploy_routes_aggregate

_REPO_ROOT = Path(__file__).resolve().parents[2]
_HANDOFF = _REPO_ROOT / "docs/evidence/runtime-results/handoff"
_CHK = _HANDOFF / "failure_operator_checklists.json"
_OUT = _HANDOFF / "failure_test_sessions.json"


class DeployRunnerManualRuntimeFailureTestSessionsV1Tests(unittest.TestCase):
    def setUp(self) -> None:
        _HANDOFF.mkdir(parents=True, exist_ok=True)
        _CHK.unlink(missing_ok=True)
        _OUT.unlink(missing_ok=True)
        for tmp in _HANDOFF.glob("*.tmp"):
            tmp.unlink(missing_ok=True)

    def tearDown(self) -> None:
        self.setUp()

    def _write_checklists(self) -> None:
        checklists = []
        for c in _FAILURE_CASES:
            ft = str(c["failure_type"])
            rr = ft in _ROLLBACK_REQUIRED_TYPES
            checklists.append(
                {
                    "failure_type": ft,
                    "risk_level": "medium" if rr else "low",
                    "destructive": False,
                    "rollback_required": rr,
                    "required_media": ["external_usb_test_drive"],
                    "operator_checklist": [f"Prepare controlled scenario for {ft}."],
                    "expected_detection_points": ["layer"],
                    "required_evidence": ["operator_log"],
                    "abort_conditions": ["unknown_target"],
                }
            )
        _CHK.write_text(
            json.dumps(
                {
                    "checklist_schema_version": 1,
                    "strict_mode": "real_laptop_failure_operator_checklists",
                    "generated_at": "2026-05-08T12:00:00Z",
                    "checklists": checklists,
                    "warnings": [],
                    "blocked_reasons": [],
                }
            ),
            encoding="utf-8",
        )

    def test_sessions_erzeugbar(self) -> None:
        self._write_checklists()
        out = build_manual_runtime_failure_test_sessions(explicit_overwrite=True)
        self.assertEqual(out["sessions_status"], "ok")
        self.assertTrue(_OUT.is_file())

    def test_alle_failure_typen_enthalten(self) -> None:
        self._write_checklists()
        build_manual_runtime_failure_test_sessions(explicit_overwrite=True)
        data = json.loads(_OUT.read_text(encoding="utf-8"))
        exp = {str(c["failure_type"]) for c in _FAILURE_CASES}
        got = {str(s.get("failure_type")) for s in data["test_sessions"]}
        self.assertEqual(got, exp)

    def test_destructive_immer_false(self) -> None:
        self._write_checklists()
        build_manual_runtime_failure_test_sessions(explicit_overwrite=True)
        data = json.loads(_OUT.read_text(encoding="utf-8"))
        self.assertTrue(all(bool(s.get("destructive")) is False for s in data["test_sessions"]))

    def test_operator_steps_vorhanden(self) -> None:
        self._write_checklists()
        build_manual_runtime_failure_test_sessions(explicit_overwrite=True)
        data = json.loads(_OUT.read_text(encoding="utf-8"))
        self.assertTrue(all(isinstance(s.get("operator_steps"), list) and len(s["operator_steps"]) > 0 for s in data["test_sessions"]))

    def test_evidence_to_capture_vorhanden(self) -> None:
        self._write_checklists()
        build_manual_runtime_failure_test_sessions(explicit_overwrite=True)
        data = json.loads(_OUT.read_text(encoding="utf-8"))
        self.assertTrue(all(isinstance(s.get("evidence_to_capture"), list) and len(s["evidence_to_capture"]) > 0 for s in data["test_sessions"]))

    def test_abort_conditions_vorhanden(self) -> None:
        self._write_checklists()
        build_manual_runtime_failure_test_sessions(explicit_overwrite=True)
        data = json.loads(_OUT.read_text(encoding="utf-8"))
        self.assertTrue(all(isinstance(s.get("abort_conditions"), list) and len(s["abort_conditions"]) > 0 for s in data["test_sessions"]))

    def test_expected_final_state_vorhanden(self) -> None:
        self._write_checklists()
        build_manual_runtime_failure_test_sessions(explicit_overwrite=True)
        data = json.loads(_OUT.read_text(encoding="utf-8"))
        self.assertTrue(all(isinstance(s.get("expected_final_state"), list) and len(s["expected_final_state"]) > 0 for s in data["test_sessions"]))

    def test_keine_produktiven_targets(self) -> None:
        self._write_checklists()
        build_manual_runtime_failure_test_sessions(explicit_overwrite=True)
        payload = _OUT.read_text(encoding="utf-8").lower()
        self.assertNotIn("/dev/nvme0n1", payload)
        self.assertNotIn("productive_internal_partition", payload)

    def test_atomisches_schreiben(self) -> None:
        self._write_checklists()
        build_manual_runtime_failure_test_sessions(explicit_overwrite=True)
        self.assertFalse(any(p.name.endswith(".tmp") for p in _HANDOFF.iterdir()))

    def test_no_forbidden_systemcalls(self) -> None:
        src = (_REPO_ROOT / "backend/deploy/runner_manual_runtime_failure_test_sessions.py").read_text(encoding="utf-8").lower()
        for token in ["subprocess", "os.system", "mkfs", " dd ", "wipefs", "restore ", "rm -rf"]:
            self.assertNotIn(token, src)

    def test_no_execute_subroutes(self) -> None:
        routes = read_deploy_routes_aggregate()
        self.assertIn("/runner/manual-runtime/failure-test-sessions", routes)
        for forbidden in [
            "/runner/manual-runtime/failure-test-sessions/execute",
            "/runner/manual-runtime/failure-test-sessions/apply",
            "/runner/manual-runtime/failure-test-sessions/install",
            "/runner/manual-runtime/failure-test-sessions/delete",
            "/runner/manual-runtime/failure-test-sessions/release",
        ]:
            self.assertNotIn(forbidden, routes)


if __name__ == "__main__":
    unittest.main()
