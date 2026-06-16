"""MSI Windows read-only handlers (Phase F.1)."""

from __future__ import annotations

from typing import Any

from core import windows_ntfs_detection_contract as contract


async def get_precheck_schema() -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "run_id": "F1-MSI-WINDOWS-READONLY-PRECHECK",
        "mode": "read_only",
        "evidence_schema_path": "docs/evidence/msi/MSI_WINDOWS_EVIDENCE_SCHEMA.json",
        "required_fields": ["blkid", "findmnt"],
        "optional_fields": ["lsblk_json", "efi_boot_hints", "operator_selected_source", "backup_target_candidates"],
        "forbidden_operations": [
            "mount",
            "backup_execute",
            "restore_execute",
            "wipe",
            "password_reset",
            "bitlocker_unlock",
        ],
    }


async def get_capabilities() -> dict[str, Any]:
    return contract.capabilities_payload()


async def parse_readonly_precheck(body: dict[str, Any]) -> dict[str, Any]:
    lsblk = body.get("lsblk_json") or body.get("lsblk_rows")
    blkid = body.get("blkid") or body.get("blkid_rows") or ""
    findmnt = body.get("findmnt") or body.get("findmnt_rows") or ""
    efi_hints = body.get("efi_boot_hints") or []
    operator_source = body.get("operator_selected_source")
    target_candidates = body.get("backup_target_candidates") or []

    classification = contract.classify_windows_ntfs_layout(
        lsblk,
        blkid,
        findmnt,
        efi_boot_hints=efi_hints if isinstance(efi_hints, list) else [],
    )
    decision = contract.build_msi_windows_precheck_decision(
        classification,
        backup_target_candidates=target_candidates if isinstance(target_candidates, list) else [],
        operator_selected_source=operator_source,
    )
    return {
        "status": "success",
        "classification": classification,
        "decision": decision,
        "contract_version": contract.CONTRACT_VERSION,
    }
