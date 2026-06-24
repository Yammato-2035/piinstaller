from __future__ import annotations

import json
import unittest
from pathlib import Path

from deploy.runner_manual_runtime_failure_execution_preview import build_manual_runtime_failure_execution_preview
from deploy.runner_manual_runtime_failure_injection_matrix import _FAILURE_CASES
from deploy.routes_source_aggregate import read_deploy_routes_aggregate

_REPO_ROOT = Path(__file__).resolve().parents[2]
_HANDOFF = _REPO_ROOT / "docs/evidence/runtime-results/handoff"
_MATRIX = _HANDOFF / "failure_injection_matrix.json"
_OUT = _HANDOFF / "failure_execution_preview.json"


class DeployRunnerManualRuntimeFailureExecutionPreviewV1Tests(unittest.TestCase):
    def setUp(self) -> None:
        _HANDOFF.mkdir(parents=True, exist_ok=True)
        _MATRIX.unlink(missing_ok=True)
        _OUT.unlink(missing_ok=True)
        for tmp in _HANDOFF.glob("*.tmp"):
            tmp.unlink(missing_ok=True)

    def tearDown(self) -> None:
        self.setUp()

    def _write_matrix(self) -> None:
        _MATRIX.write_text(
            json.dumps(
                {
                    "matrix_schema_version": 1,
                    "strict_mode": "real_hardware_failure_injection_matrix",
                    "generated_at": "2026-05-08T12:00:00Z",
                    "failure_cases": [
                        {
                            "failure_type": str(c["failure_type"]),
                            "expected_detection_layer": str(c["expected_detection_layer"]),
                            "expected_status": str(c["expected_status"]),
                            "rollback_required": str(c["failure_type"]) in {
                                "interrupted_verify",
                                "interrupted_restore_preview",
                                "mount_changed",
                            },
                            "destructive": False,
                        }
                        for c in _FAILURE_CASES
                    ],
                    "warnings": [],
                    "blocked_reasons": [],
                }
            ),
            encoding="utf-8",
        )

    def test_preview_erzeugbar(self) -> None:
        self._write_matrix()
        out = build_manual_runtime_failure_execution_preview(explicit_overwrite=True)
        self.assertEqual(out["preview_status"], "ok")
        self.assertTrue(_OUT.is_file())

    def test_alle_failure_typen_enthalten(self) -> None:
        self._write_matrix()
        build_manual_runtime_failure_execution_preview(explicit_overwrite=True)
        data = json.loads(_OUT.read_text(encoding="utf-8"))
        exp = {str(c["failure_type"]) for c in _FAILURE_CASES}
        got = {str(c.get("failure_type")) for c in data["preview_cases"]}
        self.assertEqual(got, exp)

    def test_destructive_immer_false(self) -> None:
        self._write_matrix()
        build_manual_runtime_failure_execution_preview(explicit_overwrite=True)
        data = json.loads(_OUT.read_text(encoding="utf-8"))
        self.assertTrue(all(bool(c.get("destructive")) is False for c in data["preview_cases"]))

    def test_rollback_required_korrekt(self) -> None:
        self._write_matrix()
        build_manual_runtime_failure_execution_preview(explicit_overwrite=True)
        data = json.loads(_OUT.read_text(encoding="utf-8"))
        for c in data["preview_cases"]:
            self.assertIn("rollback_required", c)

    def test_operator_steps_vorhanden(self) -> None:
        self._write_matrix()
        build_manual_runtime_failure_execution_preview(explicit_overwrite=True)
        data = json.loads(_OUT.read_text(encoding="utf-8"))
        self.assertTrue(all(isinstance(c.get("operator_steps"), list) and len(c["operator_steps"]) > 0 for c in data["preview_cases"]))

    def test_evidence_expectations_vorhanden(self) -> None:
        self._write_matrix()
        build_manual_runtime_failure_execution_preview(explicit_overwrite=True)
        data = json.loads(_OUT.read_text(encoding="utf-8"))
        self.assertTrue(
            all(isinstance(c.get("evidence_expectations"), list) and len(c["evidence_expectations"]) > 0 for c in data["preview_cases"])
        )

    def test_keine_produktiven_targets(self) -> None:
        self._write_matrix()
        build_manual_runtime_failure_execution_preview(explicit_overwrite=True)
        data = json.loads(_OUT.read_text(encoding="utf-8"))
        payload = json.dumps(data).lower()
        self.assertNotIn("/dev/nvme0n1", payload)
        self.assertNotIn("productive_internal_system_partition", payload)

    def test_atomisches_schreiben(self) -> None:
        self._write_matrix()
        build_manual_runtime_failure_execution_preview(explicit_overwrite=True)
        self.assertFalse(any(p.name.endswith(".tmp") for p in _HANDOFF.iterdir()))

    def test_no_forbidden_systemcalls(self) -> None:
        src = (_REPO_ROOT / "backend/deploy/runner_manual_runtime_failure_execution_preview.py").read_text(
            encoding="utf-8"
        ).lower()
        for token in ["subprocess", "os.system", "mkfs", " dd ", "wipefs", "rm -rf", "restore "]:
            self.assertNotIn(token, src)

    def test_no_execute_subroutes(self) -> None:
        routes = read_deploy_routes_aggregate()
        self.assertIn("/runner/manual-runtime/failure-execution-preview", routes)
        for forbidden in [
            "/runner/manual-runtime/failure-execution-preview/execute",
            "/runner/manual-runtime/failure-execution-preview/apply",
            "/runner/manual-runtime/failure-execution-preview/install",
            "/runner/manual-runtime/failure-execution-preview/delete",
            "/runner/manual-runtime/failure-execution-preview/release",
        ]:
            self.assertNotIn(forbidden, routes)


if __name__ == "__main__":
    unittest.main()
