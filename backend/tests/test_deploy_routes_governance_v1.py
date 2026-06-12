"""Deploy governance router extraction Phase D.5 — plan-only, no runner execution."""

from __future__ import annotations

import ast
import re
import sys
import unittest
from pathlib import Path

_BACKEND = Path(__file__).resolve().parent.parent
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

from deploy.routes_governance import router as governance_router

D5_RUNNER_IDS = (
    "runner_next_phase_gate",
    "runner_version_governance",
    "runner_version_source_of_truth_check",
)

D5_PUBLIC_PATHS = (
    "/api/deploy/runner/next-phase/gate",
    "/api/deploy/version-governance/state",
    "/api/deploy/version-source-of-truth-check",
)


class DeployRoutesGovernanceV1Tests(unittest.TestCase):
    def test_governance_module_no_runner_imports(self) -> None:
        src = (_BACKEND / "deploy" / "routes_governance.py").read_text(encoding="utf-8")
        self.assertNotIn("subprocess", src)
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                if node.module.startswith("deploy.runner_") and node.module != "deploy.runner_api_facade":
                    self.fail(f"unexpected runner import: {node.module}")

    def test_governance_router_route_count(self) -> None:
        self.assertEqual(len(governance_router.routes), 3)
        for route in governance_router.routes:
            self.assertEqual(route.methods, {"POST"})

    def test_governance_router_uses_build_plan_only_response(self) -> None:
        src = (_BACKEND / "deploy" / "routes_governance.py").read_text(encoding="utf-8")
        self.assertEqual(src.count("build_plan_only_response("), 3)
        for rid in D5_RUNNER_IDS:
            self.assertIn(f'"{rid}"', src)

    def test_no_execute_apply_write_routes(self) -> None:
        src = (_BACKEND / "deploy" / "routes_governance.py").read_text(encoding="utf-8")
        for bad in ("execute", "apply", "install", "write", "delete"):
            self.assertNotRegex(src, rf'@router\.post\("[^"]*{bad}')

    def test_public_paths_unchanged(self) -> None:
        paths = sorted({route.path for route in governance_router.routes})
        self.assertEqual(
            paths,
            [
                "/runner/next-phase/gate",
                "/version-governance/state",
                "/version-source-of-truth-check",
            ],
        )
        routes_src = (_BACKEND / "deploy" / "routes.py").read_text(encoding="utf-8")
        self.assertIn("include_router(deploy_governance_router)", routes_src)

    def test_routes_py_no_duplicate_governance_handlers(self) -> None:
        routes_src = (_BACKEND / "deploy" / "routes.py").read_text(encoding="utf-8")
        self.assertNotIn("def post_deploy_runner_next_phase_gate", routes_src)
        self.assertNotIn("def post_deploy_version_governance_state", routes_src)
        self.assertNotIn('@router.post("/version-governance/state")', routes_src)
        self.assertNotIn("build_plan_only_response", routes_src)

    def test_allowed_to_execute_stays_false(self) -> None:
        from deploy.runner_api_facade import build_plan_only_response, clear_registry_cache

        clear_registry_cache()
        res = build_plan_only_response("runner_version_governance")
        self.assertFalse(res["allowed_to_execute"])
        self.assertTrue(res["facade_decoupling_c5"])

    def test_runner_import_count_unchanged(self) -> None:
        routes_src = (_BACKEND / "deploy" / "routes.py").read_text(encoding="utf-8")
        count = len(re.findall(r"^from deploy\.runner_", routes_src, flags=re.M))
        self.assertEqual(count, 81)
