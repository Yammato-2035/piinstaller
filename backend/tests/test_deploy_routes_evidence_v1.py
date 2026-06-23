"""Deploy evidence router extraction Phase D.4/D.7 — plan-only, no runner execution."""

from __future__ import annotations

import ast
import re
import sys
import unittest
from pathlib import Path

_BACKEND = Path(__file__).resolve().parent.parent
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

from deploy.routes_evidence import router as evidence_router

D4_RUNNER_IDS = (
    "runner_legacy_identifier_inventory",
    "runner_legacy_identifier_hotspot_analysis",
    "runner_setuphelfer_identifier_consistency_check",
    "runner_manual_runtime_validator_seal_index",
    "runner_manual_runtime_evidence_timeline",
    "runner_manual_runtime_evidence_final_snapshot",
)

D7_RUNNER_IDS = (
    "runner_legacy_identifier_cleanup_classifier",
    "runner_legacy_runtime_compatibility_validation",
    "runner_manual_runtime_failure_test_result_capture",
    "runner_manual_runtime_failure_result_evaluation",
    "runner_manual_runtime_validator_seal_consistency_audit",
)

D7_PUBLIC_PATHS = (
    "/api/deploy/legacy-identifier-cleanup-classification",
    "/api/deploy/legacy-runtime-compatibility-inventory",
    "/api/deploy/legacy-runtime-coexistence-analysis",
    "/api/deploy/runner/manual-runtime/failure-test-results",
    "/api/deploy/runner/manual-runtime/failure-result-evaluation",
    "/api/deploy/runner/manual-runtime/result-validator-seal-consistency-audit",
)

ALL_EVIDENCE_PATHS = (
    "/legacy-identifier-hotspot-analysis",
    "/legacy-identifier-inventory",
    "/setuphelfer-identifier-consistency-check",
    "/runner/manual-runtime/evidence-final-snapshot",
    "/runner/manual-runtime/evidence-timeline",
    "/runner/manual-runtime/result-validator-seal-index",
    "/legacy-identifier-cleanup-classification",
    "/legacy-runtime-compatibility-inventory",
    "/legacy-runtime-coexistence-analysis",
    "/runner/manual-runtime/failure-test-results",
    "/runner/manual-runtime/failure-result-evaluation",
    "/runner/manual-runtime/result-validator-seal-consistency-audit",
)


class DeployRoutesEvidenceV1Tests(unittest.TestCase):
    def test_evidence_module_no_runner_imports(self) -> None:
        src = (_BACKEND / "deploy" / "routes_evidence.py").read_text(encoding="utf-8")
        self.assertNotIn("subprocess", src)
        tree = ast.parse(src)
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                if node.module.startswith("deploy.runner_") and node.module != "deploy.runner_api_facade":
                    self.fail(f"unexpected runner import: {node.module}")

    def test_evidence_router_route_count(self) -> None:
        self.assertEqual(len(evidence_router.routes), 12)
        for route in evidence_router.routes:
            self.assertEqual(route.methods, {"POST"})

    def test_d4_routes_still_present(self) -> None:
        src = (_BACKEND / "deploy" / "routes_evidence.py").read_text(encoding="utf-8")
        for rid in D4_RUNNER_IDS:
            self.assertIn(f'"{rid}"', src)

    def test_d7_routes_present(self) -> None:
        src = (_BACKEND / "deploy" / "routes_evidence.py").read_text(encoding="utf-8")
        for rid in D7_RUNNER_IDS:
            self.assertIn(f'"{rid}"', src)
        self.assertEqual(src.count('decoupling_phase="d7"'), 6)

    def test_evidence_router_uses_build_plan_only_response(self) -> None:
        src = (_BACKEND / "deploy" / "routes_evidence.py").read_text(encoding="utf-8")
        self.assertEqual(src.count("build_plan_only_response("), 12)

    def test_no_execute_apply_write_routes(self) -> None:
        src = (_BACKEND / "deploy" / "routes_evidence.py").read_text(encoding="utf-8")
        self.assertNotIn("/execute", src)
        self.assertNotIn("/apply", src)
        for bad in ("execute", "apply", "install", "write", "delete"):
            self.assertNotRegex(src, rf'@router\.post\("[^"]*{bad}')

    def test_public_paths_unchanged(self) -> None:
        paths = sorted({route.path for route in evidence_router.routes})
        self.assertEqual(paths, sorted(ALL_EVIDENCE_PATHS))
        routes_src = (_BACKEND / "deploy" / "routes.py").read_text(encoding="utf-8")
        self.assertIn("include_router(deploy_evidence_router)", routes_src)

    def test_routes_py_no_duplicate_d7_handlers(self) -> None:
        routes_src = (_BACKEND / "deploy" / "routes.py").read_text(encoding="utf-8")
        for path in (
            "/legacy-identifier-cleanup-classification",
            "/legacy-runtime-compatibility-inventory",
            "/legacy-runtime-coexistence-analysis",
            "/runner/manual-runtime/failure-test-results",
            "/runner/manual-runtime/failure-result-evaluation",
            "/runner/manual-runtime/result-validator-seal-consistency-audit",
        ):
            self.assertNotIn(f'@router.post("{path}")', routes_src)

    def test_allowed_to_execute_stays_false(self) -> None:
        from deploy.runner_api_facade import build_plan_only_response, clear_registry_cache

        clear_registry_cache()
        for rid in D7_RUNNER_IDS:
            res = build_plan_only_response(rid, decoupling_phase="d7")
            self.assertFalse(res["allowed_to_execute"], rid)
            self.assertTrue(res["facade_decoupling_d7"])

    def test_runner_import_count_reduced(self) -> None:
        routes_src = (_BACKEND / "deploy" / "routes.py").read_text(encoding="utf-8")
        count = len(re.findall(r"^from deploy\.runner_", routes_src, flags=re.M))
        self.assertEqual(count, 77)
