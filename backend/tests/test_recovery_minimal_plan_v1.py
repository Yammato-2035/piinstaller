"""Recovery minimal plan phase 1 tests."""

from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

_BACKEND = Path(__file__).resolve().parent.parent
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))


def _load(rel: str, mod_name: str):
    p = _BACKEND / rel
    spec = importlib.util.spec_from_file_location(mod_name, p)
    if not spec or not spec.loader:
        raise ImportError(rel)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


plan_mod = _load("recovery/minimal_plan.py", "setuphelfer_recovery_minimal_plan_test")
routes_mod = _load("recovery/routes.py", "setuphelfer_recovery_routes_test")


generate_recovery_minimal_plan = plan_mod.generate_recovery_minimal_plan


class TestRecoveryMinimalPlanV1(unittest.TestCase):
    def test_windows_blocked(self):
        with tempfile.TemporaryDirectory() as td:
            r = generate_recovery_minimal_plan(td, inspect_result={"classification": {"system_type": "WINDOWS"}})
            self.assertEqual(r.get("plan_status"), "blocked")
            self.assertIn("RECOVERY_BLOCKED_WINDOWS", r.get("blocked_steps", []))

    def test_dualboot_blocked(self):
        with tempfile.TemporaryDirectory() as td:
            r = generate_recovery_minimal_plan(td, inspect_result={"classification": {"system_type": "DUALBOOT"}})
            self.assertEqual(r.get("plan_status"), "blocked")
            self.assertIn("RECOVERY_BLOCKED_DUALBOOT", r.get("blocked_steps", []))

    def test_unknown_layout_defensive(self):
        with tempfile.TemporaryDirectory() as td:
            r = generate_recovery_minimal_plan(td, inspect_result={"classification": {"system_type": "UNKNOWN"}})
            self.assertIn(r.get("plan_status"), {"blocked", "review_required"})

    def test_safety_blocked(self):
        with tempfile.TemporaryDirectory() as td:
            r = generate_recovery_minimal_plan(td, safety_summary={"targets": [{"write_allowed": False}]})
            self.assertEqual(r.get("plan_status"), "blocked")
            self.assertIn("RECOVERY_BLOCKED_SAFETY", r.get("blocked_steps", []))

    def test_target_missing(self):
        r = generate_recovery_minimal_plan('/tmp/not-existing-recovery-minimal-plan-target')
        self.assertIn(r.get("plan_status"), {"blocked", "not_applicable"})

    def test_linux_plausible(self):
        with tempfile.TemporaryDirectory() as td:
            r = generate_recovery_minimal_plan(
                td,
                inspect_result={"classification": {"system_type": "LINUX"}},
                boot_capability={"status": "boot_likely", "warnings": []},
                safety_summary={"targets": [{"write_allowed": True}]},
            )
            self.assertIn(r.get("plan_status"), {"ok", "review_required"})

    def test_all_required_steps_auto_allowed_false(self):
        with tempfile.TemporaryDirectory() as td:
            r = generate_recovery_minimal_plan(td)
            self.assertTrue(all(s.get("auto_allowed") is False for s in r.get("required_steps", [])))

    def test_api_contract_stable(self):
        app = FastAPI()
        app.include_router(routes_mod.router)
        c = TestClient(app)
        with tempfile.TemporaryDirectory() as td:
            resp = c.post('/api/recovery/minimal/plan', json={"target_path": td, "inspect_result": {}, "boot_capability": {}, "post_restore": {}, "safety_summary": {}})
            self.assertEqual(resp.status_code, 200)
            payload = resp.json()
            self.assertIn(payload.get("code"), {
                "RECOVERY_MINIMAL_PLAN_OK",
                "RECOVERY_MINIMAL_PLAN_REVIEW_REQUIRED",
                "RECOVERY_MINIMAL_PLAN_BLOCKED",
                "RECOVERY_MINIMAL_PLAN_NOT_APPLICABLE",
            })
            self.assertIsInstance(payload.get("plan"), dict)

    def test_execute_route_present_for_prep_contract(self):
        app = FastAPI()
        app.include_router(routes_mod.router)
        c = TestClient(app)
        resp = c.post('/api/recovery/minimal/execute', json={})
        # Route exists in prep phase, but enforces request contract.
        self.assertEqual(resp.status_code, 422)

