"""
Kanonische Restore-Preview-Profil-Metadaten (keine Ausführung, kein Tar, kein Mount).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

PROFILE_OFFLINE_FULL_RESTORE_PREVIEW = "offline-full-restore-preview"

CANONICAL_RESTORE_PREVIEW_MODULE = "modules.rescue_restore_dryrun"
CANONICAL_RESTORE_PREVIEW_ENTRY = "run_restore_dryrun_pipeline"
CANONICAL_VERIFY_MODULE = "modules.backup_verify"
CANONICAL_VERIFY_ENTRIES = ("verify_basic", "verify_deep")

_FORBIDDEN_ACTIONS: tuple[str, ...] = (
    "tar_extract",
    "rsync",
    "mkfs",
    "parted",
    "mount_rw",
    "bootloader_write",
    "efi_write",
)


def get_restore_profile(profile_id: str) -> dict[str, Any]:
    pid = (profile_id or "").strip().lower()
    if pid != PROFILE_OFFLINE_FULL_RESTORE_PREVIEW:
        return {"profile_id": pid, "unknown": True}

    return {
        "profile_id": PROFILE_OFFLINE_FULL_RESTORE_PREVIEW,
        "description": "Preview restore from offline/rescue backup archive to selected target",
        "execution_allowed": False,
        "requires_manifest": True,
        "requires_archive": True,
        "requires_verify_before_restore": True,
        "requires_target_device": True,
        "requires_target_write_approval": True,
        "requires_backup_before_overwrite": True,
        "requires_external_or_explicit_target": True,
        "allowed_contexts": ["rescue", "offline"],
        "forbidden_actions": list(_FORBIDDEN_ACTIONS),
        "unknown": False,
    }


def _module_file_text(module_dotted: str) -> str | None:
    """Read-only: locate backend module source without importing heavy deps."""
    parts = module_dotted.split(".")
    if not parts or parts[0] != "modules":
        return None
    rel = Path("modules") / "/".join(parts[1:])
    for base in (Path(__file__).resolve().parent.parent,):
        candidate = base / f"{rel}.py"
        if candidate.is_file():
            try:
                return candidate.read_text(encoding="utf-8", errors="replace")
            except OSError:
                return None
    return None


def canonical_restore_preview_available() -> bool:
    text = _module_file_text(CANONICAL_RESTORE_PREVIEW_MODULE)
    if not text:
        return False
    return f"def {CANONICAL_RESTORE_PREVIEW_ENTRY}" in text


def canonical_verify_available() -> bool:
    text = _module_file_text(CANONICAL_VERIFY_MODULE)
    if not text:
        return False
    return all(f"def {name}" in text for name in CANONICAL_VERIFY_ENTRIES)
