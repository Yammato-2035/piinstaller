"""Deploy diagnostics router extraction Phase D.8 — plan-only, no runner execution."""

from __future__ import annotations

import ast
import re
import sys
import unittest
from pathlib import Path

_BACKEND = Path(__file__).resolve().parent.parent
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

from deploy.routes_diagnostics import router as diagnostics_router

D8_RUNNER_IDS = (
    "runner_manual_runtime_failure_injection_matrix",
    "runner_manual_runtime_failure_execution_preview",
    "runner_manual_runtime_failure_operator_checklists",
    "runner_manual_runtime_failure_test_sessions",
    "runner_manual_runtime_failure_readiness_gate",
    "runner_runtime_identifier_zero_state_verification",
)

D8_PUBLIC_PATHS = (
    "/runner/manual-runtime/failure-injection-matrix",
    "/runner/manual-runtime/failure-execution-preview",
    "/runner/manual-runtime/failure-operator-checklists",
    "/runner/manual-runtime/failure-test-sessions",
    "/runner/manual-runtime/failure-readiness-gate",
    "/runtime-identifier-zero-state-verification",
)


class DeployRoutesDiagnosticsV1Tests(unittest.TestCase):
    def test_diagnostics_module_no_runner_imports(self) -> None:
        src = (_BACKEND / "deploy" / "routes_diagnostics.py").read_text(encoding="utf-8")
        self.assertNotIn("subprocess", src)
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                if node.module.startswith("deploy.runner_") and node.module != "deploy.runner_api_facade":
                    self.fail(f"unexpected runner import: {node.module}")

    def test_diagnostics_router_route_count(self) -> None:
        self.assertEqual(len(diagnostics_router.routes), 6)
        for route in diagnostics_router.routes:
            self.assertEqual(route.methods, {"POST"})

    def test_diagnostics_router_uses_build_plan_only_response(self) -> None:
        src = (_BACKEND / "deploy" / "routes_diagnostics.py").read_text(encoding="utf-8")
        self.assertEqual(src.count("build_plan_only_response("), 6)
        for rid in D8_RUNNER_IDS:
            self.assertIn(f'"{rid}"', src)
        self.assertEqual(src.count('decoupling_phase="d8"'), 6)

    def test_no_execute_apply_write_routes(self) -> None:
        src = (_BACKEND / "deploy" / "routes_diagnostics.py").read_text(encoding="utf-8")
        for bad in ("execute", "apply", "install", "write", "delete"):
            self.assertNotRegex(src, rf'@router\.post\("[^"]*{bad}')

    def test_public_paths_unchanged(self) -> None:
        paths = sorted({route.path for route in diagnostics_router.routes})
        self.assertEqual(paths, sorted(D8_PUBLIC_PATHS))
        routes_src = (_BACKEND / "deploy" / "routes.py").read_text(encoding="utf-8")
        self.assertIn("include_router(deploy_diagnostics_router)", routes_src)

    def test_routes_py_no_duplicate_d8_handlers(self) -> None:
        routes_src = (_BACKEND / "deploy" / "routes.py").read_text(encoding="utf-8")
        for path in D8_PUBLIC_PATHS:
            self.assertNotIn(f'@router.post("{path}")', routes_src)

    def test_allowed_to_execute_stays_false(self) -> None:
        from deploy.runner_api_facade import build_plan_only_response, clear_registry_cache

        clear_registry_cache()
        for rid in D8_RUNNER_IDS:
            res = build_plan_only_response(rid, decoupling_phase="d8")
            self.assertFalse(res["allowed_to_execute"], rid)
            self.assertTrue(res["facade_decoupling_d8"])

    def test_runner_import_count_reduced(self) -> None:
        routes_src = (_BACKEND / "deploy" / "routes.py").read_text(encoding="utf-8")
        count = len(re.findall(r"^from deploy\.runner_", routes_src, flags=re.M))
        self.assertEqual(count, 81)
