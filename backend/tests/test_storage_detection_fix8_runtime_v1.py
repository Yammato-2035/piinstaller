from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

from modules.storage_detection import BackupTargetValidationError, validate_backup_target


class TestStorageDetectionFix8RuntimeV1(unittest.TestCase):
    def test_validate_backup_target_uses_resolved_mount_source(self) -> None:
        with tempfile.TemporaryDirectory(prefix="fix8-sd-") as td:
            base = Path(td)
            archive = base / "sample.tar.gz"

            with patch(
                "modules.storage_detection.resolve_mount_source_for_path",
                return_value={
                    "mount_source_seen": "systemd-1",
                    "resolved_source": "/dev/sdb1",
                    "fstype": "ext4",
                    "target": str(base),
                    "reason": "ok_after_automount_trigger",
                },
            ) as m_resolve:
                with patch("modules.storage_detection.validate_write_target") as m_validate_write:
                    validate_backup_target(archive, runner=None)
                    self.assertEqual(m_resolve.call_count, 1)
                    self.assertEqual(m_validate_write.call_count, 1)

    def test_validate_backup_target_non_block_source_detail(self) -> None:
        with tempfile.TemporaryDirectory(prefix="fix8-sd-") as td:
            archive = Path(td) / "sample.tar.gz"
            with patch(
                "modules.storage_detection.resolve_mount_source_for_path",
                return_value={
                    "mount_source_seen": "systemd-1",
                    "resolved_source": "",
                    "fstype": "autofs",
                    "target": str(Path(td)),
                    "reason": "automount_layer_no_resolved_block_source",
                },
            ):
                with self.assertRaises(BackupTargetValidationError) as ctx:
                    validate_backup_target(archive, runner=None)
        self.assertEqual(ctx.exception.message_key, "backup_recovery.error.backup_target_non_block_source")
        self.assertIn("systemd-1", ctx.exception.detail or "")

    def test_validate_backup_target_not_mounted_reason_passthrough(self) -> None:
        with tempfile.TemporaryDirectory(prefix="fix8-sd-") as td:
            archive = Path(td) / "sample.tar.gz"
            with patch(
                "modules.storage_detection.resolve_mount_source_for_path",
                return_value={
                    "mount_source_seen": "",
                    "resolved_source": "",
                    "fstype": "",
                    "target": str(Path(td)),
                    "reason": "findmnt_t_no_entries",
                },
            ):
                with self.assertRaises(BackupTargetValidationError) as ctx:
                    validate_backup_target(archive, runner=None)
        self.assertEqual(ctx.exception.message_key, "backup_recovery.error.backup_target_not_mounted")


if __name__ == "__main__":
    unittest.main()

