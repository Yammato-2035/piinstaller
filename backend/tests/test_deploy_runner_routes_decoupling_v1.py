"""Deploy runner routes decoupling Phase C.5/C.6 — plan-only slices, no execution."""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

_BACKEND = Path(__file__).resolve().parent.parent
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

from deploy.runner_api_facade import (
    DECOUPLED_ROUTE_RUNNER_IDS,
    DECOUPLED_ROUTE_RUNNER_IDS_C5,
    DECOUPLED_ROUTE_RUNNER_IDS_C6,
    DECOUPLED_ROUTE_RUNNER_IDS_D7,
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

    def test_c6_plan_only_response_tag(self) -> None:
        res = build_plan_only_response(
            "runner_manual_runtime_evidence_timeline",
            decoupling_phase="c6",
        )
        self.assertTrue(res["facade_decoupling_c6"])
        self.assertFalse(res["allowed_to_execute"])

    def test_d7_plan_only_response_tag(self) -> None:
        res = build_plan_only_response(
            "runner_legacy_identifier_cleanup_classifier",
            decoupling_phase="d7",
        )
        self.assertTrue(res["facade_decoupling_d7"])
        self.assertFalse(res["allowed_to_execute"])

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

    def test_c5_imports_removed_from_routes(self) -> None:
        routes_src = (_BACKEND / "deploy" / "routes.py").read_text(encoding="utf-8")
        for needle in (
            "from deploy.runner_next_phase_gate import",
            "from deploy.runner_version_governance import",
            "from deploy.runner_version_source_of_truth_check import",
            "from deploy.runner_legacy_identifier_inventory import",
        ):
            self.assertNotIn(needle, routes_src)

    def test_c6_imports_removed_from_routes(self) -> None:
        routes_src = (_BACKEND / "deploy" / "routes.py").read_text(encoding="utf-8")
        for needle in (
            "from deploy.runner_legacy_identifier_hotspot_analysis import",
            "from deploy.runner_setuphelfer_identifier_consistency_check import",
            "from deploy.runner_manual_runtime_evidence_timeline import",
            "from deploy.runner_manual_runtime_evidence_final_snapshot import",
            "from deploy.runner_manual_runtime_validator_seal_index import",
        ):
            self.assertNotIn(needle, routes_src)
        combined = routes_src + (_BACKEND / "deploy" / "routes_evidence.py").read_text(encoding="utf-8")
        combined += (_BACKEND / "deploy" / "routes_governance.py").read_text(encoding="utf-8")
        self.assertIn('decoupling_phase="c6"', combined)

    def test_d7_imports_removed_from_routes(self) -> None:
        routes_src = (_BACKEND / "deploy" / "routes.py").read_text(encoding="utf-8")
        for needle in (
            "from deploy.runner_legacy_identifier_cleanup_classifier import",
            "from deploy.runner_manual_runtime_failure_test_result_capture import",
            "from deploy.runner_manual_runtime_failure_result_evaluation import",
            "from deploy.runner_manual_runtime_validator_seal_consistency_audit import",
        ):
            self.assertNotIn(needle, routes_src)
        ev = (_BACKEND / "deploy" / "routes_evidence.py").read_text(encoding="utf-8")
        self.assertIn('decoupling_phase="d7"', ev)
        self.assertNotIn("classify_active_legacy_identifiers", routes_src)

    def test_d8_imports_removed_from_routes(self) -> None:
        routes_src = (_BACKEND / "deploy" / "routes.py").read_text(encoding="utf-8")
        for needle in (
            "from deploy.runner_manual_runtime_failure_injection_matrix import",
            "from deploy.runner_manual_runtime_failure_execution_preview import",
            "from deploy.runner_manual_runtime_failure_operator_checklists import",
            "from deploy.runner_manual_runtime_failure_test_sessions import",
            "from deploy.runner_manual_runtime_failure_readiness_gate import",
            "from deploy.runner_runtime_identifier_zero_state_verification import",
        ):
            self.assertNotIn(needle, routes_src)
        diag = (_BACKEND / "deploy" / "routes_diagnostics.py").read_text(encoding="utf-8")
        self.assertIn('decoupling_phase="d8"', diag)

    def test_d8_plan_only_response_tag(self) -> None:
        res = build_plan_only_response(
            "runner_manual_runtime_failure_readiness_gate",
            decoupling_phase="d8",
        )
        self.assertTrue(res["facade_decoupling_d8"])
        self.assertFalse(res["allowed_to_execute"])

    def test_direct_import_count_reduced(self) -> None:
        routes_src = (_BACKEND / "deploy" / "routes.py").read_text(encoding="utf-8")
        count = len(re.findall(r"^from deploy\.runner_", routes_src, flags=re.M))
        self.assertEqual(count, 77)

    def test_no_new_unsafe_runners_post_routes(self) -> None:
        routes_src = (_BACKEND / "deploy" / "routes.py").read_text(encoding="utf-8")
        self.assertNotIn('@router.post("/runners/', routes_src)

    def test_routes_facade_no_subprocess(self) -> None:
        facade_src = (_BACKEND / "deploy" / "runner_api_facade.py").read_text(encoding="utf-8")
        self.assertNotIn("subprocess", facade_src)

    def test_decoupled_runner_ids_count(self) -> None:
        self.assertEqual(len(DECOUPLED_ROUTE_RUNNER_IDS_C5), 4)
        self.assertEqual(len(DECOUPLED_ROUTE_RUNNER_IDS_C6), 5)
        self.assertEqual(len(DECOUPLED_ROUTE_RUNNER_IDS_D7), 5)
        self.assertEqual(len(DECOUPLED_ROUTE_RUNNER_IDS), 14)

    def test_all_decoupled_runners_allowed_plan_only(self) -> None:
        entries = build_runner_registry_from_files(root=_BACKEND / "deploy")
        for rid in DECOUPLED_ROUTE_RUNNER_IDS:
            d = evaluate_runner_risk_gate(rid, entries=entries)
            self.assertTrue(d.allowed_to_plan, rid)
            self.assertFalse(d.allowed_to_execute, rid)


if __name__ == "__main__":
    unittest.main()
