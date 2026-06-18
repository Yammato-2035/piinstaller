"""GUI watchdog contract — fallback to TUI on failure (RS-P2C)."""

from __future__ import annotations

from typing import Any

CONTRACT_VERSION = 1

GUI_ERROR_CODES = frozenset(
    {
        "gui_backend_unreachable",
        "gui_frontend_missing",
        "gui_display_missing",
        "gui_browser_missing",
        "gui_start_timeout",
        "gui_unknown_failure",
    }
)


def build_gui_watchdog_result(
    *,
    backend_ok: bool,
    frontend_ok: bool,
    display_ok: bool,
    browser_ok: bool,
    started: bool = False,
    timed_out: bool = False,
    error_code: str = "",
) -> dict[str, Any]:
    if not frontend_ok:
        code = "gui_frontend_missing"
    elif not backend_ok:
        code = "gui_backend_unreachable"
    elif not display_ok:
        code = "gui_display_missing"
    elif not browser_ok:
        code = "gui_browser_missing"
    elif timed_out:
        code = "gui_start_timeout"
    elif error_code in GUI_ERROR_CODES:
        code = error_code
    elif started:
        code = ""
    else:
        code = "gui_unknown_failure"

    fallback = bool(code)
    return {
        "contract_version": CONTRACT_VERSION,
        "gui_started": started and not fallback,
        "gui_failed": fallback,
        "gui_error_code": code or None,
        "fallback_to_tui": fallback,
        "execute_allowed": False,
    }
