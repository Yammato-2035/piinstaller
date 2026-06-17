"""
Rescue backup plan contract — plan-only, execute_allowed=false in RS-F2B.1.
"""

from __future__ import annotations

import uuid
from typing import Any

from core.msi_windows_image_backup import (
    OPERATOR_CONFIRMATION_1,
    OPERATOR_CONFIRMATION_2,
    compute_required_bytes,
    run_f2_preflight,
)
from core.rescue_backup_encryption_contract import build_encryption_preflight
from core.rescue_backup_verify_contract import build_backup_verify_plan
from core.rescue_disk_role_classifier import (
    ROLE_EXTERNAL_BACKUP,
    ROLE_LINUX_SYSTEM,
    ROLE_WINDOWS_SYSTEM,
    classify_disk_role,
    validate_source_target_pair,
)
from core.rescue_os_detection import classify_detected_os
from core.rescue_backup_target_policy import classify_storage_role
from core.rescue_wifi_diagnostics import classify_wifi_status
from core.rescue_setup_logs_persistence import resolve_rescue_evidence_root

CONTRACT_VERSION = 2
SETUP_LOGS_LABELS = frozenset({"SETUP_LOGS"})


def _err(code: str, msg: str) -> dict[str, str]:
    return {"code": code, "message": msg}


def build_rescue_backup_plan(body: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = body if isinstance(body, dict) else {}
    warnings: list[dict[str, str]] = []
    errors: list[dict[str, str]] = []

    session_id = str(payload.get("rescue_session_id") or uuid.uuid4().hex[:16])
    target_mode = str(payload.get("target_mode") or "external_hdd").lower()
    wifi_override = str(payload.get("wifi_status") or "").lower()
    if wifi_override in ("available", "missing", "not_required"):
        wifi = classify_wifi_status()
        if wifi_override == "missing":
            wifi = {
                **wifi,
                "status": "missing",
                "blocks_cloud_backup": True,
                "blocks_local_hdd_backup": False,
            }
        elif wifi_override == "available":
            wifi = {**wifi, "status": "available", "blocks_cloud_backup": False}
    else:
        wifi = classify_wifi_status()
    evidence = resolve_rescue_evidence_root()

    source_device = str(payload.get("source_device") or "")
    target_mount = str(payload.get("target_mount") or "")
    target_device = str(payload.get("target_device") or "")
    free_bytes = int(payload.get("free_bytes") or 0)
    source_size = int(payload.get("source_size_bytes") or 0)
    fstype = str(payload.get("fstype") or "ext4")

    if not source_device:
        errors.append(_err("source_missing", "Keine Windows-/NTFS-Quelle angegeben."))
    elif source_device.startswith("/dev/nvme1") and str(payload.get("backup_mode") or "") != "linux_full_root_tar":
        errors.append(_err("source_ambiguous", "Interne Linux-Quelle blockiert."))

    target_label = str(payload.get("target_label") or "").upper()
    if target_label in SETUP_LOGS_LABELS or "SETUP_LOGS" in target_mount.upper():
        errors.append(_err("target_is_rescue_stick", "SETUP_LOGS darf nicht Backupziel sein."))

    target_role = classify_storage_role(
        {"path": target_device or target_mount, "label": payload.get("target_label"), "tran": payload.get("target_tran")}
    )
    if target_role in ("rescue_usb_stick", "rescue_usb_target_candidate"):
        errors.append(_err("target_is_rescue_stick", "Rettungsstick darf nicht Backupziel sein."))
    if target_role == "linux_system_disk":
        errors.append(_err("target_not_external", "Internes Ziel blockiert."))

    if target_mode == "cloud":
        if wifi.get("blocks_cloud_backup"):
            errors.append(_err("cloud_selected_but_wifi_missing", "Cloud gewählt, aber kein WLAN/Netz."))
    else:
        if not target_mount and not target_device:
            errors.append(_err("target_missing", "Kein externes Backupziel gewählt."))
        if wifi.get("status") != "available" and not wifi.get("blocks_local_hdd_backup"):
            warnings.append(
                _err(
                    "wifi_missing_but_not_required",
                    "WLAN nicht verfügbar — für lokales HDD-Backup nicht erforderlich.",
                )
            )

    pf = None
    op_c1 = OPERATOR_CONFIRMATION_1 if payload.get("operator_confirm_source") and payload.get("operator_confirm_target") else None
    op_c2 = OPERATOR_CONFIRMATION_2 if payload.get("operator_confirm_no_restore") else None
    if source_device and target_mount and target_mode != "cloud" and not errors:
        pf = run_f2_preflight(
            source_device=source_device,
            source_size_bytes=source_size or 1,
            target_mount=target_mount,
            target_device=target_device,
            free_bytes=free_bytes,
            fstype=fstype,
            operator_confirmation_1=op_c1,
            operator_confirmation_2=op_c2,
        )
        if pf.reason == "blocked_insufficient_target_capacity":
            errors.append(_err("target_capacity_insufficient", "Ziel zu klein für raw Image + 5%."))
        elif pf.reason == "blocked_external_target_mount_missing":
            errors.append(_err("target_missing", "Externes Backup-Mount nicht aktiv."))
        elif pf.reason == "blocked_operator_confirmation_missing":
            warnings.append(_err("operator_confirmation_missing", "Operator-Bestätigungen fehlen noch."))
        elif pf.reason == "blocked_invalid_source":
            errors.append(_err("source_ambiguous", "Quelle nicht erlaubt oder uneindeutig."))
        elif not pf.ok and pf.reason not in ("ok",):
            errors.append(_err(str(pf.reason), "Preflight blockiert."))

    if evidence.get("non_persistent"):
        warnings.append(_err("setup_logs_not_persistent", evidence.get("warning") or "Evidence nicht persistent."))

    plan_status = "blocked"
    if not errors:
        plan_status = "review_required" if warnings else "ready"

    backup_mode = "raw_image" if target_mode == "external_hdd" else "cloud_deferred"

    return {
        "contract_version": CONTRACT_VERSION,
        "plan_status": plan_status,
        "plan_id": f"RBP-{session_id[:8]}",
        "backup_mode": backup_mode,
        "source": {"device": source_device, "type": payload.get("source_type", "windows_ntfs_disk")},
        "target": {
            "mode": target_mode,
            "mount": target_mount,
            "device": target_device,
            "role": target_role,
        },
        "capacity": {
            "source_size_bytes": source_size,
            "free_bytes": free_bytes,
            "required_bytes": compute_required_bytes(source_size) if source_size else 0,
        },
        "wifi": {
            "required": target_mode == "cloud",
            "available": wifi.get("status") == "available",
            "blocks_plan": target_mode == "cloud" and wifi.get("blocks_cloud_backup", True),
            "diagnostics": wifi,
        },
        "telemetry": {
            "local_evidence_path": evidence.get("evidence_root"),
            "persistent": evidence.get("persistent", False),
            "network_upload_attempted": False,
        },
        "commands": [],
        "execute_allowed": False,
        "required_confirmations": [
            "operator_confirm_source",
            "operator_confirm_target",
            "operator_confirm_no_restore",
            "operator_confirm_no_wipe",
        ],
        "preflight": pf.to_dict() if pf else None,
        "warnings": warnings,
        "errors": errors,
    }


def build_rescue_full_backup_plan(body: dict[str, Any] | None = None) -> dict[str, Any]:
    """Full-backup plan with encryption/verify/cloud-pro gates; execute_allowed=false in RS-P1."""
    payload = body if isinstance(body, dict) else {}
    base = build_rescue_backup_plan(payload)
    backup_mode = str(payload.get("backup_mode") or payload.get("source_type") or "auto")
    target_mode = str(payload.get("target_mode") or "external_hdd").lower()
    if backup_mode == "auto":
        os_info = classify_detected_os(
            {"path": payload.get("source_device"), "fstype": payload.get("fstype"), "type": "disk"}
        )
        backup_mode = os_info.get("backup_modes", ["raw_image"])[0] if os_info.get("backup_modes") else "raw_image"

    source_dev = {
        "path": payload.get("source_device"),
        "fstype": payload.get("fstype"),
        "label": payload.get("source_label"),
        "type": "disk",
    }
    target_dev = {
        "path": payload.get("target_device") or payload.get("target_mount"),
        "label": payload.get("target_label"),
        "fstype": payload.get("fstype"),
        "tran": payload.get("target_tran"),
    }
    pair = validate_source_target_pair(source_dev, target_dev)
    errors = list(base.get("errors") or [])
    warnings = list(base.get("warnings") or [])
    for e in pair.get("errors") or []:
        if e not in errors:
            errors.append(e)

    if target_mode in ("cloud", "cloud_pro"):
        errors.append(_err("cloud_pro_plan_only", "Cloud-Backup ist Pro/private-only — kein Execute im Public-Repo."))
        if base.get("wifi", {}).get("blocks_plan"):
            errors.append(_err("cloud_selected_but_wifi_missing", "Cloud gewählt ohne Netzwerk."))

    encryption = build_encryption_preflight(
        encryption_requested=bool(payload.get("encryption_requested", True)),
        mode=str(payload.get("encryption_mode") or "not_configured"),
        key_configured=bool(payload.get("encryption_key_configured")),
        lab_unencrypted_confirmed=bool(payload.get("lab_unencrypted_confirmed")),
    )
    if encryption.get("blocks_execute") and encryption.get("encryption_required"):
        warnings.append(_err("encryption_key_missing", "Verschlüsselung vor Execute klären."))

    verify = build_backup_verify_plan(
        image_path=str(payload.get("planned_image_path") or ""),
        manifest_path=str(payload.get("planned_manifest_path") or ""),
        sha256_path=str(payload.get("planned_sha256_path") or ""),
        encrypted=encryption.get("encryption_status") == "configured",
    )
    if payload.get("verify_requested", True) and verify.get("verify_status") == "blocked":
        warnings.append(_err("verify_not_ready", "Verify-Preflight noch nicht bereit."))

    plan_status = base.get("plan_status")
    if errors:
        plan_status = "blocked"
    elif warnings or pair.get("review_required") or encryption.get("encryption_status") in ("missing", "deferred"):
        plan_status = "review_required"

    next_step = "Plan erneut prüfen nach Quell-/Zielwahl und Verschlüsselungskonfiguration."
    if not errors and plan_status == "ready":
        next_step = "Preflight OK — Execute folgt in RS-P3 nach Operator-Freigabe."

    base.update(
        {
            "contract_version": CONTRACT_VERSION,
            "plan_status": plan_status,
            "backup_mode": backup_mode,
            "full_backup": True,
            "manual_selection_supported": True,
            "target_selection_supported": True,
            "verify_required": bool(payload.get("verify_requested", True)),
            "verify": verify,
            "encryption": {
                "supported": True,
                "requested": bool(payload.get("encryption_requested", True)),
                "mode": encryption.get("mode"),
                "key_status": encryption.get("encryption_status"),
                "blocks_execute": encryption.get("blocks_execute", True),
                "preflight": encryption,
            },
            "cloud": {
                "available": False,
                "pro_only": True,
                "public_repo_execute_allowed": False,
                "plan_only": target_mode in ("cloud", "cloud_pro"),
            },
            "source_role": pair.get("source_role"),
            "target_role": pair.get("target_role"),
            "execute_allowed": False,
            "errors": errors,
            "warnings": warnings,
            "next_safe_step": next_step,
        }
    )
    return base
