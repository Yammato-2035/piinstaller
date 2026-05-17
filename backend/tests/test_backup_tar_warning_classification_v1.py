"""BR-001: GNU tar exit-code / stderr warning classification (no live backups)."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from core.backup_tar_warning_classification import (
    TarWarningClassification,
    classify_tar_run,
)


class TestBackupTarWarningClassificationV1(unittest.TestCase):
    def test_exit_0_ok(self) -> None:
        r = classify_tar_run(tar_exit_code=0, stderr_text="")
        self.assertEqual(r.classification, TarWarningClassification.TAR_OK)

    def test_exit_1_file_changed_volatile_path(self) -> None:
        stderr = (
            "tar: /var/log/journal/abc/system.journal: Datei hat sich beim Lesen geändert.\n"
        )
        r = classify_tar_run(tar_exit_code=1, stderr_text=stderr)
        self.assertEqual(r.classification, TarWarningClassification.TAR_LIVE_FILE_CHANGED_ONLY)
        self.assertFalse(r.io_errors_found)
        self.assertTrue(r.allows_warning_downgrade)
        self.assertFalse(r.operational_success_allowed)

    def test_exit_1_socket_volatile_only(self) -> None:
        stderr = "tar: /home/u/.cache/ibus/dbus-abc: Socket ignoriert\n"
        r = classify_tar_run(tar_exit_code=1, stderr_text=stderr)
        self.assertEqual(r.classification, TarWarningClassification.TAR_SOCKET_IGNORED_ONLY)

    def test_exit_1_io_error_fatal(self) -> None:
        stderr = "tar: /media/x/a.partial: Input/output error\n"
        r = classify_tar_run(tar_exit_code=1, stderr_text=stderr)
        self.assertEqual(r.classification, TarWarningClassification.TAR_IO_ERROR)
        self.assertTrue(r.io_errors_found)
        self.assertFalse(r.allows_warning_downgrade)

    def test_exit_1_no_space_fatal(self) -> None:
        stderr = "tar: No space left on device\n"
        r = classify_tar_run(tar_exit_code=1, stderr_text=stderr)
        self.assertEqual(r.classification, TarWarningClassification.TAR_FATAL)
        self.assertTrue(r.critical_errors_found)

    def test_exit_1_unexpected_eof_fatal(self) -> None:
        stderr = "tar: Unexpected EOF in archive\n"
        r = classify_tar_run(tar_exit_code=1, stderr_text=stderr)
        self.assertEqual(r.classification, TarWarningClassification.TAR_FATAL)

    def test_exit_1_permission_critical_path(self) -> None:
        stderr = "tar: /etc/shadow: Cannot open: Permission denied\n"
        r = classify_tar_run(tar_exit_code=1, stderr_text=stderr)
        self.assertEqual(r.classification, TarWarningClassification.TAR_PERMISSION_CRITICAL)

    def test_exit_1_file_changed_critical_etc(self) -> None:
        stderr = "tar: /etc/hosts: file changed as we read it\n"
        r = classify_tar_run(tar_exit_code=1, stderr_text=stderr)
        self.assertEqual(r.classification, TarWarningClassification.TAR_CRITICAL_WARNING)
        self.assertIn("/etc/hosts", r.critical_paths)

    def test_exit_1_file_changed_boot_critical(self) -> None:
        stderr = "tar: /boot/vmlinuz: file changed as we read it\n"
        r = classify_tar_run(tar_exit_code=1, stderr_text=stderr)
        self.assertEqual(r.classification, TarWarningClassification.TAR_CRITICAL_WARNING)

    def test_no_final_archive_never_operational_success(self) -> None:
        stderr = (
            "tar: /var/tmp/x: file changed as we read it\n"
            "tar: /home/u/.cache/ibus/dbus-x: socket ignored\n"
        )
        r = classify_tar_run(
            tar_exit_code=1,
            stderr_text=stderr,
            final_archive_path=None,
            sha256_verified=True,
            verify_deep_ok=True,
        )
        self.assertEqual(r.classification, TarWarningClassification.TAR_VOLATILE_WARNINGS_ONLY)
        self.assertTrue(r.no_archive_created)
        self.assertFalse(r.operational_success_allowed)
        self.assertIn("no_final_archive", r.downgrade_blockers)

    def test_downgrade_requires_archive_sha256_verify(self) -> None:
        stderr = "tar: /var/cache/pkg/file: file changed as we read it\n"
        with tempfile.TemporaryDirectory() as td:
            arch = Path(td) / "backup.tar.gz"
            arch.write_bytes(b"x" * 64)
            r = classify_tar_run(
                tar_exit_code=1,
                stderr_text=stderr,
                final_archive_path=arch,
                sha256_verified=False,
                verify_deep_ok=False,
            )
            self.assertTrue(r.allows_warning_downgrade)
            self.assertFalse(r.operational_success_allowed)
            r2 = classify_tar_run(
                tar_exit_code=1,
                stderr_text=stderr,
                final_archive_path=arch,
                sha256_verified=True,
                verify_deep_ok=True,
            )
            self.assertTrue(r2.operational_success_allowed)

    def test_br001_927469d42503_forensics_profile(self) -> None:
        """Replay stderr categories from failed BR-001 run 2026-05-16 (volatile-only)."""
        stderr = """tar: /root/.gnupg/S.gpg-agent: Socket ignoriert
tar: /var/log/journal/cc3dd4e4e6964881a0a0d368b6df3544/system.journal: Datei hat sich beim Lesen geändert.
tar: /home/volker/.docker/desktop/console.sock: Socket ignoriert
tar: /home/volker/.cache/ibus/dbus-GBSsHp1C: Socket ignoriert
sh failed with exit status 1.
"""
        r = classify_tar_run(tar_exit_code=1, stderr_text=stderr, final_archive_path=None)
        self.assertEqual(r.classification, TarWarningClassification.TAR_VOLATILE_WARNINGS_ONLY)
        self.assertFalse(r.io_errors_found)
        self.assertFalse(r.critical_errors_found)
        self.assertTrue(r.no_archive_created)
        self.assertFalse(r.operational_success_allowed)


if __name__ == "__main__":
    unittest.main()
