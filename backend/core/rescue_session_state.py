"""Global rescue session state — primary runtime truth (001D7)."""

from __future__ import annotations

import json
import os
import secrets
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SESSION_STATE_SCHEMA = "setuphelfer.rescue.session-state.v1"
FALLBACK_EVIDENCE_DIR = Path("/run/setuphelfer-rescue/fallback-evidence")

PHASES: tuple[str, ...] = (
    "boot_initializing",
    "session_created",
    "setup_logs_waiting",
    "setup_logs_ready",
    "msi_evidence_waiting",
    "msi_hardware_check",
    "discovery_starting",
    "machine_identity_collecting",
    "firmware_collecting",
    "cpu_memory_collecting",
    "pci_collecting",
    "usb_collecting",
    "storage_waiting",
    "storage_collecting",
    "partition_collecting",
    "filesystem_collecting",
    "smart_collecting",
    "kernel_collecting",
    "network_hardware_collecting",
    "lan_collecting",
    "wifi_collecting",
    "internet_collecting",
    "backend_collecting",
    "services_collecting",
    "payload_collecting",
    "privacy_redaction",
    "evidence_validation",
    "telemetry_preparing",
    "telemetry_sending",
    "diagnostics_waiting",
    "evidence_syncing",
    "shutdown_pending",
    "passed",
    "review_required",
    "failed",
    "blocked",
    "cancelled",
    "timeout",
)

PHASE_LABELS_DE: dict[str, str] = {
    "boot_initializing": "Session wird vorbereitet",
    "session_created": "Session wird vorbereitet",
    "setup_logs_waiting": "SETUP_LOGS wird geprüft",
    "setup_logs_ready": "SETUP_LOGS wird geprüft",
    "msi_evidence_waiting": "Warte auf MSI-Evidence…",
    "msi_hardware_check": "MSI-Hardware wird erkannt",
    "machine_identity_collecting": "MSI-Hardware wird erkannt",
    "firmware_collecting": "Firmware wird erfasst",
    "cpu_memory_collecting": "CPU und Arbeitsspeicher werden erfasst",
    "pci_collecting": "PCI-Geräte werden erfasst",
    "usb_collecting": "USB-Geräte werden erfasst",
    "storage_waiting": "Datenträger werden erkannt",
    "storage_collecting": "Datenträger werden erkannt",
    "partition_collecting": "Partitionen werden analysiert",
    "filesystem_collecting": "Dateisysteme werden bewertet",
    "smart_collecting": "SMART-Daten werden gelesen",
    "kernel_collecting": "Kernelwarnungen werden ausgewertet",
    "network_hardware_collecting": "Netzwerk wird geprüft",
    "lan_collecting": "Netzwerk wird geprüft",
    "wifi_collecting": "Netzwerk wird geprüft",
    "internet_collecting": "Netzwerk wird geprüft",
    "backend_collecting": "Dienste werden geprüft",
    "services_collecting": "Dienste werden geprüft",
    "payload_collecting": "Payload wird geprüft",
    "privacy_redaction": "Datenschutzprüfung läuft",
    "evidence_validation": "Evidence wird validiert",
    "telemetry_preparing": "Evidence wird an Telemetrie gesendet",
    "telemetry_sending": "Evidence wird an Telemetrie gesendet",
    "diagnostics_waiting": "Evidence wird gespeichert",
    "evidence_syncing": "Evidence wird gespeichert",
    "shutdown_pending": "System wird heruntergefahren",
    "discovery_starting": "Automatische Systemerkundung startet",
    "passed": "Evidence wird gespeichert",
    "review_required": "Review erforderlich",
    "failed": "Discovery fehlgeschlagen",
    "blocked": "Discovery blockiert",
    "cancelled": "Abgebrochen",
    "timeout": "Zeitüberschreitung",
}

DISCOVERY_UI_PHASES: tuple[str, ...] = (
    "session_created",
    "setup_logs_waiting",
    "msi_hardware_check",
    "firmware_collecting",
    "cpu_memory_collecting",
    "pci_collecting",
    "usb_collecting",
    "storage_collecting",
    "partition_collecting",
    "filesystem_collecting",
    "smart_collecting",
    "network_hardware_collecting",
    "kernel_collecting",
    "services_collecting",
    "payload_collecting",
    "privacy_redaction",
    "evidence_validation",
    "telemetry_sending",
    "evidence_syncing",
    "shutdown_pending",
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _boot_id() -> str:
    try:
        return Path("/proc/sys/kernel/random/boot_id").read_text(encoding="utf-8").strip()
    except OSError:
        return str(uuid.uuid4())


def generate_session_id() -> str:
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    token = secrets.token_hex(4)
    return f"rescue-session-{ts}-{token}"


def session_state_dir() -> Path:
    return Path(os.environ.get("SETUPHELFER_RESCUE_SESSION_DIR", "/run/setuphelfer-rescue/session"))


def session_state_path() -> Path:
    return session_state_dir() / "state.json"


def session_journal_path() -> Path:
    return session_state_dir() / "journal.jsonl"


def _atomic_write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    with tmp.open("rb") as handle:
        os.fsync(handle.fileno())
    tmp.replace(path)
    try:
        fd = os.open(str(path.parent), os.O_DIRECTORY)
        os.fsync(fd)
        os.close(fd)
    except OSError:
        pass


def append_journal(event: dict[str, Any]) -> None:
    path = session_journal_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    row = dict(event)
    row.setdefault("timestamp", _utc_now())
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def init_session_state(
    *,
    session_id: str | None = None,
    payload_version: str = "",
    source: str = "physical_msi",
    run_mode: str = "",
) -> dict[str, Any]:
    sid = session_id or generate_session_id()
    now = _utc_now()
    state = {
        "schema": SESSION_STATE_SCHEMA,
        "session_id": sid,
        "boot_id": _boot_id(),
        "payload_version": payload_version,
        "source": source,
        "run_mode": run_mode or None,
        "started_at": now,
        "updated_at": now,
        "current_phase": "session_created",
        "phase_started_at": now,
        "last_heartbeat_at": now,
        "progress_percent": 0,
        "terminal": False,
        "result": None,
        "blocking_reason": None,
        "shutdown_safe": False,
        "evidence_complete": False,
        "last_completed_module": "",
        "current_warning": "",
    }
    _atomic_write_json(session_state_path(), state)
    append_journal(
        {
            "event": "session_created",
            "session_id": sid,
            "boot_id": state["boot_id"],
            "run_mode": run_mode or None,
        }
    )
    return state


def read_session_state() -> dict[str, Any] | None:
    path = session_state_path()
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None


def update_session_state(**fields: Any) -> dict[str, Any]:
    state = read_session_state() or init_session_state()
    now = _utc_now()
    phase = fields.get("current_phase")
    if phase and phase != state.get("current_phase"):
        state["phase_started_at"] = now
    state.update(fields)
    state["updated_at"] = now
    state["last_heartbeat_at"] = now
    _atomic_write_json(session_state_path(), state)
    append_journal({"event": "state_update", "phase": state.get("current_phase"), "fields": sorted(fields.keys())})
    return state


def heartbeat(*, module: str = "", warning: str = "") -> dict[str, Any]:
    fields: dict[str, Any] = {"last_heartbeat_at": _utc_now()}
    if module:
        fields["last_completed_module"] = module
    if warning:
        fields["current_warning"] = warning
    return update_session_state(**fields)


def set_phase(phase: str, *, warning: str = "", progress_percent: int | None = None) -> dict[str, Any]:
    fields: dict[str, Any] = {"current_phase": phase}
    if warning:
        fields["current_warning"] = warning
    if progress_percent is not None:
        fields["progress_percent"] = progress_percent
    return update_session_state(**fields)


def mark_terminal(*, result: str, evidence_complete: bool = False, shutdown_safe: bool = False) -> dict[str, Any]:
    return update_session_state(
        terminal=True,
        result=result,
        evidence_complete=evidence_complete,
        shutdown_safe=shutdown_safe,
        current_phase=result if result in PHASES else "failed",
    )


def session_evidence_dir(setup_logs_base: Path | None, session_id: str) -> Path:
    if setup_logs_base and setup_logs_base.is_dir():
        return setup_logs_base / "setuphelfer" / "evidence" / "sessions" / session_id
    return FALLBACK_EVIDENCE_DIR / session_id
