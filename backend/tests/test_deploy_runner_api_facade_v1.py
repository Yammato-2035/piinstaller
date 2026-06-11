"""Deploy runner API facade Phase C.3 — read-only, no runner execution."""

from __future__ import annotations

import ast
import sys
import unittest
from pathlib import Path

_BACKEND = Path(__file__).resolve().parent.parent
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

from deploy.runner_api_facade import (
    FACADE_VERSION,
    build_runner_catalog,
    build_runner_catalog_summary,
    build_runner_policy_warnings,
    build_runner_risk_gate_summary,
    clear_registry_cache,
    get_runner_empty_result,
    get_runner_registry_entry,
    get_runner_risk_gate_decision,
    is_unsafe_runner_route_path,
    list_runner_registry_entries,
    read_only_runner_route_paths,
    validate_runner_empty_result,
)


class DeployRunnerApiFacadeV1Tests(unittest.TestCase):
    def setUp(self) -> None:
        clear_registry_cache()

    def test_facade_import_without_runner_modules(self) -> None:
        src = (_BACKEND / "deploy" / "runner_api_facade.py").read_text(encoding="utf-8")
        self.assertNotIn("subprocess", src)
        self.assertNotIn("importlib.import_module", src)
        tree = ast.parse(src)
        allowed = {
            "deploy.runner_registry",
            "deploy.runner_result_contract",
            "deploy.runner_risk_gate",
        }
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                if node.module.startswith("deploy.runner_") and node.module not in allowed:
                    self.fail(f"unexpected runner import: {node.module}")

    def test_catalog_contains_runners(self) -> None:
        res = build_runner_catalog()
        self.assertEqual(res["status"], "ok")
        catalog = res["data"]["catalog"]
        self.assertGreater(len(catalog), 0)
        self.assertIn("runner_id", catalog[0])

    def test_summary_counts_runners(self) -> None:
        res = build_runner_catalog_summary()
        self.assertEqual(res["status"], "ok")
        total = res["data"]["total"]
        self.assertGreaterEqual(total, 115)
        list_total = list_runner_registry_entries()["data"]["total"]
        self.assertEqual(total, list_total)

    def test_unknown_runner_blocked(self) -> None:
        res = get_runner_registry_entry("runner_does_not_exist_xyz")
        self.assertEqual(res["status"], "blocked")
        self.assertTrue(res["errors"])

    def test_empty_result_validates_against_contract(self) -> None:
        cat = build_runner_catalog()
        runner_id = cat["data"]["catalog"][0]["runner_id"]
        v = validate_runner_empty_result(runner_id)
        self.assertEqual(v["status"], "ok")
        self.assertTrue(v["data"]["valid"])

    def test_policy_warnings_delivered(self) -> None:
        res = build_runner_policy_warnings()
        self.assertIn(res["status"], {"ok", "review_required"})
        self.assertIn("warnings", res["data"])

    def test_empty_result_no_execution(self) -> None:
        cat = build_runner_catalog()
        runner_id = cat["data"]["catalog"][0]["runner_id"]
        res = get_runner_empty_result(runner_id)
        self.assertTrue(res["data"]["no_execution_performed"])
        self.assertTrue(res["data"]["result"]["no_execution_performed"])

    def test_read_only_route_paths_safe(self) -> None:
        for path in read_only_runner_route_paths():
            self.assertFalse(is_unsafe_runner_route_path(path), path)

    def test_new_routes_in_routes_py_are_get_only(self) -> None:
        routes_src = (_BACKEND / "deploy" / "routes.py").read_text(encoding="utf-8")
        for fragment in (
            '@router.get("/runners/catalog")',
            '@router.get("/runners/summary")',
            '@router.get("/runners/policy-warnings")',
            '@router.get("/runners/risk-gate/summary")',
            '@router.get("/runners/{runner_id}/risk-gate")',
            '@router.get("/runners/{runner_id}")',
            '@router.get("/runners/{runner_id}/empty-result")',
        ):
            self.assertIn(fragment, routes_src)
        self.assertNotIn('@router.post("/runners/', routes_src)
        self.assertNotIn('@router.delete("/runners/', routes_src)

    def test_facade_version(self) -> None:
        self.assertEqual(FACADE_VERSION, 4)

    def test_risk_gate_decision_never_executes(self) -> None:
        cat = build_runner_catalog()
        runner_id = cat["data"]["catalog"][0]["runner_id"]
        res = get_runner_risk_gate_decision(runner_id)
        self.assertFalse(res["data"]["allowed_to_execute"])

    def test_risk_gate_summary(self) -> None:
        res = build_runner_risk_gate_summary()
        self.assertIn("by_decision", res["data"])
        self.assertFalse(res["data"]["allowed_to_execute_in_c4"])


if __name__ == "__main__":
    unittest.main()
