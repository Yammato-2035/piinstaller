"""
System Status Core — canonical ampel/status computation for system status facade.

Phase G.12: ampel logic extracted from ``app._compute_system_status``; facade delegates only.
Security/updates probes remain legacy adapters to ``app`` inside this core (not in facade).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

SYSTEM_STATUS_CORE_VERSION = 1

_AMPEL_KEYS = ("backup", "restore", "security", "updates")


def _load_realtest_state() -> dict[str, Any]:
    import app as app_module

    backup = app_module.APP_SETTINGS.get("backup") if isinstance(app_module.APP_SETTINGS, dict) else {}
    rs = backup.get("realtest_state") if isinstance(backup, dict) else {}
    return rs if isinstance(rs, dict) else {}


def _legacy_get_security_config() -> dict[str, Any]:
    import app as app_module

    sec = app_module.get_security_config()
    return sec if isinstance(sec, dict) else {}


def _legacy_get_updates_categorized() -> dict[str, Any]:
    import app as app_module

    upd = app_module.get_updates_categorized()
    return upd if isinstance(upd, dict) else {}


def load_backup_realtest_state() -> dict[str, Any]:
    """Public read-only accessor for persisted backup realtest_state."""
    return _load_realtest_state()


def build_backup_status(*, realtest_state: dict[str, Any] | None = None) -> str:
    """Legacy ampel color for backup (green/yellow/red)."""
    rs = realtest_state if realtest_state is not None else _load_realtest_state()
    if rs.get("last_verify_ok") is True:
        p = rs.get("last_verify_path")
        if p and Path(str(p)).exists():
            return "green"
        return "yellow"
    if rs.get("last_verify_shallow_ok") is True:
        return "yellow"
    if rs.get("last_verify_ok") is False:
        return "yellow"
    return "red"


def build_restore_status(*, realtest_state: dict[str, Any] | None = None) -> str:
    """Legacy ampel color for restore (green/yellow/red)."""
    rs = realtest_state if realtest_state is not None else _load_realtest_state()
    if rs.get("last_preview_ok") is True:
        return "green"
    if rs.get("last_dry_run_ok") is True:
        return "yellow"
    if rs.get("last_preview_ok") is False or rs.get("last_dry_run_ok") is False:
        return "yellow"
    return "red"


def build_security_status() -> str:
    """Legacy ampel color for security from live config probes."""
    try:
        sec = _legacy_get_security_config() or {}
        ufw = sec.get("ufw") or {}
        ssh_cfg = str((sec.get("ssh") or {}).get("config") or "").lower()
        ufw_status = str(ufw.get("status") or "").lower()
        ufw_active_effective = bool(ufw.get("active")) or (
            bool(ufw.get("installed"))
            and (
                "active" in ufw_status
                or "aktiv" in ufw_status
                or "enabled=yes" in ufw_status
                or "via systemctl" in ufw_status
                or "wahrscheinlich" in ufw_status
            )
        )
        active_count = (
            (1 if ufw_active_effective else 0)
            + (1 if bool((sec.get("fail2ban") or {}).get("running")) else 0)
            + (1 if bool((sec.get("auto_updates") or {}).get("enabled")) else 0)
            + (1 if bool((sec.get("ssh_hardening") or {}).get("enabled")) else 0)
            + (1 if bool((sec.get("audit_logging") or {}).get("enabled")) else 0)
        )
        if not bool(ufw.get("installed")):
            return "red"
        if "permitrootlogin yes" in ssh_cfg:
            return "red"
        if active_count >= 5:
            return "green"
        if active_count >= 1:
            return "yellow"
        return "red"
    except Exception:
        return "yellow"


def build_update_status() -> str:
    """Legacy ampel color for updates from categorized apt list."""
    try:
        upd = _legacy_get_updates_categorized()
        total = int(upd.get("total") or 0)
        cats = upd.get("categories") or {}
        sec_cnt = int(cats.get("security") or 0)
        crit_cnt = int(cats.get("critical") or 0)
        if total == 0:
            return "green"
        if sec_cnt > 0 or crit_cnt > 0:
            return "red"
        return "yellow"
    except Exception:
        return "yellow"


def build_overall_status(*, realtest_state: dict[str, Any] | None = None) -> dict[str, str]:
    """Full legacy ampel dict (``_compute_system_status`` shape)."""
    rs = realtest_state if realtest_state is not None else _load_realtest_state()
    return {
        "backup": build_backup_status(realtest_state=rs),
        "restore": build_restore_status(realtest_state=rs),
        "security": build_security_status(),
        "updates": build_update_status(),
    }


def build_system_status_diagnostics() -> dict[str, Any]:
    return {
        "core_version": SYSTEM_STATUS_CORE_VERSION,
        "core_module": "core.system_status_core",
        "public_functions": [
            "build_backup_status",
            "build_restore_status",
            "build_security_status",
            "build_update_status",
            "build_overall_status",
            "build_system_status_diagnostics",
        ],
        "ampel_keys": list(_AMPEL_KEYS),
        "legacy_adapters_in_core": [
            "app.APP_SETTINGS.backup.realtest_state",
            "app.get_security_config",
            "app.get_updates_categorized",
        ],
        "facade_ampel_computation": False,
        "read_only": True,
        "writes_allowed": False,
    }
