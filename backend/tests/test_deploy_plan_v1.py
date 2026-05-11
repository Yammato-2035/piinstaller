"""Deploy plan (advisory only) — contract and decision tests."""

from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

_BACKEND = Path(__file__).resolve().parent.parent
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))


def _load(rel: str, name: str):
    p = _BACKEND / rel
    spec = importlib.util.spec_from_file_location(name, p)
    if not spec or not spec.loader:
        raise ImportError(rel)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


plan_mod = _load("deploy/plan.py", "setuphelfer_deploy_plan_test")
routes_mod = _load("deploy/routes.py", "setuphelfer_deploy_routes_test")
generate_deploy_plan = plan_mod.generate_deploy_plan


def _safety(targets: list[dict]) -> dict:
    return {"policy_code": "safety.summary.v1", "targets": targets}


def _inspect(**kwargs) -> dict:
    base = {
        "system": {},
        "storage": {"devices_classified": [], "devices_raw": [], "mountability": []},
        "filesystems": {"detected": {}, "uuid_conflicts": {}},
        "capabilities": {"os_hints": {}},
        "network": {"interfaces": ["lo"], "ipv4": [], "code": "rescue.network.summary"},
    }
    base.update(kwargs)
    return base


class TestDeployPlanV1(unittest.TestCase):
    def test_empty_disk_ok(self):
        ir = _inspect(
            storage={
                "devices_classified": [
                    {"device": "/dev/sdY", "type": "disk", "size": "120G", "partitions": []},
                ],
                "devices_raw": [{"device": "/dev/sdY", "type": "disk", "partitions": []}],
                "mountability": [],
            },
            capabilities={"os_hints": {"possible_empty_disk": True, "unknown_layout": False}},
        )
        safety = _safety(
            [
                {
                    "device": "/dev/sdY",
                    "write_allowed": True,
                    "reason_code": "SAFETY_EMPTY_DISK",
                    "classification": "allowed",
                }
            ]
        )
        plan = generate_deploy_plan(ir, safety, {"system_type": "EMPTY", "risk_level": "low"})
        self.assertEqual(plan["plan_status"], "ok")
        self.assertEqual(plan["blocked_steps"], [])
        self.assertTrue(all(s["auto_allowed"] is False for s in plan["required_steps"]))
        self.assertTrue(all(s["requires_confirmation"] for s in plan["required_steps"]))

    def test_windows_blocked(self):
        ir = _inspect(filesystems={"detected": {"/dev/sda1": {"type": "ntfs"}}, "uuid_conflicts": {}})
        safety = _safety([{"device": "/dev/sda", "reason_code": "SAFETY_WINDOWS_DETECTED", "write_allowed": False}])
        plan = generate_deploy_plan(ir, safety, {"system_type": "WINDOWS"})
        self.assertEqual(plan["plan_status"], "blocked")
        self.assertIn("DEPLOY_BLOCKED_WINDOWS", plan["blocked_steps"])

    def test_dualboot_blocked(self):
        ir = _inspect()
        safety = _safety([{"device": "/dev/sda", "reason_code": "SAFETY_DUALBOOT", "write_allowed": False}])
        plan = generate_deploy_plan(ir, safety, {"system_type": "DUALBOOT"})
        self.assertEqual(plan["plan_status"], "blocked")
        self.assertIn("DEPLOY_BLOCKED_DUALBOOT", plan["blocked_steps"])

    def test_system_disk_blocked(self):
        ir = _inspect()
        safety = _safety([{"device": "/dev/nvme0n1", "reason_code": "SAFETY_SYSTEM_DISK", "write_allowed": False}])
        plan = generate_deploy_plan(ir, safety, {"system_type": "LINUX"})
        self.assertEqual(plan["plan_status"], "blocked")
        self.assertIn("DEPLOY_BLOCKED_SYSTEM_DISK", plan["blocked_steps"])

    def test_nonempty_blocked(self):
        ir = _inspect(
            filesystems={"detected": {"/dev/sdb1": {"type": "ext4"}}, "uuid_conflicts": {}},
        )
        safety = _safety([{"device": "/dev/sdb", "reason_code": "SAFETY_BACKUP_TARGET_OK", "write_allowed": True}])
        plan = generate_deploy_plan(ir, safety, {"system_type": "LINUX"})
        self.assertEqual(plan["plan_status"], "blocked")
        self.assertIn("DEPLOY_BLOCKED_NOT_EMPTY", plan["blocked_steps"])

    def test_unknown_layout_review(self):
        ir = _inspect(
            capabilities={"os_hints": {"unknown_layout": True, "possible_empty_disk": False}},
            storage={
                "devices_classified": [{"device": "/dev/sdx", "type": "disk", "size": "64G", "partitions": []}],
                "devices_raw": [],
                "mountability": [],
            },
        )
        safety = _safety(
            [{"device": "/dev/sdx", "reason_code": "SAFETY_EMPTY_DISK", "write_allowed": True, "classification": "allowed"}]
        )
        plan = generate_deploy_plan(ir, safety, {"system_type": "UNKNOWN", "risk_level": "medium"})
        self.assertEqual(plan["plan_status"], "review_required")

    def test_hardware_summary(self):
        ir = _inspect(
            system={"cpu_count": 4, "total_memory_gb": 16.0},
            storage={
                "devices_classified": [{"device": "/dev/sda", "type": "disk", "size": "200G", "partitions": []}],
                "devices_raw": [],
                "mountability": [],
            },
            network={"interfaces": ["eth0", "lo"], "ipv4": [{"interface": "eth0", "address": "10.0.0.2"}], "code": "rescue.network.summary"},
        )
        safety = _safety([{"device": "/dev/sda", "reason_code": "SAFETY_EMPTY_DISK", "write_allowed": True}])
        plan = generate_deploy_plan(ir, safety, {"system_type": "EMPTY"})
        hw = plan["hardware_summary"]
        self.assertEqual(hw["cpu_class"], "medium")
        self.assertEqual(hw["ram_class"], "high")
        self.assertEqual(hw["storage_class"], "medium")
        self.assertEqual(hw["network_available"], True)

    def test_profile_structure(self):
        ir = _inspect(
            system={"cpu_count": 2, "total_memory_gb": 4.0},
            storage={
                "devices_classified": [{"device": "/dev/sda", "type": "disk", "size": "64G", "partitions": []}],
                "devices_raw": [],
                "mountability": [],
            },
        )
        safety = _safety([{"device": "/dev/sda", "reason_code": "SAFETY_EMPTY_DISK", "write_allowed": True}])
        plan = generate_deploy_plan(ir, safety, {"system_type": "EMPTY"})
        for p in plan["deploy_profiles"]:
            self.assertIn("code", p)
            self.assertIn("requirements", p)
            self.assertIn("risk_level", p)
            self.assertFalse(p["auto_allowed"])
            self.assertTrue(p["requires_confirmation"])

    def test_recommended_only_when_safe(self):
        ir_ok = _inspect(
            system={"cpu_count": 4, "total_memory_gb": 8.0},
            storage={
                "devices_classified": [{"device": "/dev/sda", "type": "disk", "size": "256G", "partitions": []}],
                "devices_raw": [],
                "mountability": [],
            },
            network={"interfaces": ["eth0"], "ipv4": [{"interface": "eth0", "address": "10.0.0.1"}], "code": "rescue.network.summary"},
        )
        safety_ok = _safety([{"device": "/dev/sda", "reason_code": "SAFETY_EMPTY_DISK", "write_allowed": True}])
        plan_ok = generate_deploy_plan(ir_ok, safety_ok, {"system_type": "EMPTY", "risk_level": "low"})
        self.assertEqual(plan_ok["plan_status"], "ok")
        self.assertTrue(plan_ok["recommended_profile"])
        self.assertEqual(plan_ok["recommended_profile"]["code"], "DEPLOY_PROFILE_MINIMAL_LINUX")

        ir_blocked = _inspect(
            filesystems={"detected": {"/dev/sdb1": {"type": "ext4"}}, "uuid_conflicts": {}},
        )
        safety_b = _safety([{"device": "/dev/sdb", "reason_code": "SAFETY_SYSTEM_DISK", "write_allowed": False}])
        plan_b = generate_deploy_plan(ir_blocked, safety_b, {"system_type": "LINUX"})
        self.assertEqual(plan_b["plan_status"], "blocked")
        self.assertFalse(plan_b["recommended_profile"])

    def test_required_steps_auto_allowed_false(self):
        ir = _inspect(
            storage={
                "devices_classified": [{"device": "/dev/z", "type": "disk", "size": "100G", "partitions": []}],
                "devices_raw": [],
                "mountability": [],
            },
        )
        safety = _safety([{"device": "/dev/z", "reason_code": "SAFETY_EMPTY_DISK", "write_allowed": True}])
        plan = generate_deploy_plan(ir, safety, {"system_type": "EMPTY"})
        self.assertTrue(all(x["auto_allowed"] is False for x in plan["required_steps"]))

    def test_execute_route_present_for_prep_contract(self):
        app = FastAPI()
        app.include_router(routes_mod.router)
        c = TestClient(app)
        r = c.post("/api/deploy/execute", json={})
        self.assertEqual(r.status_code, 422)

    def test_api_plan_contract(self):
        app = FastAPI()
        app.include_router(routes_mod.router)
        c = TestClient(app)
        body = {
            "inspect_result": _inspect(
                storage={
                    "devices_classified": [{"device": "/dev/sda", "type": "disk", "size": "128G", "partitions": []}],
                    "devices_raw": [],
                    "mountability": [],
                },
            ),
            "safety_summary": _safety([{"device": "/dev/sda", "reason_code": "SAFETY_EMPTY_DISK", "write_allowed": True}]),
            "classification": {"system_type": "EMPTY", "risk_level": "low"},
        }
        resp = c.post("/api/deploy/plan", json=body)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("code", data)
        self.assertIn("plan", data)
        self.assertEqual(data["code"], "DEPLOY_PLAN_OK")
