"""Boot repair execute phase 2 tests."""

from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
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


mod = _load("boot/repair_execute.py", "setuphelfer_boot_repair_execute_test")


class TestBootRepairExecuteV1(unittest.TestCase):
    def setUp(self):
        mod._REPAIR_SESSION_STORE.clear()

    def _plan(self, action="REPAIR_REGENERATE_FSTAB", risk="low"):
        return {
            "plan_status": "review_required",
            "issues": ["missing_fstab"],
            "proposed_actions": [
                {
                    "code": action,
                    "applicable": True,
                    "risk_level": risk,
                    "requires_confirmation": True,
                    "auto_allowed": False,
                }
            ],
            "risks": [],
            "requires_manual_review": False,
        }

    def _cap(self, warnings=None, hints=None):
        return {
            "status": "boot_warning",
            "warnings": warnings or [],
            "boot_type_hints": hints or [],
            "errors": [],
            "checks": [],
            "risks": [],
            "recommendations": [],
        }

    def test_no_session(self):
        r = mod.execute_boot_repair({"repair_session_id": "x", "confirmation_token": "y", "action_code": "REPAIR_REGENERATE_FSTAB", "target_path": "/tmp"})
        self.assertEqual(r.get("code"), "BOOT_REPAIR_SESSION_NOT_FOUND")

    def test_wrong_token(self):
        with tempfile.TemporaryDirectory() as td:
            s = mod.create_boot_repair_session(
                target_path=td,
                selected_action_code="REPAIR_REGENERATE_FSTAB",
                inspect_result={},
                post_verify={},
                boot_capability=self._cap(),
                boot_repair_plan=self._plan(),
            )
            r = mod.execute_boot_repair({
                "repair_session_id": s["repair_session_id"],
                "confirmation_token": "wrong",
                "action_code": "REPAIR_REGENERATE_FSTAB",
                "target_path": td,
            })
            self.assertEqual(r.get("code"), "BOOT_REPAIR_TOKEN_INVALID")

    def test_expired_session(self):
        with tempfile.TemporaryDirectory() as td:
            s = mod.create_boot_repair_session(
                target_path=td,
                selected_action_code="REPAIR_REGENERATE_FSTAB",
                inspect_result={},
                post_verify={},
                boot_capability=self._cap(),
                boot_repair_plan=self._plan(),
            )
            sid = s["repair_session_id"]
            mod._REPAIR_SESSION_STORE[sid]["expires_at"] = (datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat()
            r = mod.execute_boot_repair({
                "repair_session_id": sid,
                "confirmation_token": s["confirmation_token"],
                "action_code": "REPAIR_REGENERATE_FSTAB",
                "target_path": td,
            })
            self.assertEqual(r.get("code"), "BOOT_REPAIR_SESSION_EXPIRED")

    def test_action_mismatch(self):
        with tempfile.TemporaryDirectory() as td:
            s = mod.create_boot_repair_session(
                target_path=td,
                selected_action_code="REPAIR_REGENERATE_FSTAB",
                inspect_result={},
                post_verify={},
                boot_capability=self._cap(),
                boot_repair_plan=self._plan(),
            )
            r = mod.execute_boot_repair({
                "repair_session_id": s["repair_session_id"],
                "confirmation_token": s["confirmation_token"],
                "action_code": "REPAIR_CHECK_UUID_MAPPING",
                "target_path": td,
            })
            self.assertEqual(r.get("code"), "BOOT_REPAIR_ACTION_MISMATCH")

    def test_windows_blocked(self):
        with tempfile.TemporaryDirectory() as td:
            s = mod.create_boot_repair_session(
                target_path=td,
                selected_action_code="REPAIR_REGENERATE_FSTAB",
                inspect_result={},
                post_verify={},
                boot_capability=self._cap(warnings=["BOOT_WINDOWS_BOOTMANAGER_FOUND"], hints=["BOOT_WINDOWS_BOOTMANAGER_FOUND"]),
                boot_repair_plan=self._plan(),
            )
            self.assertEqual(s.get("code"), "BOOT_REPAIR_ACTION_NOT_ALLOWED")

    def test_dualboot_blocked(self):
        with tempfile.TemporaryDirectory() as td:
            s = mod.create_boot_repair_session(
                target_path=td,
                selected_action_code="REPAIR_REGENERATE_FSTAB",
                inspect_result={},
                post_verify={},
                boot_capability=self._cap(warnings=["BOOT_DUALBOOT_RISK"]),
                boot_repair_plan=self._plan(),
            )
            self.assertEqual(s.get("code"), "BOOT_REPAIR_ACTION_NOT_ALLOWED")

    def test_high_risk_blocked(self):
        with tempfile.TemporaryDirectory() as td:
            s = mod.create_boot_repair_session(
                target_path=td,
                selected_action_code="REPAIR_REGENERATE_FSTAB",
                inspect_result={},
                post_verify={},
                boot_capability=self._cap(),
                boot_repair_plan=self._plan(risk="high"),
            )
            self.assertEqual(s.get("code"), "BOOT_REPAIR_ACTION_NOT_ALLOWED")

    def test_allowed_action_success_mocked(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "etc").mkdir()
            s = mod.create_boot_repair_session(
                target_path=td,
                selected_action_code="REPAIR_REGENERATE_FSTAB",
                inspect_result={},
                post_verify={},
                boot_capability=self._cap(),
                boot_repair_plan=self._plan(),
            )
            r = mod.execute_boot_repair({
                "repair_session_id": s["repair_session_id"],
                "confirmation_token": s["confirmation_token"],
                "action_code": "REPAIR_REGENERATE_FSTAB",
                "target_path": td,
            })
            self.assertEqual(r.get("code"), "BOOT_REPAIR_EXECUTE_COMPLETED")

    def test_post_check_runs(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "etc").mkdir()
            s = mod.create_boot_repair_session(
                target_path=td,
                selected_action_code="REPAIR_REGENERATE_FSTAB",
                inspect_result={},
                post_verify={},
                boot_capability=self._cap(),
                boot_repair_plan=self._plan(),
            )
            r = mod.execute_boot_repair({
                "repair_session_id": s["repair_session_id"],
                "confirmation_token": s["confirmation_token"],
                "action_code": "REPAIR_REGENERATE_FSTAB",
                "target_path": td,
            })
            self.assertIn("after_action", (r.get("post_check") or {}))

    def test_single_use_token(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "etc").mkdir()
            s = mod.create_boot_repair_session(
                target_path=td,
                selected_action_code="REPAIR_REGENERATE_FSTAB",
                inspect_result={},
                post_verify={},
                boot_capability=self._cap(),
                boot_repair_plan=self._plan(),
            )
            req = {
                "repair_session_id": s["repair_session_id"],
                "confirmation_token": s["confirmation_token"],
                "action_code": "REPAIR_REGENERATE_FSTAB",
                "target_path": td,
            }
            r1 = mod.execute_boot_repair(req)
            self.assertEqual(r1.get("code"), "BOOT_REPAIR_EXECUTE_COMPLETED")
            r2 = mod.execute_boot_repair(req)
            self.assertEqual(r2.get("code"), "BOOT_REPAIR_SESSION_NOT_FOUND")

