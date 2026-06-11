"""Deploy runner result contract Phase C.2 — validation and normalization only."""

from __future__ import annotations

import ast
import sys
import unittest
from pathlib import Path

_BACKEND = Path(__file__).resolve().parent.parent
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

from deploy.runner_registry import (
    RunnerExecutionPolicy,
    RunnerRiskLevel,
    build_runner_registry_from_files,
    build_empty_result_for_registry_entry,
    validate_registry_result_contract,
)
from deploy.runner_result_contract import (
    CONTRACT_VERSION,
    RunnerMessage,
    RunnerResultKind,
    RunnerResultSeverity,
    RunnerResultStatus,
    build_runner_result,
    normalize_legacy_runner_result,
    summarize_runner_results,
    validate_runner_result,
)


class DeployRunnerResultContractV1Tests(unittest.TestCase):
    def test_valid_ok_result_accepted(self) -> None:
        result = build_runner_result(
            runner_id="runner_test",
            status=RunnerResultStatus.OK,
            kind=RunnerResultKind.STATIC_ANALYSIS,
            summary="ok",
            warnings=[],
            errors=[],
        )
        v = validate_runner_result(result.to_dict())
        self.assertTrue(v.valid, v.errors)

    def test_blocked_without_errors_rejected(self) -> None:
        result = build_runner_result(
            runner_id="runner_test",
            status=RunnerResultStatus.BLOCKED,
            kind=RunnerResultKind.READINESS_GATE,
            summary="blocked",
            errors=[],
        )
        v = validate_runner_result(result.to_dict())
        self.assertFalse(v.valid)
        self.assertTrue(any("blocked_requires_errors" in e for e in v.errors))

    def test_failed_without_errors_rejected(self) -> None:
        result = build_runner_result(
            runner_id="runner_test",
            status=RunnerResultStatus.FAILED,
            kind=RunnerResultKind.RUNTIME_OPERATION,
            summary="failed",
            errors=[],
        )
        v = validate_runner_result(result.to_dict())
        self.assertFalse(v.valid)

    def test_review_required_without_messages_rejected(self) -> None:
        result = build_runner_result(
            runner_id="runner_test",
            status=RunnerResultStatus.REVIEW_REQUIRED,
            kind=RunnerResultKind.MANUAL_PRECHECK,
            summary="review",
            warnings=[],
            errors=[],
        )
        v = validate_runner_result(result.to_dict())
        self.assertFalse(v.valid)

    def test_unknown_status_rejected(self) -> None:
        payload = build_runner_result(
            runner_id="runner_test",
            status=RunnerResultStatus.OK,
            kind=RunnerResultKind.UNKNOWN,
            summary="x",
            warnings=[RunnerMessage(code="W", message="w", severity=RunnerResultSeverity.WARNING)],
        ).to_dict()
        payload["status"] = "mystery"
        v = validate_runner_result(payload)
        self.assertFalse(v.valid)

    def test_absolute_evidence_path_rejected(self) -> None:
        result = build_runner_result(
            runner_id="runner_test",
            status=RunnerResultStatus.OK,
            kind=RunnerResultKind.EVIDENCE_GENERATION,
            summary="ev",
            evidence_paths=[{"path": "/opt/setuphelfer/secret.json"}],
            warnings=[RunnerMessage(code="W", message="w", severity=RunnerResultSeverity.WARNING)],
        )
        v = validate_runner_result(result.to_dict())
        self.assertFalse(v.valid)

    def test_env_path_rejected(self) -> None:
        payload = build_runner_result(
            runner_id="runner_test",
            status=RunnerResultStatus.OK,
            kind=RunnerResultKind.STATIC_ANALYSIS,
            summary="x",
            warnings=[RunnerMessage(code="W", message="w", severity=RunnerResultSeverity.WARNING)],
        ).to_dict()
        payload["evidence_paths"] = ["docs/.env"]
        v = validate_runner_result(payload)
        self.assertFalse(v.valid)

    def test_secret_metadata_rejected(self) -> None:
        payload = build_runner_result(
            runner_id="runner_test",
            status=RunnerResultStatus.OK,
            kind=RunnerResultKind.STATIC_ANALYSIS,
            summary="x",
            warnings=[RunnerMessage(code="W", message="w", severity=RunnerResultSeverity.WARNING)],
            metadata={"password": "x"},
        ).to_dict()
        v = validate_runner_result(payload)
        self.assertFalse(v.valid)

    def test_normalize_legacy_ok_status(self) -> None:
        norm = normalize_legacy_runner_result("runner_x", {"status": "ok", "summary": "legacy ok"})
        self.assertEqual(norm.status, RunnerResultStatus.OK)

    def test_unknown_legacy_status_not_ok(self) -> None:
        norm = normalize_legacy_runner_result("runner_x", {"status": "weird_status"})
        self.assertNotEqual(norm.status, RunnerResultStatus.OK)
        self.assertEqual(norm.status, RunnerResultStatus.REVIEW_REQUIRED)

    def test_destructive_requires_never_auto(self) -> None:
        payload = build_runner_result(
            runner_id="runner_usb",
            status=RunnerResultStatus.REVIEW_REQUIRED,
            kind=RunnerResultKind.DEVICE_OPERATION,
            summary="device",
            risk_level=RunnerRiskLevel.DESTRUCTIVE,
            execution_policy=RunnerExecutionPolicy.LAB_ONLY,
            requires_operator=True,
            warnings=[RunnerMessage(code="W", message="w", severity=RunnerResultSeverity.WARNING)],
        ).to_dict()
        v = validate_runner_result(payload)
        self.assertFalse(v.valid)

    def test_empty_registry_result_valid(self) -> None:
        entries = build_runner_registry_from_files(root=_BACKEND / "deploy")
        self.assertGreater(len(entries), 0)
        entry = entries[0]
        empty = build_empty_result_for_registry_entry(entry)
        v = validate_registry_result_contract(entry, empty)
        self.assertTrue(v.valid, v.errors)

    def test_summarize_runner_results(self) -> None:
        a = build_runner_result(
            runner_id="a",
            status=RunnerResultStatus.OK,
            kind=RunnerResultKind.STATIC_ANALYSIS,
            summary="a",
            warnings=[RunnerMessage(code="W", message="w", severity=RunnerResultSeverity.WARNING)],
        )
        b = build_runner_result(
            runner_id="b",
            status=RunnerResultStatus.FAILED,
            kind=RunnerResultKind.RUNTIME_OPERATION,
            summary="b",
            errors=[RunnerMessage(code="E", message="e", severity=RunnerResultSeverity.ERROR)],
        )
        summary = summarize_runner_results([a, b])
        self.assertEqual(summary["total"], 2)
        self.assertEqual(summary["by_status"]["ok"], 1)
        self.assertEqual(summary["by_status"]["failed"], 1)

    def test_no_runner_import_or_execution(self) -> None:
        src = (_BACKEND / "deploy" / "runner_result_contract.py").read_text(encoding="utf-8")
        tree = ast.parse(src)
        imports_runner_modules = any(
            isinstance(n, ast.ImportFrom) and n.module and "runner_" in n.module and n.module != "deploy.runner_registry"
            for n in ast.walk(tree)
        )
        self.assertFalse(imports_runner_modules)
        self.assertNotIn("importlib.import_module", src)

    def test_contract_version(self) -> None:
        self.assertEqual(CONTRACT_VERSION, 1)


if __name__ == "__main__":
    unittest.main()
