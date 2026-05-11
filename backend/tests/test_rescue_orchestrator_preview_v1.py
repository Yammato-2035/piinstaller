"""Rescue Orchestrator Phase 1: Preview-only Contract/Behavior."""

from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
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


orch = _load("rescue/orchestrator.py", "setuphelfer_rescue_orch_test")


class _Resp:
    def __init__(self, data: dict):
        self._data = data

    def model_dump(self):
        return self._data




def _assert_preview_contract(tc: unittest.TestCase, data: dict) -> None:
    for k in (
        "code",
        "preview_id",
        "target",
        "backup",
        "safety",
        "verify",
        "preview",
        "preflight",
        "warnings",
        "errors",
    ):
        tc.assertIn(k, data)
    tc.assertIsInstance(data["target"], dict)
    tc.assertIsInstance(data["backup"], dict)
    tc.assertIsInstance(data["safety"], dict)
    tc.assertIsInstance(data["verify"], dict)
    tc.assertIsInstance(data["preview"], dict)
    tc.assertIsInstance(data["preflight"], dict)
    tc.assertIsInstance(data["warnings"], list)
    tc.assertIsInstance(data["errors"], list)

def _inspect_base() -> dict:
    return {
        "storage": {
            "devices_classified": [
                {
                    "device": "/dev/sdz",
                    "type": "disk",
                    "size": "10G",
                    "partitions": [
                        {
                            "device": "/dev/sdz1",
                            "type": "part",
                            "category": "backup_candidate",
                            "mountpoint": "/tmp",
                            "fstype": "ext4",
                            "partitions": [],
                        }
                    ],
                }
            ],
            "devices_raw": [{"device": "/dev/sdz", "type": "disk", "partitions": [{"device": "/dev/sdz1"}]}],
            "mountability": [],
        },
        "filesystems": {"detected": {"/dev/sdz1": {"type": "ext4"}}, "uuid_conflicts": {}},
        "capabilities": {},
    }


class TestRescueOrchestratorPreviewV1(unittest.TestCase):
    def setUp(self):
        self.old_collect = orch.collect_inspect_result
        self.old_eval = orch.evaluate_write_target
        self.old_verify = orch.verify_basic
        self.old_dryrun = orch.run_restore_dryrun_pipeline
        self.old_pf = dict(orch._PREFLIGHT_PLAN_STORE)
        orch._PREFLIGHT_PLAN_STORE.clear()

    def tearDown(self):
        orch.collect_inspect_result = self.old_collect
        orch.evaluate_write_target = self.old_eval
        orch.verify_basic = self.old_verify
        orch.run_restore_dryrun_pipeline = self.old_dryrun
        orch._PREFLIGHT_PLAN_STORE.clear()
        orch._PREFLIGHT_PLAN_STORE.update(self.old_pf)

    def test_blocked_target(self):
        orch.collect_inspect_result = lambda: _Resp(_inspect_base())
        orch.evaluate_write_target = lambda *_a, **_k: {
            "allowed": False,
            "reason_code": "SAFETY_SYSTEM_DISK",
            "risk_level": "high",
        }

        r = orch.preview_rescue_restore(
            {
                "backup_path": "/tmp/backup.tar.gz",
                "target_device": "/dev/sdz",
            }
        )
        self.assertEqual(r.get("code"), "RESCUE_TARGET_BLOCKED")
        _assert_preview_contract(self, r)

    def test_backup_not_found(self):
        orch.collect_inspect_result = lambda: _Resp(_inspect_base())
        orch.evaluate_write_target = lambda *_a, **_k: {
            "allowed": True,
            "reason_code": "SAFETY_BACKUP_TARGET_OK",
            "risk_level": "low",
        }
        r = orch.preview_rescue_restore(
            {
                "backup_path": "/tmp/definitely-not-existing-preflight-backup.tar.gz",
                "target_device": "/dev/sdz",
            }
        )
        self.assertEqual(r.get("code"), "RESCUE_BACKUP_NOT_FOUND")
        _assert_preview_contract(self, r)

    def test_verify_failed(self):
        orch.collect_inspect_result = lambda: _Resp(_inspect_base())
        orch.evaluate_write_target = lambda *_a, **_k: {
            "allowed": True,
            "reason_code": "SAFETY_BACKUP_TARGET_OK",
            "risk_level": "low",
        }
        orch.verify_basic = lambda *_a, **_k: (False, "backup.verify_failed", None)

        with tempfile.NamedTemporaryFile(suffix=".tar.gz") as tf:
            r = orch.preview_rescue_restore(
                {
                    "backup_path": tf.name,
                    "target_device": "/dev/sdz",
                }
            )
        self.assertEqual(r.get("code"), "RESCUE_BACKUP_VERIFY_FAILED")
        _assert_preview_contract(self, r)

    def test_preview_success_with_mocked_dryrun(self):
        orch.collect_inspect_result = lambda: _Resp(_inspect_base())
        orch.evaluate_write_target = lambda *_a, **_k: {
            "allowed": True,
            "reason_code": "SAFETY_BACKUP_TARGET_OK",
            "risk_level": "low",
        }
        orch.verify_basic = lambda *_a, **_k: (True, "backup.verify_ok", None)

        class _DryResp:
            def model_dump(self):
                return {
                    "status": "ok",
                    "restore_risk_level": "yellow",
                    "restore_decision": "proceed_with_explicit_risk_ack",
                    "allow_restore": False,
                    "recommended_actions": ["rescue.action.review_target"],
                    "findings": [{"code": "rescue.finding.sample"}],
                }

        orch.run_restore_dryrun_pipeline = lambda *_a, **_k: _DryResp()

        with tempfile.NamedTemporaryFile(suffix=".tar.gz") as tf:
            r = orch.preview_rescue_restore(
                {
                    "backup_path": tf.name,
                    "target_device": "/dev/sdz",
                }
            )

        self.assertEqual(r.get("code"), "RESCUE_PREVIEW_CREATED")
        _assert_preview_contract(self, r)

    def test_execute_function_present_phase2(self):
        self.assertTrue(hasattr(orch, "execute_rescue_restore"))


try:
    from fastapi.testclient import TestClient
    from app import app

    _HAS_APP = True
except Exception:
    _HAS_APP = False
    TestClient = None
    app = None


@unittest.skipUnless(_HAS_APP, "FastAPI TestClient oder app nicht verfügbar")
class TestRescuePreviewRoute(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app, base_url="http://localhost")

    def test_preview_route_contract(self):
        r = self.client.post(
            "/api/rescue/preview",
            json={
                "backup_path": "/tmp/not-there.tar.gz",
                "target_device": "/dev/not-present",
            },
        )
        self.assertEqual(r.status_code, 200, r.text)
        data = r.json()
        _assert_preview_contract(self, data)

