"""
Pfadauflösung für Debug-Logs. Keine Rotation/Logging-Logik.
"""

import os
from pathlib import Path
from typing import Optional

DEFAULT_DEBUG_LOG_PATH = "/var/log/piinstaller/piinstaller.debug.jsonl"
FALLBACK_DEBUG_LOG_PATH = "~/.cache/piinstaller/logs/piinstaller.debug.jsonl"


def _ensure_fallback_path() -> str:
    """Stellt Fallback-Pfad her (Parent anlegen) und gibt ihn zurück."""
    fallback = Path(FALLBACK_DEBUG_LOG_PATH).expanduser().resolve()
    try:
        fallback.parent.mkdir(parents=True, exist_ok=True)
    except (OSError, PermissionError):
        pass
    return str(fallback)


def resolve_debug_log_path(preferred_path: Optional[str] = None) -> str:
    """
    Liefert den zu verwendenden Debug-Log-Pfad.
    - Wenn preferred_path gesetzt: nutze ihn nur, wenn Parent-Dir erstellbar und schreibbar ist; sonst Fallback.
    - Sonst: versuche /var/log/piinstaller/ (schreibbar?), sonst Fallback in Home-Cache.
    """
    if preferred_path and preferred_path.strip():
        p = Path(preferred_path.strip()).expanduser().resolve()
        try:
            p.parent.mkdir(parents=True, exist_ok=True)
            if os.access(p.parent, os.W_OK):
                return str(p)
        except (OSError, PermissionError):
            pass
        # Preferred nicht nutzbar (z. B. /var/log/piinstaller ohne root) → Fallback
        return _ensure_fallback_path()
    # Kein preferred_path: zuerst /var/log/piinstaller prüfen
    default_dir = Path(DEFAULT_DEBUG_LOG_PATH).parent
    try:
        default_dir.mkdir(parents=True, exist_ok=True)
        if os.access(default_dir, os.W_OK):
            return DEFAULT_DEBUG_LOG_PATH
    except (OSError, PermissionError):
        pass
    return _ensure_fallback_path()
