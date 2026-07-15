#!/usr/bin/env python3
"""Non-blocking live TUI for auto physical E2E (001D6)."""

from __future__ import annotations

import os
import select
import sys
import termios
import tty
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
    PHASE_LABELS_DE,
    AUTO_E2E_PHASES,
    heartbeat_age_sec,
    read_auto_e2e_state,
    refresh_auto_e2e_phase_from_runtime,
    request_cancel,
    request_shutdown,
)


def _format_display(state: dict) -> str:
    phase = state.get("phase") or "msi_hardware_check"
    hb = heartbeat_age_sec()
    hb_txt = f"{hb:.0f}s" if hb is not None else "—"
    lines = [
        "══════════════════════════════════════════════════════════",
        "  Automatischer Setuphelfer-Test",
        "══════════════════════════════════════════════════════════",
        "",
        "Ablauf:",
    ]
    idx_cur = AUTO_E2E_PHASES.index(phase) if phase in AUTO_E2E_PHASES else 0
    for idx, key in enumerate(AUTO_E2E_PHASES, start=1):
        label = PHASE_LABELS_DE.get(key, key)
        if idx - 1 < idx_cur:
            mark = "✓"
        elif idx - 1 == idx_cur:
            mark = "→"
        else:
            mark = " "
        lines.append(f"  [{mark}] {idx:2}. {label}")
    lines.extend(
        [
            "",
            f"Aktuelle Phase:   {PHASE_LABELS_DE.get(phase, phase)}",
            f"Status:           {state.get('status', 'wartet')}",
            f"Verstrichene Zeit: {state.get('elapsed_sec', 0)} s",
            f"Heartbeat-Alter:   {hb_txt}",
            f"Fortschritt:       {state.get('last_progress') or '—'}",
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
            state = refresh_auto_e2e_phase_from_runtime()
            text = _format_display(state)
            sys.stdout.write("\033[2J\033[H" + text + "\n")
            sys.stdout.flush()
            terminal = str(state.get("status") or "")
            if terminal in {"passed", "failed", "blocked", "cancelled"}:
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
