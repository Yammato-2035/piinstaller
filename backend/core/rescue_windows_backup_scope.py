"""Windows backup scope: full vs selective personal/custom (Phase B)."""

from __future__ import annotations

from typing import Any

SCOPE_FULL = "full"
SCOPE_SELECTIVE_PERSONAL = "selective_personal"
SCOPE_SELECTIVE_CUSTOM = "selective_custom"
SCOPES = frozenset({SCOPE_FULL, SCOPE_SELECTIVE_PERSONAL, SCOPE_SELECTIVE_CUSTOM})

# Relative to Windows user profile root (Users/<name>/...).
PERSONAL_PROFILE_REL_PATHS: tuple[str, ...] = (
    "Documents",
    "Desktop",
    "Pictures",
    "Videos",
    "Music",
    "Downloads",
    "Favorites",
)

PERSONAL_EXCLUDE_REL_PATHS: tuple[str, ...] = (
    "AppData/Local/Temp",
    "AppData/Local/Microsoft/Windows/INetCache",
    "AppData/Local/CrashDumps",
)


def normalize_backup_scope(value: str | None) -> str:
    raw = str(value or SCOPE_FULL).strip().lower()
    if raw in ("full_disk", "full_image", "system", "raw_image"):
        return SCOPE_FULL
    if raw in ("personal", "selective", "users", "user_data"):
        return SCOPE_SELECTIVE_PERSONAL
    if raw in ("custom", "manual", "paths"):
        return SCOPE_SELECTIVE_CUSTOM
    if raw in SCOPES:
        return raw
    return SCOPE_FULL


def build_selective_personal_paths(*, users_root: str = "Users") -> list[str]:
    """Glob-style relative include paths under the Windows volume mount."""
    return [f"{users_root}/*/{rel}" for rel in PERSONAL_PROFILE_REL_PATHS]


def build_backup_scope_plan(
    *,
    scope: str | None,
    custom_paths: list[str] | None = None,
    users_root: str = "Users",
) -> dict[str, Any]:
    normalized = normalize_backup_scope(scope)
    if normalized == SCOPE_FULL:
        return {
            "scope": SCOPE_FULL,
            "label_de": "Vollbackup (Systemvolume)",
            "include_paths": ["*"],
            "exclude_paths": [],
            "requires_ntfs_ro_mount": True,
            "artifact_kind": "volume_image_or_full_tree",
        }
    if normalized == SCOPE_SELECTIVE_PERSONAL:
        return {
            "scope": SCOPE_SELECTIVE_PERSONAL,
            "label_de": "Persönliche Daten (Benutzerprofile)",
            "include_paths": build_selective_personal_paths(users_root=users_root),
            "exclude_paths": list(PERSONAL_EXCLUDE_REL_PATHS),
            "requires_ntfs_ro_mount": True,
            "artifact_kind": "selective_tar",
        }
    paths = [str(p).strip().lstrip("/") for p in (custom_paths or []) if str(p).strip()]
    return {
        "scope": SCOPE_SELECTIVE_CUSTOM,
        "label_de": "Manuelle Auswahl",
        "include_paths": paths,
        "exclude_paths": list(PERSONAL_EXCLUDE_REL_PATHS),
        "requires_ntfs_ro_mount": True,
        "artifact_kind": "selective_tar",
        "errors": [] if paths else [{"code": "custom_paths_missing", "message": "Keine Pfade gewählt."}],
    }


def validate_scope_against_target(
    *,
    scope_plan: dict[str, Any],
    target_role: str,
) -> list[dict[str, str]]:
    errors: list[dict[str, str]] = []
    if target_role in {"windows_system_disk", "linux_system_disk", "rescue_usb_stick"}:
        errors.append(
            {
                "code": "target_not_external",
                "message": "Backupziel muss eine externe HDD sein.",
            }
        )
    if scope_plan.get("scope") == SCOPE_SELECTIVE_CUSTOM and not scope_plan.get("include_paths"):
        errors.append({"code": "custom_paths_missing", "message": "Keine Pfade gewählt."})
    return errors
