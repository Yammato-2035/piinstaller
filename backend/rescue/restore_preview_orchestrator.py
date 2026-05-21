"""
Rescue restore preview orchestrator — plan/handoff only; no restore, tar extract, or mount execution.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from core.backup_before_write_gate import evaluate_backup_before_write_requirement
from core.restore_profiles import (
    CANONICAL_RESTORE_PREVIEW_ENTRY,
    CANONICAL_RESTORE_PREVIEW_MODULE,
    CANONICAL_VERIFY_MODULE,
    PROFILE_OFFLINE_FULL_RESTORE_PREVIEW,
    canonical_restore_preview_available,
    canonical_verify_available,
    get_restore_profile,
)
from rescue.boot_context import build_rescue_boot_context

_SOURCE_MODULES = (
    "rescue.restore_preview_orchestrator",
    "rescue.boot_context",
    "core.restore_profiles",
    "core.backup_before_write_gate",
    "core.storage_facade",
    "core.mount_facade",
)


def _path_under(parent: str, child: str) -> bool:
    try:
        pp = Path(parent).resolve()
        pc = Path(child).resolve()
    except OSError:
        return False
    return pc == pp or pp in pc.parents


def _is_internal_critical_target(target: str, *, explicit_override: bool = False) -> bool:
    if explicit_override:
        return False
    t = target.replace("\\", "/").rstrip("/") or "/"
    return t in ("/", "/boot", "/efi", "/boot/efi")


def _target_looks_like_backup_media(
    target: str,
    archive_path: str,
    manifest_path: str,
    storage_snapshot: dict[str, Any] | None,
) -> bool:
    t = target.replace("\\", "/").rstrip("/")
    for ref in (archive_path, manifest_path):
        r = ref.replace("\\", "/").rstrip("/")
        if r and (_path_under(t, r) or _path_under(r, t)):
            return True
        if r and t and (t in r or r.startswith(t + "/")):
            return True
    if not isinstance(storage_snapshot, dict):
        return False
    for cand in storage_snapshot.get("backup_target_candidates") or []:
        if not isinstance(cand, dict):
            continue
        hint = str(cand.get("device_hint") or "")
        if hint and hint in t and cand.get("role") == "backup_target":
            return True
    return False


def _normalize_verify_status(verify_status: str | None) -> str:
    v = (verify_status or "unknown").strip().lower()
    if v in ("ok", "passed", "success", "verified"):
        return "ok"
    if v in ("failed", "fail", "error", "blocked"):
        return "failed"
    return "unknown"


def build_rescue_restore_preview_plan(
    *,
    boot_context: dict[str, Any] | None = None,
    storage_snapshot: dict[str, Any] | None = None,
    mount_snapshot: dict[str, Any] | None = None,
    restore_profile_id: str = "offline-full-restore-preview",
    backup_archive_path: str | None = None,
    manifest_path: str | None = None,
    target_device_or_path: str | None = None,
    target_classification: str | None = None,
    verify_status: str | None = None,
    operator_hints: dict[str, Any] | None = None,
    existing_filesystems: bool | None = None,
    existing_os_indicators: bool | None = None,
    user_data_indicators: bool | None = None,
    backup_evidence: dict[str, Any] | None = None,
    operator_override: bool = False,
    source_root: str | None = None,
) -> dict[str, Any]:
    """
    Build restore preview handoff plan. Never starts restore, tar extract, verify deep, or mount.
    """
    warnings: list[str] = []
    errors: list[str] = []
    blocked_reasons: list[str] = []
    hints = operator_hints if isinstance(operator_hints, dict) else {}

    ctx_envelope: dict[str, Any] | None = None
    if boot_context is None or not isinstance(boot_context, dict) or "source_root" not in boot_context:
        ctx_envelope = build_rescue_boot_context(
            source_root=source_root,
            storage_snapshot=storage_snapshot,
            mount_snapshot=mount_snapshot,
        )
        boot_context = ctx_envelope.get("boot_context") if isinstance(ctx_envelope.get("boot_context"), dict) else {}
        if ctx_envelope.get("status") == "blocked":
            blocked_reasons.append("boot_context_blocked")
        elif ctx_envelope.get("status") == "review_required":
            warnings.append("BOOT_CONTEXT_REVIEW_REQUIRED")
        warnings.extend(ctx_envelope.get("warnings") or [])

    archive = (backup_archive_path or hints.get("backup_archive_path") or "").strip()
    manifest = (manifest_path or hints.get("manifest_path") or "").strip()
    target = (target_device_or_path or hints.get("target_device_or_path") or "").strip()
    src_root = (source_root or (boot_context or {}).get("source_root") or "").strip()
    prof_id = (restore_profile_id or PROFILE_OFFLINE_FULL_RESTORE_PREVIEW).strip().lower()

    profile = get_restore_profile(prof_id)
    if profile.get("unknown"):
        blocked_reasons.append("unknown_restore_profile")

    if not archive:
        blocked_reasons.append("missing_backup_archive_path")
    if not manifest:
        blocked_reasons.append("missing_manifest_path")
    if not target:
        blocked_reasons.append("missing_target_device_or_path")

    if not canonical_restore_preview_available():
        blocked_reasons.append("canonical_restore_preview_unavailable")
    if not canonical_verify_available():
        blocked_reasons.append("canonical_verify_unavailable")

    vstat = _normalize_verify_status(verify_status or hints.get("verify_status"))
    if vstat == "failed":
        blocked_reasons.append("verify_status_failed")
    elif vstat == "unknown":
        warnings.append("VERIFY_STATUS_UNKNOWN")

    if src_root and target and _path_under(src_root, target):
        blocked_reasons.append("target_under_backup_source_root")

    if archive and target and _target_looks_like_backup_media(target, archive, manifest, storage_snapshot):
        blocked_reasons.append("target_looks_like_backup_media")

    explicit_target_ok = hints.get("explicit_target_override") is True or operator_override
    if target and _is_internal_critical_target(target, explicit_override=explicit_target_ok):
        blocked_reasons.append("target_internal_system_critical")

    tc = (target_classification or hints.get("target_classification") or "unknown").strip().lower()
    if tc == "unknown":
        warnings.append("TARGET_CLASSIFICATION_UNKNOWN")

    bbw = evaluate_backup_before_write_requirement(
        target_classification=tc,
        existing_filesystems=existing_filesystems,
        existing_os_indicators=existing_os_indicators,
        user_data_indicators=user_data_indicators,
        backup_evidence=backup_evidence,
        operator_override=operator_override,
    )
    if profile.get("requires_backup_before_overwrite"):
        if bbw["status"] == "blocked":
            blocked_reasons.append("backup_before_overwrite_blocked")
        elif bbw["status"] == "required":
            blocked_reasons.append("backup_before_overwrite_required")
        elif bbw["status"] == "review_required":
            warnings.append("BACKUP_BEFORE_OVERWRITE_REVIEW_REQUIRED")

    if hints.get("bootloader_repair_later") or hints.get("efi_repair_later"):
        warnings.append("BOOTLOADER_EFI_REPAIR_LATER_REQUIRED")
    if hints.get("malware_suspected"):
        warnings.append("MALWARE_SUSPECTED_REVIEW_REQUIRED")
    if hints.get("size_unknown"):
        warnings.append("RESTORE_SIZE_UNKNOWN")

    status = "blocked" if blocked_reasons else "ready"
    if not blocked_reasons and warnings:
        status = "review_required"

    safety_gates = [
        "backup_before_overwrite",
        "verify_before_restore",
        "target_write_approval",
        "path_containment",
    ]
    if profile.get("requires_external_or_explicit_target"):
        safety_gates.append("external_or_explicit_target")

    plan = {
        "profile_id": prof_id,
        "backup_archive_path": archive,
        "manifest_path": manifest,
        "target_device_or_path": target,
        "execution_allowed": False,
        "requires_operator_confirmation": True,
        "requires_verify_before_restore": bool(profile.get("requires_verify_before_restore")),
        "requires_backup_before_overwrite": bool(profile.get("requires_backup_before_overwrite")),
        "restore_engine": f"{CANONICAL_RESTORE_PREVIEW_MODULE}.{CANONICAL_RESTORE_PREVIEW_ENTRY}",
        "verify_engine": CANONICAL_VERIFY_MODULE,
        "safety_gates": safety_gates,
        "expected_preview_outputs": [
            "restore_dryrun_decision",
            "target_assessment",
            "risk_report",
            "verify_summary",
            "boot_preconditions_preview",
        ],
        "backup_before_write_gate": bbw,
        "forbidden_actions": list(profile.get("forbidden_actions") or []),
    }

    return {
        "status": status,
        "plan": plan,
        "blocked_reasons": blocked_reasons,
        "warnings": list(dict.fromkeys(warnings)),
        "errors": errors,
        "source_modules": list(_SOURCE_MODULES),
    }
