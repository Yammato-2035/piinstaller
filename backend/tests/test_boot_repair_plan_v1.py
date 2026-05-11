"""Boot Repair Plan v1 (plan only, no execution)."""

from __future__ import annotations

import importlib.util
import sys
import unittest

from fastapi import FastAPI
from fastapi.testclient import TestClient
from pathlib import Path

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


plan_mod = _load("boot/repair_plan.py", "setuphelfer_boot_repair_plan_test")
routes_mod = _load("boot/routes.py", "setuphelfer_boot_routes_repair_plan_test")
generate_boot_repair_plan = plan_mod.generate_boot_repair_plan


class TestBootRepairPlanV1(unittest.TestCase):
    def test_missing_fstab_issue_and_action(self):
        r = generate_boot_repair_plan(
            target_path="/tmp/target",
            inspect_result={},
            post_verify={"warnings": ["POST_RESTORE_FSTAB_MISSING"]},
            boot_capability={"status": "boot_warning", "warnings": ["BOOT_FSTAB_MISSING"], "boot_type_hints": []},
        )
        self.assertIn("missing_fstab", r.get("issues", []))
        codes = [a.get("code") for a in r.get("proposed_actions", [])]
        self.assertIn("REPAIR_REGENERATE_FSTAB", codes)
        self.assertTrue(all(a.get("auto_allowed") is False for a in r.get("proposed_actions", [])))

    def test_missing_kernel_suggests_rebuild_initramfs(self):
        r = generate_boot_repair_plan(
            target_path="/tmp/target",
            inspect_result={},
            post_verify={"warnings": ["POST_RESTORE_KERNEL_MISSING"]},
            boot_capability={"status": "boot_warning", "warnings": ["BOOT_KERNEL_MISSING"], "boot_type_hints": ["BOOT_GRUB_HINT_FOUND"]},
        )
        codes = [a.get("code") for a in r.get("proposed_actions", [])]
        self.assertIn("REPAIR_REBUILD_INITRAMFS", codes)

    def test_missing_boot_suggests_grub(self):
        r = generate_boot_repair_plan(
            target_path="/tmp/target",
            inspect_result={},
            post_verify={"warnings": ["POST_RESTORE_BOOT_DIR_MISSING"]},
            boot_capability={"status": "boot_warning", "warnings": ["BOOT_DIR_MISSING"], "boot_type_hints": []},
        )
        codes = [a.get("code") for a in r.get("proposed_actions", [])]
        self.assertIn("REPAIR_REINSTALL_GRUB", codes)

    def test_windows_manual_required_high_risk(self):
        r = generate_boot_repair_plan(
            target_path="/tmp/target",
            inspect_result={"classification": {"system_type": "WINDOWS"}},
            post_verify={"warnings": []},
            boot_capability={"status": "boot_warning", "warnings": ["BOOT_WINDOWS_BOOTMANAGER_FOUND"], "boot_type_hints": ["BOOT_WINDOWS_BOOTMANAGER_FOUND"]},
        )
        self.assertTrue(r.get("requires_manual_review"))
        self.assertIn("BOOT_REPAIR_RISK_WINDOWS_OVERWRITE", r.get("risks", []))

    def test_dualboot_manual_required(self):
        r = generate_boot_repair_plan(
            target_path="/tmp/target",
            inspect_result={"classification": {"system_type": "DUALBOOT"}},
            post_verify={"warnings": []},
            boot_capability={"status": "boot_warning", "warnings": ["BOOT_DUALBOOT_RISK"], "boot_type_hints": ["BOOT_WINDOWS_BOOTMANAGER_FOUND"]},
        )
        self.assertTrue(r.get("requires_manual_review"))
        self.assertIn("dualboot_detected", r.get("issues", []))

    def test_no_issues_plan_ok(self):
        r = generate_boot_repair_plan(
            target_path="/tmp/target",
            inspect_result={},
            post_verify={"warnings": []},
            boot_capability={"status": "boot_likely", "warnings": [], "boot_type_hints": ["BOOT_GRUB_HINT_FOUND", "BOOT_EFI_HINT_FOUND"]},
        )
        self.assertEqual(r.get("plan_status"), "ok")

    def test_unknown_not_applicable(self):
        r = generate_boot_repair_plan(
            target_path="/tmp/target",
            inspect_result={},
            post_verify={},
            boot_capability={"status": "boot_unknown", "warnings": [], "boot_type_hints": []},
        )
        self.assertIn(r.get("plan_status"), {"not_applicable", "review_required"})

    def test_api_contract_stable(self):
        app = FastAPI()
        app.include_router(routes_mod.router)
        client = TestClient(app)
        resp = client.post(
            "/api/boot/repair/plan",
            json={
                "target_path": "/tmp/target",
                "inspect": {},
                "post_verify": {"warnings": ["POST_RESTORE_FSTAB_MISSING"]},
                "boot_capability": {"status": "boot_warning", "warnings": ["BOOT_FSTAB_MISSING"], "boot_type_hints": []},
            },
        )
        self.assertEqual(resp.status_code, 200)
        payload = resp.json()
        self.assertIn(payload.get("code"), {
            "BOOT_REPAIR_PLAN_OK",
            "BOOT_REPAIR_PLAN_REVIEW_REQUIRED",
            "BOOT_REPAIR_PLAN_NOT_APPLICABLE",
        })
        plan = payload.get("plan")
        self.assertIsInstance(plan, dict)
        self.assertIn("plan_status", plan)
        self.assertIn("issues", plan)
        self.assertIn("proposed_actions", plan)
        self.assertTrue(all((a.get("auto_allowed") is False) for a in plan.get("proposed_actions", [])))

