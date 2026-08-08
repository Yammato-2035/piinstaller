"""
Hardware baseline safety gate — additive, never bypasses ``safety_facade``.

PI-RS-HW-BASELINE-DIAG-I18N-002 Phase 11.

Aggregates the memory/CPU/GPU/storage baseline subsystem results into one
overall gate decision and per-operation permissions (backup, restore, OS
installation, GUI mode). This gate is deliberately **additive**: it sits
*in front of* the existing ``core.safety_facade`` write-target validation
and can only make an operation *more* cautious, never bypass or replace
the safety facade's own checks. A "blocked" baseline gate does not mean
the safety facade is skipped — both must agree.

``evaluate_operation_against_baseline_gate`` layers per-disk source/target
role awareness on top of the aggregated gate: a failing *source* disk is
still a valid backup target to read *from* (that's the whole point of an
emergency backup), while a failing *target* disk must never receive a
restore or OS installation.
"""

from __future__ import annotations

from typing import Any

from core.hardware_baseline_contracts import (
    BaselineSeverity,
    BaselineStatus,
    HardwareBaselineGate,
    HardwareSubsystemResult,
)

HARDWARE_BASELINE_GATE_VERSION = 1

_SEVERITY_RANK = {
    BaselineSeverity.GREEN.value: 0,
    BaselineSeverity.GRAY.value: 1,
    BaselineSeverity.YELLOW.value: 2,
    BaselineSeverity.RED.value: 3,
}

_STATUS_SEVERITY = {
    BaselineStatus.NO_IMMEDIATE_ISSUE_DETECTED.value: BaselineSeverity.GREEN.value,
    BaselineStatus.EXTENDED_TEST_RECOMMENDED.value: BaselineSeverity.YELLOW.value,
    BaselineStatus.DEGRADED.value: BaselineSeverity.YELLOW.value,
    BaselineStatus.REVIEW_REQUIRED.value: BaselineSeverity.YELLOW.value,
    BaselineStatus.IMMEDIATE_ISSUE_DETECTED.value: BaselineSeverity.RED.value,
    BaselineStatus.EXTENDED_TEST_REQUIRED.value: BaselineSeverity.RED.value,
    BaselineStatus.TEST_UNAVAILABLE.value: BaselineSeverity.GRAY.value,
    BaselineStatus.NOT_TESTED.value: BaselineSeverity.GRAY.value,
}


def _worst_status(statuses: list[str]) -> str:
    """Pick the status whose severity rank is highest; ties keep the first
    occurrence. An empty list yields NOT_TESTED (nothing to aggregate)."""
    if not statuses:
        return BaselineStatus.NOT_TESTED.value
    return max(statuses, key=lambda s: _SEVERITY_RANK.get(_STATUS_SEVERITY.get(s, BaselineSeverity.GRAY.value), 1))


def _is_red(status: str) -> bool:
    return _STATUS_SEVERITY.get(status, BaselineSeverity.GRAY.value) == BaselineSeverity.RED.value


def _is_yellow(status: str) -> bool:
    return _STATUS_SEVERITY.get(status, BaselineSeverity.GRAY.value) == BaselineSeverity.YELLOW.value


def _is_not_tested(status: str) -> bool:
    return status == BaselineStatus.NOT_TESTED.value


def build_hardware_baseline_gate(
    *,
    memory: HardwareSubsystemResult,
    cpu: HardwareSubsystemResult,
    gpu: HardwareSubsystemResult,
    storage: list[HardwareSubsystemResult] | None = None,
) -> HardwareBaselineGate:
    storage = storage or []
    storage_status = _worst_status([s.status for s in storage]) if storage else BaselineStatus.NOT_TESTED.value

    reasons: list[str] = []
    warnings: list[str] = []
    required_next_actions: list[str] = []

    data_critical_statuses = [memory.status, cpu.status, storage_status]
    any_data_critical_red = any(_is_red(s) for s in data_critical_statuses)
    any_data_critical_yellow = any(_is_yellow(s) for s in data_critical_statuses)
    any_not_tested = _is_not_tested(memory.status) or _is_not_tested(cpu.status) or _is_not_tested(gpu.status)

    for label, result in (("memory", memory), ("cpu", cpu)):
        if _is_red(result.status):
            reasons.append(f"{label} baseline reports {result.status}.")
        elif _is_yellow(result.status):
            warnings.append(f"{label} baseline reports {result.status}.")
    for s in storage:
        if _is_red(s.status):
            reasons.append(f"storage device {s.device_id} reports {s.status}.")
        elif _is_yellow(s.status):
            warnings.append(f"storage device {s.device_id} reports {s.status}.")
    if _is_red(gpu.status):
        warnings.append(f"gpu baseline reports {gpu.status}.")
    elif _is_yellow(gpu.status):
        warnings.append(f"gpu baseline reports {gpu.status}.")

    if any_data_critical_red:
        required_next_actions.append("Review the red-flagged memory/CPU/storage findings before restore or OS installation.")
    elif any_data_critical_yellow:
        required_next_actions.append("Review the flagged findings; extended tests are recommended before heavy use.")

    if any_not_tested:
        status = "incomplete"
    elif any_data_critical_red:
        status = "blocked"
    elif any_data_critical_yellow or _is_yellow(gpu.status) or _is_red(gpu.status):
        status = "review_required"
    else:
        status = "passed"

    backup_allowed = True  # baseline never blocks a read-only backup of a source disk
    restore_allowed = not any_data_critical_red and not any_not_tested
    os_installation_allowed = not any_data_critical_red and not any_not_tested
    gui_mode_allowed = not _is_red(gpu.status)

    if not gui_mode_allowed:
        required_next_actions.append("Use safe TUI-only mode until the GPU kernel error is reviewed.")

    # Explicit action impact (severity can be yellow/review while restore stays allowed).
    if not restore_allowed:
        restore_impact = "blocked"
    elif any_data_critical_yellow:
        restore_impact = "review_required"
    else:
        restore_impact = "allowed"
    if not os_installation_allowed:
        os_impact = "blocked"
    elif any_data_critical_yellow:
        os_impact = "review_required"
    else:
        os_impact = "allowed"
    gui_impact = "allowed" if gui_mode_allowed else "blocked"
    action_impact = (
        ("backup", "allowed" if backup_allowed else "blocked"),
        ("restore", restore_impact),
        ("os_install", os_impact),
        ("gpu_gui", gui_impact if not _is_not_tested(gpu.status) else "not_applicable"),
    )

    return HardwareBaselineGate(
        status=status,
        memory_status=memory.status,
        cpu_status=cpu.status,
        gpu_status=gpu.status,
        storage_status=storage_status,
        backup_allowed=backup_allowed,
        restore_allowed=restore_allowed,
        os_installation_allowed=os_installation_allowed,
        gui_mode_allowed=gui_mode_allowed,
        reasons=tuple(reasons),
        warnings=tuple(warnings),
        required_next_actions=tuple(required_next_actions),
        action_impact=action_impact,
    )


def evaluate_operation_against_baseline_gate(
    gate: HardwareBaselineGate,
    operation: str,
    *,
    source_disk_status: str | None = None,
    target_disk_status: str | None = None,
) -> dict[str, Any]:
    """Evaluate one operation ("backup"|"restore"|"os_installation"|
    "gui_mode") against the aggregated gate plus optional per-disk role
    awareness. This is an **additional** check layered on top of
    ``core.safety_facade`` — it never replaces or bypasses it; both must
    independently allow the operation for it to actually proceed.
    """
    reasons: list[str] = []

    if operation == "backup":
        # A failing *source* disk is exactly why an emergency backup is
        # needed — it must still be allowed to read from it. Only a failing
        # *target* (where the backup image is written to) blocks this.
        allowed = gate.backup_allowed
        if target_disk_status is not None and _is_red(target_disk_status):
            allowed = False
            reasons.append("Backup target disk baseline reports an immediate issue; choose a different backup destination.")
        if not allowed and not reasons:
            reasons.append("Backup blocked by hardware baseline gate.")
    elif operation == "restore":
        allowed = gate.restore_allowed
        if not allowed:
            reasons.append("Restore blocked: hardware baseline gate reports red-flagged memory/CPU/storage findings.")
        if target_disk_status is not None and _is_red(target_disk_status):
            allowed = False
            reasons.append("Restore target disk baseline reports an immediate issue; do not restore onto this disk.")
    elif operation == "os_installation":
        allowed = gate.os_installation_allowed
        if not allowed:
            reasons.append("OS installation blocked: hardware baseline gate reports red-flagged memory/CPU/storage findings.")
        if target_disk_status is not None and _is_red(target_disk_status):
            allowed = False
            reasons.append("OS installation target disk baseline reports an immediate issue; do not install onto this disk.")
    elif operation == "gui_mode":
        allowed = gate.gui_mode_allowed
        if not allowed:
            reasons.append("GUI mode blocked: GPU baseline reports a kernel-level error; use safe TUI-only mode.")
    else:
        allowed = False
        reasons.append(f"Unknown operation '{operation}'.")

    return {
        "operation": operation,
        "allowed": allowed,
        "reasons": reasons,
        "bypasses_safety_facade": False,
    }


def build_hardware_baseline_gate_diagnostics() -> dict[str, Any]:
    return {
        "module_version": HARDWARE_BASELINE_GATE_VERSION,
        "module": "rescue.hardware_baseline_gate",
        "read_only": True,
        "bypasses_safety_facade": False,
        "additive_only": True,
    }


__all__ = [
    "HARDWARE_BASELINE_GATE_VERSION",
    "build_hardware_baseline_gate",
    "evaluate_operation_against_baseline_gate",
    "build_hardware_baseline_gate_diagnostics",
]
