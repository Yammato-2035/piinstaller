"""Deploy routes orchestrator structure Phase D.6 — analysis only, no execution."""

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
from deploy.routes_evidence import router as evidence_router
from deploy.routes_governance import router as governance_router
from deploy.routes_registry import router as registry_router
from deploy.routes_risk_gate import router as risk_gate_router
from deploy.routes_runtime import router as runtime_router
from deploy.routes_versioning import router as versioning_router

SUBROUTER_MODULES = (
    "routes_registry.py",
    "routes_risk_gate.py",
    "routes_evidence.py",
    "routes_governance.py",
    "routes_diagnostics.py",
    "routes_versioning.py",
    "routes_runtime.py",
)

UNSAFE_PATH_FRAGMENTS = ("execute", "apply", "install", "write", "delete")


class DeployRoutesOrchestratorStructureV1Tests(unittest.TestCase):
    def test_subrouter_modules_exist(self) -> None:
        for name in SUBROUTER_MODULES:
            self.assertTrue((_BACKEND / "deploy" / name).is_file(), name)

    def test_routes_py_includes_all_subrouters(self) -> None:
        src = (_BACKEND / "deploy" / "routes.py").read_text(encoding="utf-8")
        for needle in (
            "include_router(deploy_registry_router)",
            "include_router(deploy_risk_gate_router)",
            "include_router(deploy_evidence_router)",
            "include_router(deploy_governance_router)",
            "include_router(deploy_diagnostics_router)",
            "include_router(deploy_versioning_router)",
            "include_router(deploy_runtime_router)",
        ):
            self.assertIn(needle, src)

    def test_subrouter_route_counts(self) -> None:
        self.assertEqual(len(registry_router.routes), 5)
        self.assertEqual(len(risk_gate_router.routes), 5)
        self.assertEqual(len(evidence_router.routes), 12)
        self.assertEqual(len(governance_router.routes), 3)
        self.assertEqual(len(diagnostics_router.routes), 6)
        self.assertEqual(len(versioning_router.routes), 8)
        self.assertEqual(len(runtime_router.routes), 8)

    def test_subrouters_no_runner_py_imports(self) -> None:
        for name in SUBROUTER_MODULES:
            src = (_BACKEND / "deploy" / name).read_text(encoding="utf-8")
            tree = ast.parse(src)
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and node.module:
                    if node.module.startswith("deploy.runner_") and node.module != "deploy.runner_api_facade":
                        self.fail(f"{name}: unexpected {node.module}")

    def test_subrouters_no_unsafe_routes(self) -> None:
        for router in (
            registry_router,
            risk_gate_router,
            evidence_router,
            governance_router,
            diagnostics_router,
            versioning_router,
            runtime_router,
        ):
            for route in router.routes:
                pl = route.path.lower()
                for frag in UNSAFE_PATH_FRAGMENTS:
                    if frag == "write" and pl == "/setuphelfer-safe-rewrite-plan":
                        continue
                    self.assertNotIn(frag, pl, msg=f"unsafe fragment in {route.path}")

    def test_decoupled_plan_routes_allowed_to_execute_false(self) -> None:
        from deploy.runner_api_facade import build_plan_only_response, clear_registry_cache

        clear_registry_cache()
        for rid in (
            "runner_legacy_identifier_inventory",
            "runner_next_phase_gate",
            "runner_manual_runtime_evidence_timeline",
        ):
            phase = "c6" if "manual_runtime" in rid or "hotspot" in rid else None
            kwargs = {"decoupling_phase": phase} if phase else {}
            res = build_plan_only_response(rid, **kwargs)
            self.assertFalse(res["allowed_to_execute"], rid)

    def test_routes_py_runner_import_count_documented(self) -> None:
        src = (_BACKEND / "deploy" / "routes.py").read_text(encoding="utf-8")
        count = len(re.findall(r"^from deploy\.runner_", src, flags=re.M))
        self.assertEqual(count, 81)

    def test_no_build_plan_only_in_routes_py(self) -> None:
        src = (_BACKEND / "deploy" / "routes.py").read_text(encoding="utf-8")
        self.assertNotIn("build_plan_only_response", src)

    def test_subrouters_use_facade_only(self) -> None:
        for name in (
            "routes_evidence.py",
            "routes_governance.py",
            "routes_diagnostics.py",
            "routes_versioning.py",
            "routes_runtime.py",
        ):
            src = (_BACKEND / "deploy" / name).read_text(encoding="utf-8")
            self.assertIn("build_plan_only_response", src)
            self.assertIn("runner_api_facade", src)
