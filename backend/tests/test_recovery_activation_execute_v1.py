"""Recovery activation controlled execute tests."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .recovery_imports import import_recovery_submodule

_BACKEND = Path(__file__).resolve().parent.parent
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))


mod = import_recovery_submodule("activation_execute")
routes_mod = import_recovery_submodule("routes")


class TestRecoveryActivationExecuteV1(unittest.TestCase):
    def setUp(self):
        mod._ACTIVATION_SESSION_STORE.clear()

    def _plan(self):
        return {
            "plan_status": "review_required",
            "blocked_steps": [],
            "required_steps": [
                {"code": "ACTIVATION_STEP_PREPARE_SSH_KEY_AUTH", "applicable": True, "auto_allowed": False},
                {"code": "ACTIVATION_STEP_DISABLE_PASSWORD_LOGIN", "applicable": True, "auto_allowed": False},
                {"code": "ACTIVATION_STEP_CREATE_RECOVERY_USER_SECURE", "applicable": True, "auto_allowed": False},
                {"code": "ACTIVATION_STEP_ENABLE_SSH_SERVICE", "applicable": True, "auto_allowed": False},
                {"code": "ACTIVATION_STEP_ENABLE_SETUPHELPER_BACKEND", "applicable": True, "auto_allowed": False},
                {"code": "ACTIVATION_STEP_BIND_BACKEND_TO_SAFE_INTERFACE", "applicable": True, "auto_allowed": False},
                {"code": "ACTIVATION_STEP_CONFIGURE_BASIC_FIREWALL", "applicable": True, "auto_allowed": False},
                {"code": "ACTIVATION_STEP_LOG_REMOTE_ACCESS_DETAILS", "applicable": True, "auto_allowed": False},
            ],
        }

    def _create_session(self, target_path: str, selected_steps: list[str]):
        out = mod.create_recovery_activation_session(
            {
                "target_path": target_path,
                "selected_steps": selected_steps,
                "plan": self._plan(),
            }
        )
        self.assertEqual(out.get("code"), "RECOVERY_ACTIVATION_SESSION_CREATED")
        return out

    def _execute(self, session: dict[str, object], target_path: str, **extra):
        body = {
            "activation_session_id": session.get("activation_session_id"),
            "confirmation_token": session.get("confirmation_token"),
            "target_path": target_path,
            "plan": self._plan(),
        }
        body.update(extra)
        return mod.execute_recovery_activation(body)

    def test_session_single_use(self):
        with tempfile.TemporaryDirectory() as td:
            s = self._create_session(td, ["ACTIVATION_STEP_DISABLE_PASSWORD_LOGIN"])
            first = self._execute(s, td)
            self.assertEqual(first.get("code"), "RECOVERY_ACTIVATION_EXECUTE_COMPLETED")
            second = self._execute(s, td)
            self.assertEqual(second.get("code"), "RECOVERY_ACTIVATION_SESSION_ALREADY_USED")

    def test_ssh_key_missing(self):
        with tempfile.TemporaryDirectory() as td:
            s = self._create_session(td, ["ACTIVATION_STEP_PREPARE_SSH_KEY_AUTH"])
            out = self._execute(s, td)
            self.assertEqual(out.get("code"), "RECOVERY_ACTIVATION_EXECUTE_FAILED")
            self.assertEqual(out.get("steps", [])[0].get("result_code"), "RECOVERY_ACTIVATION_SSH_KEY_REQUIRED")

    def test_ssh_key_invalid_private_or_multiline(self):
        with tempfile.TemporaryDirectory() as td:
            s1 = self._create_session(td, ["ACTIVATION_STEP_PREPARE_SSH_KEY_AUTH"])
            out1 = self._execute(s1, td, ssh_public_key="-----BEGIN OPENSSH PRIVATE KEY-----")
            self.assertEqual(out1.get("steps", [])[0].get("result_code"), "RECOVERY_ACTIVATION_SSH_KEY_INVALID")

            s2 = self._create_session(td, ["ACTIVATION_STEP_PREPARE_SSH_KEY_AUTH"])
            out2 = self._execute(s2, td, ssh_public_key="ssh-ed25519 AAAA\nBBBB")
            self.assertEqual(out2.get("steps", [])[0].get("result_code"), "RECOVERY_ACTIVATION_SSH_KEY_INVALID")

    def test_valid_ssh_key_written_under_target_only(self):
        with tempfile.TemporaryDirectory() as td:
            s = self._create_session(td, ["ACTIVATION_STEP_PREPARE_SSH_KEY_AUTH"])
            key = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIFakeKey material@test"
            out = self._execute(s, td, ssh_public_key=key)
            self.assertEqual(out.get("code"), "RECOVERY_ACTIVATION_EXECUTE_COMPLETED")
            ak = Path(td) / "home/setuphelfer-recovery/.ssh/authorized_keys"
            self.assertTrue(ak.exists())
            self.assertIn("ssh-ed25519", ak.read_text(encoding="utf-8"))

    def test_target_root_blocked(self):
        s = self._create_session("/tmp", ["ACTIVATION_STEP_DISABLE_PASSWORD_LOGIN"])
        out = self._execute(s, "/")
        self.assertEqual(out.get("code"), "RECOVERY_ACTIVATION_TARGET_INVALID")

    def test_path_traversal_blocked(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            with self.assertRaises(ValueError):
                mod._safe_under_target(root, "../escape.txt", create_parent=True)

    def test_password_and_root_login_disabled_only_in_target(self):
        with tempfile.TemporaryDirectory() as td:
            s = self._create_session(td, ["ACTIVATION_STEP_DISABLE_PASSWORD_LOGIN"])
            out = self._execute(s, td)
            self.assertEqual(out.get("code"), "RECOVERY_ACTIVATION_EXECUTE_COMPLETED")
            cfg = Path(td) / "etc/ssh/sshd_config.setuphelfer_recovery"
            content = cfg.read_text(encoding="utf-8")
            self.assertIn("PasswordAuthentication no", content)
            self.assertIn("PermitRootLogin no", content)

    def test_lan_bind_without_confirmation_stays_localhost(self):
        with tempfile.TemporaryDirectory() as td:
            s = self._create_session(td, ["ACTIVATION_STEP_BIND_BACKEND_TO_SAFE_INTERFACE"])
            out = self._execute(s, td, allow_lan_backend_bind=False)
            self.assertEqual(out.get("code"), "RECOVERY_ACTIVATION_EXECUTE_COMPLETED")
            cfg = json.loads((Path(td) / "opt/setuphelfer/backend-bind.json").read_text(encoding="utf-8"))
            self.assertEqual(cfg.get("host"), "127.0.0.1")
            self.assertEqual(out.get("warnings"), [])

    def test_lan_bind_with_confirmation_adds_warning(self):
        with tempfile.TemporaryDirectory() as td:
            s = self._create_session(td, ["ACTIVATION_STEP_BIND_BACKEND_TO_SAFE_INTERFACE"])
            out = self._execute(s, td, allow_lan_backend_bind=True)
            self.assertEqual(out.get("code"), "RECOVERY_ACTIVATION_EXECUTE_COMPLETED")
            cfg = json.loads((Path(td) / "opt/setuphelfer/backend-bind.json").read_text(encoding="utf-8"))
            self.assertEqual(cfg.get("host"), "0.0.0.0")
            self.assertIn("RECOVERY_ACTIVATION_LAN_BIND_REQUIRES_CONFIRMATION", out.get("warnings", []))

    def test_missing_backend_source_stops_follow_steps(self):
        with tempfile.TemporaryDirectory() as td:
            s = self._create_session(td, [
                "ACTIVATION_STEP_ENABLE_SETUPHELPER_BACKEND",
                "ACTIVATION_STEP_LOG_REMOTE_ACCESS_DETAILS",
            ])
            original = list(mod._BACKEND_SOURCE_CANDIDATES)
            try:
                mod._BACKEND_SOURCE_CANDIDATES = [Path(td) / "missing-source"]
                out = self._execute(s, td)
            finally:
                mod._BACKEND_SOURCE_CANDIDATES = original
            self.assertEqual(out.get("code"), "RECOVERY_ACTIVATION_EXECUTE_FAILED")
            self.assertEqual(len(out.get("steps", [])), 1)

    def test_step_failure_stops_next_steps(self):
        with tempfile.TemporaryDirectory() as td:
            s = self._create_session(td, [
                "ACTIVATION_STEP_PREPARE_SSH_KEY_AUTH",
                "ACTIVATION_STEP_DISABLE_PASSWORD_LOGIN",
            ])
            out = self._execute(s, td)
            self.assertEqual(out.get("code"), "RECOVERY_ACTIVATION_EXECUTE_FAILED")
            self.assertEqual(len(out.get("steps", [])), 1)

    def test_expired_session(self):
        with tempfile.TemporaryDirectory() as td:
            s = self._create_session(td, ["ACTIVATION_STEP_DISABLE_PASSWORD_LOGIN"])
            sid = str(s.get("activation_session_id"))
            mod._ACTIVATION_SESSION_STORE[sid]["expires_at"] = (datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat()
            out = self._execute(s, td)
            self.assertEqual(out.get("code"), "RECOVERY_ACTIVATION_SESSION_EXPIRED")

    def test_no_forbidden_calls(self):
        src = Path(mod.__file__).read_text(encoding="utf-8")
        forbidden = ["systemctl", "useradd", "passwd", "chroot", "mount", "curl", "wget"]
        for token in forbidden:
            self.assertNotIn(token, src)

    def test_execute_route_contract_present(self):
        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        app = FastAPI()
        app.include_router(routes_mod.router)
        c = TestClient(app)
        resp = c.post("/api/recovery/activation/execute", json={})
        self.assertEqual(resp.status_code, 422)


if __name__ == "__main__":
    unittest.main()
