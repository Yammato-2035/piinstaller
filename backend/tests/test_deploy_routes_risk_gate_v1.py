"""Deploy risk-gate router extraction Phase D.3 — read-only, no runner execution."""

from __future__ import annotations

import ast
import re
import sys
import unittest
from pathlib import Path

_BACKEND = Path(__file__).resolve().parent.parent
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

from deploy.runner_api_facade import build_runner_risk_gate_summary, get_runner_risk_gate_decision
from deploy.routes_risk_gate import router as risk_gate_router

EXPECTED_PUBLIC_PATHS = (
    "/api/deploy/runners/risk-gate/summary",
    "/api/deploy/runners/risk-gate/operator-required",
    "/api/deploy/runners/risk-gate/never-auto",
    "/api/deploy/runners/risk-gate/plan-allowed",
    "/api/deploy/runners/{runner_id}/risk-gate",
)


class DeployRoutesRiskGateV1Tests(unittest.TestCase):
    def test_risk_gate_module_no_runner_imports(self) -> None:
        src = (_BACKEND / "deploy" / "routes_risk_gate.py").read_text(encoding="utf-8")
        self.assertNotIn("subprocess", src)
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                if node.module.startswith("deploy.runner_") and node.module != "deploy.runner_api_facade":
                    self.fail(f"unexpected runner import: {node.module}")

    def test_risk_gate_router_only_get_routes(self) -> None:
        for route in risk_gate_router.routes:
            self.assertEqual(route.methods, {"GET"}, msg=f"unexpected methods on {route.path}")
        self.assertEqual(len(risk_gate_router.routes), 5)

    def test_risk_gate_router_uses_facade(self) -> None:
        src = (_BACKEND / "deploy" / "routes_risk_gate.py").read_text(encoding="utf-8")
        self.assertIn("from deploy.runner_api_facade import", src)
        for fn in (
            "build_runner_risk_gate_summary",
            "list_runner_operator_required",
            "list_runner_never_auto",
            "list_runner_plan_allowed",
            "get_runner_risk_gate_decision",
        ):
            self.assertIn(fn, src)

    def test_public_paths_unchanged(self) -> None:
        paths = sorted({route.path for route in risk_gate_router.routes})
        self.assertEqual(
            paths,
            [
                "/runners/risk-gate/never-auto",
                "/runners/risk-gate/operator-required",
                "/runners/risk-gate/plan-allowed",
                "/runners/risk-gate/summary",
                "/runners/{runner_id}/risk-gate",
            ],
        )
        deploy_routes = (_BACKEND / "deploy" / "routes.py").read_text(encoding="utf-8")
        self.assertIn("deploy_risk_gate_router", deploy_routes)
        self.assertIn("router.include_router(deploy_risk_gate_router)", deploy_routes)

    def test_routes_py_no_duplicate_risk_gate_handlers(self) -> None:
        routes_src = (_BACKEND / "deploy" / "routes.py").read_text(encoding="utf-8")
        self.assertNotIn("def get_deploy_runners_risk_gate_summary", routes_src)
        self.assertNotIn("def get_deploy_runner_risk_gate", routes_src)
        self.assertNotIn('@router.get("/runners/risk-gate/summary")', routes_src)
        self.assertNotIn("build_runner_risk_gate_summary", routes_src)

    def test_allowed_to_execute_stays_false(self) -> None:
        summary = build_runner_risk_gate_summary()
        self.assertFalse(summary["data"]["allowed_to_execute_in_c4"])
        decision = get_runner_risk_gate_decision("runner_next_phase_gate")
        self.assertFalse(decision["data"]["allowed_to_execute"])

    def test_runner_import_count_unchanged(self) -> None:
        routes_src = (_BACKEND / "deploy" / "routes.py").read_text(encoding="utf-8")
        count = len(re.findall(r"^from deploy\.runner_", routes_src, flags=re.M))
        self.assertEqual(count, 104)
