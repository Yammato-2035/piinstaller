"""Deploy versioning router extraction Phase D.10 — plan-only, no runner execution."""

from __future__ import annotations

import ast
import re
import sys
import unittest
from pathlib import Path

_BACKEND = Path(__file__).resolve().parent.parent
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

from deploy.routes_versioning import router as versioning_router

D10_RUNNER_IDS = (
    "runner_setuphelfer_runtime_identifier_migration",
    "runner_setuphelfer_safe_rewrite_plan",
    "runner_setuphelfer_runtime_identifier_elimination",
    "runner_runtime_identifier_patch_bump_preparation",
    "runner_legacy_runtime_compatibility_validation",
)

D10_PUBLIC_PATHS = (
    "/setuphelfer-runtime-identifier-migration",
    "/setuphelfer-safe-rewrite-plan",
    "/runtime-identifier-elimination-targets",
    "/runtime-identifier-elimination-plan",
    "/runtime-compatibility-alias-validation",
    "/runtime-identifier-patch-bump-preparation",
    "/legacy-runtime-safe-migration-recommendations",
    "/legacy-upgrade-path-matrix",
)


class DeployRoutesVersioningV1Tests(unittest.TestCase):
    def test_versioning_module_no_runner_imports(self) -> None:
        src = (_BACKEND / "deploy" / "routes_versioning.py").read_text(encoding="utf-8")
        self.assertNotIn("subprocess", src)
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                if node.module.startswith("deploy.runner_") and node.module != "deploy.runner_api_facade":
                    self.fail(f"unexpected runner import: {node.module}")

    def test_versioning_router_route_count(self) -> None:
        self.assertEqual(len(versioning_router.routes), 8)
        for route in versioning_router.routes:
            self.assertEqual(route.methods, {"POST"})

    def test_versioning_router_uses_build_plan_only_response(self) -> None:
        src = (_BACKEND / "deploy" / "routes_versioning.py").read_text(encoding="utf-8")
        self.assertEqual(src.count("build_plan_only_response("), 8)
        self.assertEqual(src.count('decoupling_phase="d10"'), 8)

    def test_no_execute_apply_write_routes(self) -> None:
        src = (_BACKEND / "deploy" / "routes_versioning.py").read_text(encoding="utf-8")
        for route in versioning_router.routes:
            pl = route.path.lower()
            self.assertNotIn("execute", pl)
            self.assertNotIn("apply", pl)
            self.assertNotIn("install", pl)
            self.assertNotIn("delete", pl)
            if pl != "/setuphelfer-safe-rewrite-plan":
                self.assertNotIn("/write", pl)
                self.assertFalse(pl.endswith("-write"))

    def test_public_paths_unchanged(self) -> None:
        paths = sorted({route.path for route in versioning_router.routes})
        self.assertEqual(paths, sorted(D10_PUBLIC_PATHS))
        routes_src = (_BACKEND / "deploy" / "routes.py").read_text(encoding="utf-8")
        self.assertIn("include_router(deploy_versioning_router)", routes_src)

    def test_routes_py_no_duplicate_d10_handlers(self) -> None:
        routes_src = (_BACKEND / "deploy" / "routes.py").read_text(encoding="utf-8")
        for path in D10_PUBLIC_PATHS:
            self.assertNotIn(f'@router.post("{path}")', routes_src)

    def test_allowed_to_execute_stays_false(self) -> None:
        from deploy.runner_api_facade import build_plan_only_response, clear_registry_cache

        clear_registry_cache()
        for rid in (
            "runner_setuphelfer_runtime_identifier_migration",
            "runner_setuphelfer_safe_rewrite_plan",
            "runner_setuphelfer_runtime_identifier_elimination",
            "runner_runtime_identifier_patch_bump_preparation",
            "runner_legacy_runtime_compatibility_validation",
        ):
            res = build_plan_only_response(rid, decoupling_phase="d10")
            self.assertFalse(res["allowed_to_execute"], rid)
            self.assertTrue(res["facade_decoupling_d10"])

    def test_runner_import_count_reduced(self) -> None:
        routes_src = (_BACKEND / "deploy" / "routes.py").read_text(encoding="utf-8")
        count = len(re.findall(r"^from deploy\.runner_", routes_src, flags=re.M))
        self.assertEqual(count, 81)
