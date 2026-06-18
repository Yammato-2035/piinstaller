"""Boot evidence for rescue stick — redacted persistence to SETUP_LOGS (RS-P2C)."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from core.rescue_boot_mode_contract import parse_cmdline
from core.telemetry_redaction_contract import redact_telemetry_payload

BOOT_EVIDENCE_VERSION = 1

_MAC_RE = re.compile(r"([0-9A-Fa-f]{2}(?::[0-9A-Fa-f]{2}){5})")
_IP_RE = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
_SERIAL_KEYS = frozenset({"serial", "SERIAL", "serial_number", "disk_serial"})


def _read_cmdline() -> str:
    try:
        return Path("/proc/cmdline").read_text(encoding="utf-8", errors="replace").strip()
    except OSError:
        return ""


def build_boot_state(*, phase: str = "", extra: dict[str, Any] | None = None) -> dict[str, Any]:
    cmdline = _read_cmdline()
    mode = parse_cmdline(cmdline)
    body: dict[str, Any] = {
        "schema_version": BOOT_EVIDENCE_VERSION,
        "phase": phase,
        "cmdline": cmdline,
        "selected_mode": mode.get("setuphelfer_mode"),
        "kiosk_requested": mode.get("setuphelfer_kiosk"),
        "text_mode_started": mode.get("setuphelfer_mode") == "text" or phase == "text_mode_started",
        "gui_requested": mode.get("gui_autostart_allowed") or phase == "gui_requested",
        "backup_execute_allowed": False,
    }
    if extra:
        body.update(extra)
    return body


_SECRET_CMD_RE = re.compile(
    r"(?i)(wifi_psk|psk|password|passwd|token|api_key|secret)=[^\s]+"
)


def redact_boot_state(payload: dict[str, Any]) -> dict[str, Any]:
    redacted = redact_telemetry_payload(payload)
    cmd = str(redacted.get("cmdline") or "")
    cmd = _SECRET_CMD_RE.sub(r"\1=[REDACTED]", cmd)
    cmd = _MAC_RE.sub("[MAC_REDACTED]", cmd)
    cmd = _IP_RE.sub("[IP_REDACTED]", cmd)
    redacted["cmdline"] = cmd
    for key in list(redacted.keys()):
        if key in _SERIAL_KEYS:
            redacted[key] = "[SERIAL_REDACTED]"
    return redacted


def write_boot_state_files(
    *,
    phase: str = "",
    extra: dict[str, Any] | None = None,
    state_dir: Path | None = None,
    evidence_dir: Path | None = None,
) -> dict[str, str]:
    raw = build_boot_state(phase=phase, extra=extra)
    redacted = redact_boot_state(raw)
    run_dir = state_dir or Path("/run/setuphelfer-rescue")
    ev_dir = evidence_dir or Path("/var/lib/setuphelfer-rescue/local/evidence")
    run_dir.mkdir(parents=True, exist_ok=True)
    ev_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "boot_state": run_dir / "boot_state.json",
        "boot_state_redacted": ev_dir / "boot_state_redacted.json",
    }
    paths["boot_state"].write_text(json.dumps(raw, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    paths["boot_state_redacted"].write_text(
        json.dumps(redacted, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return {k: str(v) for k, v in paths.items()}
