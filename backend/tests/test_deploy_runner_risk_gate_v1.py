"""Deploy runner risk gate Phase C.4 — policy only, no execution."""

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
    RunnerRegistryEntry,
    RunnerRiskLevel,
    build_runner_registry_from_files,
)
from deploy.runner_risk_gate import (
    RISK_GATE_VERSION,
    RunnerOperatorConfirmation,
    RunnerRiskDecision,
    build_risk_gate_summary,
    evaluate_registry_entry_risk,
    evaluate_runner_risk_gate,
    list_blocked_runners,
    list_operator_required_runners,
)


class DeployRunnerRiskGateV1Tests(unittest.TestCase):
    def test_no_runner_module_imports(self) -> None:
        src = (_BACKEND / "deploy" / "runner_risk_gate.py").read_text(encoding="utf-8")
        self.assertNotIn("subprocess", src)
        tree = ast.parse(src)
        allowed = {"deploy.runner_registry", "deploy.runner_result_contract"}
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                if node.module.startswith("deploy.runner_") and node.module not in allowed:
                    self.fail(node.module)

    def test_allowed_to_execute_always_false(self) -> None:
        entries = build_runner_registry_from_files(root=_BACKEND / "deploy")
        for entry in entries[:20]:
            d = evaluate_registry_entry_risk(entry)
            self.assertFalse(d.allowed_to_execute, entry.runner_id)

    def test_unknown_runner_blocked(self) -> None:
        d = evaluate_runner_risk_gate("runner_nonexistent_xyz")
        self.assertEqual(d.decision, RunnerRiskDecision.BLOCKED_UNKNOWN_RUNNER)
        self.assertFalse(d.allowed_to_execute)

    def test_destructive_never_auto_blocked(self) -> None:
        entries = build_runner_registry_from_files(root=_BACKEND / "deploy")
        destructive = [e for e in entries if e.risk_level == RunnerRiskLevel.DESTRUCTIVE]
        self.assertGreater(len(destructive), 0)
        d = evaluate_registry_entry_risk(destructive[0])
        self.assertEqual(d.decision, RunnerRiskDecision.BLOCKED_NEVER_AUTO)
        self.assertFalse(d.allowed_to_execute)

    def test_destructive_with_operator_still_no_execute(self) -> None:
        entries = build_runner_registry_from_files(root=_BACKEND / "deploy")
        destructive = [e for e in entries if e.risk_level == RunnerRiskLevel.DESTRUCTIVE][0]
        d = evaluate_registry_entry_risk(
            destructive,
            RunnerOperatorConfirmation(confirmed=True, operator_id="op1"),
        )
        self.assertFalse(d.allowed_to_execute)
        self.assertEqual(d.decision, RunnerRiskDecision.BLOCKED_NEVER_AUTO)

    def test_sudo_without_operator_blocked(self) -> None:
        entries = build_runner_registry_from_files(root=_BACKEND / "deploy")
        sudo_entries = [e for e in entries if e.uses_sudo and e.risk_level != RunnerRiskLevel.DESTRUCTIVE]
        self.assertGreater(len(sudo_entries), 0)
        d = evaluate_registry_entry_risk(sudo_entries[0])
        self.assertIn(
            d.decision,
            {RunnerRiskDecision.BLOCKED_OPERATOR_REQUIRED, RunnerRiskDecision.BLOCKED_NEVER_AUTO},
        )

    def test_read_only_plan_allowed(self) -> None:
        entries = build_runner_registry_from_files(root=_BACKEND / "deploy")
        ro = [e for e in entries if e.risk_level == RunnerRiskLevel.READ_ONLY]
        self.assertGreater(len(ro), 0)
        d = evaluate_registry_entry_risk(ro[0])
        self.assertEqual(d.decision, RunnerRiskDecision.ALLOWED_PLAN_ONLY)
        self.assertTrue(d.allowed_to_plan)

    def test_runtime_gate_false_blocks_elevated(self) -> None:
        entries = build_runner_registry_from_files(root=_BACKEND / "deploy")
        elevated = [
            e
            for e in entries
            if e.risk_level == RunnerRiskLevel.LOCAL_RUNTIME_CHANGE and not e.uses_sudo
        ]
        if not elevated:
            self.skipTest("no local_runtime_change sample")
        d = evaluate_registry_entry_risk(
            elevated[0],
            RunnerOperatorConfirmation(confirmed=True),
            {"runtime_gate_ok": False},
        )
        self.assertEqual(d.decision, RunnerRiskDecision.BLOCKED_OPERATOR_REQUIRED)

    def test_build_risk_gate_summary(self) -> None:
        entries = build_runner_registry_from_files(root=_BACKEND / "deploy")
        summary = build_risk_gate_summary(entries)
        self.assertEqual(summary["total"], len(entries))
        self.assertFalse(summary["allowed_to_execute_in_c4"])

    def test_list_operator_required_nonempty(self) -> None:
        entries = build_runner_registry_from_files(root=_BACKEND / "deploy")
        ids = list_operator_required_runners(entries)
        self.assertGreater(len(ids), 0)

    def test_list_blocked_runners(self) -> None:
        entries = build_runner_registry_from_files(root=_BACKEND / "deploy")
        blocked = list_blocked_runners(entries)
        self.assertGreater(len(blocked), 0)

    def test_risk_gate_version(self) -> None:
        self.assertEqual(RISK_GATE_VERSION, 1)


if __name__ == "__main__":
    unittest.main()
