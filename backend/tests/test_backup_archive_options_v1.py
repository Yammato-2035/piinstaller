"""backup_archive_options: Profile, pigz/gzip, kein stiller full-expert-Default."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from core import backup_archive_options as bao


def test_default_profile_not_full_expert() -> None:
    p, warns = bao.normalize_backup_profile(None)
    assert p == bao.PROFILE_RECOMMENDED
    assert p != bao.PROFILE_FULL_EXPERT


def test_full_expert_warns() -> None:
    p, warns = bao.normalize_backup_profile("full-expert")
    assert p == bao.PROFILE_FULL_EXPERT
    assert "backup_profile_full_expert_selected" in warns


def test_unknown_profile_defaults_recommended() -> None:
    p, warns = bao.normalize_backup_profile("nope")
    assert p == bao.PROFILE_RECOMMENDED
    assert "backup_profile_unknown_defaulted" in warns


def test_pigz_preferred_when_available(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(bao, "pigz_available", lambda: True)
    monkeypatch.setattr(bao, "is_pi_like_host", lambda: False)
    meta = bao.resolve_compression_choice(profile=bao.PROFILE_RECOMMENDED)
    assert meta["compression_method"] == "pigz"
    assert meta["uses_builtin_tar_czf"] is False


def test_gzip_fallback_when_no_pigz(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(bao, "pigz_available", lambda: False)
    meta = bao.resolve_compression_choice(profile=bao.PROFILE_RECOMMENDED)
    assert meta["compression_method"] == "gzip"
    assert meta["uses_builtin_tar_czf"] is True


def test_build_full_contains_safety_excludes() -> None:
    cmd, meta = bao.build_full_root_tar_command("/tmp/x.partial", "/tmp/backupdir", profile=bao.PROFILE_FULL_EXPERT)
    assert "--exclude=/proc" in cmd
    assert "tar" in cmd
    assert meta["profile_normalized"] == bao.PROFILE_FULL_EXPERT


def test_recommended_adds_cache_excludes() -> None:
    cmd, _meta = bao.build_full_root_tar_command("/tmp/x.partial", "/tmp/backupdir", profile=bao.PROFILE_RECOMMENDED)
    assert "/var/cache" in cmd or "var/cache" in cmd
