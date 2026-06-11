"""Deploy runner routes decoupling Phase C.5 — plan-only slice, no execution."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

_BACKEND = Path(__file__).resolve().parent.parent
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

from deploy.runner_api_facade import (
    DECOUPLED_ROUTE_RUNNER_IDS,
    assert_runner_plan_allowed,
    build_plan_only_response,
    clear_registry_cache,
)
from deploy.runner_registry import build_runner_registry_from_files
from deploy.runner_risk_gate import RunnerRiskDecision, evaluate_runner_risk_gate


class DeployRunnerRoutesDecouplingV1Tests(unittest.TestCase):
    def setUp(self) -> None:
        clear_registry_cache()

    def test_plan_only_response_uses_risk_gate(self) -> None:
        res = build_plan_only_response("runner_next_phase_gate")
        self.assertIn("risk_gate", res)
        self.assertEqual(res["risk_gate"]["decision"], RunnerRiskDecision.ALLOWED_PLAN_ONLY.value)
        self.assertTrue(res["facade_decoupling_c5"])

    def test_blocked_runner_not_plan_allowed(self) -> None:
        res = build_plan_only_response("runner_rescue_iso_build_execution_plan")
        self.assertIn(res["status"], {"blocked", "review_required"})
        self.assertFalse(res.get("allowed_to_execute", False))

    def test_allowed_plan_only_execute_false(self) -> None:
        res = build_plan_only_response("runner_version_governance")
        self.assertEqual(res["status"], "ok")
        self.assertFalse(res["allowed_to_execute"])
        self.assertFalse(res["risk_gate"]["allowed_to_execute"])

    def test_assert_runner_plan_allowed_raises_when_blocked(self) -> None:
        with self.assertRaises(ValueError):
            assert_runner_plan_allowed("runner_rescue_iso_build_execution_plan")

    def test_decoupled_slice_imports_removed_from_routes(self) -> None:
        routes_src = (_BACKEND / "deploy" / "routes.py").read_text(encoding="utf-8")
        removed = [
            "from deploy.runner_next_phase_gate import",
            "from deploy.runner_version_governance import",
            "from deploy.runner_version_source_of_truth_check import",
            "from deploy.runner_legacy_identifier_inventory import",
        ]
        for needle in removed:
            self.assertNotIn(needle, routes_src)
        self.assertIn("build_plan_only_response", routes_src)

    def test_no_new_unsafe_runners_post_routes(self) -> None:
        routes_src = (_BACKEND / "deploy" / "routes.py").read_text(encoding="utf-8")
        self.assertNotIn('@router.post("/runners/', routes_src)
        self.assertNotIn('@router.post("/runners/execute', routes_src)

    def test_routes_facade_no_subprocess(self) -> None:
        facade_src = (_BACKEND / "deploy" / "runner_api_facade.py").read_text(encoding="utf-8")
        self.assertNotIn("subprocess", facade_src)

    def test_decoupled_runner_ids_count(self) -> None:
        self.assertEqual(len(DECOUPLED_ROUTE_RUNNER_IDS), 4)

    def test_migrated_runners_allowed_plan_only(self) -> None:
        entries = build_runner_registry_from_files(root=_BACKEND / "deploy")
        for rid in DECOUPLED_ROUTE_RUNNER_IDS:
            d = evaluate_runner_risk_gate(rid, entries=entries)
            self.assertTrue(d.allowed_to_plan, rid)
            self.assertFalse(d.allowed_to_execute, rid)


if __name__ == "__main__":
    unittest.main()
