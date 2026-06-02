"""Safety-Facade: zentrale, read-only Sicherheitsentscheidungen für Write-Operationen."""

from __future__ import annotations

from typing import Any

from safety.write_guard import evaluate_write_target


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


def build_safety_decision(*, target: str, context: str) -> dict[str, Any]:
    base = validate_no_system_disk_write(target)
    return {
        "context": context,
        "target": target,
        "allowed": bool(base.get("allowed")),
        "reason_code": base.get("reason_code", "SAFETY_UNKNOWN_DEVICE"),
        "risk_level": base.get("risk_level", "high"),
    }

