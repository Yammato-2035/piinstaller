from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from deploy.runner_rescue_io import guard_handoff_overwrite, load_json_handoff, resolve_handoff_path, write_json_handoff

_DISC_REL = "docs/evidence/runtime-results/handoff/rescue_storage_discovery_result.json"
_MNT_REL = "docs/evidence/runtime-results/handoff/readonly_mount_result.json"
_OUT_REL = "docs/evidence/runtime-results/handoff/rescue_efi_boot_analysis.json"
_MAX_BYTES = 768 * 1024


def _emit(status: str, body: dict[str, Any], *, wrote: bool, warnings: list[str], errors: list[str]) -> dict[str, Any]:
    return {
        "rescue_efi_boot_analysis_status": status,
        "rescue_efi_boot_analysis_file_path": _OUT_REL,
        "rescue_efi_boot_analysis": body,
        "rescue_efi_boot_analysis_handoff_written": wrote,
        "warnings": list(dict.fromkeys(warnings)),
        "errors": list(dict.fromkeys(errors)) if status == "blocked" else [],
        "blocked_reasons": list(dict.fromkeys(errors)),
    }


def build_rescue_efi_boot_analysis(*, explicit_overwrite: bool = False) -> dict[str, Any]:
    out_path, oerr = resolve_handoff_path(_OUT_REL, "RESCUE_EFI")
    if oerr or out_path is None:
        return _emit("blocked", {}, wrote=False, warnings=[], errors=[oerr or "RESCUE_EFI_INVALID"])
    gerr = guard_handoff_overwrite(out_path, explicit_overwrite=explicit_overwrite, prefix="RESCUE_EFI")
    if gerr:
        return _emit("blocked", {}, wrote=False, warnings=[], errors=[gerr])

    disc, _ = load_json_handoff(_DISC_REL, "RESCUE_EFI_DISC")
    mnt, _ = load_json_handoff(_MNT_REL, "RESCUE_EFI_MNT")

    rows: list[dict[str, Any]] = []
    if isinstance(disc, dict) and isinstance(disc.get("lsblk_rows"), list):
        rows = [r for r in disc["lsblk_rows"] if isinstance(r, dict)]

    efi_present = any(str(r.get("fstype") or "").lower() == "vfat" for r in rows)
    grub_hints = any("grub" in json.dumps(r).lower() for r in rows)
    bootloader_files_hint = efi_present and grub_hints
    uuid_conflicts = []
    cls = disc.get("classification") if isinstance(disc, dict) else {}
    if isinstance(cls, dict) and isinstance(cls.get("uuid_conflicts"), list):
        uuid_conflicts = list(cls["uuid_conflicts"])

    mnt_ok = False
    if isinstance(mnt, dict):
        evm = mnt.get("evaluation") if isinstance(mnt.get("evaluation"), dict) else {}
        mnt_ok = evm.get("readonly_mount_eval_status") == "ok" and bool(evm.get("readonly_enforced", False))

    warnings: list[str] = []
    if not rows:
        warnings.append("RESCUE_EFI_NO_DISCOVERY_ROWS")
    if not grub_hints and efi_present:
        warnings.append("RESCUE_EFI_GRUB_NOT_DETECTED_IN_HINTS")

    body: dict[str, Any] = {
        "rescue_efi_boot_analysis_schema_version": 1,
        "strict_mode": "rescue_efi_boot_readonly",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "efi_present": efi_present,
        "grub_configuration_hints": grub_hints,
        "bootloader_files_hint": bootloader_files_hint,
        "efi_partition_plausible": efi_present,
        "uuid_conflicts": uuid_conflicts,
        "fstab_problems_hint": bool(uuid_conflicts),
        "missing_mountpoints_hint": not mnt_ok,
        "damaged_boot_structure_hints": [],
        "repair_forbidden": True,
        "inputs": {"rescue_storage_discovery_result": _DISC_REL, "readonly_mount_result": _MNT_REL},
    }

    st = "ok" if efi_present or rows else "review_required"
    if not rows:
        st = "review_required"

    werr = write_json_handoff(out_path, body, max_bytes=_MAX_BYTES)
    if werr:
        return _emit("blocked", body, wrote=False, warnings=warnings, errors=[werr])
    return _emit(st, body, wrote=True, warnings=warnings, errors=[])
