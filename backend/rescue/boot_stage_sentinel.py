"""
Boot-stage sentinel — exact markers for rescue boot progression.

PI-RS-ASUS-EMERGENCY-LINUX-TELEMETRY-003 Phase 4/5.

Additive to ``rescue_boot_status`` / ``rescue_evidence_spool``; does not replace them.
Never claims boot success beyond the last confirmed marker.
"""

from __future__ import annotations

import json
import time
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

BOOT_STAGES: tuple[str, ...] = (
    "firmware_handoff",
    "bootloader_started",
    "kernel_started",
    "initramfs_started",
    "root_device_discovered",
    "root_mounted",
    "systemd_started",
    "udev_initial_scan",
    "critical_modules_loaded",
    "hardware_inventory_complete",
    "baseline_diagnostics_complete",
    "network_link_ready",
    "ip_configuration_ready",
    "telemetry_connectivity_ready",
    "telemetry_ingest_confirmed",
    "diagnostics_confirmed",
    "graphical_target_requested",
    "drm_ready",
    "x11_or_wayland_ready",
    "browser_or_rescue_ui_ready",
    "user_session_ready",
    "shutdown_requested",
    "shutdown_complete",
)

_STAGE_INDEX = {name: idx for idx, name in enumerate(BOOT_STAGES)}

# Heuristic failure scopes when a later expected stage is missing.
FAILURE_SCOPE_BY_GAP: dict[tuple[str, str], str] = {
    ("critical_modules_loaded", "drm_ready"): "graphics_initialization",
    ("drm_ready", "x11_or_wayland_ready"): "display_server",
    ("x11_or_wayland_ready", "browser_or_rescue_ui_ready"): "rescue_ui_launch",
    ("network_link_ready", "ip_configuration_ready"): "network_configuration",
    ("ip_configuration_ready", "telemetry_connectivity_ready"): "telemetry_connectivity",
    ("telemetry_connectivity_ready", "telemetry_ingest_confirmed"): "telemetry_ingest",
    ("telemetry_ingest_confirmed", "diagnostics_confirmed"): "diagnostics_forwarding",
    ("root_device_discovered", "root_mounted"): "rootfs_mount",
    ("initramfs_started", "root_device_discovered"): "root_device_discovery",
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass
class BootStageState:
    run_id: str
    boot_id: str
    boot_attempt: int
    boot_profile: str
    reached: list[str] = field(default_factory=list)
    failed: list[str] = field(default_factory=list)
    last_successful_marker: str | None = None
    first_failed_marker: str | None = None
    boot_failure_scope: str = "none"
    updated_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def new_boot_stage_state(
    *,
    run_id: str,
    boot_id: str | None = None,
    boot_attempt: int = 0,
    boot_profile: str = "ASUS-00",
) -> BootStageState:
    return BootStageState(
        run_id=run_id,
        boot_id=boot_id or str(uuid.uuid4()),
        boot_attempt=int(boot_attempt),
        boot_profile=boot_profile,
    )


def mark_stage_reached(state: BootStageState, stage: str, *, monotonic_ms: int | None = None) -> dict[str, Any]:
    if stage not in _STAGE_INDEX:
        raise ValueError(f"unknown_boot_stage:{stage}")
    if stage not in state.reached:
        state.reached.append(stage)
    state.last_successful_marker = stage
    # Clear failure scope if we progressed past a previous fail (re-attempt marker).
    if state.first_failed_marker and _STAGE_INDEX[stage] >= _STAGE_INDEX.get(state.first_failed_marker, -1):
        if stage == state.first_failed_marker:
            state.failed = [f for f in state.failed if f != stage]
            state.first_failed_marker = state.failed[0] if state.failed else None
    state.boot_failure_scope = _compute_failure_scope(state)
    state.updated_at = _now_iso()
    return build_stage_event(state, stage=stage, outcome="reached", monotonic_ms=monotonic_ms)


def mark_stage_failed(state: BootStageState, stage: str, *, issue_code: str = "", technical_summary: str = "") -> dict[str, Any]:
    if stage not in _STAGE_INDEX:
        raise ValueError(f"unknown_boot_stage:{stage}")
    if stage not in state.failed:
        state.failed.append(stage)
    if state.first_failed_marker is None:
        state.first_failed_marker = stage
    state.boot_failure_scope = _compute_failure_scope(state, explicit_failed=stage)
    state.updated_at = _now_iso()
    return build_stage_event(
        state,
        stage=stage,
        outcome="failed",
        issue_code=issue_code or f"boot_stage_failed:{stage}",
        technical_summary=technical_summary or f"boot stage {stage} failed",
    )


def _compute_failure_scope(state: BootStageState, *, explicit_failed: str | None = None) -> str:
    last_ok = state.last_successful_marker
    first_fail = explicit_failed or state.first_failed_marker
    if not first_fail:
        return "none"
    if last_ok and (last_ok, first_fail) in FAILURE_SCOPE_BY_GAP:
        return FAILURE_SCOPE_BY_GAP[(last_ok, first_fail)]
    if last_ok:
        return f"after_{last_ok}_before_or_at_{first_fail}"
    return f"failed_at_{first_fail}"


def diagnose_missing_next_stage(state: BootStageState, expected_next: str) -> dict[str, Any]:
    """Return a concrete failure scope instead of boot_failed_unknown."""
    last_ok = state.last_successful_marker
    scope = "boot_failed_unknown"
    if last_ok and (last_ok, expected_next) in FAILURE_SCOPE_BY_GAP:
        scope = FAILURE_SCOPE_BY_GAP[(last_ok, expected_next)]
    elif last_ok:
        scope = f"after_{last_ok}_missing_{expected_next}"
    elif expected_next:
        scope = f"missing_{expected_next}"
    return {
        "last_successful_marker": last_ok,
        "first_missing_or_failed_marker": expected_next,
        "boot_failure_scope": scope,
    }


def build_stage_event(
    state: BootStageState,
    *,
    stage: str,
    outcome: str,
    monotonic_ms: int | None = None,
    issue_code: str = "",
    technical_summary: str = "",
    evidence_refs: Sequence[str] | None = None,
) -> dict[str, Any]:
    return {
        "event_id": str(uuid.uuid4()),
        "run_id": state.run_id,
        "boot_id": state.boot_id,
        "boot_attempt": state.boot_attempt,
        "boot_profile": state.boot_profile,
        "timestamp": _now_iso(),
        "monotonic_ms": int(monotonic_ms if monotonic_ms is not None else time.monotonic() * 1000),
        "boot_stage": stage,
        "device_id": "",
        "device_class": "boot",
        "vendor_id": "",
        "product_id": "",
        "driver_expected": "",
        "driver_actual": "",
        "module_state": "",
        "firmware_state": "",
        "operational_state": outcome,
        "severity": "error" if outcome == "failed" else "info",
        "issue_code": issue_code,
        "technical_summary": technical_summary or f"boot stage {stage} {outcome}",
        "evidence_refs": list(evidence_refs or []),
        "last_successful_marker": state.last_successful_marker,
        "first_failed_marker": state.first_failed_marker,
        "boot_failure_scope": state.boot_failure_scope,
    }


def persist_boot_stage_state(state: BootStageState, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(state.to_dict(), indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)


def load_boot_stage_state(path: Path) -> BootStageState | None:
    if not path.is_file():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    return BootStageState(
        run_id=str(data.get("run_id") or ""),
        boot_id=str(data.get("boot_id") or ""),
        boot_attempt=int(data.get("boot_attempt") or 0),
        boot_profile=str(data.get("boot_profile") or ""),
        reached=list(data.get("reached") or []),
        failed=list(data.get("failed") or []),
        last_successful_marker=data.get("last_successful_marker"),
        first_failed_marker=data.get("first_failed_marker"),
        boot_failure_scope=str(data.get("boot_failure_scope") or "none"),
        updated_at=str(data.get("updated_at") or _now_iso()),
    )


def validate_stage_sequence(reached: Iterable[str]) -> list[str]:
    """Return warnings if stages appear out of canonical order."""
    warnings: list[str] = []
    last_idx = -1
    for stage in reached:
        idx = _STAGE_INDEX.get(stage)
        if idx is None:
            warnings.append(f"unknown_stage:{stage}")
            continue
        if idx < last_idx:
            warnings.append(f"out_of_order:{stage}")
        last_idx = max(last_idx, idx)
    return warnings
