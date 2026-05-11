from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from deploy.runner_rescue_io import guard_handoff_overwrite, resolve_handoff_path, write_json_handoff

_OUT_REL = "docs/evidence/runtime-results/handoff/rescue_recovery_scenario_matrix.json"
_MAX_BYTES = 768 * 1024


def _emit(status: str, body: dict[str, Any], *, wrote: bool, warnings: list[str], errors: list[str]) -> dict[str, Any]:
    return {
        "rescue_recovery_scenario_matrix_status": status,
        "rescue_recovery_scenario_matrix_file_path": _OUT_REL,
        "rescue_recovery_scenario_matrix": body,
        "rescue_recovery_scenario_matrix_handoff_written": wrote,
        "warnings": list(dict.fromkeys(warnings)),
        "errors": list(dict.fromkeys(errors)) if status == "blocked" else [],
        "blocked_reasons": list(dict.fromkeys(errors)),
    }


_SCENARIOS: list[dict[str, Any]] = [
    {
        "scenario_id": "missing_efi_files",
        "risk": "boot_failure",
        "destructive": False,
        "recovery_stage": "inspect",
        "expected_detection_layer": "efi_boot_analysis",
        "expected_status": "review_required",
        "manual_only": True,
    },
    {
        "scenario_id": "damaged_fstab",
        "risk": "mount_failure",
        "destructive": False,
        "recovery_stage": "inspect",
        "expected_detection_layer": "efi_boot_analysis",
        "expected_status": "review_required",
        "manual_only": True,
    },
    {
        "scenario_id": "wrong_uuid",
        "risk": "wrong_root_mount",
        "destructive": False,
        "recovery_stage": "target_validation",
        "expected_detection_layer": "storage_discovery",
        "expected_status": "review_required",
        "manual_only": True,
    },
    {
        "scenario_id": "missing_grub",
        "risk": "unbootable_linux",
        "destructive": False,
        "recovery_stage": "inspect",
        "expected_detection_layer": "efi_boot_analysis",
        "expected_status": "review_required",
        "manual_only": True,
    },
    {
        "scenario_id": "unbootable_linux_partition",
        "risk": "no_kernel_chainload",
        "destructive": False,
        "recovery_stage": "readonly_mount_validation",
        "expected_detection_layer": "readonly_mount_orchestrator",
        "expected_status": "review_required",
        "manual_only": True,
    },
    {
        "scenario_id": "lost_backup_target",
        "risk": "no_restore_source",
        "destructive": False,
        "recovery_stage": "backup_discovery",
        "expected_detection_layer": "backup_discovery_verify",
        "expected_status": "blocked",
        "manual_only": True,
    },
    {
        "scenario_id": "damaged_backup",
        "risk": "restore_integrity_failure",
        "destructive": False,
        "recovery_stage": "backup_verify",
        "expected_detection_layer": "backup_discovery_verify",
        "expected_status": "blocked",
        "manual_only": True,
    },
    {
        "scenario_id": "legacy_parallel_runtime",
        "risk": "branding_or_path_conflict",
        "destructive": False,
        "recovery_stage": "runtime_compat",
        "expected_detection_layer": "branding_guard",
        "expected_status": "review_required",
        "manual_only": True,
    },
    {
        "scenario_id": "broken_mountpoints",
        "risk": "partial_boot",
        "destructive": False,
        "recovery_stage": "inspect",
        "expected_detection_layer": "efi_boot_analysis",
        "expected_status": "review_required",
        "manual_only": True,
    },
    {
        "scenario_id": "readonly_system_disk",
        "risk": "cannot_repair_in_place_readonly",
        "destructive": False,
        "recovery_stage": "readonly_mount_validation",
        "expected_detection_layer": "readonly_mount_orchestrator",
        "expected_status": "ok",
        "manual_only": True,
    },
    {
        "scenario_id": "no_network",
        "risk": "remote_help_degraded",
        "destructive": False,
        "recovery_stage": "remote_help",
        "expected_detection_layer": "remote_help_preparation",
        "expected_status": "review_required",
        "manual_only": True,
    },
    {
        "scenario_id": "missing_backup_manifest",
        "risk": "unverifiable_backup",
        "destructive": False,
        "recovery_stage": "backup_discovery",
        "expected_detection_layer": "backup_discovery_verify",
        "expected_status": "review_required",
        "manual_only": True,
    },
]


def build_rescue_recovery_scenario_matrix(*, explicit_overwrite: bool = False) -> dict[str, Any]:
    out_path, oerr = resolve_handoff_path(_OUT_REL, "RESCUE_RSMAT")
    if oerr or out_path is None:
        return _emit("blocked", {}, wrote=False, warnings=[], errors=[oerr or "RESCUE_RSMAT_INVALID"])
    gerr = guard_handoff_overwrite(out_path, explicit_overwrite=explicit_overwrite, prefix="RESCUE_RSMAT")
    if gerr:
        return _emit("blocked", {}, wrote=False, warnings=[], errors=[gerr])

    body: dict[str, Any] = {
        "rescue_recovery_scenario_matrix_schema_version": 1,
        "strict_mode": "rescue_recovery_simulation_readonly",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "scenarios": _SCENARIOS,
        "simulation_only": True,
        "no_restore_execute": True,
    }
    werr = write_json_handoff(out_path, body, max_bytes=_MAX_BYTES)
    if werr:
        return _emit("blocked", body, wrote=False, warnings=[], errors=[werr])
    return _emit("ok", body, wrote=True, warnings=[], errors=[])
