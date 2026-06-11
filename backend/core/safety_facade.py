"""
Safety-Facade: zentrale, read-only Sicherheitsentscheidungen für Write-Operationen.

Phase A.1 (Facade Freeze): ``validate_*`` and ``build_safety_decision`` are the canonical
public surface. Direct ``write_guard`` / ``safe_device`` usage is legacy (see CORE_FACADE_RULES).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from safety.write_guard import evaluate_write_target

FACADE_CONTRACT_VERSION = 1


class SafetyContext(str, Enum):
    """Execution context for safety decisions (future modules must pass explicitly)."""

    LIVE = "live"
    RESCUE = "rescue"
    PARTITION_HELPER = "partition_helper"
    CLOUDSERVER_FUTURE = "cloudserver_future"


@dataclass(frozen=True)
class SafetyDecision:
    """Public contract: normalized safety decision envelope."""

    context: SafetyContext
    target: str
    allowed: bool
    reason_code: str
    risk_level: str = "high"
    requires_confirmation: bool = False
    requires_override: bool = False
    facade_version: int = FACADE_CONTRACT_VERSION


def validate_backup_target_for_write(path: str, context: str = "live") -> dict[str, Any]:
    """Bewertet ein Zielgerät für Backup-Schreiben via bestehendem Write-Guard."""
    inspect_result = {"storage": {"devices_classified": [], "devices_raw": [], "mountability": []}, "filesystems": {"detected": {}}}
    device = path if path.startswith("/dev/") else f"/dev/{path}"
    decision = evaluate_write_target(device, inspect_result)
    decision["context"] = context
    return decision


def validate_restore_target(path: str, context: str = "rescue") -> dict[str, Any]:
    decision = validate_backup_target_for_write(path, context=context)
    decision["restore_allowed"] = bool(decision.get("allowed"))
    return decision


def validate_no_system_disk_write(path: str) -> dict[str, Any]:
    if path in {"/", "/dev/sda", "/dev/nvme0n1"}:
        return {
            "allowed": False,
            "reason_code": "SAFETY_SYSTEM_DISK",
            "risk_level": "high",
            "requires_confirmation": True,
            "requires_override": True,
        }
    return {
        "allowed": True,
        "reason_code": "SAFETY_BACKUP_TARGET_OK",
        "risk_level": "low",
        "requires_confirmation": False,
        "requires_override": False,
    }


def validate_backup_target(path: str, context: str | SafetyContext = SafetyContext.LIVE) -> dict[str, Any]:
    """Canonical alias for backup write-target validation."""
    ctx = context.value if isinstance(context, SafetyContext) else str(context)
    return validate_backup_target_for_write(path, context=ctx)


def validate_partition_target(path: str, context: str | SafetyContext = SafetyContext.PARTITION_HELPER) -> dict[str, Any]:
    """
    Partition-helper write target (contract stub; full logic migrates in a later phase).
    """
    ctx = context.value if isinstance(context, SafetyContext) else str(context)
    base = validate_no_system_disk_write(path)
    return {
        "context": ctx,
        "target": path,
        "partition_allowed": bool(base.get("allowed")),
        "allowed": bool(base.get("allowed")),
        "reason_code": base.get("reason_code", "SAFETY_PARTITION_UNKNOWN"),
        "risk_level": base.get("risk_level", "high"),
        "facade_version": FACADE_CONTRACT_VERSION,
    }


def build_safety_decision(*, target: str, context: str | SafetyContext) -> dict[str, Any]:
    ctx = context.value if isinstance(context, SafetyContext) else str(context)
    base = validate_no_system_disk_write(target)
    return {
        "context": ctx,
        "target": target,
        "allowed": bool(base.get("allowed")),
        "reason_code": base.get("reason_code", "SAFETY_UNKNOWN_DEVICE"),
        "risk_level": base.get("risk_level", "high"),
        "facade_version": FACADE_CONTRACT_VERSION,
    }


def build_safety_decision_contract(*, target: str, context: SafetyContext) -> SafetyDecision:
    """Typed contract wrapper around ``build_safety_decision``."""
    raw = build_safety_decision(target=target, context=context)
    return SafetyDecision(
        context=context,
        target=str(raw.get("target") or target),
        allowed=bool(raw.get("allowed")),
        reason_code=str(raw.get("reason_code") or "SAFETY_UNKNOWN_DEVICE"),
        risk_level=str(raw.get("risk_level") or "high"),
        requires_confirmation=bool(raw.get("requires_confirmation")),
        requires_override=bool(raw.get("requires_override")),
    )

