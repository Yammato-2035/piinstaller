"""
Hardware state sentinel — per-device lifecycle without raw serials.

PI-RS-ASUS-EMERGENCY-LINUX-TELEMETRY-003 Phase 4.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Mapping, Sequence

SUCCESS_FLOW: tuple[str, ...] = (
    "detected",
    "identified",
    "driver_candidate_resolved",
    "driver_bound",
    "firmware_loaded",
    "device_node_created",
    "operational_probe",
    "stable",
)

ERROR_STATES: frozenset[str] = frozenset(
    {
        "not_detected",
        "driver_unknown",
        "driver_missing",
        "driver_bind_failed",
        "module_load_failed",
        "firmware_missing",
        "firmware_load_failed",
        "device_node_missing",
        "initialization_timeout",
        "operational_probe_failed",
        "device_removed",
        "device_reset",
        "degraded",
        "blocked",
    }
)

ALLOWED_STATES = frozenset(SUCCESS_FLOW) | ERROR_STATES


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass
class HardwareDeviceState:
    device_id: str
    device_class: str
    vendor_id: str = ""
    product_id: str = ""
    state: str = "not_detected"
    driver_expected: str = ""
    driver_actual: str = ""
    module_state: str = "unknown"
    firmware_state: str = "unknown"
    operational_state: str = "unknown"
    history: list[str] = field(default_factory=list)
    updated_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def transition_device(
    device: HardwareDeviceState,
    new_state: str,
    *,
    run_id: str,
    boot_id: str,
    boot_attempt: int = 0,
    boot_profile: str = "",
    boot_stage: str = "",
    driver_expected: str | None = None,
    driver_actual: str | None = None,
    module_state: str | None = None,
    firmware_state: str | None = None,
    operational_state: str | None = None,
    issue_code: str = "",
    technical_summary: str = "",
    evidence_refs: Sequence[str] | None = None,
    severity: str | None = None,
) -> dict[str, Any]:
    if new_state not in ALLOWED_STATES:
        raise ValueError(f"unknown_hardware_state:{new_state}")
    device.state = new_state
    device.history.append(new_state)
    if driver_expected is not None:
        device.driver_expected = driver_expected
    if driver_actual is not None:
        device.driver_actual = driver_actual
    if module_state is not None:
        device.module_state = module_state
    if firmware_state is not None:
        device.firmware_state = firmware_state
    if operational_state is not None:
        device.operational_state = operational_state
    else:
        device.operational_state = new_state
    device.updated_at = _now_iso()
    sev = severity or ("error" if new_state in ERROR_STATES else "info")
    return {
        "event_id": str(uuid.uuid4()),
        "run_id": run_id,
        "boot_id": boot_id,
        "boot_attempt": boot_attempt,
        "boot_profile": boot_profile,
        "timestamp": _now_iso(),
        "monotonic_ms": int(time.monotonic() * 1000),
        "boot_stage": boot_stage,
        "device_id": device.device_id,
        "device_class": device.device_class,
        "vendor_id": device.vendor_id,
        "product_id": device.product_id,
        "driver_expected": device.driver_expected,
        "driver_actual": device.driver_actual,
        "module_state": device.module_state,
        "firmware_state": device.firmware_state,
        "operational_state": device.operational_state,
        "severity": sev,
        "issue_code": issue_code or (f"hw_{new_state}" if new_state in ERROR_STATES else ""),
        "technical_summary": technical_summary or f"{device.device_class}:{device.device_id} -> {new_state}",
        "evidence_refs": list(evidence_refs or []),
        # Explicitly never include raw serial numbers.
        "serial_number": None,
    }


def redact_device_identity(raw: Mapping[str, Any]) -> dict[str, Any]:
    """Drop serial-like keys from identity payloads."""
    banned = {"serial", "serial_number", "SerialNumber", "ID_SERIAL", "ID_SERIAL_SHORT"}
    out: dict[str, Any] = {}
    for key, value in raw.items():
        if key in banned or "serial" in key.lower():
            continue
        out[key] = value
    return out
