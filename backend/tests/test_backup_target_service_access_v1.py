"""backup_target_service_access: Diagnose-IDs und Mountbaum-Erkennung."""

from __future__ import annotations

from pathlib import Path

import pytest

from core.backup_target_service_access import (
    BACKUP_TARGET_NOT_WRITABLE_002,
    BACKUP_TARGET_USER_MOUNT_003,
    assert_backup_target_writable_for_service,
    extract_backup_target_diagnosis_id,
    is_user_session_media_tree,
    preview_backup_target_access,
)


def test_is_user_session_media_tree() -> None:
    assert is_user_session_media_tree(Path("/media/alice/backup"))
    assert is_user_session_media_tree(Path("/run/media/bob/usb"))
    assert not is_user_session_media_tree(Path("/media/setuphelfer/br001"))
    assert not is_user_session_media_tree(Path("/mnt/setuphelfer/backups"))


def test_extract_backup_target_diagnosis_id() -> None:
    assert (
        extract_backup_target_diagnosis_id(f"{BACKUP_TARGET_USER_MOUNT_003}: detail")
        == BACKUP_TARGET_USER_MOUNT_003
    )
    assert extract_backup_target_diagnosis_id("STORAGE-PROTECTION-004: x") is None


def test_assert_backup_target_writable_for_service_ok(tmp_path: Path) -> None:
    d = tmp_path / "ok"
    d.mkdir()
    assert_backup_target_writable_for_service(d.resolve())


def test_assert_backup_target_writable_for_service_readonly(tmp_path: Path) -> None:
    d = tmp_path / "ro"
    d.mkdir()
    d.chmod(0o555)
    try:
        with pytest.raises(ValueError) as ei:
            assert_backup_target_writable_for_service(d.resolve())
        assert BACKUP_TARGET_NOT_WRITABLE_002 in str(ei.value)
    finally:
        d.chmod(0o755)


def test_assert_backup_user_media_classification(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    d = (tmp_path / "usb").resolve()
    d.mkdir()
    monkeypatch.setattr(
        "core.backup_target_service_access.is_user_session_media_tree",
        lambda _p: True,
    )
    monkeypatch.setattr("os.access", lambda _p, _m: False)
    with pytest.raises(ValueError) as ei:
        assert_backup_target_writable_for_service(d)
    assert BACKUP_TARGET_USER_MOUNT_003 in str(ei.value)


def test_preview_backup_target_access_empty() -> None:
    assert preview_backup_target_access("")["likely_writable_by_service"] is None
