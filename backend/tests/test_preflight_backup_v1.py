"""Preflight Backup v1 – Plan/Token/Safety Orchestrierung ohne neue Engine."""

from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

_BACKEND = Path(__file__).resolve().parent.parent
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))


def _load_module(rel: str, mod_name: str):
    p = _BACKEND / rel
    spec = importlib.util.spec_from_file_location(mod_name, p)
    if not spec or not spec.loader:
        raise ImportError(rel)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


pf = _load_module("preflight/backup.py", "setuphelfer_preflight_backup_test")


def _inspect_payload(*, reason: str = "SAFETY_BACKUP_TARGET_OK", include_unknown_source: bool = False) -> dict:
    part = {
        "device": "/dev/sdz1",
        "type": "part",
        "category": "backup_candidate" if reason == "SAFETY_BACKUP_TARGET_OK" else "unknown",
        "mountpoint": None,
        "fstype": "ext4",
        "partitions": [],
    }
    disk = {
        "device": "/dev/sdz",
        "type": "disk",
        "size": "10G",
        "category": "unknown",
        "partitions": [part],
    }
    payload = {
        "storage": {
            "devices_classified": [disk],
            "devices_raw": [{"device": "/dev/sdz", "type": "disk", "partitions": [{"device": "/dev/sdz1"}]}],
            "mountability": [],
        },
        "filesystems": {
            "detected": {"/dev/sdz1": {"type": "ext4"}},
            "uuid_conflicts": {},
        },
        "classification": {"system_type": "LINUX"},
    }

    if reason == "SAFETY_EMPTY_DISK":
        payload["storage"]["devices_classified"] = [
            {"device": "/dev/sdz", "type": "disk", "size": "10G", "category": "unknown", "partitions": []}
        ]
        payload["storage"]["devices_raw"] = [{"device": "/dev/sdz", "type": "disk", "partitions": []}]
        payload["filesystems"]["detected"] = {}

    if include_unknown_source:
        payload["storage"]["devices_classified"][0]["partitions"].append(
            {
                "device": "/dev/sdz2",
                "type": "part",
                "category": "unknown",
                "mountpoint": "/mnt/unknown-candidate",
                "fstype": "ext4",
                "partitions": [],
            }
        )

    return payload


class TestPreflightBackupV1(unittest.TestCase):
    def setUp(self):
        pf._PLAN_STORE.clear()

    def test_preview_creates_plan_and_token(self):
        with tempfile.TemporaryDirectory() as td:
            payload = _inspect_payload()
            # Mountpunkt für backup_candidate setzen
            payload["storage"]["devices_classified"][0]["partitions"][0]["mountpoint"] = td
            out = pf.create_backup_preview(target_device="/dev/sdz", inspect_result=payload)
            self.assertIn(out.get("code"), {"PREFLIGHT_PLAN_CREATED", "PREFLIGHT_TARGET_REQUIRES_CONFIRMATION"})
            self.assertTrue(out.get("plan_id"))
            self.assertTrue(out.get("confirmation_token"))

    def test_execute_blocked_target(self):
        payload = _inspect_payload(reason="SAFETY_BACKUP_TARGET_OK")

        # Preview erlaubt erst einmal
        out = pf.create_backup_preview(target_device="/dev/sdz", inspect_result=payload)
        pid = out.get("plan_id")
        tok = out.get("confirmation_token")
        self.assertTrue(pid and tok)

        # Danach Inspect-Lage verändert -> blockiert
        blocked_payload = _inspect_payload(reason="SAFETY_UNKNOWN_DEVICE")
        ex = pf.execute_backup_plan(
            plan_id=str(pid),
            confirmation_token=str(tok),
            inspect_result=blocked_payload,
        )
        self.assertEqual(ex.get("code"), "PREFLIGHT_TARGET_BLOCKED")

    def test_execute_missing_or_invalid_token_blocked(self):
        with tempfile.TemporaryDirectory() as td:
            payload = _inspect_payload()
            payload["storage"]["devices_classified"][0]["partitions"][0]["mountpoint"] = td
            out = pf.create_backup_preview(target_device="/dev/sdz", inspect_result=payload)
            pid = str(out.get("plan_id"))
            bad = pf.execute_backup_plan(
                plan_id=pid,
                confirmation_token="wrong-token",
                inspect_result=payload,
            )
            self.assertEqual(bad.get("code"), "PREFLIGHT_TOKEN_INVALID")

    def test_unknown_source_not_auto_executable(self):
        payload = _inspect_payload(include_unknown_source=True)
        sources = pf.list_candidate_sources(payload)
        unknown = [s for s in sources if s.get("kind") == "unknown_partition_candidate"]
        self.assertTrue(unknown)
        self.assertEqual(unknown[0].get("code"), "PREFLIGHT_SOURCE_UNREADABLE")

    def test_uses_existing_backup_engine_without_duplication(self):
        calls = {"create_file_backup": 0, "verify_basic": 0}

        class _Result:
            ok = True
            archive_path = "/tmp/fake-preflight.tar.gz"
            manifest = {"entries": []}
            message_key = "backup.operation_ok"

        def fake_create_file_backup(*args, **kwargs):
            calls["create_file_backup"] += 1
            return _Result()

        def fake_verify_basic(*args, **kwargs):
            calls["verify_basic"] += 1
            return (True, "backup.verify_ok", None)

        old_create = pf.create_file_backup
        old_verify = pf.verify_basic
        try:
            pf.create_file_backup = fake_create_file_backup
            pf.verify_basic = fake_verify_basic

            with tempfile.TemporaryDirectory() as td:
                payload = _inspect_payload()
                payload["storage"]["devices_classified"][0]["partitions"][0]["mountpoint"] = td
                prev = pf.create_backup_preview(target_device="/dev/sdz", inspect_result=payload)
                ex = pf.execute_backup_plan(
                    plan_id=str(prev["plan_id"]),
                    confirmation_token=str(prev["confirmation_token"]),
                    inspect_result=payload,
                )
                self.assertIn(ex.get("code"), {"PREFLIGHT_BACKUP_VERIFIED", "PREFLIGHT_BACKUP_VERIFY_FAILED"})
                self.assertEqual(calls["create_file_backup"], 1)
                self.assertEqual(calls["verify_basic"], 1)
        finally:
            pf.create_file_backup = old_create
            pf.verify_basic = old_verify


try:
    from fastapi.testclient import TestClient
    from app import app

    _HAS_APP = True
except Exception:
    _HAS_APP = False
    TestClient = None
    app = None


@unittest.skipUnless(_HAS_APP, "FastAPI TestClient oder app nicht verfügbar")
class TestPreflightRoutesV1(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app, base_url="http://localhost")

    def test_sources_endpoint_contract(self):
        r = self.client.get('/api/preflight/sources')
        self.assertEqual(r.status_code, 200, r.text)
        data = r.json()
        self.assertIn('code', data)
        self.assertIn('sources', data)
        self.assertIsInstance(data['sources'], list)
        # optionale, aber stabil normalisierte Felder
        self.assertIn('warnings', data)
        self.assertIn('errors', data)
        self.assertIsInstance(data['warnings'], list)
        self.assertIsInstance(data['errors'], list)

    def test_preview_endpoint_contract_blocked_target(self):
        # bewusst unplausibles Device => defensiv blockiert, ohne Hardware-Abhängigkeit
        r = self.client.post('/api/preflight/backup/preview', json={'target_device': '/dev/not-present-preflight'})
        self.assertEqual(r.status_code, 200, r.text)
        data = r.json()
        for key in (
            'code',
            'plan_id',
            'confirmation_token',
            'target_device',
            'target_reason',
            'requires_confirmation',
            'sources',
        ):
            self.assertIn(key, data)
        self.assertIsInstance(data['sources'], list)
        self.assertIsInstance(data['requires_confirmation'], bool)
        self.assertEqual(data['code'], 'PREFLIGHT_TARGET_BLOCKED')

    def test_execute_endpoint_contract_invalid_token(self):
        r = self.client.post(
            '/api/preflight/backup/execute',
            json={'plan_id': 'deadbeef', 'confirmation_token': 'invalid-token-123'},
        )
        self.assertEqual(r.status_code, 200, r.text)
        data = r.json()
        self.assertIn('code', data)
        self.assertIn('plan_id', data)
        # stabilisiert: result vorhanden (kann leer sein)
        self.assertIn('result', data)
        self.assertIsInstance(data['result'], dict)
        # optionale Felder stabil vorhanden
        self.assertIn('details', data)
        self.assertIn('errors', data)
        self.assertIsInstance(data['details'], dict)
        self.assertIsInstance(data['errors'], list)
        self.assertEqual(data['code'], 'PREFLIGHT_TOKEN_INVALID')

