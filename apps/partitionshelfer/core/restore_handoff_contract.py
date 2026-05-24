"""
Restore-Handoff nach Partitionierung (Phase 2) – nur Preview, kein Restore-Start.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

HandoffStatus = Literal["ready", "review_required", "blocked"]


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _verify_satisfied(verify_evidence: dict[str, Any] | None) -> bool:
    if not isinstance(verify_evidence, dict):
        return False
    if verify_evidence.get("verified") is True:
        return True
    st = str(verify_evidence.get("status") or "").lower()
    return st in ("ok", "passed", "success", "verified")


def build_partition_restore_handoff(
    *,
    partition_plan_preview: dict[str, Any] | None = None,
    hardstop_result: dict[str, Any] | None = None,
    manifest_layout_preview: dict[str, Any] | None = None,
    target_device: str | None = None,
    backup_manifest_ref: str | None = None,
    verify_evidence: dict[str, Any] | None = None,
    storage_safety_context: dict[str, Any] | None = None,
    backup_before_write: dict[str, Any] | None = None,
    operator_override: bool = False,
) -> dict[str, Any]:
    evidence_refs: list[str] = []
    if backup_manifest_ref:
        evidence_refs.append(backup_manifest_ref)
    if manifest_layout_preview and manifest_layout_preview.get("generated_at"):
        evidence_refs.append("manifest_layout_preview")
    mpath = manifest_layout_preview.get("manifest_path") if isinstance(manifest_layout_preview, dict) else None
    if mpath:
        evidence_refs.append(str(mpath))

    required_gates: list[str] = [
        "BACKUP_BEFORE_OVERWRITE_GATE",
        "VERIFY_BEFORE_RESTORE_GATE",
        "PARTITION_HARDSTOP_GATE",
    ]

    hardstop = hardstop_result if isinstance(hardstop_result, dict) else {}
    layout = manifest_layout_preview if isinstance(manifest_layout_preview, dict) else {}
    hs_status = str(hardstop.get("status") or "ok")
    layout_status = str(layout.get("status") or "unavailable")

    codes: list[str] = []
    status: HandoffStatus = "ready"
    handoff_sources: dict[str, Any] = {
        "hardstop": hardstop,
        "manifest_layout": layout,
        "storage_safety": storage_safety_context if isinstance(storage_safety_context, dict) else {},
        "partition_plan_preview": partition_plan_preview,
        "backup_manifest_ref": backup_manifest_ref,
        "verify_evidence": verify_evidence,
    }

    if hs_status == "blocked":
        status = "blocked"
        codes.append("partition.handoff.blocked_by_hardstop")
    elif layout_status in ("unavailable", "blocked"):
        status = "blocked" if layout_status == "blocked" else "review_required"
        codes.append("partition.handoff.manifest_layout_missing")
    elif hs_status == "review_required" or layout_status == "review_required":
        status = "review_required"
        codes.append("partition.warning.manual_review_required")

    if isinstance(storage_safety_context, dict) and storage_safety_context.get("status") == "blocked":
        status = "blocked"
        codes.append("partition.handoff.blocked_by_storage_facade")

    bbw = backup_before_write
    if bbw is None and isinstance(storage_safety_context, dict):
        core = storage_safety_context.get("core_results") or {}
        if isinstance(core, dict):
            bbw = core.get("backup_before_write")
    if isinstance(bbw, dict) and bbw.get("status") not in ("satisfied", None):
        if bbw.get("status") == "blocked":
            status = "blocked"
            codes.append("partition.handoff.backup_before_write_unsatisfied")
        elif status != "blocked":
            status = "review_required"
            codes.append("partition.handoff.backup_before_write_review")

    if not _verify_satisfied(verify_evidence):
        if status != "blocked":
            status = "review_required"
        codes.append("partition.handoff.verify_missing")

    if operator_override:
        if status == "ready":
            status = "review_required"
        codes.append("partition.handoff.operator_override_never_executes")

    if status != "blocked":
        codes.append("partition.handoff.requires_backup_before_overwrite_gate")
        codes.append("partition.handoff.requires_verify_before_restore")
    if status == "ready":
        codes.append("partition.handoff.ready_for_restore_preview")

    rescue_next = "rescue_stick_provisioning_readonly"
    if status == "blocked":
        rescue_next = "resolve_hardstop_and_verify_first"
    elif status == "review_required":
        rescue_next = "complete_manual_review_then_rescue_preview"

    return {
        "status": status,
        "handoff_type": "partition_to_restore_preview",
        "target_device": (target_device or "").strip() or None,
        "partition_plan_preview": partition_plan_preview,
        "hardstop_result": hardstop,
        "manifest_layout_preview": layout,
        "evidence_refs": evidence_refs,
        "required_next_gates": required_gates,
        "recommended_next_step": "restore_preview_only",
        "rescue_handoff_next": rescue_next,
        "handoff_sources": handoff_sources,
        "write_allowed": False,
        "restore_execution_allowed": False,
        "codes": codes,
        "generated_at": _utc_now(),
    }
