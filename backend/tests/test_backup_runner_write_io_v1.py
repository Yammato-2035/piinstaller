"""BR-013: classify tar/gzip target write I/O errors in backup_runner stderr."""

from __future__ import annotations

from tools import backup_runner as br


def test_stderr_target_write_io_gzip_eio() -> None:
    assert br._stderr_indicates_target_write_io_error("", "gzip: stdout: Input/output error\n")


def test_stderr_target_write_io_tar_short_write() -> None:
    tail = (
        "tar: /media/gabriel/setuphelfer-back/pi-backup-full-20260514_083550.tar.gz.partial: "
        "Wrote only 6144 of 10240 bytes\n"
    )
    assert br._stderr_indicates_target_write_io_error("", tail)


def test_stderr_target_write_io_combined_head_tail() -> None:
    h = "tar: socket ignored\n"
    t = "gzip: stdout: Input/output error\ntar: x.partial: Wrote only 1 of 99 bytes\n"
    assert br._stderr_indicates_target_write_io_error(h, t)


def test_stderr_generic_tar_error_not_write_io() -> None:
    assert not br._stderr_indicates_target_write_io_error("", "tar: broken pipe\n")


def test_backup_codes_no_verify_on_write_io_documented() -> None:
    """BR-004/BR-005 require a successful BR-001 archive; write_io_error is not success."""
    assert "backup.write_io_error" != "backup.success"


def test_wrote_only_requires_byte_word() -> None:
    assert not br._stderr_indicates_target_write_io_error("", "tar: wrote only something vague\n")
