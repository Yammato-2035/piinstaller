#!/usr/bin/env python3
"""Non-blocking live TUI for auto physical E2E / discovery (001D6/001D7B/001D7C)."""

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

from core.rescue_component_heartbeat import (  # noqa: E402
    component_heartbeat_age_sec,
    write_component_heartbeat,
)
from core.rescue_discovery_observability import read_runtime_json  # noqa: E402
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

EARLY_DISCOVERY_PHASES = (
    "discovery_start_checking",
    "discovery_service_starting",
    "discovery_session_creating",
)

EARLY_LABELS = {
    "discovery_start_checking": "Discovery-Start wird geprüft",
    "discovery_service_starting": "Discovery-Service wird gestartet",
    "discovery_session_creating": "Discovery-Session wird angelegt",
}


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


def _discovery_observability_state() -> dict | None:
    """Derive early discovery UI state from start-gate / service / finalizer audits."""
    gate = read_runtime_json("start-gate.json") or {}
    service_start = read_runtime_json("service-start.json") or {}
    orch = read_runtime_json("orchestrator-exit.json") or {}
    svc = read_runtime_json("service-result.json") or {}
    final = read_runtime_json("boot-finalizer.json") or {}

    if not any((gate, service_start, orch, svc, final)):
        return None

    labels = {**DISCOVERY_LABELS_DE, **EARLY_LABELS}
    error = ""
    status = "running"
    phase = "discovery_start_checking"
    progress = "Discovery-Start wird geprüft"

    if gate.get("called") and gate.get("start_allowed") is False:
        status = "failed"
        error = str(gate.get("decision_code") or "discovery_start_gate_skipped")
        progress = f"Start-Gate blockiert: {error}"
        phase = "discovery_start_checking"
    elif gate.get("start_allowed") and not service_start:
        phase = "discovery_service_starting"
        progress = "Discovery-Service wird gestartet"
    elif service_start and not orch and not svc:
        phase = "discovery_session_creating"
        progress = "Discovery-Session wird angelegt"
    elif orch or svc:
        exit_code = orch.get("exit_code") if orch else svc.get("exit_code")
        if exit_code not in (None, 0):
            status = "failed"
            error = str(svc.get("status") or orch.get("status") or "failed_discovery")
            progress = f"Fehler: {error}"
            phase = "discovery_session_creating"
        else:
            phase = "session_created"
            progress = "Discovery-Orchestrator beendet"
    if final.get("terminal") and str(final.get("status") or "").startswith("failed_"):
        status = "failed"
        error = str(final.get("status"))
        progress = f"Boot-Finalizer: {error}"

    hb = component_heartbeat_age_sec("discovery")
    # Only surface missing discovery heartbeat after the service actually started.
    warn_discovery_hb = bool(service_start) and (hb is None or hb >= 60)

    return {
        "phase": phase,
        "status": status,
        "elapsed_sec": 0,
        "last_progress": progress,
        "labels": labels,
        "discovery_mode": True,
        "heartbeat_age": hb if service_start else component_heartbeat_age_sec("tui"),
        "run_mode": "auto_discovery_only",
        "error_code": error,
        "warn_discovery_hb": warn_discovery_hb,
        "early_phases": True,
    }


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
            "heartbeat_age": _session_heartbeat_age(session) or component_heartbeat_age_sec("discovery"),
            "run_mode": "auto_discovery_only" if discovery_only else session.get("run_mode"),
            "error_code": "",
            "warn_discovery_hb": False,
            "early_phases": False,
        }

    if discovery_only:
        obs = _discovery_observability_state()
        if obs:
            # Keep running forever on soft waiting states — never treat MSI e2e "passed" as terminal.
            if obs.get("status") != "failed":
                # Overlay MSI progress text carefully.
                e2e = refresh_auto_e2e_phase_from_runtime()
                progress = str(obs.get("last_progress") or "")
                banned = ("physischer E2E", "Backup startet", "Restore startet", "Testfestplatte")
                msi_progress = str(e2e.get("last_progress") or "")
                if msi_progress and not any(token in msi_progress for token in banned):
                    if "MSI" in msi_progress or "Evidence" in msi_progress:
                        progress = msi_progress
                obs["last_progress"] = progress
                obs["elapsed_sec"] = e2e.get("elapsed_sec") or 0
                # Force non-terminal until discovery session or explicit failure audits.
                obs["status"] = "running"
            return obs

        e2e = refresh_auto_e2e_phase_from_runtime()
        progress = str(e2e.get("last_progress") or "")
        banned = ("physischer E2E", "Backup startet", "Restore startet", "Testfestplatte")
        if any(token in progress for token in banned):
            progress = "Discovery-Start wird geprüft"
        return {
            "phase": "discovery_start_checking",
            "status": "running",  # never inherit MSI "passed"
            "elapsed_sec": e2e.get("elapsed_sec") or 0,
            "last_progress": progress or "Discovery-Start wird geprüft",
            "labels": {**DISCOVERY_LABELS_DE, **EARLY_LABELS},
            "discovery_mode": True,
            "heartbeat_age": component_heartbeat_age_sec("tui") or heartbeat_age_sec(),
            "run_mode": "auto_discovery_only",
            "error_code": "",
            "warn_discovery_hb": False,
            "early_phases": True,
        }

    e2e = refresh_auto_e2e_phase_from_runtime()
    e2e["labels"] = PHASE_LABELS_DE
    e2e["discovery_mode"] = False
    e2e["heartbeat_age"] = heartbeat_age_sec()
    e2e["error_code"] = ""
    e2e["warn_discovery_hb"] = False
    e2e["early_phases"] = False
    return e2e


def _format_display(state: dict) -> str:
    labels = state.get("labels") or PHASE_LABELS_DE
    phase = state.get("phase") or "msi_hardware_check"
    hb = state.get("heartbeat_age")
    if hb is None:
        hb = heartbeat_age_sec()
    hb_txt = f"{hb:.0f}s" if hb is not None else "—"
    hb_note = ""
    if state.get("warn_discovery_hb"):
        hb_note = "  ⚠ Discovery-Heartbeat fehlt"
    elif hb is not None and hb >= 60:
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

    if discovery_mode and state.get("early_phases") and phase in EARLY_DISCOVERY_PHASES:
        phase_keys = list(EARLY_DISCOVERY_PHASES) + list(DISCOVERY_UI_PHASES)
        idx_cur = phase_keys.index(phase) if phase in phase_keys else 0
        for idx, key in enumerate(phase_keys[:8], start=1):  # early + first discovery steps
            label = labels.get(key, EARLY_LABELS.get(key, key))
            if idx - 1 < idx_cur:
                mark = "✓"
            elif idx - 1 == idx_cur:
                mark = "→"
            else:
                mark = " "
            lines.append(f"  [{mark}] {idx:2}. {label}")
        lines.append("  …")
    elif discovery_mode:
        phase_keys = list(DISCOVERY_UI_PHASES)
        idx_cur = phase_keys.index(phase) if phase in phase_keys else 0
        aliases = {
            "boot_initializing": "session_created",
            "setup_logs_ready": "setup_logs_waiting",
            "discovery_starting": "session_created",
            "discovery_start_checking": "session_created",
            "discovery_service_starting": "session_created",
            "discovery_session_creating": "session_created",
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
                progress = "Discovery-Start wird geprüft"
                break

    error = str(state.get("error_code") or "")
    lines.extend(
        [
            "",
            f"Aktuelle Phase:   {labels.get(phase, EARLY_LABELS.get(phase, phase))}",
            f"Status:           {state.get('status', 'wartet')}",
            f"Modus:            {state.get('run_mode') or ('auto_discovery_only' if discovery_mode else 'auto_physical_e2e')}",
            f"Verstrichene Zeit: {state.get('elapsed_sec', 0)} s",
            f"Heartbeat-Alter:   {hb_txt}{hb_note}",
            f"Fortschritt:       {progress}",
        ]
    )
    if error:
        lines.append(f"Fehlercode:        {error}")
    lines.extend(
        [
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
            write_component_heartbeat("tui", state="display")
            state = _active_state()
            text = _format_display(state)
            sys.stdout.write("\033[2J\033[H" + text + "\n")
            sys.stdout.flush()
            terminal = str(state.get("status") or "")
            # Discovery mode: exit only on explicit failure (parent shows hold) or shutdown phase.
            if bool(state.get("discovery_mode")):
                if terminal == "failed":
                    break
                if state.get("phase") == "shutdown_pending":
                    break
            elif terminal in {"passed", "failed", "blocked", "cancelled", "review_required", "timeout"}:
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
