from __future__ import annotations

import json
import unittest
from pathlib import Path

from deploy.runner_manual_runtime_failure_injection_matrix import (
    _FAILURE_CASES,
    _ROLLBACK_REQUIRED_TYPES,
    build_manual_runtime_failure_injection_matrix,
)
from deploy.routes_source_aggregate import read_deploy_routes_aggregate

_REPO_ROOT = Path(__file__).resolve().parents[2]
_HANDOFF = _REPO_ROOT / "docs/evidence/runtime-results/handoff"
_ACC = _HANDOFF / "validator_final_acceptance.json"
_OUT = _HANDOFF / "failure_injection_matrix.json"


class DeployRunnerManualRuntimeFailureInjectionMatrixV1Tests(unittest.TestCase):
    def setUp(self) -> None:
        _HANDOFF.mkdir(parents=True, exist_ok=True)
        _ACC.unlink(missing_ok=True)
        _OUT.unlink(missing_ok=True)
        for tmp in _HANDOFF.glob("*.tmp"):
            tmp.unlink(missing_ok=True)

    def tearDown(self) -> None:
        self.setUp()

    def _write_acceptance(self, status: str) -> None:
        _ACC.write_text(
            json.dumps(
                {
                    "acceptance_schema_version": 1,
                    "strict_mode": "final_evidence_acceptance_gate",
                    "generated_at": "2026-05-08T12:00:00Z",
                    "snapshot_path": "docs/evidence/runtime-results/handoff/validator_evidence_final_snapshot.json",
                    "snapshot_sha256": "a" * 64,
                    "event_count": 1,
                    "acceptance_status": status,
                }
            ),
            encoding="utf-8",
        )

    def test_matrix_erzeugbar(self) -> None:
        self._write_acceptance("accepted")
        out = build_manual_runtime_failure_injection_matrix(explicit_overwrite=True)
        self.assertEqual(out["matrix_status"], "ok")
        self.assertTrue(_OUT.is_file())

    def test_alle_failure_typen_vorhanden(self) -> None:
        self._write_acceptance("accepted")
        build_manual_runtime_failure_injection_matrix(explicit_overwrite=True)
        data = json.loads(_OUT.read_text(encoding="utf-8"))
        exp = {str(x["failure_type"]) for x in _FAILURE_CASES}
        got = {str(x.get("failure_type")) for x in data.get("failure_cases", [])}
        self.assertEqual(got, exp)

    def test_destructive_immer_false(self) -> None:
        self._write_acceptance("accepted")
        build_manual_runtime_failure_injection_matrix(explicit_overwrite=True)
        data = json.loads(_OUT.read_text(encoding="utf-8"))
        self.assertTrue(all(bool(c.get("destructive")) is False for c in data["failure_cases"]))

    def test_rollback_required_korrekt(self) -> None:
        self._write_acceptance("accepted")
        build_manual_runtime_failure_injection_matrix(explicit_overwrite=True)
        data = json.loads(_OUT.read_text(encoding="utf-8"))
        got = {c["failure_type"] for c in data["failure_cases"] if bool(c.get("rollback_required"))}
        self.assertEqual(got, set(_ROLLBACK_REQUIRED_TYPES))

    def test_keine_produktiven_targets_erlaubt(self) -> None:
        self._write_acceptance("blocked")
        out = build_manual_runtime_failure_injection_matrix(explicit_overwrite=True)
        self.assertEqual(out["matrix_status"], "blocked")
        self.assertIn("FAILURE_MATRIX_ACCEPTANCE_BLOCKED", out["blocked_reasons"])

    def test_no_forbidden_systemcalls(self) -> None:
        src = (_REPO_ROOT / "backend/deploy/runner_manual_runtime_failure_injection_matrix.py").read_text(
            encoding="utf-8"
        ).lower()
        for token in ["subprocess", "os.system", "chmod(", "chown(", "systemctl", " dd ", "mkfs", "wipefs", "mount "]:
            self.assertNotIn(token, src)

    def test_no_execute_subroutes(self) -> None:
        routes = read_deploy_routes_aggregate()
        self.assertIn("/runner/manual-runtime/failure-injection-matrix", routes)
        for forbidden in [
            "/runner/manual-runtime/failure-injection-matrix/execute",
            "/runner/manual-runtime/failure-injection-matrix/apply",
            "/runner/manual-runtime/failure-injection-matrix/install",
            "/runner/manual-runtime/failure-injection-matrix/delete",
            "/runner/manual-runtime/failure-injection-matrix/release",
        ]:
            self.assertNotIn(forbidden, routes)

    def test_json_schema_stabil(self) -> None:
        self._write_acceptance("review_required")
        out = build_manual_runtime_failure_injection_matrix(explicit_overwrite=True)
        self.assertEqual(out["matrix_status"], "review_required")
        data = json.loads(_OUT.read_text(encoding="utf-8"))
        self.assertEqual(data["matrix_schema_version"], 1)
        self.assertEqual(data["strict_mode"], "real_hardware_failure_injection_matrix")
        self.assertIsInstance(data["failure_cases"], list)
        self.assertIsInstance(data["warnings"], list)
        self.assertIsInstance(data["blocked_reasons"], list)

    def test_atomic_schreiben(self) -> None:
        self._write_acceptance("accepted")
        build_manual_runtime_failure_injection_matrix(explicit_overwrite=True)
        self.assertFalse(any(p.name.endswith(".tmp") for p in _HANDOFF.iterdir()))

    def test_overwrite_blockiert(self) -> None:
        self._write_acceptance("accepted")
        build_manual_runtime_failure_injection_matrix(explicit_overwrite=True)
        second = build_manual_runtime_failure_injection_matrix(explicit_overwrite=False)
        self.assertEqual(second["matrix_status"], "blocked")
        self.assertIn("FAILURE_MATRIX_EXISTS_NO_OVERWRITE", second["blocked_reasons"])


if __name__ == "__main__":
    unittest.main()
