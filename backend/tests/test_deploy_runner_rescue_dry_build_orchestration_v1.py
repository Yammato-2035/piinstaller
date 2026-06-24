from __future__ import annotations

import json
import unittest
from pathlib import Path

from deploy.runner_rescue_dry_build_orchestration import (
    build_rescue_dry_build_final_gate,
    build_rescue_dry_build_input_resolution,
    build_rescue_dry_build_stage_graph,
    build_rescue_package_resolution_plan,
    simulate_rescue_dry_build_execution,
    validate_rescue_build_order,
    validate_rescue_dry_build_safety,
)
from deploy.runner_rescue_debian_live_build_inputs import (
    build_debian_live_config_structure,
    build_debian_live_package_lists,
)
from deploy.routes_source_aggregate import read_deploy_routes_aggregate

_REPO = Path(__file__).resolve().parents[2]
_BR = _REPO / "build" / "rescue"
_H = _REPO / "docs" / "evidence" / "runtime-results" / "handoff"
_GRAPH = _BR / "dry_build_stage_graph.json"
_ORDER = _BR / "build_order_validation.json"
_SIM = _BR / "dry_build_execution_simulation.json"
_RES = _BR / "dry_build_input_resolution.json"
_PKG = _BR / "package_resolution_plan.json"
_SAFE = _H / "rescue_dry_build_safety_validation.json"
_FIN = _H / "rescue_dry_build_final_gate.json"
_ROUTES = _REPO / "backend" / "deploy" / "routes.py"
_RUNNER = _REPO / "backend" / "deploy" / "runner_rescue_dry_build_orchestration.py"

_HANDOFFS_SEED = (
    _H / "rescue_runtime_bundle_consistency_check.json",
    _H / "debian_live_build_inputs_final_gate.json",
    _H / "rescue_runtime_assembly_final_gate.json",
    _H / "rescue_pseudo_boot_final_readiness.json",
    _H / "setuphelfer_branding_guard_check.json",
    _H / "runtime_identifier_zero_state_verification.json",
)


class DeployRunnerRescueDryBuildOrchestrationV1Tests(unittest.TestCase):
    def setUp(self) -> None:
        _H.mkdir(parents=True, exist_ok=True)
        _BR.mkdir(parents=True, exist_ok=True)
        self._bak: dict[Path, bytes | None] = {}
        for p in (
            _GRAPH,
            _ORDER,
            _SIM,
            _RES,
            _PKG,
            _SAFE,
            _FIN,
            *_HANDOFFS_SEED,
        ):
            self._bak[p] = p.read_bytes() if p.exists() else None
            p.unlink(missing_ok=True)

    def tearDown(self) -> None:
        for p, b in self._bak.items():
            if b is None:
                p.unlink(missing_ok=True)
            else:
                p.write_bytes(b)

    def test_stage_graph_complete_ten_stages(self) -> None:
        r = build_rescue_dry_build_stage_graph(explicit_overwrite=True)
        self.assertEqual(r.get("rescue_dry_build_stage_graph_status"), "ok")
        body = r.get("rescue_dry_build_stage_graph") or {}
        stages = body.get("stages") or []
        self.assertEqual(len(stages), 10)
        for s in stages:
            self.assertFalse(s.get("destructive"))
            self.assertFalse(s.get("execute_allowed"))

    def test_build_order_blocks_cycle(self) -> None:
        build_rescue_dry_build_stage_graph(explicit_overwrite=True)
        bad = {
            "dry_build_stage_graph_schema_version": 1,
            "stages": [
                {
                    "stage_id": "a1",
                    "dependencies": ["b1"],
                    "required_inputs": [],
                    "expected_outputs": [],
                    "destructive": False,
                    "execute_allowed": False,
                },
                {
                    "stage_id": "b1",
                    "dependencies": ["a1"],
                    "required_inputs": [],
                    "expected_outputs": [],
                    "destructive": False,
                    "execute_allowed": False,
                },
            ],
        }
        _GRAPH.write_text(json.dumps(bad), encoding="utf-8")
        r = validate_rescue_build_order(explicit_overwrite=True)
        self.assertEqual(r.get("rescue_dry_build_build_order_validation_status"), "blocked")
        self.assertIn("RESCUE_DRY_BO_CYCLE", r.get("errors") or [])

    def test_build_order_blocks_missing_inputs(self) -> None:
        build_rescue_dry_build_stage_graph(explicit_overwrite=True)
        _RES.write_text(
            json.dumps({"missing_inputs": ["x:y"], "blocked_inputs": [], "resolved_inputs": []}),
            encoding="utf-8",
        )
        r = validate_rescue_build_order(explicit_overwrite=True)
        self.assertEqual(r.get("rescue_dry_build_build_order_validation_status"), "blocked")
        self.assertIn("RESCUE_DRY_BO_MISSING_INPUTS", r.get("errors") or [])

    def test_package_resolution_reads_list(self) -> None:
        build_debian_live_config_structure(explicit_overwrite=True)
        build_debian_live_package_lists(explicit_overwrite=True)
        r = build_rescue_package_resolution_plan(explicit_overwrite=True)
        self.assertEqual(r.get("rescue_dry_build_package_resolution_status"), "ok")
        body = r.get("rescue_dry_build_package_resolution") or {}
        self.assertIn("python3", body.get("required_packages") or [])

    def test_simulation_only_no_iso(self) -> None:
        _ORDER.parent.mkdir(parents=True, exist_ok=True)
        _ORDER.write_text(
            json.dumps(
                {
                    "ordered_stage_ids": ["s01", "s02"],
                    "rescue_dry_build_build_order_validation_status": "ok",
                }
            ),
            encoding="utf-8",
        )
        r = simulate_rescue_dry_build_execution(explicit_overwrite=True)
        self.assertEqual(r.get("rescue_dry_build_execution_simulation_status"), "ok")
        body = r.get("rescue_dry_build_execution_simulation") or {}
        self.assertTrue(body.get("simulation_only"))
        self.assertTrue(body.get("no_real_build"))
        for row in body.get("stage_progression") or []:
            self.assertFalse(row.get("iso_output"))

    def test_runner_no_subprocess(self) -> None:
        raw = _RUNNER.read_text(encoding="utf-8").lower()
        self.assertNotIn("subprocess", raw)

    def test_routes_dry_build_endpoints(self) -> None:
        txt = read_deploy_routes_aggregate()
        for n in (
            "/rescue/dry-build/stage-graph",
            "/rescue/dry-build/input-resolution",
            "/rescue/dry-build/package-resolution",
            "/rescue/dry-build/build-order-validation",
            "/rescue/dry-build/execution-simulation",
            "/rescue/dry-build/final-gate",
            "/rescue/dry-build/safety-validation",
        ):
            self.assertIn(n, txt)

    def test_routes_no_forbidden_segments(self) -> None:
        low = read_deploy_routes_aggregate().lower()
        for bad in (
            "/rescue/dry-build/execute",
            "/rescue/dry-build/chroot",
            "/rescue/dry-build/publish",
            "/rescue/dry-build/release",
            "qemu-system",
        ):
            self.assertNotIn(bad, low)

    def test_safety_validation_ok(self) -> None:
        r = validate_rescue_dry_build_safety(explicit_overwrite=True)
        self.assertEqual(r.get("rescue_dry_build_safety_validation_status"), "ok")

    def test_final_gate_blocked_when_safety_blocked(self) -> None:
        build_rescue_dry_build_stage_graph(explicit_overwrite=True)
        _RES.write_text(
            json.dumps(
                {
                    "missing_inputs": [],
                    "blocked_inputs": [],
                    "resolved_inputs": ["all"],
                }
            ),
            encoding="utf-8",
        )
        _PKG.write_text(
            json.dumps(
                {
                    "required_packages": ["python3"],
                    "rescue_dry_build_package_resolution_status": "ok",
                }
            ),
            encoding="utf-8",
        )
        _ORDER.write_text(
            json.dumps(
                {
                    "ordered_stage_ids": ["s01"],
                    "rescue_dry_build_build_order_validation_status": "ok",
                }
            ),
            encoding="utf-8",
        )
        _SIM.write_text(
            json.dumps({"rescue_dry_build_execution_simulation_status": "ok"}),
            encoding="utf-8",
        )
        for p, payload in (
            (_H / "rescue_runtime_bundle_consistency_check.json", {"consistency_status": "ok"}),
            (_H / "debian_live_build_inputs_final_gate.json", {"gate_status": "ready"}),
            (_H / "rescue_runtime_assembly_final_gate.json", {"gate_status": "ready"}),
            (_H / "rescue_pseudo_boot_final_readiness.json", {"gate_status": "ready"}),
            (_H / "setuphelfer_branding_guard_check.json", {"branding_guard_status": "ok"}),
            (_H / "runtime_identifier_zero_state_verification.json", {"zero_state_status": "ok"}),
        ):
            p.write_text(json.dumps(payload), encoding="utf-8")
        _SAFE.write_text(
            json.dumps(
                {
                    "evaluation": {"rescue_dry_build_safety_eval_status": "blocked"},
                }
            ),
            encoding="utf-8",
        )
        g = build_rescue_dry_build_final_gate(explicit_overwrite=True)
        self.assertEqual(g.get("rescue_dry_build_final_gate_status"), "blocked")
        self.assertIn("RESCUE_DRY_FIN_SAFETY_BLOCKED", g.get("errors") or [])
