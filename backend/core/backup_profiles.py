"""
Zentrales Backup-Profilmodell (API, Preview, Runner-Mapping).

Full-Root bleibt Expertenpfad; Standard fuer fehlendes type-Feld ist profile/recommended (Data-Runner).
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Any

PROFILE_RECOMMENDED = "recommended"
PROFILE_FAST_SYSTEM = "fast-system"
PROFILE_USER_DATA = "user-data"
PROFILE_DEVELOPER = "developer"
PROFILE_FULL_EXPERT = "full-expert"
PROFILE_FULL_ROOT_STABLE = "full-root-stable"

DEFAULT_BACKUP_PROFILE = PROFILE_RECOMMENDED

VALID_BACKUP_PROFILES: frozenset[str] = frozenset(
    {
        PROFILE_RECOMMENDED,
        PROFILE_FAST_SYSTEM,
        PROFILE_USER_DATA,
        PROFILE_DEVELOPER,
        PROFILE_FULL_EXPERT,
        PROFILE_FULL_ROOT_STABLE,
    }
)

# Live snapshot store — changes during read; excluded from stability-oriented full-root-stable only.
_BR001_TIMESHIFT_EXCLUDES: tuple[str, ...] = (
    "/timeshift",
    "/timeshift/*",
    "/timeshift/snapshots",
    "/timeshift/snapshots/*",
)

# Volatile browser/desktop caches — not restore-critical; avoids live-file tar failures on BR-001.
_BR001_VOLATILE_CACHE_EXCLUDES: tuple[str, ...] = (
    "/home/*/.cache",
    "/home/*/.cache/google-chrome",
    "/home/*/.cache/chromium",
    "/home/*/.cache/mozilla",
    "/home/*/.config/google-chrome/Default/Cache",
    "/home/*/.config/google-chrome/Default/Code Cache",
    "/home/*/.config/chromium/Default/Cache",
    "/home/*/.config/chromium/Default/Code Cache",
    "/home/*/.local/share/Trash",
)

PROFILE_EXTRA_EXCLUDES: dict[str, tuple[str, ...]] = {
    PROFILE_RECOMMENDED: ("/var/cache", "/var/tmp"),
    PROFILE_FAST_SYSTEM: ("/var/cache", "/var/tmp"),
    PROFILE_USER_DATA: (),
    PROFILE_DEVELOPER: ("/var/cache", "/var/tmp"),
    PROFILE_FULL_EXPERT: (),
    PROFILE_FULL_ROOT_STABLE: _BR001_TIMESHIFT_EXCLUDES + _BR001_VOLATILE_CACHE_EXCLUDES,
}

_DEVELOPER_EXCLUDE_GLOBS = (
    "**/node_modules",
    "**/.venv",
    "**/venv",
    "**/target",
    "**/dist",
    "**/build",
    "**/.cache",
)


def normalize_backup_profile(raw: str | None) -> tuple[str, list[str]]:
    p = (raw or "").strip().lower() or DEFAULT_BACKUP_PROFILE
    if p not in VALID_BACKUP_PROFILES:
        return DEFAULT_BACKUP_PROFILE, ["backup_profile_unknown_defaulted"]
    if p == PROFILE_FULL_EXPERT:
        return p, ["backup_profile_full_expert_selected"]
    if p == PROFILE_FULL_ROOT_STABLE:
        return p, ["backup_profile_full_root_stable_selected"]
    return p, []


def _under_resolved(parent: Path, child: Path) -> bool:
    try:
        rp = parent.resolve()
        rc = child.resolve()
    except OSError:
        return False
    return rc == rp or rp in rc.parents


def filter_included_paths_for_target(included: list[str], backup_dir: str) -> tuple[list[str], list[str]]:
    """Entfernt Quellpfade, die das Backup-Ziel einschliessen wuerden (Safety)."""
    warns: list[str] = []
    try:
        bd = Path(backup_dir).resolve()
    except OSError:
        return list(included), ["backup_target_path_resolve_failed"]
    out: list[str] = []
    for s in included:
        p = Path(s)
        try:
            pr = p.resolve()
        except OSError:
            out.append(s)
            continue
        if _under_resolved(pr, bd) or _under_resolved(bd, pr):
            warns.append(f"excluded_source_overlaps_target:{s}")
            continue
        out.append(s)
    return out, warns


def _logical_included_paths(profile: str) -> list[str]:
    """Beschreibende Quellpfade fuer Preview (nicht zwingend alle im Data-Runner v1)."""
    if profile in (PROFILE_FULL_EXPERT, PROFILE_FULL_ROOT_STABLE, PROFILE_FAST_SYSTEM):
        return ["/"]
    if profile == PROFILE_RECOMMENDED:
        return [
            "/var/lib/setuphelfer",
            "/etc/setuphelfer",
            "/etc/default",
            "/etc/apt",
            "/home",
        ]
    if profile == PROFILE_USER_DATA:
        return ["/home"]
    if profile == PROFILE_DEVELOPER:
        return ["/home", "/opt/setuphelfer", "/var/lib/setuphelfer"]
    return []


def logical_excluded_patterns(profile: str) -> list[str]:
    base = [
        "proc",
        "sys",
        "dev",
        "tmp",
        "run",
        "mnt",
        "media",
        "run/media",
    ]
    if profile == PROFILE_DEVELOPER:
        return list(base) + list(_DEVELOPER_EXCLUDE_GLOBS)
    if profile in (PROFILE_RECOMMENDED, PROFILE_FAST_SYSTEM):
        return list(base) + ["/var/cache", "/var/tmp"]
    if profile == PROFILE_FULL_ROOT_STABLE:
        return list(base) + list(_BR001_TIMESHIFT_EXCLUDES) + list(_BR001_VOLATILE_CACHE_EXCLUDES)
    return list(base)


def resolve_profile_request(*, request_type: str, profile_raw: str | None) -> dict[str, Any]:
    """
    Mappt API type/profile auf Runner-backup_type und normalisiertes Profil.

    request_type: profile | full | data | incremental (incremental unveraendert durchreichen).
    """
    warnings: list[str] = []
    t = (request_type or "").strip().lower()
    if t == "incremental":
        return {
            "runner_backup_type": "incremental",
            "normalized_profile": DEFAULT_BACKUP_PROFILE,
            "warning_codes": [],
            "requires_expert_confirmation": False,
            "recommended": False,
            "api_request_type": t,
        }

    if t == "data":
        prof, w = normalize_backup_profile(profile_raw)
        warnings.extend(w)
        return {
            "runner_backup_type": "data",
            "normalized_profile": prof,
            "warning_codes": warnings,
            "requires_expert_confirmation": False,
            "recommended": prof == PROFILE_RECOMMENDED,
            "api_request_type": t,
        }

    if t == "full":
        warnings.append("legacy_type_full_maps_to_full_expert")
        prof, w = normalize_backup_profile(PROFILE_FULL_EXPERT)
        warnings.extend(w)
        return {
            "runner_backup_type": "full",
            "normalized_profile": prof,
            "warning_codes": warnings,
            "requires_expert_confirmation": True,
            "recommended": False,
            "api_request_type": t,
        }

    # profile (default) oder unbekannter type -> wie profile behandeln
    if t not in ("profile", ""):
        warnings.append("backup_unknown_request_type_treated_as_profile")
    prof, w = normalize_backup_profile(profile_raw)
    warnings.extend(w)

    if prof == PROFILE_FULL_EXPERT:
        return {
            "runner_backup_type": "full",
            "normalized_profile": prof,
            "warning_codes": warnings,
            "requires_expert_confirmation": True,
            "recommended": False,
            "api_request_type": "profile",
        }
    if prof == PROFILE_FULL_ROOT_STABLE:
        return {
            "runner_backup_type": "full",
            "normalized_profile": prof,
            "warning_codes": warnings + ["backup_profile_br001_stable_excludes"],
            "requires_expert_confirmation": True,
            "recommended": False,
            "api_request_type": "profile",
        }
    if prof == PROFILE_FAST_SYSTEM:
        return {
            "runner_backup_type": "full",
            "normalized_profile": prof,
            "warning_codes": warnings + ["full_root_backup_long_runtime", "profile_fast_system_uses_full_root_v1"],
            "requires_expert_confirmation": True,
            "recommended": False,
            "api_request_type": "profile",
        }
    return {
        "runner_backup_type": "data",
        "normalized_profile": prof,
        "warning_codes": warnings,
        "requires_expert_confirmation": False,
        "recommended": prof == PROFILE_RECOMMENDED,
        "api_request_type": "profile",
    }


def profile_specs_public() -> list[dict[str, Any]]:
    """Statische Metadaten fuer API GET /api/backup/profiles (i18n-Keys, keine Freitexte)."""
    return [
        {
            "id": PROFILE_RECOMMENDED,
            "warning_level": "info",
            "strict_full_root": False,
            "i18n_title_key": "backup.profiles.recommended.title",
            "i18n_desc_key": "backup.profiles.recommended.desc",
            "exclude_categories_key": "backup.profiles.recommended.excludes",
        },
        {
            "id": PROFILE_FAST_SYSTEM,
            "warning_level": "warning",
            "strict_full_root": True,
            "i18n_title_key": "backup.profiles.fast_system.title",
            "i18n_desc_key": "backup.profiles.fast_system.desc",
            "exclude_categories_key": "backup.profiles.fast_system.excludes",
        },
        {
            "id": PROFILE_USER_DATA,
            "warning_level": "info",
            "strict_full_root": False,
            "i18n_title_key": "backup.profiles.user_data.title",
            "i18n_desc_key": "backup.profiles.user_data.desc",
            "exclude_categories_key": "backup.profiles.user_data.excludes",
        },
        {
            "id": PROFILE_DEVELOPER,
            "warning_level": "info",
            "strict_full_root": False,
            "i18n_title_key": "backup.profiles.developer.title",
            "i18n_desc_key": "backup.profiles.developer.desc",
            "exclude_categories_key": "backup.profiles.developer.excludes",
        },
        {
            "id": PROFILE_FULL_EXPERT,
            "warning_level": "critical",
            "strict_full_root": True,
            "i18n_title_key": "backup.profiles.full_expert.title",
            "i18n_desc_key": "backup.profiles.full_expert.desc",
            "exclude_categories_key": "backup.profiles.full_expert.excludes",
        },
        {
            "id": PROFILE_FULL_ROOT_STABLE,
            "warning_level": "warning",
            "strict_full_root": True,
            "i18n_title_key": "backup.profiles.full_root_stable.title",
            "i18n_desc_key": "backup.profiles.full_root_stable.desc",
            "exclude_categories_key": "backup.profiles.full_root_stable.excludes",
        },
    ]


def build_profile_preview(
    *,
    profile_raw: str | None,
    backup_dir: str,
    target_free_bytes: int | None = None,
) -> dict[str, Any]:
    prof, w = normalize_backup_profile(profile_raw)
    res = resolve_profile_request(request_type="profile", profile_raw=prof)
    included = _logical_included_paths(prof)
    included_f, tw = filter_included_paths_for_target(included, backup_dir)
    exc = logical_excluded_patterns(prof)
    warnings = list(w) + list(tw) + list(res.get("warning_codes") or [])
    return {
        "profile": prof,
        "included_paths": included_f,
        "excluded_patterns": exc,
        "warning_codes": warnings,
        "estimated_size_bytes": None,
        "target_free_bytes": target_free_bytes,
        "requires_expert_confirmation": bool(res.get("requires_expert_confirmation")),
        "recommended": bool(res.get("recommended")),
        "runner_backup_type": res.get("runner_backup_type"),
    }
