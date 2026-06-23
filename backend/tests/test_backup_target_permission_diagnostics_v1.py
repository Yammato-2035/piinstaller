"""
BR-001: Diagnose bei nicht traversierbarem Pfad unter /media — STORAGE-006 statt falscher STORAGE-001.
"""

from __future__ import annotations

import importlib.util
import os
import shutil
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from core.safe_device import WriteTargetProtectionError, validate_write_target


def _has_testclient_stack() -> bool:
    return importlib.util.find_spec("fastapi") is not None and importlib.util.find_spec("httpx") is not None


class TestBackupTargetPermissionDiagnosticsV1(unittest.TestCase):
    def test_media_traverse_denied_is_006_not_001(self) -> None:
        target = Path("/media/gabriel/setuphelfer-test-traverse-denied/target")

        orig_stat = os.stat

        def fake_stat(path_str: str | os.PathLike[str], *args: object, **kwargs: object):
            s = os.fspath(path_str).rstrip("/")
            if s == "/media/gabriel":
                raise PermissionError("simulated")
            return orig_stat(path_str, *args, **kwargs)

        with patch("core.safe_device.os.stat", side_effect=fake_stat):
            with self.assertRaises(WriteTargetProtectionError) as ctx:
                validate_write_target(target, runner=None)
        self.assertEqual(ctx.exception.diagnosis_id, "STORAGE-PROTECTION-006")
        self.assertNotEqual(ctx.exception.diagnosis_id, "STORAGE-PROTECTION-001")

    def test_root_still_blocked_001(self) -> None:
        with self.assertRaises(WriteTargetProtectionError) as ctx:
            validate_write_target(Path("/"), runner=None)
        self.assertEqual(ctx.exception.diagnosis_id, "STORAGE-PROTECTION-001")

    def test_tmp_setuphelfer_prefix_still_ok_with_mocks(self) -> None:
        import json
        from subprocess import CompletedProcess

        mount = "/tmp/setuphelfer-test/perm-diag-ok"
        Path(mount).mkdir(parents=True, exist_ok=True)
        self.addCleanup(lambda: shutil.rmtree(mount, ignore_errors=True))

        def fake_run(argv, **kwargs):
            if argv[:2] == ["lsblk", "-J"]:
                body = {
                    "blockdevices": [
                        {
                            "name": "sdb",
                            "path": "/dev/sdb",
                            "type": "disk",
                            "tran": "usb",
                            "children": [
                                {
                                    "name": "sdb1",
                                    "path": "/dev/sdb1",
                                    "type": "part",
                                    "fstype": "ext4",
                                    "mountpoints": [mount],
                                }
                            ],
                        }
                    ]
                }
                return CompletedProcess(argv, 0, json.dumps(body), "")
            if argv[:3] == ["findmnt", "-J", "-T"]:
                body = {
                    "filesystems": [
                        {"source": "/dev/sdb1", "target": mount, "fstype": "ext4"},
                    ]
                }
                return CompletedProcess(argv, 0, json.dumps(body), "")
            return CompletedProcess(argv, 1, "", "")

        validate_write_target(Path(mount) / "arch.tar.gz", runner=fake_run)

    @unittest.skipUnless(_has_testclient_stack(), "TestClient stack")
    def test_target_check_api_maps_006_to_backup_target_traverse_denied(self) -> None:
        import app as app_module
        from fastapi.testclient import TestClient

        with patch(
            "core.backup_target_check_handler.rt.validate_backup_dir",
            side_effect=ValueError("STORAGE-PROTECTION-006: Simulated traverse denied"),
        ):
            client = TestClient(app_module.app)
            r = client.get(
                "/api/backup/target-check",
                params={"backup_dir": "/media/gabriel/setuphelfer-back", "create": 0},
            )
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertEqual(body.get("code"), "backup.target_traverse_denied")
        self.assertEqual(body.get("details", {}).get("diagnosis_id"), "STORAGE-PROTECTION-006")
        self.assertNotIn("STORAGE-PROTECTION-001", body.get("message", ""))
        self.assertNotIn("STORAGE-PROTECTION-001", str(body.get("details", {})))
