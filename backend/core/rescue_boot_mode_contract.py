"""Rescue boot mode contract — text default, GUI optional (RS-P2C)."""

from __future__ import annotations

import re
from typing import Any

CONTRACT_VERSION = 1

_MODE_RE = re.compile(r"(?:^|\s)setuphelfer_mode=(\w+)(?:\s|$)")
_KIOSK_RE = re.compile(r"(?:^|\s)setuphelfer_kiosk=(\d)(?:\s|$)")


def parse_cmdline(cmdline: str) -> dict[str, Any]:
    mode_match = _MODE_RE.search(cmdline or "")
    kiosk_match = _KIOSK_RE.search(cmdline or "")
    mode = mode_match.group(1) if mode_match else "text"
    kiosk = kiosk_match.group(1) == "1" if kiosk_match else False
    if mode == "gui":
        kiosk = True
    if "setuphelfer_kiosk=0" in (cmdline or ""):
        kiosk = False
    return {
        "contract_version": CONTRACT_VERSION,
        "setuphelfer_mode": mode,
        "setuphelfer_kiosk": kiosk,
        "text_mode_default": mode == "text" and not kiosk,
        "gui_autostart_allowed": mode == "gui" and kiosk,
        "diagnostics_mode": mode == "diagnostics",
        "hardware_mode": mode == "hardware",
        "backup_execute_allowed": False,
    }


def should_start_gui(cmdline: str) -> bool:
    parsed = parse_cmdline(cmdline)
    return bool(parsed.get("gui_autostart_allowed"))


def should_start_text_tui(cmdline: str) -> bool:
    parsed = parse_cmdline(cmdline)
    return parsed.get("setuphelfer_mode") in ("text", "diagnostics", "hardware") or not parsed.get("setuphelfer_kiosk")
