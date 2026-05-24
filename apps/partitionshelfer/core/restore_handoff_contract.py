"""
Restore-Handoff nach Partitionierung (Phase 2) – nur Preview, kein Restore-Start.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

HandoffStatus = Literal["ready", "review_required", "blocked"]


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_partition_restore_handoff(
    *,
    partition_plan_preview: dict[str, Any] | None = None,
    hardstop_result: dict[str, Any] | None = None,
    manifest_layout_preview: dict[str, Any] | None = None,
    target_device: str | None = None,
    backup_manifest_ref: str | None = None,
) -> dict[str, Any]:
    evidence_refs: list[str] = []
    if backup_manifest_ref:
        evidence_refs.append(backup_manifest_ref)
    if manifest_layout_preview and manifest_layout_preview.get("generated_at"):
        evidence_refs.append("manifest_layout_preview")

    required_gates: list[str] = ["BACKUP_BEFORE_OVERWRITE_GATE"]

    hardstop = hardstop_result if isinstance(hardstop_result, dict) else {}
    layout = manifest_layout_preview if isinstance(manifest_layout_preview, dict) else {}
    hs_status = str(hardstop.get("status") or "ok")
    layout_status = str(layout.get("status") or "unavailable")

    codes: list[str] = []
    status: HandoffStatus = "ready"

    if hs_status == "blocked":
        status = "blocked"
        codes.append("partition.handoff.blocked_by_hardstop")
    elif layout_status == "unavailable":
        status = "review_required"
        codes.append("partition.handoff.manifest_layout_missing")
    elif hs_status == "review_required" or layout_status == "review_required":
        status = "review_required"
        codes.append("partition.warning.manual_review_required")

    if status != "blocked":
        codes.append("partition.handoff.requires_backup_before_overwrite_gate")
    if status == "ready":
        codes.append("partition.handoff.ready_for_restore_preview")

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
        "write_allowed": False,
        "restore_execution_allowed": False,
        "codes": codes,
        "generated_at": _utc_now(),
    }
