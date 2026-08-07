"""PI-RS-ASUS-ROOTCAUSE-TELEMETRY-006 — startx/Xorg failure taxonomy helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any

STARTX_FORENSICS_SCHEMA_VERSION = 1

ISSUE_CODES = (
    "gui.startx.binary_missing",
    "gui.startx.permission_denied",
    "gui.startx.no_controlling_tty",
    "gui.startx.invalid_vt",
    "gui.startx.xauth_failed",
    "gui.startx.xinit_failed",
    "gui.xorg.exec_failed",
    "gui.xorg.config_failed",
    "gui.xorg.no_device",
    "gui.xorg.no_screen",
    "gui.xorg.driver_missing",
    "gui.xorg.permission_failed",
    "gui.xorg.socket_not_created",
    "gui.xorg.exited_early",
    "gui.xorg.timeout",
    "gui.display_not_ready",
    "gui.backend_not_ready",
    "gui.ui_port_conflict",
    "gui.chromium_started_without_display",
)


def classify_startx_failure(
    *,
    startx_invoked: bool,
    startx_exit_code: int | None,
    xorg_started: bool,
    xorg_log_created: bool,
    x_socket_created: bool,
    stderr_excerpt: str = "",
) -> dict[str, Any]:
    low = (stderr_excerpt or "").lower()
    code = "gui.xorg.exited_early"
    if not startx_invoked:
        code = "gui.startx.binary_missing"
    elif startx_exit_code in (126, 127):
        code = "gui.startx.binary_missing"
    elif "permission" in low or startx_exit_code == 13:
        code = "gui.startx.permission_denied"
    elif "no screens" in low:
        code = "gui.xorg.no_screen"
    elif "no devices" in low or "no device" in low:
        code = "gui.xorg.no_device"
    elif "xauth" in low or "authorization" in low:
        code = "gui.startx.xauth_failed"
    elif startx_invoked and not xorg_started:
        code = "gui.xorg.exec_failed"
    elif xorg_started and not xorg_log_created:
        code = "gui.xorg.config_failed"
    elif xorg_started and not x_socket_created:
        code = "gui.xorg.socket_not_created"
    elif xorg_started and x_socket_created:
        code = "gui.display_not_ready"
    return {
        "schema_version": STARTX_FORENSICS_SCHEMA_VERSION,
        "issue_code": code,
        "startx_invoked": startx_invoked,
        "startx_exit_code": startx_exit_code,
        "xorg_started": xorg_started,
        "xorg_log_created": xorg_log_created,
        "x_socket_created": x_socket_created,
        "known_issue_codes": list(ISSUE_CODES),
        "production_ready": False,
    }


def x_socket_present(x11_unix: Path | None = None) -> bool:
    root = x11_unix or Path("/tmp/.X11-unix")
    if not root.is_dir():
        return False
    return any(root.glob("X*"))


def build_xorg_process_sentinel(
    *,
    startx_invoked: bool = False,
    startx_pid: int = 0,
    startx_exit_code: int | None = None,
    xinit_started: bool = False,
    xorg_started: bool = False,
    xorg_pid: int | None = None,
    x_socket_created: bool = False,
    xorg_log_created: bool = False,
) -> dict[str, Any]:
    return {
        "schema_version": STARTX_FORENSICS_SCHEMA_VERSION,
        "startx_invoked": startx_invoked,
        "startx_pid": startx_pid,
        "startx_exit_code": startx_exit_code,
        "xinit_started": xinit_started,
        "xorg_started": xorg_started,
        "xorg_pid": xorg_pid,
        "x_socket_created": x_socket_created,
        "xorg_log_created": xorg_log_created,
        "production_ready": False,
    }
