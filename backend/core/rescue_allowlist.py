"""
Gemeinsame Pfad-Allowlists für Rescue-Dry-Run (Backup lesen, Sandbox schreiben).

Spiegelt die in ``app.py`` genutzten Backup-Lesewurzeln, ohne ``app`` zu importieren.
"""

from __future__ import annotations

from pathlib import Path

RESCUE_BACKUP_READ_PREFIXES: tuple[Path, ...] = (
    Path("/mnt").resolve(),
    Path("/media").resolve(),
    Path("/run/media").resolve(),
    Path("/home").resolve(),
    Path("/tmp/setuphelfer-test").resolve(),
)

# Staging nur unter festen /tmp-Präfixen (Restore-Preview + Rescue-Dry-Run)
RESCUE_DRYRUN_WRITE_PREFIXES: tuple[Path, ...] = (
    Path("/tmp/setuphelfer-rescue-dryrun-staging").resolve(),
    Path("/tmp/setuphelfer-restore-test").resolve(),
)

# Echter Rescue-Restore nur unter dedizierten Präfixen (nicht direkt auf /)
RESCUE_LIVE_RESTORE_PREFIXES: tuple[Path, ...] = (
    Path("/mnt/setuphelfer-restore-live").resolve(),
    Path("/tmp/setuphelfer-rescue-restore-test").resolve(),
)

# Persistente Dry-Run-Grants (kurzlebig, Token-Dateien)
RESCUE_DRYRUN_STATE_DIR = Path("/tmp/setuphelfer-rescue-dryrun-state").resolve()


def _resolved(p: Path) -> Path:
    try:
        return p.resolve()
    except OSError:
        return p


def path_under_prefixes(p: Path, prefixes: tuple[Path, ...]) -> bool:
    rp = _resolved(p)
    for root in prefixes:
        base = _resolved(root)
        try:
            rp.relative_to(base)
            return True
        except ValueError:
            if rp == base:
                return True
    return False


def normalize_rescue_abs_path(path_str: str) -> Path:
    """Wie ``app._normalize_path``: absolut, resolve, keine Shell-Metazeichen."""
    if not isinstance(path_str, str):
        raise ValueError("path must be str")
    stripped = path_str.strip()
    if not stripped:
        raise ValueError("path empty")
    if not stripped.startswith("/"):
        raise ValueError("path must be absolute")
    forbidden = ["\n", "\r", "\t", "\x00", "`", "$", ";", "&", "|", "<", ">", "!", "\"", "'"]
    if any(ch in stripped for ch in forbidden):
        raise ValueError("path contains forbidden characters")
    return Path(stripped).resolve()


def assert_backup_readable_path(path_str: str) -> Path:
    """Pfad muss existierende Datei sein und unter Backup-Lesewurzeln liegen."""
    p = normalize_rescue_abs_path(path_str)
    if not p.is_file():
        raise ValueError("not a file")
    if not path_under_prefixes(p, RESCUE_BACKUP_READ_PREFIXES):
        raise ValueError("backup path not under allowed roots")
    return p


def assert_dryrun_staging_path(path_str: str) -> Path:
    """Zielverzeichnis für Extraktion muss unter Dry-Run-Staging liegen."""
    p = normalize_rescue_abs_path(path_str)
    if not path_under_prefixes(p, RESCUE_DRYRUN_WRITE_PREFIXES):
        raise ValueError("staging path not under allowed dry-run roots")
    return p


def assert_restore_live_target_directory(path_str: str) -> Path:
    """Zielverzeichnis für echten Restore (extrahiertes Root) nur unter Live-Restore-Präfixen."""
    p = normalize_rescue_abs_path(path_str)
    if not path_under_prefixes(p, RESCUE_LIVE_RESTORE_PREFIXES):
        raise ValueError("restore target directory not under allowed live-restore roots")
    return p


__all__ = [
    "RESCUE_BACKUP_READ_PREFIXES",
    "RESCUE_DRYRUN_STATE_DIR",
    "RESCUE_DRYRUN_WRITE_PREFIXES",
    "RESCUE_LIVE_RESTORE_PREFIXES",
    "assert_backup_readable_path",
    "assert_dryrun_staging_path",
    "assert_restore_live_target_directory",
    "normalize_rescue_abs_path",
    "path_under_prefixes",
]
