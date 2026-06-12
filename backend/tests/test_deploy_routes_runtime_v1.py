"""Deploy runtime router extraction Phase D.11 — read-only/plan-only, no runner execution."""

from __future__ import annotations

import ast
import re
import sys
import unittest
from pathlib import Path

_BACKEND = Path(__file__).resolve().parent.parent
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

from deploy.routes_runtime import router as runtime_router

D11_PUBLIC_PATHS = (
    "/runner/release/readiness",
    "/runner/lab-readiness/unblock-plan",
    "/runner/lab-readiness/status",
    "/runner/runtime-runbook/bundle",
    "/runner/runtime-runbook/export",
    "/runner/runtime-results/validate",
    "/runner/lab-readiness/acceptance",
    "/runner/lab-phase/consolidation",
)

D11_RUNNER_IDS = (
    "runner_release_readiness",
    "runner_lab_readiness_plan",
    "runner_lab_readiness_status",
    "runner_runtime_runbook_bundle",
    "runner_runtime_runbook_export",
    "runner_runtime_result_validator",
    "runner_lab_acceptance_aggregator",
    "runner_lab_phase_consolidation",
)


class DeployRoutesRuntimeV1Tests(unittest.TestCase):
    def test_runtime_module_no_runner_imports(self) -> None:
        src = (_BACKEND / "deploy" / "routes_runtime.py").read_text(encoding="utf-8")
        self.assertNotIn("subprocess", src)
        self.assertNotIn("systemctl", src)
        self.assertNotIn("sudo", src.lower().replace("sudoers", ""))
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                if node.module.startswith("deploy.runner_") and node.module != "deploy.runner_api_facade":
                    self.fail(f"unexpected runner import: {node.module}")

    def test_runtime_router_route_count(self) -> None:
        self.assertEqual(len(runtime_router.routes), 8)
        for route in runtime_router.routes:
            self.assertEqual(route.methods, {"POST"})

    def test_runtime_router_uses_build_plan_only_response(self) -> None:
        src = (_BACKEND / "deploy" / "routes_runtime.py").read_text(encoding="utf-8")
        self.assertEqual(src.count("build_plan_only_response("), 8)
        self.assertEqual(src.count('decoupling_phase="d11"'), 8)

    def test_no_unsafe_routes(self) -> None:
        for route in runtime_router.routes:
            pl = route.path.lower()
            for bad in ("execute", "apply", "install", "delete", "restart", "deploy"):
                self.assertNotIn(bad, pl, msg=route.path)
            if "/write" not in pl and not pl.endswith("-write"):
                pass

    def test_public_paths_unchanged(self) -> None:
        paths = sorted({route.path for route in runtime_router.routes})
        self.assertEqual(paths, sorted(D11_PUBLIC_PATHS))
        routes_src = (_BACKEND / "deploy" / "routes.py").read_text(encoding="utf-8")
        self.assertIn("include_router(deploy_runtime_router)", routes_src)

    def test_routes_py_no_duplicate_d11_handlers(self) -> None:
        routes_src = (_BACKEND / "deploy" / "routes.py").read_text(encoding="utf-8")
        for path in D11_PUBLIC_PATHS:
            self.assertNotIn(f'@router.post("{path}")', routes_src)

    def test_allowed_to_execute_stays_false(self) -> None:
        from deploy.runner_api_facade import build_plan_only_response, clear_registry_cache

        clear_registry_cache()
        for rid in D11_RUNNER_IDS:
            res = build_plan_only_response(rid, decoupling_phase="d11")
            self.assertFalse(res["allowed_to_execute"], rid)
            self.assertTrue(res["facade_decoupling_d11"])

    def test_runner_import_count_reduced(self) -> None:
        routes_src = (_BACKEND / "deploy" / "routes.py").read_text(encoding="utf-8")
        count = len(re.findall(r"^from deploy\.runner_", routes_src, flags=re.M))
        self.assertEqual(count, 81)
