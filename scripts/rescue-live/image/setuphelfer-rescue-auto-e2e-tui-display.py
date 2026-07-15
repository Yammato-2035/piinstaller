#!/usr/bin/env python3
"""Non-blocking live TUI for auto physical E2E / discovery (001D6/001D7B)."""

from __future__ import annotations

import select
import sys
import termios
import time
import tty
from datetime import datetime
from pathlib import Path

REFRESH_SEC = 1.0

# Ensure backend on path
_backend = Path("/opt/setuphelfer-rescue/backend")
if _backend.is_dir():
    sys.path.insert(0, str(_backend))
else:
    _repo = Path(__file__).resolve().parents[3] / "backend"
    if _repo.is_dir():
        sys.path.insert(0, str(_repo))

from core.rescue_physical_e2e_auto_e2e_state import (  # noqa: E402
    AUTO_E2E_PHASES,
    PHASE_LABELS_DE,
    heartbeat_age_sec,
    refresh_auto_e2e_phase_from_runtime,
    request_cancel,
    request_shutdown,
)
from core.rescue_run_mode import resolve_run_mode  # noqa: E402
from core.rescue_session_state import (  # noqa: E402
    DISCOVERY_UI_PHASES,
    PHASE_LABELS_DE as DISCOVERY_LABELS_DE,
    read_session_state,
)


def _parse_ts(value: str | None) -> float | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()
    except ValueError:
        return None


def _session_heartbeat_age(session: dict) -> float | None:
    ts = _parse_ts(str(session.get("last_heartbeat_at") or ""))
    if ts is None:
        return None
    return max(0.0, time.time() - ts)


def _active_state() -> dict:
    mode = resolve_run_mode()
    discovery_only = bool(mode.get("ok") and mode.get("run_mode") == "auto_discovery_only")
    session = read_session_state()
    if session and (not session.get("terminal") or discovery_only):
        phase = str(session.get("current_phase") or "session_created")
        status = "running"
        if session.get("terminal"):
            status = str(session.get("result") or "passed")
        warning = str(session.get("current_warning") or "")
        if discovery_only and phase in {"msi_evidence_complete", "msi_evidence_waiting"}:
            warning = warning or "Automatische Systemerkundung startet"
        return {
            "phase": phase,
            "status": status,
            "elapsed_sec": 0,
            "last_progress": warning or session.get("last_completed_module") or "",
            "labels": DISCOVERY_LABELS_DE,
            "discovery_mode": True,
            "heartbeat_age": _session_heartbeat_age(session),
            "run_mode": "auto_discovery_only" if discovery_only else session.get("run_mode"),
        }

    if discovery_only:
        e2e = refresh_auto_e2e_phase_from_runtime()
        progress = str(e2e.get("last_progress") or "")
        # Never show physical-E2E / backup / restore texts in discovery mode.
        banned = ("physischer E2E", "Backup startet", "Restore startet", "Testfestplatte")
        if any(token in progress for token in banned):
            progress = "MSI-Evidence abgeschlossen — Automatische Systemerkundung startet"
        return {
            "phase": e2e.get("phase") or "discovery_starting",
            "status": e2e.get("status") or "running",
            "elapsed_sec": e2e.get("elapsed_sec") or 0,
            "last_progress": progress,
            "labels": DISCOVERY_LABELS_DE,
            "discovery_mode": True,
            "heartbeat_age": heartbeat_age_sec(),
            "run_mode": "auto_discovery_only",
        }

    e2e = refresh_auto_e2e_phase_from_runtime()
    e2e["labels"] = PHASE_LABELS_DE
    e2e["discovery_mode"] = False
    e2e["heartbeat_age"] = heartbeat_age_sec()
    return e2e


def _format_display(state: dict) -> str:
    labels = state.get("labels") or PHASE_LABELS_DE
    phase = state.get("phase") or "msi_hardware_check"
    hb = state.get("heartbeat_age")
    if hb is None:
        hb = heartbeat_age_sec()
    hb_txt = f"{hb:.0f}s" if hb is not None else "—"
    hb_note = ""
    if hb is not None and hb >= 60:
        hb_note = "  ⚠ Heartbeat-Fehler (>60s)"
    elif hb is not None and hb >= 10:
        hb_note = "  ⚠ Heartbeat veraltet (>10s)"

    discovery_mode = bool(state.get("discovery_mode"))
    title = "Automatische Systemerkundung" if discovery_mode else "Automatischer Setuphelfer-Test"
    lines = [
        "══════════════════════════════════════════════════════════",
        f"  {title}",
        "══════════════════════════════════════════════════════════",
        "",
        "Ablauf:",
    ]

    if discovery_mode:
        phase_keys = list(DISCOVERY_UI_PHASES)
        idx_cur = phase_keys.index(phase) if phase in phase_keys else 0
        # Map close aliases onto UI list.
        aliases = {
            "boot_initializing": "session_created",
            "setup_logs_ready": "setup_logs_waiting",
            "discovery_starting": "session_created",
            "msi_evidence_waiting": "msi_hardware_check",
            "storage_waiting": "storage_collecting",
            "machine_identity_collecting": "msi_hardware_check",
            "lan_collecting": "network_hardware_collecting",
            "passed": "evidence_syncing",
        }
        mapped = aliases.get(phase, phase)
        if mapped in phase_keys:
            idx_cur = phase_keys.index(mapped)
        for idx, key in enumerate(phase_keys, start=1):
            label = labels.get(key, key)
            if idx - 1 < idx_cur:
                mark = "✓"
            elif idx - 1 == idx_cur:
                mark = "→"
            else:
                mark = " "
            lines.append(f"  [{mark}] {idx:2}. {label}")
    else:
        idx_cur = AUTO_E2E_PHASES.index(phase) if phase in AUTO_E2E_PHASES else 0
        for idx, key in enumerate(AUTO_E2E_PHASES, start=1):
            label = labels.get(key, key)
            if idx - 1 < idx_cur:
                mark = "✓"
            elif idx - 1 == idx_cur:
                mark = "→"
            else:
                mark = " "
            lines.append(f"  [{mark}] {idx:2}. {label}")

    progress = str(state.get("last_progress") or "—")
    if discovery_mode:
        for banned in ("physischer E2E", "Backup startet", "Restore startet", "Testfestplatte"):
            if banned in progress:
                progress = "Automatische Systemerkundung startet"
                break

    lines.extend(
        [
            "",
            f"Aktuelle Phase:   {labels.get(phase, phase)}",
            f"Status:           {state.get('status', 'wartet')}",
            f"Modus:            {state.get('run_mode') or ('auto_discovery_only' if discovery_mode else 'auto_physical_e2e')}",
            f"Verstrichene Zeit: {state.get('elapsed_sec', 0)} s",
            f"Heartbeat-Alter:   {hb_txt}{hb_note}",
            f"Fortschritt:       {progress}",
            "",
            "──────────────────────────────────────────────────────────",
            "  [A] Abbrechen    [H] Herunterfahren    (Auto-Refresh aktiv)",
            "══════════════════════════════════════════════════════════",
        ]
    )
    return "\n".join(lines)


def _handle_key(ch: str) -> None:
    if ch in ("a", "A"):
        request_cancel()
    elif ch in ("h", "H"):
        request_shutdown()


def main() -> int:
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setcbreak(fd)
        while True:
            state = _active_state()
            text = _format_display(state)
            sys.stdout.write("\033[2J\033[H" + text + "\n")
            sys.stdout.flush()
            terminal = str(state.get("status") or "")
            if terminal in {"passed", "failed", "blocked", "cancelled", "review_required", "timeout"}:
                break
            rlist, _, _ = select.select([sys.stdin], [], [], REFRESH_SEC)
            if rlist:
                ch = sys.stdin.read(1)
                if ch:
                    _handle_key(ch)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
