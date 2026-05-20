"""
Backup-Archive: Kompression (gzip-kompatibel), optionale Excludes.

Profile-IDs und Excludes-Map: siehe ``core.backup_profiles``.
zstd ist vorbereitet (Erkennung + Metadaten), End-to-End erst nach
Anpassung der Manifest-/Hash-Pipeline an nicht-gzip-Streams.
"""

from __future__ import annotations

import os
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
    PROFILE_FULL_ROOT_STABLE,
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
    "PROFILE_FULL_ROOT_STABLE",
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

_COMPRESSION_ENGINES = frozenset({"auto", "gzip", "pigz"})


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


def _compression_engine_env() -> str:
    raw = (os.environ.get("SETUPHELFER_BACKUP_COMPRESSION_ENGINE") or "auto").strip().lower()
    return raw if raw in _COMPRESSION_ENGINES else "auto"


def _pigz_level_env(*, pi_like: bool) -> int:
    raw = (os.environ.get("SETUPHELFER_BACKUP_PIGZ_LEVEL") or "").strip()
    if raw.isdigit():
        return max(1, min(9, int(raw)))
    return 2 if pi_like else 6


def _pigz_threads_env() -> int | None:
    raw = (os.environ.get("SETUPHELFER_BACKUP_PIGZ_THREADS") or "auto").strip().lower()
    if raw in ("", "auto"):
        try:
            return max(1, os.cpu_count() or 1)
        except Exception:
            return 2
    if raw.isdigit():
        return max(1, int(raw))
    return None


def resolve_compression_choice(*, profile: str) -> dict[str, Any]:
    """
    gzip-kompatible Kompression für tar (finalize bleibt r:gz/w:gz).

    Priorität bei engine=auto: pigz → tar -czf (gzip).
    engine=gzip erzwingt tar -czf.
    engine=pigz erfordert pigz (kein stiller Fallback).
    """
    pi = is_pi_like_host()
    engine_req = _compression_engine_env()
    pigz_ok = pigz_available()
    level = _pigz_level_env(pi_like=pi)
    threads = _pigz_threads_env()
    warning_codes: list[str] = []

    use_pigz = False
    reason = "gzip_builtin_tar_czf"
    compression_available = True

    if engine_req == "pigz":
        if not pigz_ok:
            return {
                "compression_engine": "pigz",
                "compression_method": "pigz",
                "compression_available": False,
                "compression_reason": "pigz_explicit_not_found",
                "compression_preflight_blocked": True,
                "compression_preflight_message": (
                    "SETUPHELFER_BACKUP_COMPRESSION_ENGINE=pigz, aber pigz ist nicht installiert. "
                    "auto oder gzip verwenden, oder pigz ohne apt im Betrieb bereitstellen."
                ),
                "profile": profile,
                "pi_like": pi,
            }
        use_pigz = True
        reason = "pigz_explicit"
    elif engine_req == "gzip":
        use_pigz = False
        reason = "gzip_explicit"
    else:
        if pigz_ok:
            use_pigz = True
            reason = "pigz_found"
        else:
            use_pigz = False
            reason = "pigz_not_found_fallback_gzip"
            warning_codes.append("compression_fallback_gzip")

    if use_pigz:
        tp = threads if threads is not None else 2
        inner = f"pigz -p {tp} -{level}"
        method = "pigz"
        tar_flags = f"--use-compress-program={shlex.quote(inner)} -cf"
        return {
            "compression_engine": "pigz",
            "compression_method": method,
            "compression_inner_label": inner,
            "compression_threads": tp,
            "compression_level": level,
            "compression_available": True,
            "compression_reason": reason,
            "tar_create_flags": tar_flags,
            "uses_builtin_tar_czf": False,
            "zstd_available": zstd_available(),
            "zstd_used": False,
            "zstd_deferred_reason": "finalize_pipeline_requires_gzip_stream_today",
            "profile": profile,
            "pi_like": pi,
            "compression_warning_codes": warning_codes,
        }

    inner = "gzip (tar -czf)"
    return {
        "compression_engine": "gzip",
        "compression_method": "gzip",
        "compression_inner_label": inner,
        "compression_threads": None,
        "compression_level": None,
        "compression_available": compression_available,
        "compression_reason": reason,
        "tar_create_flags": "-czf",
        "uses_builtin_tar_czf": True,
        "zstd_available": zstd_available(),
        "zstd_used": False,
        "zstd_deferred_reason": "finalize_pipeline_requires_gzip_stream_today",
        "profile": profile,
        "pi_like": pi,
        "compression_warning_codes": warning_codes,
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
    if meta.get("compression_preflight_blocked"):
        return "", meta
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
