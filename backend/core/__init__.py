"""
PI-Installer Core – zentrale Konfiguration und Konstanten.
Erweiterung für Remote-Companion-Settings (Phase 1).
"""

from .settings import (
    get_remote_defaults,
    get_remote_settings,
)

__all__ = [
    "get_remote_defaults",
    "get_remote_settings",
]
