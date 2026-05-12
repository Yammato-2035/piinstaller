"""
Pfad-Whitelist für Backup-Lesezugriffe: kein Zugriff außerhalb freigegebener Präfixe.
"""

from __future__ import annotations

from pathlib import Path
from typing import Sequence


def _resolved_or_same(p: Path) -> Path:
    try:
        return p.resolve()
    except OSError:
        return p


def path_under_any_prefix(path: Path, prefixes: Sequence[Path]) -> bool:
    """True wenn resolve(path) unter mindestens einem resolve(prefix) liegt."""
    rp = _resolved_or_same(path)
    for pref in prefixes:
        try:
            base = _resolved_or_same(pref)
            rp.relative_to(base)
            return True
        except ValueError:
            continue
    return False


def assert_paths_allowed(paths: Sequence[str | Path], allowed_prefixes: Sequence[Path]) -> None:
    from core.backup_recovery_i18n import K_PATH_NOT_ALLOWED, tr

    if not allowed_prefixes:
        raise ValueError(tr(K_PATH_NOT_ALLOWED))
    for raw in paths:
        p = Path(raw)
        if not path_under_any_prefix(p, allowed_prefixes):
            raise ValueError(tr(K_PATH_NOT_ALLOWED))
