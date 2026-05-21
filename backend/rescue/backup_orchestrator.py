"""
Rescue offline backup orchestrator — plan only; execution via canonical backup_runner.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from core.backup_profiles import (
    CANONICAL_BACKUP_RUNNER_MODULE,
    get_backup_profile,
    logical_excluded_patterns,
    normalize_backup_profile,
)
from rescue.boot_context import build_rescue_boot_context

_SOURCE_MODULES = (
    "rescue.backup_orchestrator",
    "rescue.boot_context",
    "core.backup_profiles",
    "core.storage_facade",
)


def _path_under(parent: str, child: str) -> bool:
    try:
        pp = Path(parent).resolve()
        pc = Path(child).resolve()
    except OSError:
        return False
    return pc == pp or pp in pc.parents


def _is_external_target(target_path: str, storage_snapshot: dict[str, Any] | None) -> bool:
    t = target_path.replace("\\", "/").rstrip("/")
    if t.startswith("/media/") or t.startswith("/run/media/"):
        return True
    if not isinstance(storage_snapshot, dict):
        return False
    for cand in storage_snapshot.get("backup_target_candidates") or []:
        if not isinstance(cand, dict):
            continue
        hint = str(cand.get("device_hint") or "")
        if hint and hint in t:
            return True
        role = cand.get("role")
        if role == "backup_target":
            return True
    for row in storage_snapshot.get("lsblk_rows") or []:
        if not isinstance(row, dict):
            continue
        mp = row.get("mountpoint")
        if isinstance(mp, str) and mp and _path_under(mp, target_path):
            if str(row.get("tran") or "").lower() == "usb":
                return True
    return False


def _is_internal_critical_target(target_path: str) -> bool:
    t = target_path.replace("\\", "/").rstrip("/") or "/"
    if t in ("/", "/boot", "/efi", "/boot/efi"):
        return True
    if t.startswith("/mnt/setuphelfer") and "/back" not in t:
        return False
    return False


def build_rescue_offline_backup_plan(
    *,
    source_root: str | None = None,
    target_path: str | None = None,
    boot_context: dict[str, Any] | None = None,
    storage_snapshot: dict[str, Any] | None = None,
    mount_snapshot: dict[str, Any] | None = None,
    backup_profile_id: str = "offline-full",
) -> dict[str, Any]:
    """
    Build offline BR-001 backup plan. Never starts backup, tar, systemd, or verify.
    """
    warnings: list[str] = []
    errors: list[str] = []
    blocked_reasons: list[str] = []

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

    src = (source_root or (boot_context or {}).get("source_root") or "").strip()
    tgt = (target_path or "").strip()
    prof_id = (backup_profile_id or "offline-full").strip().lower()

    if not src:
        blocked_reasons.append("missing_source_root")
    if not tgt:
        blocked_reasons.append("missing_target_path")

    profile = get_backup_profile(prof_id)
    if profile.get("unknown"):
        blocked_reasons.append("unknown_backup_profile")

    if src and tgt and _path_under(src, tgt):
        blocked_reasons.append("target_under_source_root")

    if tgt and _is_internal_critical_target(tgt):
        blocked_reasons.append("target_internal_system_critical")

    if profile.get("write_target_must_be_external") and tgt and not _is_external_target(tgt, storage_snapshot):
        blocked_reasons.append("target_not_classified_external")

    norm_prof, prof_warn = normalize_backup_profile(prof_id if not profile.get("unknown") else None)
    warnings.extend(prof_warn)

    expected_excludes = logical_excluded_patterns(norm_prof) if not profile.get("unknown") else []

    status = "blocked" if blocked_reasons else "ready"
    if not blocked_reasons and (warnings or profile.get("verify_after_backup_recommended")):
        if any("BOOT_CONTEXT" in w for w in warnings):
            status = "review_required"

    plan = {
        "profile_id": prof_id,
        "source_root": src,
        "target_path": tgt,
        "runner": CANONICAL_BACKUP_RUNNER_MODULE,
        "execution_allowed": False,
        "requires_operator_confirmation": True,
        "requires_external_target": bool(profile.get("write_target_must_be_external")),
        "expected_excludes": expected_excludes,
        "manifest_required": bool(profile.get("manifest_required")),
        "sha256_required": bool(profile.get("sha256_required")),
        "verify_after_backup_recommended": bool(profile.get("verify_after_backup_recommended")),
        "runner_env_hints": {
            "SETUPHELFER_BACKUP_SOURCE_ROOT": src,
            "backup_profile": norm_prof,
            "backup_type": "full",
        },
    }

    return {
        "status": status,
        "plan": plan,
        "blocked_reasons": blocked_reasons,
        "warnings": list(dict.fromkeys(warnings)),
        "errors": errors,
        "source_modules": list(_SOURCE_MODULES),
    }
