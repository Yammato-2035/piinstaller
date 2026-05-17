"""BR-001: backup_runner tar exit-1 classification integration (no live backups)."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from core.backup_tar_warning_classification import (
    classification_to_job_status_fields,
    TarWarningClassification,
    classify_tar_run,
    decide_tar_nonzero_job_outcome,
)
from tools import backup_runner as br

_BR001_STDERR = """tar: /root/.gnupg/S.gpg-agent: Socket ignoriert
tar: /var/log/journal/cc3dd4e4e6964881a0a0d368b6df3544/system.journal: Datei hat sich beim Lesen geändert.
tar: /home/volker/.docker/desktop/console.sock: Socket ignoriert
tar: /home/volker/.cache/ibus/dbus-GBSsHp1C: Socket ignoriert
sh failed with exit status 1.
"""


class TestDecideTarNonzeroJobOutcome(unittest.TestCase):
    def test_rc0_not_handled_here(self) -> None:
        r = classify_tar_run(tar_exit_code=0, stderr_text="")
        self.assertEqual(r.classification, TarWarningClassification.TAR_OK)

    def test_volatile_only_no_final_archive_failed(self) -> None:
        o = decide_tar_nonzero_job_outcome(
            tar_exit_code=1,
            stderr_text=_BR001_STDERR,
            partial_exists=False,
            partial_bytes=0,
            final_archive_exists=False,
            finalize_attempted=False,
            finalize_ok=False,
            sha256_verified=False,
            verify_deep_ok=False,
        )
        self.assertEqual(o["status"], "error")
        self.assertIn(o["code"], ("backup.failed", "backup.warning_not_promoted"))
        self.assertNotEqual(o.get("code"), "backup.success")
        self.assertFalse(o.get("operational_success_allowed"))
        self.assertEqual(o["tar_warning_classification"], "TAR_VOLATILE_WARNINGS_ONLY")

    def test_volatile_partial_no_finalize_cleanup(self) -> None:
        o = decide_tar_nonzero_job_outcome(
            tar_exit_code=1,
            stderr_text=_BR001_STDERR,
            partial_exists=True,
            partial_bytes=1024,
            final_archive_exists=False,
            finalize_attempted=True,
            finalize_ok=False,
            sha256_verified=False,
            verify_deep_ok=False,
        )
        self.assertEqual(o["abort_reason"], "tar_volatile_finalize_failed")
        self.assertTrue(o.get("partial_deleted"))

    def test_volatile_final_no_sha256(self) -> None:
        o = decide_tar_nonzero_job_outcome(
            tar_exit_code=1,
            stderr_text=_BR001_STDERR,
            partial_exists=True,
            partial_bytes=1,
            final_archive_exists=True,
            finalize_attempted=True,
            finalize_ok=True,
            sha256_verified=False,
            verify_deep_ok=False,
        )
        self.assertEqual(o["abort_reason"], "tar_volatile_sha256_failed")
        self.assertNotEqual(o.get("code"), "backup.success_with_warnings")

    def test_volatile_final_sha256_no_verify(self) -> None:
        o = decide_tar_nonzero_job_outcome(
            tar_exit_code=1,
            stderr_text=_BR001_STDERR,
            partial_exists=True,
            partial_bytes=1,
            final_archive_exists=True,
            finalize_attempted=True,
            finalize_ok=True,
            sha256_verified=True,
            verify_deep_ok=False,
        )
        self.assertEqual(o["abort_reason"], "tar_volatile_verify_deep_failed")

    def test_volatile_success_with_warnings_chain(self) -> None:
        o = decide_tar_nonzero_job_outcome(
            tar_exit_code=1,
            stderr_text=_BR001_STDERR,
            partial_exists=True,
            partial_bytes=1,
            final_archive_exists=True,
            finalize_attempted=True,
            finalize_ok=True,
            sha256_verified=True,
            verify_deep_ok=True,
        )
        self.assertEqual(o["code"], "backup.success_with_warnings")
        self.assertEqual(o["warning_status"], "completed_with_warnings")
        self.assertTrue(o.get("operational_success_allowed"))

    def test_io_error_fatal(self) -> None:
        o = decide_tar_nonzero_job_outcome(
            tar_exit_code=1,
            stderr_text="tar: x: Input/output error\n",
            partial_exists=True,
            partial_bytes=99,
            final_archive_exists=False,
            finalize_attempted=False,
            finalize_ok=False,
            sha256_verified=False,
            verify_deep_ok=False,
        )
        self.assertEqual(o["abort_reason"], "tar_failed")
        self.assertTrue(o.get("fatal_patterns_found"))

    def test_no_space_fatal(self) -> None:
        o = decide_tar_nonzero_job_outcome(
            tar_exit_code=1,
            stderr_text="tar: No space left on device\n",
            partial_exists=False,
            partial_bytes=0,
            final_archive_exists=False,
            finalize_attempted=False,
            finalize_ok=False,
            sha256_verified=False,
            verify_deep_ok=False,
        )
        self.assertEqual(o["tar_warning_classification"], "TAR_FATAL")

    def test_eof_fatal(self) -> None:
        o = decide_tar_nonzero_job_outcome(
            tar_exit_code=1,
            stderr_text="tar: Unexpected EOF in archive\n",
            partial_exists=False,
            partial_bytes=0,
            final_archive_exists=False,
            finalize_attempted=False,
            finalize_ok=False,
            sha256_verified=False,
            verify_deep_ok=False,
        )
        self.assertEqual(o["tar_warning_classification"], "TAR_FATAL")

    def test_critical_etc_changed(self) -> None:
        o = decide_tar_nonzero_job_outcome(
            tar_exit_code=1,
            stderr_text="tar: /etc/hosts: file changed as we read it\n",
            partial_exists=True,
            partial_bytes=1,
            final_archive_exists=False,
            finalize_attempted=False,
            finalize_ok=False,
            sha256_verified=False,
            verify_deep_ok=False,
        )
        self.assertEqual(o["tar_warning_classification"], "TAR_CRITICAL_WARNING")
        self.assertNotEqual(o.get("code"), "backup.success_with_warnings")

    def test_br001_replay_volatile_only(self) -> None:
        c = classify_tar_run(tar_exit_code=1, stderr_text=_BR001_STDERR)
        self.assertEqual(c.classification, TarWarningClassification.TAR_VOLATILE_WARNINGS_ONLY)
        self.assertFalse(c.operational_success_allowed)


class TestPublishTarNonzeroStatusFields(unittest.TestCase):
    def test_status_json_contains_classification(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            status_dir = Path(td)
            job_id = "testclass01"
            job_dir = status_dir / job_id
            job_dir.mkdir(parents=True)
            status_file = job_dir / "status.json"
            state: dict = {"job_id": job_id}
            outcome = decide_tar_nonzero_job_outcome(
                tar_exit_code=1,
                stderr_text=_BR001_STDERR,
                partial_exists=False,
                partial_bytes=0,
                final_archive_exists=False,
                finalize_attempted=False,
                finalize_ok=False,
                sha256_verified=False,
                verify_deep_ok=False,
            )
            cls = classify_tar_run(tar_exit_code=1, stderr_text=_BR001_STDERR)
            br._publish_tar_nonzero_failure(
                status_file,
                state,
                partial_path=str(job_dir / "x.partial"),
                rc=1,
                stderr_excerpt="",
                stderr_tail="",
                stderr_log_path=None,
                tar_class_fields=classification_to_job_status_fields(cls),
                outcome=outcome,
            )
            data = json.loads(status_file.read_text(encoding="utf-8"))
            self.assertEqual(data["tar_warning_classification"], "TAR_VOLATILE_WARNINGS_ONLY")
            self.assertIn("tar_warning_downgrade_allowed", data)
            self.assertFalse(data["operational_success_allowed"])


if __name__ == "__main__":
    unittest.main()
