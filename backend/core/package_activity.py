"""Erkennung blockierender Paketmanager-Aktivität (Backup-Preflight, UPDATE-CONFLICT-041)."""

from __future__ import annotations

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


def is_blocking_package_activity(hay: str, name: str) -> bool:
    hay_l = hay.lower()
    name_l = name.lower()
    if "/usr/lib/apt/methods/" in hay_l:
        return False
    if "unattended-upgrade-shutdown" in hay_l:
        return False
    if any(marker in hay_l for marker in _READONLY_APT_MARKERS):
        return False
    if any(
        token in hay_l
        for token in (
            " apt-get ",
            " dpkg ",
            "unattended-upgrade",
            "apt.systemd.daily",
        )
    ):
        return True
    if " apt " in hay_l:
        return True
    return name_l in {"apt", "apt-get", "dpkg", "apt.systemd.daily"}


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
