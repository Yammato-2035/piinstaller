from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from deploy.runner_rescue_io import guard_handoff_overwrite, resolve_handoff_path, write_json_handoff

_OUT_REL = "docs/evidence/runtime-results/handoff/rescue_live_hardware_matrix.json"
_MAX_BYTES = 512 * 1024


def _emit(status: str, body: dict[str, Any], *, wrote: bool, warnings: list[str], errors: list[str]) -> dict[str, Any]:
    return {
        "rescue_live_hardware_matrix_status": status,
        "rescue_live_hardware_matrix_file_path": _OUT_REL,
        "rescue_live_hardware_matrix": body,
        "rescue_live_hardware_matrix_handoff_written": wrote,
        "warnings": list(dict.fromkeys(warnings)),
        "errors": list(dict.fromkeys(errors)) if status == "blocked" else [],
        "blocked_reasons": list(dict.fromkeys(errors)),
    }


def build_rescue_live_hardware_matrix(*, explicit_overwrite: bool = False) -> dict[str, Any]:
    out_path, oerr = resolve_handoff_path(_OUT_REL, "RESCUE_HWMAT")
    if oerr or out_path is None:
        return _emit("blocked", {}, wrote=False, warnings=[], errors=[oerr or "RESCUE_HWMAT_INVALID"])
    gerr = guard_handoff_overwrite(out_path, explicit_overwrite=explicit_overwrite, prefix="RESCUE_HWMAT")
    if gerr:
        return _emit("blocked", {}, wrote=False, warnings=[], errors=[gerr])

    body: dict[str, Any] = {
        "rescue_live_hardware_matrix_schema_version": 1,
        "strict_mode": "rescue_live_hardware_readonly",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "tested": {
            "asus_rog": {"status": "lab_reported", "notes": ["UEFI", "NVMe"]},
            "nvme": True,
            "usb_sticks": True,
            "ext4": True,
            "ntfs": True,
            "efi": True,
            "wlan_lan": True,
        },
        "later": {
            "raspberry_pi": False,
            "arm64": False,
            "secure_boot": "review_required",
            "raid": False,
            "luks_recovery": False,
            "bitlocker_readonly": False,
        },
    }
    werr = write_json_handoff(out_path, body, max_bytes=_MAX_BYTES)
    if werr:
        return _emit("blocked", body, wrote=False, warnings=[], errors=[werr])
    return _emit("ok", body, wrote=True, warnings=[], errors=[])
