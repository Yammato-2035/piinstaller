"""PI-RS-MSI-GUI-003 — central rescue boot / GUI availability profile."""

from __future__ import annotations

import re
from typing import Any

PROFILE_SCHEMA_VERSION = 1

_MSI_COMPAT_RE = re.compile(r"(?:^|\s)setuphelfer_msi_compat=1(?:\s|$)")
_MSI_PROFILE_RE = re.compile(r"(?:^|\s)setuphelfer_msi_profile=1(?:\s|$)")
_PCI_NOAER_RE = re.compile(r"(?:^|\s)pci=noaer(?:\s|$)")
_NOMODESET_RE = re.compile(r"(?:^|\s)nomodeset(?:\s|$)")
_NOUVEAU_MODESET0_RE = re.compile(r"(?:^|\s)nouveau\.modeset=0(?:\s|$)")

_FORBIDDEN_GUI_PROGRESS_MESSAGES = (
    "Grafische Oberfläche wird gestartet …",
    "X11 wird gestartet …",
    "Chromium wird gestartet …",
    "Wechsel zur grafischen Oberfläche …",
)


def _cmdline_has(pattern: re.Pattern[str], cmdline: str) -> bool:
    return bool(pattern.search(cmdline or ""))


def msi_compat_active(cmdline: str) -> bool:
    return (
        _cmdline_has(_MSI_COMPAT_RE, cmdline)
        or _cmdline_has(_MSI_PROFILE_RE, cmdline)
        or _cmdline_has(_PCI_NOAER_RE, cmdline)
    )


def nomodeset_active(cmdline: str) -> bool:
    return _cmdline_has(_NOMODESET_RE, cmdline) or _cmdline_has(_NOUVEAU_MODESET0_RE, cmdline)


def should_disable_gui_for_msi_compat(cmdline: str, *, dmi_suggests_msi_ge63: bool = False) -> bool:
    if not msi_compat_active(cmdline):
        return False
    if nomodeset_active(cmdline):
        return True
    return dmi_suggests_msi_ge63


def resolve_rescue_boot_profile(
    cmdline: str,
    *,
    dmi_suggests_msi_ge63: bool = False,
) -> dict[str, Any]:
    gui_blocked = should_disable_gui_for_msi_compat(cmdline, dmi_suggests_msi_ge63=dmi_suggests_msi_ge63)
    if gui_blocked:
        return {
            "schema_version": PROFILE_SCHEMA_VERSION,
            "boot_mode": "tui_only",
            "gui_available": False,
            "gui_start_allowed": False,
            "gui_progress_allowed": False,
            "gui_console_transition_allowed": False,
            "reason_code": "msi_compat_nomodeset",
            "operator_mode": "stable_tui",
        }
    return {
        "schema_version": PROFILE_SCHEMA_VERSION,
        "boot_mode": "gui_capable",
        "gui_available": True,
        "gui_start_allowed": True,
        "gui_progress_allowed": True,
        "gui_console_transition_allowed": True,
        "reason_code": "default",
        "operator_mode": "standard",
    }


def is_forbidden_gui_progress_message(message: str) -> bool:
    text = (message or "").strip()
    return any(text == forbidden or forbidden in text for forbidden in _FORBIDDEN_GUI_PROGRESS_MESSAGES)


def forbidden_gui_progress_phases_under_tui_only() -> frozenset[str]:
    return frozenset(
        {
            "x11_starting",
            "gui_starting",
            "openvt_starting",
            "startx_starting",
            "xorg_starting",
            "chromium_starting",
        }
    )
