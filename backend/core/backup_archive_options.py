"""
Backup-Archive: Kompression (gzip-kompatibel), optionale Excludes.

Profile-IDs und Excludes-Map: siehe ``core.backup_profiles``.
zstd ist vorbereitet (Erkennung + Metadaten), End-to-End erst nach
Anpassung der Manifest-/Hash-Pipeline an nicht-gzip-Streams.
"""

from __future__ import annotations

import platform
import shlex
import shutil
from pathlib import Path
from typing import Any

from core.backup_profiles import (
    DEFAULT_BACKUP_PROFILE,
    PROFILE_DEVELOPER,
    PROFILE_EXTRA_EXCLUDES,
    PROFILE_FAST_SYSTEM,
    PROFILE_FULL_EXPERT,
    PROFILE_RECOMMENDED,
    PROFILE_USER_DATA,
    VALID_BACKUP_PROFILES,
    normalize_backup_profile,
)

__all__ = [
    "DEFAULT_BACKUP_PROFILE",
    "PROFILE_DEVELOPER",
    "PROFILE_EXTRA_EXCLUDES",
    "PROFILE_FAST_SYSTEM",
    "PROFILE_FULL_EXPERT",
    "PROFILE_RECOMMENDED",
    "PROFILE_USER_DATA",
    "VALID_BACKUP_PROFILES",
    "normalize_backup_profile",
    "is_pi_like_host",
    "zstd_available",
    "pigz_available",
    "resolve_compression_choice",
    "build_full_root_tar_command",
]


def is_pi_like_host() -> bool:
    m = (platform.machine() or "").lower()
    if m in ("armv7l", "aarch64", "arm64"):
        return True
    try:
        dt = Path("/proc/device-tree/model")
        if dt.is_file():
            txt = dt.read_text(encoding="utf-8", errors="ignore").lower()
            if "raspberry" in txt:
                return True
    except OSError:
        pass
    return False


def zstd_available() -> bool:
    return bool(shutil.which("zstd"))


def pigz_available() -> bool:
    return bool(shutil.which("pigz"))


def resolve_compression_choice(*, profile: str) -> dict[str, Any]:
    """
    gzip-kompatible Kompression für tar (finalize bleibt r:gz/w:gz).

    Priorität: pigz → tar -czf.
    """
    pi = is_pi_like_host()
    pigz_level = "2" if pi else "4"
    use_pigz = pigz_available()
    if use_pigz:
        inner = f"pigz -{pigz_level}"
        method = "pigz"
        tar_flags = f"--use-compress-program={shlex.quote(inner)} -cf"
    else:
        inner = "gzip (tar -czf)"
        method = "gzip"
        tar_flags = "-czf"
    return {
        "compression_method": method,
        "compression_inner_label": inner,
        "tar_create_flags": tar_flags,
        "uses_builtin_tar_czf": not use_pigz,
        "zstd_available": zstd_available(),
        "zstd_used": False,
        "zstd_deferred_reason": "finalize_pipeline_requires_gzip_stream_today",
        "profile": profile,
        "pi_like": pi,
    }


def build_full_root_tar_command(
    partial_path: str,
    backup_dir_resolved: str,
    *,
    profile: str,
) -> tuple[str, dict[str, Any]]:
    bd = str(Path(backup_dir_resolved).resolve())
    prof, warns = normalize_backup_profile(profile)
    meta = resolve_compression_choice(profile=prof)
    meta["profile_normalized"] = prof
    meta["profile_warnings"] = warns

    excludes: list[str] = [
        f"--exclude={shlex.quote(bd)}",
        "--exclude=/proc",
        "--exclude=/sys",
        "--exclude=/dev",
        "--exclude=/tmp",
        "--exclude=/run",
        "--exclude=/mnt",
        "--exclude=/media",
        "--exclude=/run/media",
    ]
    for ex in PROFILE_EXTRA_EXCLUDES.get(prof, ()):
        excludes.append(f"--exclude={shlex.quote(ex)}")

    if meta["uses_builtin_tar_czf"]:
        cmd = f"tar -czf {shlex.quote(partial_path)} " + " ".join(excludes) + " /"
    else:
        cmd = f"tar {meta['tar_create_flags']} {shlex.quote(partial_path)} " + " ".join(excludes) + " /"
    return cmd, meta
