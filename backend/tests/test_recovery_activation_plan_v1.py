"""Recovery activation plan v1 tests (plan only)."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from .recovery_imports import import_recovery_submodule

_BACKEND = Path(__file__).resolve().parent.parent
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))


plan_mod = import_recovery_submodule("activation_plan")
routes_mod = import_recovery_submodule("routes")


generate_recovery_activation_plan = plan_mod.generate_recovery_activation_plan


class TestRecoveryActivationPlanV1(unittest.TestCase):
    def test_windows_blocked(self):
        with tempfile.TemporaryDirectory() as td:
            r = generate_recovery_activation_plan(td, inspect_result={"classification": {"system_type": "WINDOWS"}})
            self.assertEqual(r.get("plan_status"), "blocked")

    def test_dualboot_blocked(self):
        with tempfile.TemporaryDirectory() as td:
            r = generate_recovery_activation_plan(td, inspect_result={"classification": {"system_type": "DUALBOOT"}})
            self.assertEqual(r.get("plan_status"), "blocked")

    def test_boot_failed_blocked(self):
        with tempfile.TemporaryDirectory() as td:
            r = generate_recovery_activation_plan(td, boot_capability={"status": "boot_failed"})
            self.assertEqual(r.get("plan_status"), "blocked")

    def test_unknown_layout_defensive(self):
        with tempfile.TemporaryDirectory() as td:
            r = generate_recovery_activation_plan(td, inspect_result={"classification": {"system_type": "UNKNOWN"}})
            self.assertIn(r.get("plan_status"), {"blocked", "review_required"})

    def test_linux_plausible(self):
        with tempfile.TemporaryDirectory() as td:
            r = generate_recovery_activation_plan(
                td,
                inspect_result={"classification": {"system_type": "LINUX"}, "network": {"interfaces": ["eth0"]}},
                boot_capability={"status": "boot_likely"},
                safety_summary={"targets": [{"write_allowed": True}]},
                recovery_minimal_plan={"plan_status": "ok"},
            )
            self.assertIn(r.get("plan_status"), {"ok", "review_required"})

    def test_exposed_services_structure(self):
        with tempfile.TemporaryDirectory() as td:
            r = generate_recovery_activation_plan(td)
            services = r.get("exposed_services", [])
            self.assertTrue(len(services) >= 1)
            self.assertTrue(all(isinstance(x, dict) and "service" in x and "port" in x for x in services))

    def test_required_steps_auto_allowed_false(self):
        with tempfile.TemporaryDirectory() as td:
            r = generate_recovery_activation_plan(td)
            self.assertTrue(all(s.get("auto_allowed") is False for s in r.get("required_steps", [])))

    def test_api_contract(self):
        app = FastAPI()
        app.include_router(routes_mod.router)
        c = TestClient(app)
        with tempfile.TemporaryDirectory() as td:
            resp = c.post('/api/recovery/activation/plan', json={"target_path": td, "inspect_result": {}, "post_restore": {}, "boot_capability": {}, "recovery_minimal_plan": {}, "safety_summary": {}})
            self.assertEqual(resp.status_code, 200)
            payload = resp.json()
            self.assertIn(payload.get("code"), {
                "RECOVERY_ACTIVATION_PLAN_OK",
                "RECOVERY_ACTIVATION_PLAN_REVIEW_REQUIRED",
                "RECOVERY_ACTIVATION_PLAN_BLOCKED",
                "RECOVERY_ACTIVATION_PLAN_NOT_APPLICABLE",
            })

    def test_execute_route_present_for_prep_contract(self):
        app = FastAPI()
        app.include_router(routes_mod.router)
        c = TestClient(app)
        resp = c.post('/api/recovery/activation/execute', json={})
        # Prep route exists and validates contract.
        self.assertEqual(resp.status_code, 422)

