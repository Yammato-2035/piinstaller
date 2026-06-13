"""
System Status Providers — legacy probe adapters for system_status_core (Phase G.14).

Security/updates probes remain in ``app`` until fully extracted; this module is the
only layer that may import ``app`` for system-status ampel computation.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

SYSTEM_STATUS_PROVIDER_VERSION = 1

_PROVIDER_MODULE = "core.system_status_providers"


def load_backup_realtest_state() -> dict[str, Any]:
    """Read persisted ``backup.realtest_state`` from config.json (no app import)."""
    try:
        from core.install_paths import get_config_dir

        path = get_config_dir() / "config.json"
        if not path.is_file():
            return {}
        cfg = json.loads(path.read_text(encoding="utf-8"))
        settings = cfg.get("settings") if isinstance(cfg.get("settings"), dict) else {}
        backup = settings.get("backup") if isinstance(settings.get("backup"), dict) else {}
        rs = backup.get("realtest_state")
        return rs if isinstance(rs, dict) else {}
    except Exception:
        return {}


def provide_security_config() -> dict[str, Any]:
    """Legacy security probe bundle (delegates to ``app.get_security_config``)."""
    import app as app_module

    sec = app_module.get_security_config()
    return sec if isinstance(sec, dict) else {}


def provide_updates_categorized() -> dict[str, Any]:
    """Legacy updates categorization (delegates to ``app.get_updates_categorized``)."""
    import app as app_module

    upd = app_module.get_updates_categorized()
    return upd if isinstance(upd, dict) else {}


def build_system_status_providers_diagnostics() -> dict[str, Any]:
    return {
        "provider_version": SYSTEM_STATUS_PROVIDER_VERSION,
        "provider_module": _PROVIDER_MODULE,
        "public_functions": [
            "load_backup_realtest_state",
            "provide_security_config",
            "provide_updates_categorized",
            "build_system_status_providers_diagnostics",
        ],
        "app_import_allowed": True,
        "read_only": True,
        "writes_allowed": False,
    }
