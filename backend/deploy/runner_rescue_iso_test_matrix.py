from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from deploy.runner_rescue_io import guard_handoff_overwrite, resolve_handoff_path, write_json_handoff

_OUT_REL = "docs/evidence/runtime-results/handoff/rescue_iso_test_matrix.json"
_MAX_BYTES = 768 * 1024


def _emit(
    status: str,
    body: dict[str, Any],
    *,
    wrote: bool,
    warnings: list[str],
    errors: list[str],
) -> dict[str, Any]:
    return {
        "rescue_iso_test_matrix_status": status,
        "rescue_iso_test_matrix_file_path": _OUT_REL,
        "rescue_iso_test_matrix": body,
        "rescue_iso_test_matrix_handoff_written": wrote,
        "warnings": list(dict.fromkeys(warnings)),
        "errors": list(dict.fromkeys(errors)) if status == "blocked" else [],
        "blocked_reasons": list(dict.fromkeys(errors)),
    }


def build_rescue_iso_test_matrix(*, explicit_overwrite: bool = False) -> dict[str, Any]:
    out_path, oerr = resolve_handoff_path(_OUT_REL, "RESCUE_ISO_MATRIX")
    if oerr or out_path is None:
        return _emit("blocked", {}, wrote=False, warnings=[], errors=[oerr or "RESCUE_ISO_MATRIX_OUTPUT_INVALID"])
    gerr = guard_handoff_overwrite(out_path, explicit_overwrite=explicit_overwrite, prefix="RESCUE_ISO_MATRIX")
    if gerr:
        return _emit("blocked", {}, wrote=False, warnings=[], errors=[gerr])

    body: dict[str, Any] = {
        "rescue_iso_test_matrix_schema_version": 1,
        "strict_mode": "setuphelfer_rescue_stick_preparation",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "vm": {
            "bios_boot": {"goal": "verify_iso_boot_bios", "disk_write": "forbidden"},
            "uefi_boot": {"goal": "verify_iso_boot_uefi", "disk_write": "forbidden"},
            "no_guest_disk_write": {"goal": "ensure_no_writes_outside_evidence_export", "disk_write": "forbidden"},
            "ui_reachable": {"goal": "local_ui_loads"},
            "backend_api_version": {"goal": "GET /api/version returns setuphelfer project_version"},
            "inspect_readonly": {"goal": "inspect endpoints remain read_only"},
            "backup_verify_readonly": {"goal": "verify without destructive paths"},
        },
        "laptop": {
            "usb_boot_detected": {"goal": "firmware_lists_usb_boot_entry"},
            "wlan_lan_detected": {"goal": "network_interfaces_visible_readonly"},
            "internal_nvme_detected": {"goal": "inspect_sees_nvme_readonly"},
            "external_usb_detected": {"goal": "removable_storage_classification"},
            "no_writes_without_gate": {"goal": "write_safety_enforced"},
            "evidence_export_possible": {"goal": "handoff_export_path_available"},
        },
        "later": {
            "raspberry_pi_hardware": {"goal": "separate_arm_track"},
            "secure_boot": {"goal": "shim_signing_review", "status": "review_required"},
            "real_restore_scenarios": {"goal": "post_mvp_controlled_lab"},
        },
    }

    werr = write_json_handoff(out_path, body, max_bytes=_MAX_BYTES)
    if werr:
        return _emit("blocked", body, wrote=False, warnings=[], errors=[werr])
    return _emit("ok", body, wrote=True, warnings=[], errors=[])
