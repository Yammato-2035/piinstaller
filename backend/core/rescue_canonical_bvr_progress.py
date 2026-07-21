"""Canonical BVR progress for GUI, TUI, Evidence and DCC (PI-RS-BVR-GUI-VT-PROGRESS-002)."""

from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "1.0"
DRIFT_CODE = "rescue.bvr.progress_source_drift"

DEFAULT_STATE_DIR = Path("/run/setuphelfer-rescue")
CANONICAL_NAME = "canonical-bvr-progress.json"
PHYSICAL_NAME = "physical-progress.json"

# Stable operator-facing phase order (contract).
CANONICAL_PHASES: tuple[str, ...] = (
    "startup",
    "device_discovery",
    "target_validation",
    "sabrent_wait",
    "backup",
    "verify",
    "restore_prepare",
    "restore",
    "manifest_compare",
    "evidence_finalize",
    "completed",
    "shutdown",
)

# Map legacy auto-e2e / physical phase names → canonical.
_LEGACY_PHASE_MAP: dict[str, str] = {
    "msi_hardware_check": "startup",
    "msi_evidence_waiting": "startup",
    "msi_evidence_running": "startup",
    "msi_evidence_complete": "device_discovery",
    "sabrent_waiting": "sabrent_wait",
    "sabrent_detected": "target_validation",
    "sabrent_identity_verified": "target_validation",
    "disk_partitioning": "target_validation",
    "disk_formatting": "target_validation",
    "test_data_create": "target_validation",
    "backup_create": "backup",
    "backup_verify": "verify",
    "restore_run": "restore",
    "restore_execute": "restore",
    "restore_verify": "restore",
    "data_compare": "manifest_compare",
    "telemetry_send": "evidence_finalize",
    "diagnostics_fetch": "evidence_finalize",
    "evidence_save": "evidence_finalize",
    "evidence_collection": "evidence_finalize",
    "shutdown_pending": "completed",
    "shutdown": "shutdown",
    "waiting": "startup",
    "starting": "startup",
    "sabrent_wait": "sabrent_wait",
    "backup": "backup",
    "verify": "verify",
    "restore_prepare": "restore_prepare",
    "restore": "restore",
    "manifest_compare": "manifest_compare",
    "evidence_finalize": "evidence_finalize",
    "completed": "completed",
    "startup": "startup",
    "device_discovery": "device_discovery",
    "target_validation": "target_validation",
}

PHASE_LABEL_KEYS: dict[str, str] = {
    phase: f"bvr.phase.{phase}" for phase in CANONICAL_PHASES
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def state_dir() -> Path:
    override = (os.environ.get("SETUPHELFER_RESCUE_STATE_DIR") or "").strip()
    if override:
        return Path(override)
    return DEFAULT_STATE_DIR


def canonical_path() -> Path:
    return state_dir() / CANONICAL_NAME


def physical_progress_path() -> Path:
    return state_dir() / PHYSICAL_NAME


def normalize_phase(phase: str | None) -> str:
    raw = str(phase or "").strip()
    if not raw:
        return "startup"
    if raw in CANONICAL_PHASES:
        return raw
    return _LEGACY_PHASE_MAP.get(raw, "startup")


def phase_index(phase: str) -> int:
    canon = normalize_phase(phase)
    return CANONICAL_PHASES.index(canon)


def _atomic_write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    with tmp.open("rb") as handle:
        os.fsync(handle.fileno())
    tmp.replace(path)


def _read_json(path: Path) -> dict[str, Any] | None:
    try:
        if not path.is_file():
            return None
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else None
    except (OSError, json.JSONDecodeError, TypeError):
        return None


def empty_progress(*, run_id: str = "") -> dict[str, Any]:
    now = _utc_now()
    return {
        "schema_version": SCHEMA_VERSION,
        "run_id": run_id,
        "sequence": 0,
        "status": "starting",
        "phase": "startup",
        "phase_index": 0,
        "phase_count": len(CANONICAL_PHASES),
        "phase_label_key": PHASE_LABEL_KEYS["startup"],
        "started_at": now,
        "updated_at": now,
        "phase_started_at": now,
        "completed_at": None,
        "heartbeat_age_s": 0,
        "progress_kind": "indeterminate",
        "progress_current": None,
        "progress_total": None,
        "source_component": "canonical",
        "message": "",
        "bvr": {
            "backup": "pending",
            "verify": "pending",
            "restore": "pending",
            "manifest": "pending",
        },
        "gui": {"status": "starting", "active_vt": None},
        "terminal": False,
        "warnings": [],
        "errors": [],
    }


def read_canonical_progress() -> dict[str, Any] | None:
    return _read_json(canonical_path())


def _mirror_targets() -> list[Path]:
    targets: list[Path] = []
    for base in (
        Path("/run/setuphelfer/esp-rw"),
        Path("/run/setuphelfer-rescue/media/SETUP_LOGS"),
    ):
        if (base / "setuphelfer").is_dir():
            targets.append(base / "setuphelfer/evidence/e2e" / CANONICAL_NAME)
            targets.append(base / "setuphelfer/evidence/e2e" / PHYSICAL_NAME)
    return targets


def _uptime_sec() -> int:
    try:
        return int(float(Path("/proc/uptime").read_text(encoding="utf-8").split()[0]))
    except (OSError, ValueError, IndexError):
        return 0


def _to_physical_compat(progress: dict[str, Any]) -> dict[str, Any]:
    return {
        "phase": str(progress.get("phase") or "startup"),
        "message": str(progress.get("message") or ""),
        "updated_at": str(progress.get("updated_at") or _utc_now()),
        "uptime_sec": _uptime_sec(),
        "sequence": int(progress.get("sequence") or 0),
        "status": str(progress.get("status") or "running"),
        "terminal": bool(progress.get("terminal")),
        "canonical": True,
    }


def write_canonical_progress(
    *,
    phase: str | None = None,
    status: str | None = None,
    message: str | None = None,
    run_id: str | None = None,
    source_component: str = "canonical",
    bvr: dict[str, str] | None = None,
    gui: dict[str, Any] | None = None,
    terminal: bool | None = None,
    warnings: list[str] | None = None,
    errors: list[str] | None = None,
    heartbeat_only: bool = False,
    allow_phase_retry: bool = False,
    retry_reason: str = "",
) -> dict[str, Any]:
    """Atomically update canonical progress. Heartbeat never changes phase."""
    existing = read_canonical_progress() or empty_progress(run_id=run_id or "")
    if existing.get("terminal") and not heartbeat_only:
        # Terminal states stay terminal unless explicit non-running finalize fields.
        if status and status not in {"passed", "failed", "cancelled"}:
            return existing

    now = _utc_now()
    if heartbeat_only:
        existing["updated_at"] = now
        existing["heartbeat_age_s"] = 0
        existing["sequence"] = int(existing.get("sequence") or 0) + 1
        _atomic_write_json(canonical_path(), existing)
        return existing

    prev_phase = normalize_phase(str(existing.get("phase") or "startup"))
    new_phase = normalize_phase(phase) if phase is not None else prev_phase
    prev_idx = phase_index(prev_phase)
    new_idx = phase_index(new_phase)
    if new_idx < prev_idx and not allow_phase_retry:
        new_phase = prev_phase
        new_idx = prev_idx
    elif new_idx < prev_idx and allow_phase_retry and retry_reason:
        warns = list(existing.get("warnings") or [])
        warns.append(f"phase_retry:{retry_reason}")
        existing["warnings"] = warns

    if run_id:
        existing["run_id"] = run_id
    if new_phase != prev_phase:
        existing["phase_started_at"] = now
    existing["phase"] = new_phase
    existing["phase_index"] = new_idx
    existing["phase_count"] = len(CANONICAL_PHASES)
    existing["phase_label_key"] = PHASE_LABEL_KEYS[new_phase]
    if status:
        existing["status"] = status
    if message is not None:
        existing["message"] = message
    existing["source_component"] = source_component
    existing["updated_at"] = now
    existing["heartbeat_age_s"] = 0
    if bvr:
        merged = dict(existing.get("bvr") or {})
        merged.update(bvr)
        existing["bvr"] = merged
    if gui:
        merged_gui = dict(existing.get("gui") or {})
        merged_gui.update(gui)
        existing["gui"] = merged_gui
    if warnings is not None:
        existing["warnings"] = warnings
    if errors is not None:
        existing["errors"] = errors

    term = bool(terminal) if terminal is not None else bool(existing.get("terminal"))
    if status in {"passed", "failed", "cancelled"} or new_phase in {"completed", "shutdown"}:
        if status in {"passed", "failed", "cancelled"} or new_phase == "shutdown":
            term = True
    existing["terminal"] = term
    if term and not existing.get("completed_at"):
        existing["completed_at"] = now

    existing["sequence"] = int(existing.get("sequence") or 0) + 1
    _atomic_write_json(canonical_path(), existing)

    # Keep physical-progress as compatibility projection of the same snapshot.
    physical = _to_physical_compat(existing)
    _atomic_write_json(physical_progress_path(), physical)
    for target in _mirror_targets():
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            if target.name == CANONICAL_NAME:
                _atomic_write_json(target, existing)
            else:
                _atomic_write_json(target, physical)
        except OSError:
            continue
    return existing


def detect_progress_source_drift(
    *,
    canonical: dict[str, Any] | None = None,
    auto_e2e_state: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Detect display/orchestration drift vs canonical progress."""
    canon = canonical if canonical is not None else read_canonical_progress()
    if not canon:
        return {"drift": False, "code": None, "detail": "no_canonical"}
    auto = auto_e2e_state
    if auto is None:
        auto_path = Path(
            os.environ.get("SETUPHELFER_AUTO_E2E_STATE_DIR", "/run/setuphelfer-rescue/auto-e2e")
        ) / "state.json"
        auto = _read_json(auto_path)
    if not auto:
        return {"drift": False, "code": None, "detail": "no_auto_e2e"}

    canon_phase = normalize_phase(str(canon.get("phase") or ""))
    auto_phase = normalize_phase(str(auto.get("phase") or ""))
    canon_term = bool(canon.get("terminal")) or str(canon.get("status") or "") in {
        "passed",
        "failed",
        "cancelled",
    }
    auto_running = str(auto.get("status") or "") == "running"
    drifted = False
    detail = ""
    if canon_term and auto_phase == "sabrent_wait" and auto_running:
        drifted = True
        detail = "auto_e2e_stuck_sabrent_wait_while_canonical_terminal"
    elif canon_term and phase_index(auto_phase) + 2 < phase_index(canon_phase):
        drifted = True
        detail = "auto_e2e_lags_canonical"
    elif canon.get("sequence") and auto.get("updated_at") and canon_term:
        # Soft check: different phase names after completion.
        if auto_phase != canon_phase and auto_phase == "sabrent_wait":
            drifted = True
            detail = "auto_e2e_sabrent_vs_canonical_shutdown"

    return {
        "drift": drifted,
        "code": DRIFT_CODE if drifted else None,
        "detail": detail,
        "canonical_phase": canon_phase,
        "auto_e2e_phase": auto_phase,
        "canonical_sequence": canon.get("sequence"),
    }


def read_progress_for_display() -> dict[str, Any]:
    """Authoritative snapshot for GUI/TUI/DCC readers."""
    canon = read_canonical_progress()
    if canon:
        drift = detect_progress_source_drift(canonical=canon)
        if drift.get("drift"):
            warns = list(canon.get("warnings") or [])
            if DRIFT_CODE not in warns:
                warns.append(DRIFT_CODE)
            canon = dict(canon)
            canon["warnings"] = warns
            canon["progress_source_drift"] = drift
        return canon

    # Bootstrap from physical-progress if canonical not yet written.
    physical = _read_json(physical_progress_path())
    if physical:
        boot = empty_progress()
        boot["phase"] = normalize_phase(str(physical.get("phase") or "startup"))
        boot["phase_index"] = phase_index(str(boot["phase"]))
        boot["phase_label_key"] = PHASE_LABEL_KEYS[str(boot["phase"])]
        boot["message"] = str(physical.get("message") or "")
        boot["updated_at"] = str(physical.get("updated_at") or _utc_now())
        boot["status"] = "passed" if boot["phase"] == "shutdown" else "running"
        boot["terminal"] = boot["phase"] in {"completed", "shutdown"}
        boot["source_component"] = "physical-progress-bootstrap"
        return boot
    return empty_progress()


def gui_status_from_canonical(progress: dict[str, Any] | None = None) -> dict[str, Any]:
    """Shape used by progress HTML / API consumers."""
    data = progress if progress is not None else read_progress_for_display()
    phase = normalize_phase(str(data.get("phase") or "startup"))
    status = str(data.get("status") or "running")
    return {
        "schema": "setuphelfer.rescue.auto-e2e-gui-status.v1",
        "schema_version": SCHEMA_VERSION,
        "active": True,
        "status": status,
        "phase": phase,
        "phase_index": int(data.get("phase_index") or phase_index(phase)),
        "phase_label_key": str(data.get("phase_label_key") or PHASE_LABEL_KEYS[phase]),
        "phase_label": str(data.get("message") or phase),
        "phase_label_de": str(data.get("message") or phase),
        "last_progress": str(data.get("message") or ""),
        "run_id": str(data.get("run_id") or ""),
        "updated_at": data.get("updated_at"),
        "sequence": int(data.get("sequence") or 0),
        "terminal": bool(data.get("terminal")),
        "bvr": data.get("bvr") or {},
        "gui": data.get("gui") or {},
        "warnings": data.get("warnings") or [],
        "errors": data.get("errors") or [],
        "progress_kind": data.get("progress_kind") or "indeterminate",
        "source_component": data.get("source_component") or "canonical",
        "canonical": True,
    }
