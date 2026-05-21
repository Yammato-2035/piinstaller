"""Rescue offline backup plan — plan only, no execution."""

from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from core.backup_profiles import CANONICAL_BACKUP_RUNNER_MODULE  # noqa: E402
from rescue.backup_orchestrator import build_rescue_offline_backup_plan  # noqa: E402

_BOOT = {
    "live_system": "false",
    "rescue_mode": "true",
    "source_root": "/mnt/setuphelfer-source",
    "runtime_root": "/opt/setuphelfer",
    "evidence_root": "/tmp/evidence",
    "ui_mode": "headless",
    "network_available": "false",
    "allowed_write_roots": [],
    "forbidden_write_roots": ["/"],
}


class RescueOfflineBackupPlanTests(unittest.TestCase):
    def _ready_plan(self, **kwargs: object) -> dict:
        defaults = {
            "source_root": "/mnt/setuphelfer-source",
            "target_path": "/media/usb-backup/backup.tar",
            "boot_context": dict(_BOOT),
            "storage_snapshot": {
                "backup_target_candidates": [
                    {"device_hint": "/media/usb-backup", "role": "backup_target"},
                ],
            },
        }
        defaults.update(kwargs)
        return build_rescue_offline_backup_plan(**defaults)  # type: ignore[arg-type]

    def test_ready_valid_external_target(self) -> None:
        res = self._ready_plan()
        self.assertEqual(res["status"], "ready")
        self.assertFalse(res["plan"]["execution_allowed"])
        self.assertEqual(res["plan"]["runner"], CANONICAL_BACKUP_RUNNER_MODULE)

    def test_blocked_missing_source_root(self) -> None:
        res = build_rescue_offline_backup_plan(
            source_root="",
            target_path="/media/usb/x",
            boot_context={**_BOOT, "source_root": ""},
        )
        self.assertEqual(res["status"], "blocked")
        self.assertIn("missing_source_root", res["blocked_reasons"])

    def test_blocked_missing_target_path(self) -> None:
        res = build_rescue_offline_backup_plan(
            source_root="/mnt/source",
            target_path="",
            boot_context={**_BOOT, "source_root": "/mnt/source"},
        )
        self.assertEqual(res["status"], "blocked")
        self.assertIn("missing_target_path", res["blocked_reasons"])

    def test_blocked_target_under_source(self) -> None:
        res = self._ready_plan(
            source_root="/mnt/source",
            target_path="/mnt/source/backups/out.tar",
            boot_context={**_BOOT, "source_root": "/mnt/source"},
        )
        self.assertEqual(res["status"], "blocked")
        self.assertIn("target_under_source_root", res["blocked_reasons"])

    def test_blocked_unknown_profile(self) -> None:
        res = self._ready_plan(backup_profile_id="no-such-profile")
        self.assertEqual(res["status"], "blocked")
        self.assertIn("unknown_backup_profile", res["blocked_reasons"])

    def test_execution_always_false(self) -> None:
        res = self._ready_plan()
        self.assertFalse(res["plan"]["execution_allowed"])

    def test_no_tar_subprocess(self) -> None:
        with patch.object(subprocess, "run", side_effect=AssertionError("subprocess.run")):
            with patch.object(subprocess, "Popen", side_effect=AssertionError("subprocess.Popen")):
                self._ready_plan()
                build_rescue_offline_backup_plan(
                    source_root="/mnt/s",
                    target_path="/",
                    boot_context=_BOOT,
                )


if __name__ == "__main__":
    unittest.main()
