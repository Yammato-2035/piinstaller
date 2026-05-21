"""Rescue restore preview plan — handoff only, no restore execution."""

from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from core.restore_profiles import (  # noqa: E402
    CANONICAL_RESTORE_PREVIEW_MODULE,
    CANONICAL_VERIFY_MODULE,
)
from rescue.restore_preview_orchestrator import build_rescue_restore_preview_plan  # noqa: E402

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


class RescueRestorePreviewPlanTests(unittest.TestCase):
    def _ready(self, **kwargs: object) -> dict:
        defaults: dict = {
            "backup_archive_path": "/media/usb-backup/archives/full-2026.tar.gz",
            "manifest_path": "/media/usb-backup/archives/manifest.json",
            "target_device_or_path": "/dev/sdb1",
            "boot_context": dict(_BOOT),
            "verify_status": "ok",
            "target_classification": "external",
            "existing_filesystems": False,
            "existing_os_indicators": False,
            "user_data_indicators": False,
        }
        defaults.update(kwargs)
        return build_rescue_restore_preview_plan(**defaults)  # type: ignore[arg-type]

    def test_ready_valid_inputs(self) -> None:
        res = self._ready()
        self.assertEqual(res["status"], "ready")
        self.assertFalse(res["plan"]["execution_allowed"])
        self.assertIn("modules.rescue_restore_dryrun", res["plan"]["restore_engine"])
        self.assertEqual(res["plan"]["verify_engine"], CANONICAL_VERIFY_MODULE)

    def test_review_required_verify_unknown(self) -> None:
        res = self._ready(verify_status="unknown")
        self.assertEqual(res["status"], "review_required")
        self.assertIn("VERIFY_STATUS_UNKNOWN", res["warnings"])

    def test_blocked_verify_failed(self) -> None:
        res = self._ready(verify_status="failed")
        self.assertEqual(res["status"], "blocked")
        self.assertIn("verify_status_failed", res["blocked_reasons"])

    def test_blocked_missing_archive(self) -> None:
        res = self._ready(backup_archive_path="")
        self.assertIn("missing_backup_archive_path", res["blocked_reasons"])

    def test_blocked_missing_manifest(self) -> None:
        res = self._ready(manifest_path="")
        self.assertIn("missing_manifest_path", res["blocked_reasons"])

    def test_blocked_missing_target(self) -> None:
        res = self._ready(target_device_or_path="")
        self.assertIn("missing_target_device_or_path", res["blocked_reasons"])

    def test_blocked_unknown_profile(self) -> None:
        res = self._ready(restore_profile_id="unknown-profile")
        self.assertIn("unknown_restore_profile", res["blocked_reasons"])

    def test_blocked_target_like_backup_media(self) -> None:
        res = self._ready(
            target_device_or_path="/media/usb-backup",
            backup_archive_path="/media/usb-backup/full.tar.gz",
            manifest_path="/media/usb-backup/manifest.json",
        )
        self.assertIn("target_looks_like_backup_media", res["blocked_reasons"])

    def test_blocked_backup_before_overwrite_required(self) -> None:
        res = self._ready(
            existing_filesystems=True,
            user_data_indicators=True,
            backup_evidence=None,
        )
        self.assertEqual(res["status"], "blocked")
        self.assertIn("backup_before_overwrite_required", res["blocked_reasons"])

    def test_execution_always_false(self) -> None:
        self.assertFalse(self._ready()["plan"]["execution_allowed"])

    def test_no_tar_subprocess(self) -> None:
        with patch.object(subprocess, "run", side_effect=AssertionError("subprocess.run")):
            with patch.object(subprocess, "Popen", side_effect=AssertionError("subprocess.Popen")):
                self._ready()
                build_rescue_restore_preview_plan(
                    backup_archive_path="/a.tar",
                    manifest_path="/m.json",
                    target_device_or_path="/",
                    boot_context=_BOOT,
                    verify_status="failed",
                )

    def test_canonical_unavailable_blocks(self) -> None:
        with patch(
            "rescue.restore_preview_orchestrator.canonical_restore_preview_available",
            return_value=False,
        ):
            res = self._ready()
        self.assertIn("canonical_restore_preview_unavailable", res["blocked_reasons"])

    def test_references_canonical_restore_module(self) -> None:
        res = self._ready()
        self.assertIn(CANONICAL_RESTORE_PREVIEW_MODULE, res["plan"]["restore_engine"])


if __name__ == "__main__":
    unittest.main()
