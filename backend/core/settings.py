"""
Remote-Companion-Konfiguration.
Nutzt die bestehende Settings-Struktur (config.json unter "settings.remote").
Alle Remote-Keys hier zentral definiert; App lädt/speichert sie über APP_SETTINGS.
"""

from typing import Any


# Defaults für Remote-Feature (eine Quelle der Wahrheit)
REMOTE_DEFAULTS = {
    "REMOTE_FEATURE_ENABLED": False,
    "REMOTE_PAIRING_TTL_SECONDS": 300,
    "REMOTE_SESSION_TTL_SECONDS": 86400,
    "REMOTE_PUBLIC_HOST": "",
    "REMOTE_BASE_URL": "",
    "REMOTE_DEVICE_NAME": "",
}


def get_remote_defaults() -> dict[str, Any]:
    """Liefert die Standardwerte für settings.remote (für _default_settings())."""
    return dict(REMOTE_DEFAULTS)


def get_remote_settings(settings: dict[str, Any] | None) -> dict[str, Any]:
    """
    Liefert die effektive Remote-Konfiguration (Defaults + ggf. gespeicherte Werte).
    settings: der komplette APP_SETTINGS-Dict oder nur settings.get("remote").
    """
    if not settings:
        return get_remote_defaults()
    remote = settings.get("remote") if isinstance(settings, dict) else None
    if not isinstance(remote, dict):
        return get_remote_defaults()
    out = get_remote_defaults()
    for k, v in remote.items():
        if k in out:
            out[k] = v
    return out
