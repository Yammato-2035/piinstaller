"""PI-RS-TUI-AUTO-001 — contracts, cmdline, key codes for TUI input diagnostic."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

DIAG_FLAG = "setuphelfer_tui_input_diag=1"
DIAG_FLAG_NAME = "setuphelfer_tui_input_diag"
AUTO_SHUTDOWN_FLAG = "setuphelfer_tui_input_diag_auto_shutdown=1"
EXTERNAL_KB_FLAG = "setuphelfer_tui_input_diag_external_keyboard=1"

BLOCKED_CODE = "RESCUE_TUI_INPUT_DIAGNOSTIC_MODE_READ_ONLY"
BLOCKED_MESSAGE_DE = "Diese Funktion ist während der Eingabediagnose gesperrt."
BLOCKED_MESSAGE_EN = "This function is disabled during input diagnostics."

# Linux input event KEY_* codes (input-event-codes.h)
KEY_CODES: dict[int, str] = {
    1: "KEY_ESC",
    15: "KEY_TAB",
    28: "KEY_ENTER",
    29: "KEY_LEFTCTRL",
    30: "KEY_A",
    42: "KEY_LEFTSHIFT",
    56: "KEY_LEFTALT",
    58: "KEY_CAPSLOCK",
    59: "KEY_F1",
    60: "KEY_F2",
    61: "KEY_F3",
    69: "KEY_NUMLOCK",
    97: "KEY_RIGHTCTRL",
    100: "KEY_RIGHTALT",
    103: "KEY_UP",
    105: "KEY_LEFT",
    106: "KEY_RIGHT",
    108: "KEY_DOWN",
}

EV_KEY = 1
EV_SYN = 0

# input_event: timeval(2x long) + type/code/value — size differs 32/64
INPUT_EVENT_FMT_64 = "llHHi"
INPUT_EVENT_SIZE_64 = 24
INPUT_EVENT_FMT_32 = "iiHHi"
INPUT_EVENT_SIZE_32 = 16


@dataclass(frozen=True)
class DiagnosticConfig:
    run_id: str
    expected_device_family: str = "msi"
    tty_menu: str = "/dev/tty1"
    tty_diagnostic: str = "/dev/tty2"
    input_test_timeout_s: int = 10
    menu_test_timeout_s: int = 25
    external_keyboard_timeout_s: int = 60
    auto_vt_switch: bool = True
    auto_shutdown: bool = False
    evidence_root: Path = Path("/run/setuphelfer/tui-input-diagnostics")
    interactive: bool = True
    observe_only: bool = False


@dataclass
class DiagnosticResult:
    run_id: str
    status: str = "review_required"
    payload_version: str | None = None
    machine_identity: dict[str, Any] = field(default_factory=dict)
    input_devices: list[dict[str, Any]] = field(default_factory=list)
    internal_keyboard_test: dict[str, Any] = field(default_factory=dict)
    external_keyboard_test: dict[str, Any] = field(default_factory=dict)
    menu_input_test: dict[str, Any] = field(default_factory=dict)
    whiptail_analysis: dict[str, Any] = field(default_factory=dict)
    tty_analysis: dict[str, Any] = field(default_factory=dict)
    process_analysis: dict[str, Any] = field(default_factory=dict)
    screen_analysis: dict[str, Any] = field(default_factory=dict)
    hypotheses: dict[str, Any] = field(default_factory=dict)
    leading_hypothesis: str | None = None
    confidence: str = "none"
    recommended_repair_path: str | None = None
    warnings: list[dict[str, Any]] = field(default_factory=list)
    errors: list[dict[str, Any]] = field(default_factory=list)
    write_actions_blocked: bool = False


@dataclass
class DiagnosticDecision:
    leading_hypothesis: str
    confidence: str
    recommended_repair_path: str | None
    reasons: list[str] = field(default_factory=list)
    contradicting_evidence: list[str] = field(default_factory=list)
    missing_evidence: list[str] = field(default_factory=list)


def parse_cmdline(cmdline: str | None = None) -> dict[str, str]:
    raw = cmdline if cmdline is not None else _read_cmdline()
    out: dict[str, str] = {}
    for tok in raw.split():
        if "=" in tok:
            k, v = tok.split("=", 1)
            out[k] = v
        else:
            out[tok] = "1"
    return out


def _read_cmdline() -> str:
    try:
        return Path("/proc/cmdline").read_text(encoding="utf-8", errors="replace").strip()
    except OSError:
        return ""


def diagnostic_mode_enabled(cmdline: str | None = None) -> bool:
    tokens = (cmdline if cmdline is not None else _read_cmdline()).split()
    return DIAG_FLAG in tokens or any(
        t.startswith(f"{DIAG_FLAG_NAME}=") and t.split("=", 1)[1] == "1" for t in tokens
    )


def diagnostic_auto_shutdown_enabled(cmdline: str | None = None) -> bool:
    tokens = (cmdline if cmdline is not None else _read_cmdline()).split()
    return AUTO_SHUTDOWN_FLAG in tokens


def diagnostic_timeout_s(cmdline: str | None = None, default: int = 45) -> int:
    parsed = parse_cmdline(cmdline)
    raw = parsed.get("setuphelfer_tui_input_diag_timeout", "")
    try:
        val = int(raw)
    except (TypeError, ValueError):
        return default
    return val if 5 <= val <= 600 else default


def write_guard_response() -> dict[str, str]:
    return {
        "status": "blocked",
        "code": BLOCKED_CODE,
        "message_de": BLOCKED_MESSAGE_DE,
        "message_en": BLOCKED_MESSAGE_EN,
    }


def blocked_tui_actions() -> frozenset[str]:
    """TUI menu tags that must not run destructive work in diagnostic mode."""
    return frozenset({"e2e", "plan", "gui", "reboot", "poweroff"})


def redact_serial_like(value: str) -> str:
    text = (value or "").strip()
    if not text:
        return ""
    if re.search(r"(?i)(serial|mac|uuid)", text) or len(text) > 24:
        import hashlib

        return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]
    return text


def default_run_id() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def config_from_cmdline(*, evidence_root: Path | None = None, interactive: bool = True) -> DiagnosticConfig:
    cmdline = _read_cmdline()
    return DiagnosticConfig(
        run_id=default_run_id(),
        auto_shutdown=diagnostic_auto_shutdown_enabled(cmdline),
        input_test_timeout_s=min(10, diagnostic_timeout_s(cmdline)),
        menu_test_timeout_s=diagnostic_timeout_s(cmdline),
        evidence_root=evidence_root
        or Path(os.environ.get("SETUPHELFER_TUI_INPUT_DIAG_ROOT", "/run/setuphelfer/tui-input-diagnostics")),
        interactive=interactive,
        observe_only=not interactive,
    )
