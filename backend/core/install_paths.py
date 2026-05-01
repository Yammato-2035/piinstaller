"""
System- und Entwicklungspfade für Setuphelfer (installierter Service vs. Repo/Dev).

- Produktion (PI_INSTALLER_DEV != 1): systemweite Pfade unter /opt/setuphelfer usw.
- Entwicklung (PI_INSTALLER_DEV=1): ~/.config/setuphelfer u. a.

Umgebungsvariablen – strikte Reihenfolge im Service-/Installationsbetrieb:
  1) SETUPHELFER_* (aktiver Standard)
  2) PI_INSTALLER_* nur wenn entsprechendes SETUPHELFER_* nicht gesetzt (Legacy-Variablenname)
  3) Default-Pfade bzw. Dev-Fallback

Hinweis: Kein Fallback mehr auf den historischen Ordner „pi-installer“ unter /opt;
aktives Ziel ist ausschließlich /opt/setuphelfer (oder SETUPHELFER_DIR).
"""

from __future__ import annotations

import os
from pathlib import Path, PurePosixPath

DEFAULT_OPT = Path("/opt/setuphelfer")
DEFAULT_ETC = Path("/etc/setuphelfer")
DEFAULT_VAR_LIB = Path("/var/lib/setuphelfer")
DEFAULT_VAR_LOG = Path("/var/log/setuphelfer")

# Historischer Ordnername (nur Diagnose / Konflikterkennung, kein aktives Installationsziel).
LEGACY_OPT_DIRNAME = "pi-installer"


def legacy_opt_live_path() -> Path:
    """Früherer Live-Pfad (falls noch vorhanden); nicht für neue Deployments verwenden."""
    return Path("/opt") / LEGACY_OPT_DIRNAME


def path_text_suggests_legacy_pi_tree(text: str) -> bool:
    """
    True, wenn Text auf den archivierten Legacy-Baum hindeutet
    (Ordner pi-installer oder pi-installer.archiv-* unter /opt).
    """
    if not text:
        return False
    t = text.strip().lower()
    if f"{LEGACY_OPT_DIRNAME}.archiv-" in t:
        return True
    try:
        first = t.split()[0] if t else ""
        parts = [x.lower() for x in PurePosixPath(first).parts]
    except ValueError:
        return False
    for i, seg in enumerate(parts):
        if seg == "opt" and i + 1 < len(parts):
            nxt = parts[i + 1]
            if nxt == LEGACY_OPT_DIRNAME or nxt.startswith(f"{LEGACY_OPT_DIRNAME}.archiv-"):
                return True
    return False


def is_dev_mode() -> bool:
    return (os.environ.get("PI_INSTALLER_DEV") or "").strip() == "1"


def _env_path_setup_then_legacy(setup_key: str, legacy_key: str) -> Path | None:
    """Liest zuerst SETUPHELFER_*, nur bei leerem Wert PI_INSTALLER_* (Legacy-ENV-Name)."""
    for key in (setup_key, legacy_key):
        raw = os.environ.get(key, "").strip()
        if raw:
            return Path(raw)
    return None


def get_opt_install_dir() -> Path:
    p = _env_path_setup_then_legacy("SETUPHELFER_DIR", "PI_INSTALLER_DIR")
    if p is not None:
        return p
    return DEFAULT_OPT


def get_config_dir() -> Path:
    """Konfigurationsverzeichnis (/etc/setuphelfer oder Dev: ~/.config/setuphelfer)."""
    p = _env_path_setup_then_legacy("SETUPHELFER_CONFIG_DIR", "PI_INSTALLER_CONFIG_DIR")
    if p is not None:
        return p
    if is_dev_mode():
        return Path.home() / ".config" / "setuphelfer"
    return DEFAULT_ETC


def get_state_dir() -> Path:
    """Laufzeit-/Zustandsdaten (Telemetrie-Dateien, sudo.key, remote.db im Service-Betrieb)."""
    p = _env_path_setup_then_legacy("SETUPHELFER_STATE_DIR", "PI_INSTALLER_STATE_DIR")
    if p is not None:
        return p
    if is_dev_mode():
        return Path.home() / ".config" / "setuphelfer"
    return DEFAULT_VAR_LIB


def get_log_dir() -> Path:
    p = _env_path_setup_then_legacy("SETUPHELFER_LOG_DIR", "PI_INSTALLER_LOG_DIR")
    if p is not None:
        return p
    if is_dev_mode():
        return Path.home() / ".local" / "share" / "setuphelfer" / "log"
    return DEFAULT_VAR_LOG


def audit_rules_file() -> Path:
    return Path("/etc/audit/rules.d/setuphelfer.rules")
