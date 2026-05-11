"""Write-Safety: evaluate_write_target (reine Logik, keine I/O)."""

from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

_BACKEND = Path(__file__).resolve().parent.parent
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))


def _load_wg():
    path = _BACKEND / "safety" / "write_guard.py"
    spec = importlib.util.spec_from_file_location("setuphelfer_write_guard_test", path)
    if not spec or not spec.loader:
        raise ImportError("write_guard")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_wg = _load_wg()
evaluate_write_target = _wg.evaluate_write_target
build_write_safety_summary = _wg.build_write_safety_summary


def _ir(**kwargs: dict) -> dict:
    base: dict = {
        "storage": {
            "devices_classified": [],
            "devices_raw": [],
            "mountability": [],
        },
        "filesystems": {"detected": {}, "uuid_conflicts": {}},
        "boot": {},
        "classification": {},
    }
    base.update(kwargs)
    return base


class TestWriteGuard(unittest.TestCase):
    def test_system_disk_blocked(self):
        r = evaluate_write_target(
            "/dev/sdX",
            _ir(
                storage={
                    "devices_classified": [
                        {
                            "device": "/dev/sdX",
                            "type": "disk",
                            "size": "1G",
                            "partitions": [
                                {
                                    "device": "/dev/sdX1",
                                    "type": "part",
                                    "category": "system_disk",
                                    "mountpoint": "/",
                                    "fstype": "ext4",
                                }
                            ],
                        }
                    ],
                    "devices_raw": [
                        {
                            "device": "/dev/sdX",
                            "type": "disk",
                            "partitions": [{"device": "/dev/sdX1", "type": "part"}],
                        }
                    ],
                    "mountability": [],
                },
                filesystems={"detected": {"/dev/sdX1": {"type": "ext4", "uuid": "u1"}}, "uuid_conflicts": {}},
            ),
        )
        self.assertFalse(r["allowed"])
        self.assertEqual(r["reason_code"], "SAFETY_SYSTEM_DISK")

    def test_empty_disk_allowed(self):
        r = evaluate_write_target(
            "/dev/sdY",
            _ir(
                storage={
                    "devices_classified": [
                        {"device": "/dev/sdY", "type": "disk", "size": "2G", "partitions": []}
                    ],
                    "devices_raw": [
                        {"device": "/dev/sdY", "type": "disk", "partitions": []}
                    ],
                    "mountability": [],
                }
            ),
        )
        self.assertTrue(r["allowed"])
        self.assertEqual(r["reason_code"], "SAFETY_EMPTY_DISK")

    def test_ntfs_only_not_auto_allowed(self):
        r = evaluate_write_target(
            "/dev/sdZ",
            _ir(
                storage={
                    "devices_classified": [
                        {
                            "device": "/dev/sdZ",
                            "type": "disk",
                            "partitions": [
                                {
                                    "device": "/dev/sdZ1",
                                    "type": "part",
                                    "category": "unknown",
                                    "fstype": "ntfs",
                                }
                            ],
                        }
                    ],
                    "devices_raw": [
                        {
                            "device": "/dev/sdZ",
                            "type": "disk",
                            "partitions": [{"device": "/dev/sdZ1"}],
                        }
                    ],
                    "mountability": [],
                },
                filesystems={"detected": {"/dev/sdZ1": {"type": "ntfs"}}, "uuid_conflicts": {}},
            ),
        )
        self.assertFalse(r["allowed"])
        self.assertEqual(r["reason_code"], "SAFETY_WINDOWS_DETECTED")

    def test_unknown_disk_blocked(self):
        r = evaluate_write_target("/dev/nonexistent", _ir())
        self.assertFalse(r["allowed"])
        self.assertEqual(r["reason_code"], "SAFETY_UNKNOWN_DEVICE")

    def test_summary_contains_targets(self):
        summary = build_write_safety_summary(
            _ir(
                storage={
                    "devices_classified": [
                        {"device": "/dev/sda", "type": "disk", "size": "10G", "partitions": []}
                    ],
                    "devices_raw": [
                        {"device": "/dev/sda", "type": "disk", "partitions": []}
                    ],
                    "mountability": [],
                }
            )
        )
        self.assertEqual(summary.get("policy_code"), "safety.summary.v1")
        self.assertTrue(summary.get("targets"))


try:
    from fastapi.testclient import TestClient
    from app import app as _app

    _HAS_APP = True
except Exception:
    _HAS_APP = False
    TestClient = None
    _app = None


@unittest.skipUnless(_HAS_APP, "FastAPI TestClient oder app nicht verfügbar")
class TestSafetyEndpoint(unittest.TestCase):
    def test_get_safety_targets_http(self):
        client = TestClient(_app, base_url="http://localhost")
        r = client.get("/api/safety/targets")
        self.assertEqual(r.status_code, 200, r.text)
        data = r.json()
        self.assertIsInstance(data, list)
        if data:
            row = data[0]
            for key in ("device", "size", "classification", "write_allowed", "reason_code"):
                self.assertIn(key, row)
