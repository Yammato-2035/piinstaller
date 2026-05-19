"""Erkennung blockierender Paketmanager-Aktivität (Backup-Preflight, UPDATE-CONFLICT-041)."""

from __future__ import annotations

import re
from typing import Any

import psutil

# Nur Inventar / Lesen — kollidiert nicht mit laufendem tar (kein Lock auf dpkg).
_READONLY_APT_MARKERS = (
    "apt list",
    "apt-cache ",
    "apt show ",
    "apt policy",
    "apt search ",
)

_SHELL_NAMES = frozenset({"sh", "bash", "dash"})
_CONTROL_PLANE_NAMES = frozenset({"systemctl", "systemd-run", "pkexec"})
_BLOCKING_CMD_RE = re.compile(
    r"(?:^|\s)(?:/usr/bin/)?(?:apt-get|dpkg|unattended-upgrade)(?:\s|$)",
    re.IGNORECASE,
)
# Nur Metadaten — kein Paketinstall (Mint-Update-Check); tar bleibt Haupt-Risiko bei upgrade/install.
_APT_GET_READONLY_RE = re.compile(
    r"\bapt-get\s+(update|clean|autoclean|check)(?:\s|$)",
    re.IGNORECASE,
)


def _apt_get_cmdline_is_mutating(hay_l: str) -> bool:
    if "apt-get" not in hay_l:
        return False
    if _APT_GET_READONLY_RE.search(hay_l):
        return False
    return True


def is_blocking_package_activity(hay: str, name: str) -> bool:
    """
    True nur für echte Paketmanager-Schreibaktivität, nicht für systemctl/pkill-Helfer
    oder Unit-Namen in Kommandozeilen (z. B. apt-daily.service).
    """
    hay_l = hay.lower()
    # apt-get mit -s / --simulate / --dry-run: nur Simulationslauf, kein Schreibzugriff.
    if "apt-get" in hay_l and re.search(r"(^|[\s/])(-s|--simulate|--dry-run)(?=\s|$)", hay_l):
        return False
    name_l = (name or "").strip().lower()
    if name_l in _CONTROL_PLANE_NAMES:
        return False
    if "/usr/lib/apt/methods/" in hay_l:
        return False
    if "unattended-upgrade-shutdown" in hay_l:
        return False
    if any(marker in hay_l for marker in _READONLY_APT_MARKERS):
        return False
    if name_l == "apt-get":
        return _apt_get_cmdline_is_mutating(hay_l)
    if name_l in {"dpkg", "apt.systemd.daily"}:
        return True
    if name_l == "apt":
        if not hay_l.replace("apt", "", 1).strip():
            return False
        if any(marker in hay_l for marker in _READONLY_APT_MARKERS):
            return False
        if re.search(
            r"\bapt\s+(install|upgrade|full-upgrade|remove|purge|dist-upgrade|autoremove|reinstall)\b",
            hay_l,
        ):
            return True
        return False
    if name_l.startswith("unattended-upgrade"):
        return True
    if name_l in _SHELL_NAMES:
        if _APT_GET_READONLY_RE.search(hay_l):
            return False
        return bool(_BLOCKING_CMD_RE.search(hay_l))
    return False


def detect_active_package_operations() -> list[dict[str, Any]]:
    active: list[dict[str, Any]] = []
    try:
        for proc in psutil.process_iter(["pid", "name", "cmdline"]):
            try:
                pid = int(proc.info.get("pid") or 0)
                name = str(proc.info.get("name") or "").strip()
                cmdline = proc.info.get("cmdline") or []
                cmd_joined = " ".join(str(x) for x in cmdline if x)
                hay = f"{name} {cmd_joined}"
                if is_blocking_package_activity(hay, name):
                    active.append(
                        {
                            "pid": pid,
                            "name": name,
                            "cmdline": cmd_joined[:300],
                        }
                    )
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
    except Exception:
        return []
    return active
