"""
Rescue restore preview contract — plan/handoff only, no restore execution.
"""

from __future__ import annotations

from typing import Any

from rescue.restore_preview_orchestrator import build_rescue_restore_preview_plan

CONTRACT_VERSION = 1


def restore_preview_preflight(body: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = body if isinstance(body, dict) else {}
    plan = build_rescue_restore_preview_plan(
        backup_archive_path=str(payload.get("archive_path") or payload.get("backup_archive_path") or ""),
        manifest_path=str(payload.get("manifest_path") or ""),
        target_device_or_path=str(payload.get("target_root") or payload.get("target_device_or_path") or ""),
        restore_profile_id=str(payload.get("profile_id") or "offline-full-restore-preview"),
        verify_status=str(payload.get("verify_status") or "unknown"),
        storage_snapshot=payload.get("storage_snapshot") if isinstance(payload.get("storage_snapshot"), dict) else None,
        operator_override=bool(payload.get("explicit_internal_override")),
    )
  return {
      "contract_version": CONTRACT_VERSION,
      "restore_executed": False,
      "preview_only": True,
      "execute_allowed_on_development_laptop": False,
      "execute_allowed_only_when_booted_from_rescue": True,
      "requires_operator_confirmation": True,
      "requires_verify_green": True,
      "plan": plan,
  }
