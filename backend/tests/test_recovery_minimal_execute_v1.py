"""Recovery minimal execute phase 2b tests."""

from __future__ import annotations

import importlib.util
import os
import shutil
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


mod = _load("recovery/minimal_execute.py", "setuphelfer_recovery_minimal_execute_test")


class TestRecoveryMinimalExecuteV1(unittest.TestCase):
    def setUp(self):
        mod._RECOVERY_MINIMAL_SESSION_STORE.clear()
        self._old_agent_candidates = list(mod._AGENT_SOURCE_CANDIDATES)

    def tearDown(self):
        mod._AGENT_SOURCE_CANDIDATES = self._old_agent_candidates

    def _mk_target(self) -> str:
        base = Path("/tmp/setuphelfer-rescue-restore-test")
        base.mkdir(parents=True, exist_ok=True)
        return tempfile.mkdtemp(prefix="recovery-min-", dir=str(base))

    def _plan(self):
        return {
            "plan_status": "review_required",
            "target": {"path": "/tmp", "exists": True, "readable": True},
            "system_assessment": {"system_type": "LINUX", "safety_blocked": False},
            "required_steps": [
                {"code": "RECOVERY_STEP_WRITE_RECOVERY_NOTES", "applicable": True, "risk_level": "low", "requires_confirmation": True, "auto_allowed": False},
                {"code": "RECOVERY_STEP_ENABLE_SSH", "applicable": True, "risk_level": "high", "requires_confirmation": True, "auto_allowed": False},
                {"code": "RECOVERY_STEP_CREATE_RECOVERY_USER", "applicable": True, "risk_level": "high", "requires_confirmation": True, "auto_allowed": False},
                {"code": "RECOVERY_STEP_CONFIGURE_NETWORK_DHCP", "applicable": True, "risk_level": "medium", "requires_confirmation": True, "auto_allowed": False},
                {"code": "RECOVERY_STEP_INSTALL_SETUPHELPER_AGENT", "applicable": True, "risk_level": "medium", "requires_confirmation": True, "auto_allowed": False},
            ],
            "blocked_steps": [],
        }

    def _create_session(self, target: str, steps: list[str], plan: dict):
        return mod.create_recovery_minimal_session({
            "target_path": target,
            "selected_steps": steps,
            "plan": plan,
        })

    def test_session_single_use_second_execute_blocked(self):
        target = self._mk_target()
        plan = self._plan()
        s = self._create_session(target, ["RECOVERY_STEP_WRITE_RECOVERY_NOTES"], plan)
        req = {
            "session_id": s["session_id"],
            "confirmation_token": s["confirmation_token"],
            "target_path": target,
            "plan": plan,
        }
        r1 = mod.execute_recovery_minimal(req)
        self.assertEqual(r1.get("code"), "RECOVERY_MINIMAL_EXECUTE_COMPLETED")
        r2 = mod.execute_recovery_minimal(req)
        self.assertEqual(r2.get("code"), "RECOVERY_MINIMAL_SESSION_ALREADY_USED")

    def test_write_recovery_notes_under_target(self):
        target = self._mk_target()
        plan = self._plan()
        s = self._create_session(target, ["RECOVERY_STEP_WRITE_RECOVERY_NOTES"], plan)
        r = mod.execute_recovery_minimal({
            "session_id": s["session_id"],
            "confirmation_token": s["confirmation_token"],
            "target_path": target,
            "plan": plan,
        })
        self.assertEqual(r.get("code"), "RECOVERY_MINIMAL_EXECUTE_COMPLETED")
        notes = Path(target) / "var/log/setuphelfer/recovery-notes.json"
        self.assertTrue(notes.is_file())

    def test_path_traversal_blocked(self):
        target = self._mk_target()
        symlink_root = Path(target) / "var/log"
        symlink_root.mkdir(parents=True, exist_ok=True)
        link = Path(target) / "var/log/setuphelfer"
        if link.exists() or link.is_symlink():
            if link.is_dir() and not link.is_symlink():
                shutil.rmtree(link)
            else:
                link.unlink()
        link.symlink_to(Path("/tmp"))

        plan = self._plan()
        s = self._create_session(target, ["RECOVERY_STEP_WRITE_RECOVERY_NOTES"], plan)
        r = mod.execute_recovery_minimal({
            "session_id": s["session_id"],
            "confirmation_token": s["confirmation_token"],
            "target_path": target,
            "plan": plan,
        })
        self.assertEqual(r.get("code"), "RECOVERY_MINIMAL_EXECUTE_FAILED")

    def test_target_root_blocked(self):
        plan = self._plan()
        s = self._create_session("/", ["RECOVERY_STEP_WRITE_RECOVERY_NOTES"], plan)
        self.assertEqual(s.get("code"), "RECOVERY_MINIMAL_EXECUTE_BLOCKED")

    def test_ssh_step_records_plan_only(self):
        target = self._mk_target()
        plan = self._plan()
        s = self._create_session(target, ["RECOVERY_STEP_ENABLE_SSH"], plan)
        r = mod.execute_recovery_minimal({
            "session_id": s["session_id"],
            "confirmation_token": s["confirmation_token"],
            "target_path": target,
            "plan": plan,
        })
        self.assertEqual(r.get("code"), "RECOVERY_MINIMAL_EXECUTE_COMPLETED")
        plan_file = Path(target) / "var/log/setuphelfer/recovery_step_enable_ssh.plan"
        self.assertTrue(plan_file.is_file())

    def test_user_step_records_plan_only(self):
        target = self._mk_target()
        plan = self._plan()
        s = self._create_session(target, ["RECOVERY_STEP_CREATE_RECOVERY_USER"], plan)
        r = mod.execute_recovery_minimal({
            "session_id": s["session_id"],
            "confirmation_token": s["confirmation_token"],
            "target_path": target,
            "plan": plan,
        })
        self.assertEqual(r.get("code"), "RECOVERY_MINIMAL_EXECUTE_COMPLETED")
        plan_file = Path(target) / "var/log/setuphelfer/recovery_step_create_recovery_user.plan"
        self.assertTrue(plan_file.is_file())

    def test_network_step_records_plan_only(self):
        target = self._mk_target()
        plan = self._plan()
        s = self._create_session(target, ["RECOVERY_STEP_CONFIGURE_NETWORK_DHCP"], plan)
        r = mod.execute_recovery_minimal({
            "session_id": s["session_id"],
            "confirmation_token": s["confirmation_token"],
            "target_path": target,
            "plan": plan,
        })
        self.assertEqual(r.get("code"), "RECOVERY_MINIMAL_EXECUTE_COMPLETED")
        plan_file = Path(target) / "var/log/setuphelfer/recovery_step_configure_network_dhcp.plan"
        self.assertTrue(plan_file.is_file())

    def test_setuphelfer_source_missing_aborts(self):
        target = self._mk_target()
        plan = self._plan()
        mod._AGENT_SOURCE_CANDIDATES = [Path("/tmp/non-existing-setuphelfer-source")]  # force missing
        s = self._create_session(target, ["RECOVERY_STEP_INSTALL_SETUPHELPER_AGENT", "RECOVERY_STEP_WRITE_RECOVERY_NOTES"], plan)
        r = mod.execute_recovery_minimal({
            "session_id": s["session_id"],
            "confirmation_token": s["confirmation_token"],
            "target_path": target,
            "plan": plan,
        })
        self.assertEqual(r.get("code"), "RECOVERY_MINIMAL_EXECUTE_FAILED")
        self.assertIn("RECOVERY_MINIMAL_LOCAL_SOURCE_MISSING", r.get("errors", []))

    def test_step_failure_stops_following_steps(self):
        target = self._mk_target()
        plan = self._plan()
        mod._AGENT_SOURCE_CANDIDATES = [Path("/tmp/non-existing-setuphelfer-source")]
        s = self._create_session(target, ["RECOVERY_STEP_INSTALL_SETUPHELPER_AGENT", "RECOVERY_STEP_WRITE_RECOVERY_NOTES"], plan)
        r = mod.execute_recovery_minimal({
            "session_id": s["session_id"],
            "confirmation_token": s["confirmation_token"],
            "target_path": target,
            "plan": plan,
        })
        self.assertEqual(r.get("code"), "RECOVERY_MINIMAL_EXECUTE_FAILED")
        steps = r.get("steps", [])
        self.assertEqual(len(steps), 1)

    def test_no_forbidden_systemcalls_used(self):
        src = Path(mod.__file__).read_text(encoding="utf-8")
        forbidden = ["systemctl", "useradd", "passwd", "ssh-keygen", "apt", "pip", "curl", "wget", "chroot", " mount("]
        for token in forbidden:
            self.assertNotIn(token, src)

