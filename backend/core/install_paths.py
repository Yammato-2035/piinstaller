"""
System- und Entwicklungspfade für Setuphelfer (installierter Service vs. Repo/Dev).

- Produktion (PI_INSTALLER_DEV != 1): systemweite Pfade, kein Home-Fallback für config.json.
- Entwicklung (PI_INSTALLER_DEV=1): ~/.config/setuphelfer u. a.

Umgebungsvariablen – strikte Reihenfolge im Service-/Installationsbetrieb:
  1) SETUPHELFER_* (aktiver Standard)
  2) PI_INSTALLER_* nur wenn entsprechendes SETUPHELFER_* nicht gesetzt (Legacy)
  3) Default-Pfade bzw. Dev-Fallback
"""

from __future__ import annotations

import os
from pathlib import Path

DEFAULT_OPT = Path("/opt/setuphelfer")
DEFAULT_ETC = Path("/etc/setuphelfer")
DEFAULT_VAR_LIB = Path("/var/lib/setuphelfer")
DEFAULT_VAR_LOG = Path("/var/log/setuphelfer")

LEGACY_OPT = Path("/opt/pi-installer")
LEGACY_ETC = Path("/etc/pi-installer")
LEGACY_VAR_LIB = Path("/var/lib/pi-installer")
LEGACY_VAR_LOG = Path("/var/log/pi-installer")


def is_dev_mode() -> bool:
    return (os.environ.get("PI_INSTALLER_DEV") or "").strip() == "1"


def _env_path_setup_then_legacy(setup_key: str, legacy_key: str) -> Path | None:
    """Liest zuerst SETUPHELFER_*, nur bei leerem Wert PI_INSTALLER_* (Legacy)."""
    for key in (setup_key, legacy_key):
        raw = os.environ.get(key, "").strip()
        if raw:
            return Path(raw)
    return None


def get_opt_install_dir() -> Path:
    p = _env_path_setup_then_legacy("SETUPHELFER_DIR", "PI_INSTALLER_DIR")
    if p is not None:
        return p
    if DEFAULT_OPT.exists() or not LEGACY_OPT.exists():
        return DEFAULT_OPT
    return LEGACY_OPT


def get_config_dir() -> Path:
    """Konfigurationsverzeichnis (/etc/setuphelfer oder Dev: ~/.config/setuphelfer)."""
    p = _env_path_setup_then_legacy("SETUPHELFER_CONFIG_DIR", "PI_INSTALLER_CONFIG_DIR")
    if p is not None:
        return p
    if is_dev_mode():
        return Path.home() / ".config" / "setuphelfer"
    if DEFAULT_ETC.exists() or not LEGACY_ETC.exists():
        return DEFAULT_ETC
    return LEGACY_ETC


def get_state_dir() -> Path:
    """Laufzeit-/Zustandsdaten (Telemetrie-Dateien, sudo.key, remote.db im Service-Betrieb)."""
    p = _env_path_setup_then_legacy("SETUPHELFER_STATE_DIR", "PI_INSTALLER_STATE_DIR")
    if p is not None:
        return p
    if is_dev_mode():
        return Path.home() / ".config" / "setuphelfer"
    if DEFAULT_VAR_LIB.exists() or not LEGACY_VAR_LIB.exists():
        return DEFAULT_VAR_LIB
    return LEGACY_VAR_LIB


def get_log_dir() -> Path:
    p = _env_path_setup_then_legacy("SETUPHELFER_LOG_DIR", "PI_INSTALLER_LOG_DIR")
    if p is not None:
        return p
    if is_dev_mode():
        return Path.home() / ".local" / "share" / "setuphelfer" / "log"
    if DEFAULT_VAR_LOG.exists() or not LEGACY_VAR_LOG.exists():
        return DEFAULT_VAR_LOG
    return LEGACY_VAR_LOG


def audit_rules_file() -> Path:
    return Path("/etc/audit/rules.d/setuphelfer.rules")
