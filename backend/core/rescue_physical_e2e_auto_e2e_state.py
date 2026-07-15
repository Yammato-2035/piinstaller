"""Shared auto-E2E state for TUI and background orchestrator (001D5)."""

from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_AUTO_E2E_STATE_DIR = Path("/run/setuphelfer-rescue/auto-e2e")


def auto_e2e_state_dir() -> Path:
    override = os.environ.get("SETUPHELFER_AUTO_E2E_STATE_DIR", "").strip()
    if override:
        return Path(override)
    return DEFAULT_AUTO_E2E_STATE_DIR


def _state_file() -> Path:
    return auto_e2e_state_dir() / "state.json"


def _events_file() -> Path:
    return auto_e2e_state_dir() / "events.jsonl"


def _cancel_file() -> Path:
    return auto_e2e_state_dir() / "cancel-requested"


def _shutdown_file() -> Path:
    return auto_e2e_state_dir() / "shutdown-requested"


def _heartbeat_file() -> Path:
    return auto_e2e_state_dir() / "heartbeat.json"

AUTO_E2E_PHASES: tuple[str, ...] = (
    "msi_hardware_check",
    "msi_evidence_waiting",
    "msi_evidence_running",
    "msi_evidence_complete",
    "sabrent_waiting",
    "sabrent_detected",
    "sabrent_identity_verified",
    "disk_partitioning",
    "disk_formatting",
    "test_data_create",
    "backup_create",
    "backup_verify",
    "restore_run",
    "data_compare",
    "telemetry_send",
    "diagnostics_fetch",
    "evidence_save",
    "shutdown_pending",
    "shutdown",
)

PHASE_LABELS_DE: dict[str, str] = {
    "msi_hardware_check": "MSI-Hardware prüfen",
    "msi_evidence_waiting": "MSI-Evidence wird vorbereitet",
    "msi_evidence_running": "MSI-Evidence wird gesammelt",
    "msi_evidence_complete": "MSI-Evidence abgeschlossen",
    "sabrent_waiting": "SABRENT-HDD wird gesucht",
    "sabrent_detected": "SABRENT-HDD erkannt",
    "sabrent_identity_verified": "SABRENT-HDD wird geprüft",
    "disk_partitioning": "Testfestplatte wird partitioniert",
    "disk_formatting": "Testfestplatte wird formatiert",
    "test_data_create": "Testdaten erzeugen",
    "backup_create": "Backup erstellen",
    "backup_verify": "Backup prüfen",
    "restore_run": "Restore durchführen",
    "data_compare": "Daten vergleichen",
    "telemetry_send": "Telemetrie senden",
    "diagnostics_fetch": "Diagnose abrufen",
    "evidence_save": "Evidence speichern",
    "shutdown_pending": "Herunterfahren vorgemerkt",
    "shutdown": "Herunterfahren",
    # legacy aliases
    "evidence_collection": "MSI-Evidence wird gesammelt",
    "test_disk_prepare": "Testfestplatte vorbereiten",
}

STATUS_VALUES = frozenset({"waiting", "running", "passed", "failed", "blocked", "cancelled"})


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def ensure_auto_e2e_state_dir() -> Path:
    path = auto_e2e_state_dir()
    path.mkdir(parents=True, exist_ok=True)
    return path


def _atomic_write_json(path: Path, data: dict[str, Any]) -> None:
    ensure_auto_e2e_state_dir()
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    with tmp.open("rb") as handle:
        os.fsync(handle.fileno())
    tmp.replace(path)


def init_auto_e2e_state(*, mode: str = "auto_physical_e2e_locked", run_id: str = "") -> dict[str, Any]:
    ensure_auto_e2e_state_dir()
    state = {
        "schema": "setuphelfer.rescue.auto-e2e-state.v1",
        "mode": mode,
        "run_id": run_id,
        "phase": AUTO_E2E_PHASES[0],
        "phase_index": 0,
        "status": "waiting",
        "started_at": _utc_now(),
        "updated_at": _utc_now(),
        "elapsed_sec": 0,
        "last_progress": "",
        "cancel_requested": False,
        "shutdown_requested": False,
        "shutdown_deferred": False,
    }
    _atomic_write_json(_state_file(), state)
    return state


def read_auto_e2e_state() -> dict[str, Any] | None:
    path = _state_file()
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None


def update_auto_e2e_state(
    *,
    phase: str | None = None,
    status: str | None = None,
    last_progress: str | None = None,
    run_id: str | None = None,
    shutdown_deferred: bool | None = None,
) -> dict[str, Any]:
    state = read_auto_e2e_state() or init_auto_e2e_state()
    if run_id:
        state["run_id"] = run_id
    if phase:
        state["phase"] = phase
        if phase in AUTO_E2E_PHASES:
            state["phase_index"] = AUTO_E2E_PHASES.index(phase)
    if status:
        state["status"] = status
    if last_progress is not None:
        state["last_progress"] = last_progress
    if shutdown_deferred is not None:
        state["shutdown_deferred"] = shutdown_deferred
    started = state.get("started_at") or _utc_now()
    try:
        started_dt = datetime.fromisoformat(str(started).replace("Z", "+00:00"))
        state["elapsed_sec"] = int((datetime.now(timezone.utc) - started_dt).total_seconds())
    except ValueError:
        state["elapsed_sec"] = 0
    state["cancel_requested"] = cancel_requested()
    state["shutdown_requested"] = shutdown_requested()
    state["updated_at"] = _utc_now()
    _atomic_write_json(_state_file(), state)
    return state


def append_auto_e2e_event(event: str, *, detail: dict[str, Any] | None = None) -> None:
    ensure_auto_e2e_state_dir()
    events_file = _events_file()
    line = {"ts": _utc_now(), "event": event}
    if detail:
        line["detail"] = detail
    with events_file.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(line, ensure_ascii=False) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def write_heartbeat(*, run_id: str = "", phase: str = "") -> None:
    ensure_auto_e2e_state_dir()
    _atomic_write_json(
        _heartbeat_file(),
        {"ts": _utc_now(), "epoch": time.time(), "run_id": run_id, "phase": phase},
    )


def heartbeat_age_sec(*, max_age: float = 120.0) -> float | None:
    path = _heartbeat_file()
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        epoch = float(data.get("epoch") or 0)
        if epoch <= 0:
            return None
        return time.time() - epoch
    except (json.JSONDecodeError, TypeError, ValueError):
        return None


def heartbeat_fresh(*, max_age: float = 120.0) -> bool:
    age = heartbeat_age_sec()
    return age is not None and age <= max_age


def cancel_requested() -> bool:
    return _cancel_file().is_file()


def shutdown_requested() -> bool:
    return _shutdown_file().is_file()


def request_cancel() -> Path:
    ensure_auto_e2e_state_dir()
    path = _cancel_file()
    path.touch()
    append_auto_e2e_event("cancel_requested")
    update_auto_e2e_state(status="cancelled", last_progress="Abbruch angefordert")
    return path


def request_shutdown() -> Path:
    ensure_auto_e2e_state_dir()
    path = _shutdown_file()
    path.touch()
    append_auto_e2e_event("shutdown_requested")
    update_auto_e2e_state(shutdown_deferred=True, last_progress="Shutdown vorgemerkt")
    return path


def check_abort(*, dangerous_phase: bool = False) -> dict[str, Any] | None:
    if cancel_requested():
        return {"abort": True, "reason": "cancelled_by_operator", "immediate": not dangerous_phase}
    if shutdown_requested():
        return {"abort": True, "reason": "shutdown_requested", "immediate": not dangerous_phase}
    return None


def mirror_state_to_setup_logs(setup_logs_base: Path) -> None:
    state = read_auto_e2e_state()
    if not state:
        return
    dest = setup_logs_base / "setuphelfer/evidence/e2e/auto-e2e-state.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _read_uptime_sec() -> int:
    try:
        return int(float(Path("/proc/uptime").read_text(encoding="utf-8").split()[0]))
    except (OSError, ValueError, IndexError):
        return 0


def _late_gate_min_uptime_sec() -> int:
    late = 120
    try:
        cmdline = Path("/proc/cmdline").read_text(encoding="utf-8")
        for token in cmdline.split():
            if token.startswith("setuphelfer_msi_lab_late_sec="):
                late = int(token.split("=", 1)[1])
                break
    except (OSError, ValueError):
        pass
    return late + 30


def _rescue_state_dir() -> Path:
    return Path(os.environ.get("SETUPHELFER_RESCUE_STATE_DIR", "/run/setuphelfer-rescue"))


def _find_setup_logs_mount() -> Path | None:
    for pattern in ("/media/*/SETUP_LOGS", "/run/media/*/SETUP_LOGS"):
        for candidate in Path("/").glob(pattern.lstrip("/")):
            if candidate.is_dir():
                return candidate
    return None


def _heartbeat_phase() -> str:
    path = _heartbeat_file()
    if not path.is_file():
        return ""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return ""
    return str(data.get("phase") or "")


def _discovery_only_mode(logs: Path | None) -> bool:
    try:
        from core.rescue_run_mode import resolve_run_mode

        resolved = resolve_run_mode(setup_logs_base=logs)
        return bool(resolved.get("ok") and resolved.get("run_mode") == "auto_discovery_only")
    except Exception:
        return False


def refresh_auto_e2e_phase_from_runtime() -> dict[str, Any]:
    """Derive visible TUI phase from boot markers when orchestrator has not updated yet."""
    existing = read_auto_e2e_state() or init_auto_e2e_state(mode="auto_physical_e2e_locked")
    terminal = str(existing.get("status") or "")
    if terminal in {"passed", "failed", "blocked", "cancelled"}:
        return existing

    uptime = _read_uptime_sec()
    late_min = _late_gate_min_uptime_sec()
    rescue = _rescue_state_dir()
    evidence_done = (rescue / "auto-msi-evidence.done").is_file()
    physical_done = (rescue / "auto-physical-e2e.done").is_file()
    discovery_done = (rescue / "auto-discovery.done").is_file()
    discovery_started = (rescue / "auto-discovery.started").is_file()
    logs = _find_setup_logs_mount()
    msi_complete = bool(
        logs and (logs / "setuphelfer/evidence/msi-rs011b/msi-evidence-complete.json").is_file()
    )
    discovery_only = _discovery_only_mode(logs)

    phase = "msi_hardware_check"
    status = "running"
    progress = "System startet…"

    if uptime >= 10:
        progress = "MSI-Hardware wird geprüft (TUI aktiv)"
    if uptime >= 20 and uptime < late_min:
        phase = "msi_evidence_waiting"
        progress = f"Late-Evidence-Gate: {uptime}/{late_min} s — bitte warten"
    elif uptime >= late_min and not evidence_done and not msi_complete:
        running = (rescue / "auto-msi-evidence.running").is_file()
        if running:
            phase = "msi_evidence_running"
            progress = "MSI-Evidence wird gesammelt…"
        else:
            phase = "msi_evidence_waiting"
            progress = "Warte auf MSI-Evidence-Service…"
    if evidence_done or msi_complete:
        phase = "msi_evidence_complete"
        if discovery_only:
            progress = "MSI-Evidence abgeschlossen — Automatische Systemerkundung startet"
        else:
            progress = "MSI-Evidence abgeschlossen — physischer E2E startet"
    if discovery_only and (discovery_started or discovery_done):
        phase = "msi_evidence_complete"
        progress = "Automatische Systemerkundung läuft…"
    if discovery_done and discovery_only:
        phase = "shutdown"
        status = "passed"
        progress = "Automatische Systemerkundung abgeschlossen"
    if physical_done and not discovery_only:
        phase = "shutdown"
        status = "passed"
        progress = "Automatischer Test abgeschlossen"

    hb_phase = _heartbeat_phase()
    if hb_phase in AUTO_E2E_PHASES:
        hb_idx = AUTO_E2E_PHASES.index(hb_phase)
        cur_idx = AUTO_E2E_PHASES.index(phase)
        if hb_idx >= cur_idx:
            phase = hb_phase
            progress = PHASE_LABELS_DE.get(phase, phase)

    cur_idx = int(existing.get("phase_index") or 0)
    new_idx = AUTO_E2E_PHASES.index(phase) if phase in AUTO_E2E_PHASES else 0
    if cur_idx > new_idx and existing.get("phase") in AUTO_E2E_PHASES:
        phase = str(existing.get("phase"))
        progress = str(existing.get("last_progress") or progress)

    return update_auto_e2e_state(phase=phase, status=status, last_progress=progress)
