"""Deploy registry router extraction Phase D.2 — read-only, no runner execution."""

from __future__ import annotations

import ast
import re
import sys
import unittest
from pathlib import Path

_BACKEND = Path(__file__).resolve().parent.parent
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

from deploy.routes_registry import router as registry_router

EXPECTED_PUBLIC_PATHS = (
    "/api/deploy/runners/catalog",
    "/api/deploy/runners/summary",
    "/api/deploy/runners/policy-warnings",
    "/api/deploy/runners/{runner_id}",
    "/api/deploy/runners/{runner_id}/empty-result",
)


class DeployRoutesRegistryV1Tests(unittest.TestCase):
    def test_registry_module_no_runner_imports(self) -> None:
        src = (_BACKEND / "deploy" / "routes_registry.py").read_text(encoding="utf-8")
        self.assertNotIn("subprocess", src)
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                if node.module.startswith("deploy.runner_") and node.module != "deploy.runner_api_facade":
                    self.fail(f"unexpected runner import: {node.module}")

    def test_registry_router_only_get_routes(self) -> None:
        for route in registry_router.routes:
            self.assertEqual(route.methods, {"GET"}, msg=f"unexpected methods on {route.path}")
        self.assertEqual(len(registry_router.routes), 5)

    def test_registry_router_uses_facade(self) -> None:
        src = (_BACKEND / "deploy" / "routes_registry.py").read_text(encoding="utf-8")
        self.assertIn("from deploy.runner_api_facade import", src)
        for fn in (
            "build_runner_catalog",
            "build_runner_catalog_summary",
            "build_runner_policy_warnings",
            "get_runner_registry_entry",
            "get_runner_empty_result",
        ):
            self.assertIn(fn, src)

    def test_public_paths_unchanged(self) -> None:
        paths = sorted({route.path for route in registry_router.routes})
        self.assertEqual(
            paths,
            [
                "/runners/catalog",
                "/runners/policy-warnings",
                "/runners/summary",
                "/runners/{runner_id}",
                "/runners/{runner_id}/empty-result",
            ],
        )
        deploy_routes = (_BACKEND / "deploy" / "routes.py").read_text(encoding="utf-8")
        self.assertIn("deploy_registry_router", deploy_routes)
        self.assertIn("router.include_router(deploy_registry_router)", deploy_routes)
        for full in EXPECTED_PUBLIC_PATHS:
            suffix = full.removeprefix("/api/deploy")
            self.assertTrue(
                suffix in paths or any(p.endswith(suffix.split("{")[0].rstrip("/")) for p in paths),
                msg=f"missing path suffix for {full}",
            )

    def test_routes_py_no_duplicate_registry_handlers(self) -> None:
        routes_src = (_BACKEND / "deploy" / "routes.py").read_text(encoding="utf-8")
        self.assertNotIn("def get_deploy_runners_catalog", routes_src)
        self.assertNotIn("def get_deploy_runners_summary", routes_src)
        self.assertNotIn("def get_deploy_runner_registry_entry", routes_src)
        self.assertNotIn('@router.get("/runners/catalog")', routes_src)
        self.assertNotIn('@router.get("/runners/risk-gate/summary")', routes_src)
        self.assertIn("include_router(deploy_risk_gate_router)", routes_src)

    def test_routes_py_registry_facade_imports_trimmed(self) -> None:
        routes_src = (_BACKEND / "deploy" / "routes.py").read_text(encoding="utf-8")
        self.assertNotIn("build_runner_catalog", routes_src)
        self.assertNotIn("get_runner_registry_entry", routes_src)
        self.assertNotIn("build_runner_risk_gate_summary", routes_src)

    def test_runner_import_count_unchanged(self) -> None:
        routes_src = (_BACKEND / "deploy" / "routes.py").read_text(encoding="utf-8")
        count = len(re.findall(r"^from deploy\.runner_", routes_src, flags=re.M))
        self.assertEqual(count, 99)
