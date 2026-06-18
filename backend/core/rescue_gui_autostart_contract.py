"""Rescue GUI autostart contract (RS-P2A)."""

from __future__ import annotations

from typing import Any

CONTRACT_VERSION = 1


def build_gui_autostart_status(
    *,
    html_present: bool,
    backend_running: bool,
    kiosk_launcher_present: bool,
    gui_start_exit_code: int | None = None,
) -> dict[str, Any]:
    if not html_present:
        return {
            "contract_version": CONTRACT_VERSION,
            "gui_enabled_by_default": True,
            "status": "failed",
            "reason": "frontend_missing",
            "display_mode": "text_fallback",
            "text_fallback_only_on_failure": True,
            "execute_allowed": False,
        }
    if not backend_running:
        return {
            "contract_version": CONTRACT_VERSION,
            "gui_enabled_by_default": True,
            "status": "failed",
            "reason": "backend_not_running",
            "display_mode": "text_fallback",
            "text_fallback_only_on_failure": True,
            "execute_allowed": False,
        }
    if not kiosk_launcher_present:
        return {
            "contract_version": CONTRACT_VERSION,
            "gui_enabled_by_default": True,
            "status": "failed",
            "reason": "kiosk_launcher_missing",
            "display_mode": "text_fallback",
            "text_fallback_only_on_failure": True,
            "execute_allowed": False,
        }
    if gui_start_exit_code not in (None, 0):
        return {
            "contract_version": CONTRACT_VERSION,
            "gui_enabled_by_default": True,
            "status": "failed",
            "reason": f"gui_start_exit_{gui_start_exit_code}",
            "display_mode": "text_fallback",
            "text_fallback_only_on_failure": True,
            "execute_allowed": False,
        }
    return {
        "contract_version": CONTRACT_VERSION,
        "gui_enabled_by_default": True,
        "status": "starting",
        "reason": "graphical_default",
        "display_mode": "graphical",
        "text_fallback_only_on_failure": True,
        "execute_allowed": False,
    }
