from __future__ import annotations

import json
import unittest
from pathlib import Path

from deploy.runner_manual_runtime_failure_injection_matrix import _FAILURE_CASES
from deploy.runner_manual_runtime_failure_operator_checklists import build_manual_runtime_failure_operator_checklists
from deploy.routes_source_aggregate import read_deploy_routes_aggregate

_REPO_ROOT = Path(__file__).resolve().parents[2]
_HANDOFF = _REPO_ROOT / "docs/evidence/runtime-results/handoff"
_PREVIEW = _HANDOFF / "failure_execution_preview.json"
_OUT = _HANDOFF / "failure_operator_checklists.json"


class DeployRunnerManualRuntimeFailureOperatorChecklistsV1Tests(unittest.TestCase):
    def setUp(self) -> None:
        _HANDOFF.mkdir(parents=True, exist_ok=True)
        _PREVIEW.unlink(missing_ok=True)
        _OUT.unlink(missing_ok=True)
        for tmp in _HANDOFF.glob("*.tmp"):
            tmp.unlink(missing_ok=True)

    def tearDown(self) -> None:
        self.setUp()

    def _write_preview(self) -> None:
        _PREVIEW.write_text(
            json.dumps(
                {
                    "preview_schema_version": 1,
                    "strict_mode": "real_laptop_failure_execution_preview",
                    "generated_at": "2026-05-08T12:00:00Z",
                    "preview_cases": [
                        {
                            "failure_type": str(c["failure_type"]),
                            "execution_mode": "manual_preview_only",
                            "required_media": ["external_usb_test_drive"],
                            "required_preconditions": ["non_production_test_environment_confirmed"],
                            "expected_detection_layer": str(c["expected_detection_layer"]),
                            "expected_runtime_status": str(c["expected_status"]),
                            "rollback_required": str(c["failure_type"]).startswith("interrupted_"),
                            "destructive": False,
                            "operator_steps": ["manual step"],
                            "evidence_expectations": ["expectation"],
                        }
                        for c in _FAILURE_CASES
                    ],
                    "warnings": [],
                    "blocked_reasons": [],
                }
            ),
            encoding="utf-8",
        )

    def test_checklisten_erzeugbar(self) -> None:
        self._write_preview()
        out = build_manual_runtime_failure_operator_checklists(explicit_overwrite=True)
        self.assertEqual(out["checklist_status"], "ok")
        self.assertTrue(_OUT.is_file())

    def test_alle_failure_typen_vorhanden(self) -> None:
        self._write_preview()
        build_manual_runtime_failure_operator_checklists(explicit_overwrite=True)
        data = json.loads(_OUT.read_text(encoding="utf-8"))
        exp = {str(c["failure_type"]) for c in _FAILURE_CASES}
        got = {str(c.get("failure_type")) for c in data["checklists"]}
        self.assertEqual(got, exp)

    def test_destructive_immer_false(self) -> None:
        self._write_preview()
        build_manual_runtime_failure_operator_checklists(explicit_overwrite=True)
        data = json.loads(_OUT.read_text(encoding="utf-8"))
        self.assertTrue(all(bool(c.get("destructive")) is False for c in data["checklists"]))

    def test_operator_checklist_vorhanden(self) -> None:
        self._write_preview()
        build_manual_runtime_failure_operator_checklists(explicit_overwrite=True)
        data = json.loads(_OUT.read_text(encoding="utf-8"))
        self.assertTrue(all(isinstance(c.get("operator_checklist"), list) and len(c["operator_checklist"]) > 0 for c in data["checklists"]))

    def test_abort_conditions_vorhanden(self) -> None:
        self._write_preview()
        build_manual_runtime_failure_operator_checklists(explicit_overwrite=True)
        data = json.loads(_OUT.read_text(encoding="utf-8"))
        self.assertTrue(all(isinstance(c.get("abort_conditions"), list) and len(c["abort_conditions"]) > 0 for c in data["checklists"]))

    def test_required_evidence_vorhanden(self) -> None:
        self._write_preview()
        build_manual_runtime_failure_operator_checklists(explicit_overwrite=True)
        data = json.loads(_OUT.read_text(encoding="utf-8"))
        self.assertTrue(all(isinstance(c.get("required_evidence"), list) and len(c["required_evidence"]) > 0 for c in data["checklists"]))

    def test_keine_produktiven_targets(self) -> None:
        self._write_preview()
        build_manual_runtime_failure_operator_checklists(explicit_overwrite=True)
        payload = _OUT.read_text(encoding="utf-8").lower()
        self.assertNotIn("/dev/nvme0n1", payload)
        self.assertNotIn("productive_system_partition", payload)

    def test_atomisches_schreiben(self) -> None:
        self._write_preview()
        build_manual_runtime_failure_operator_checklists(explicit_overwrite=True)
        self.assertFalse(any(p.name.endswith(".tmp") for p in _HANDOFF.iterdir()))

    def test_no_forbidden_systemcalls(self) -> None:
        src = (_REPO_ROOT / "backend/deploy/runner_manual_runtime_failure_operator_checklists.py").read_text(
            encoding="utf-8"
        ).lower()
        for token in ["subprocess", "os.system", "mkfs", " dd ", "wipefs", "restore ", "rm -rf"]:
            self.assertNotIn(token, src)

    def test_no_execute_subroutes(self) -> None:
        routes = read_deploy_routes_aggregate()
        self.assertIn("/runner/manual-runtime/failure-operator-checklists", routes)
        for forbidden in [
            "/runner/manual-runtime/failure-operator-checklists/execute",
            "/runner/manual-runtime/failure-operator-checklists/apply",
            "/runner/manual-runtime/failure-operator-checklists/install",
            "/runner/manual-runtime/failure-operator-checklists/delete",
            "/runner/manual-runtime/failure-operator-checklists/release",
        ]:
            self.assertNotIn(forbidden, routes)


if __name__ == "__main__":
    unittest.main()
