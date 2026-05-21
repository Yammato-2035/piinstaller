"""
Backup-before-overwrite gate — Entscheidung nur, keine Schreib- oder Backup-Ausführung.
"""

from __future__ import annotations

from typing import Any


def _evidence_indicates_backup(backup_evidence: dict[str, Any] | None) -> bool:
    if not isinstance(backup_evidence, dict):
        return False
    if backup_evidence.get("backup_completed") is True:
        return True
    st = str(backup_evidence.get("status") or backup_evidence.get("evidence_status") or "").lower()
    if st in ("ok", "satisfied", "complete", "completed"):
        return True
    if backup_evidence.get("manifest_present") is True and backup_evidence.get("sha256_verified") is True:
        return True
    return False


def evaluate_backup_before_write_requirement(
    *,
    target_classification: str | None = None,
    existing_filesystems: bool | None = None,
    existing_os_indicators: bool | None = None,
    user_data_indicators: bool | None = None,
    backup_evidence: dict[str, Any] | None = None,
    operator_override: bool = False,
) -> dict[str, Any]:
    """
    Bewertet, ob vor Restore/Overwrite ein Backup der Zieldaten nötig ist.
    """
    warnings: list[str] = []
    errors: list[str] = []
    required_actions: list[str] = []

    has_data = any(
        x is True
        for x in (existing_filesystems, existing_os_indicators, user_data_indicators)
    )

    if not has_data:
        return {
            "status": "satisfied",
            "backup_required": False,
            "reason": "target_empty_or_unclassified",
            "required_actions": [],
            "warnings": warnings,
            "errors": errors,
        }

    backup_required = True
    if _evidence_indicates_backup(backup_evidence):
        return {
            "status": "satisfied",
            "backup_required": True,
            "reason": "backup_evidence_present",
            "required_actions": [],
            "warnings": warnings,
            "errors": errors,
        }

    if operator_override:
        warnings.append("BACKUP_BEFORE_WRITE_OPERATOR_OVERRIDE")
        required_actions.append("document_operator_override")
        required_actions.append("create_target_backup_before_restore")
        return {
            "status": "review_required",
            "backup_required": True,
            "reason": "operator_override_without_backup_evidence",
            "required_actions": required_actions,
            "warnings": warnings,
            "errors": errors,
        }

    if target_classification == "internal_system" and not operator_override:
        errors.append("internal_target_requires_backup_evidence")
        required_actions.append("backup_target_before_overwrite")
        return {
            "status": "blocked",
            "backup_required": True,
            "reason": "missing_backup_evidence_on_populated_target",
            "required_actions": required_actions,
            "warnings": warnings,
            "errors": errors,
        }

    required_actions.append("backup_target_before_overwrite")
    return {
        "status": "required",
        "backup_required": True,
        "reason": "existing_data_without_backup_evidence",
        "required_actions": required_actions,
        "warnings": warnings,
        "errors": errors,
    }
