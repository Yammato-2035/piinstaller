from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from deploy.runner_rescue_io import guard_handoff_overwrite, resolve_handoff_path, write_json_handoff

_OUT_REL = "docs/evidence/runtime-results/handoff/rescue_stick_component_inventory.json"
_MAX_BYTES = 768 * 1024


def _row(
    component: str,
    *,
    status: str,
    risk: str,
    required_for_mvp: bool,
    notes: list[str],
    component_id: str,
) -> dict[str, Any]:
    return {
        "component": component,
        "component_id": component_id,
        "status": status,
        "risk": risk,
        "required_for_mvp": required_for_mvp,
        "notes": list(notes),
    }


def _emit(
    status: str,
    body: dict[str, Any],
    *,
    wrote: bool,
    warnings: list[str],
    errors: list[str],
) -> dict[str, Any]:
    return {
        "rescue_stick_component_inventory_status": status,
        "rescue_stick_component_inventory_file_path": _OUT_REL,
        "rescue_stick_component_inventory": body,
        "rescue_stick_component_inventory_handoff_written": wrote,
        "warnings": list(dict.fromkeys(warnings)),
        "errors": list(dict.fromkeys(errors)) if status == "blocked" else [],
        "blocked_reasons": list(dict.fromkeys(errors)),
    }


def build_rescue_stick_component_inventory(*, explicit_overwrite: bool = False) -> dict[str, Any]:
    out_path, oerr = resolve_handoff_path(_OUT_REL, "RESCUE_INV")
    if oerr or out_path is None:
        return _emit("blocked", {}, wrote=False, warnings=[], errors=[oerr or "RESCUE_INV_OUTPUT_INVALID"])
    gerr = guard_handoff_overwrite(out_path, explicit_overwrite=explicit_overwrite, prefix="RESCUE_INV")
    if gerr:
        return _emit("blocked", {}, wrote=False, warnings=[], errors=[gerr])

    existing = [
        _row("Inspect Engine", status="existing", risk="low", required_for_mvp=True, notes=[], component_id="inspect"),
        _row("Backup (full / flows)", status="existing", risk="low", required_for_mvp=True, notes=[], component_id="backup"),
        _row("Verify", status="existing", risk="low", required_for_mvp=True, notes=[], component_id="verify"),
        _row("Restore Preview", status="existing", risk="medium", required_for_mvp=True, notes=["preview_only_no_execute"], component_id="restore_preview"),
        _row("Safety Gates", status="existing", risk="low", required_for_mvp=True, notes=[], component_id="safety_gates"),
        _row("Device Classification", status="existing", risk="medium", required_for_mvp=True, notes=[], component_id="device_classification"),
        _row("Write Guard", status="existing", risk="low", required_for_mvp=True, notes=[], component_id="write_guard"),
        _row("Runtime Result Validation", status="existing", risk="low", required_for_mvp=False, notes=[], component_id="runtime_result_validation"),
        _row("Live Probe (readonly)", status="existing", risk="medium", required_for_mvp=False, notes=["host_probe_optional"], component_id="live_probe"),
        _row("Evidence System", status="existing", risk="low", required_for_mvp=True, notes=[], component_id="evidence_system"),
    ]
    missing = [
        _row("Debian Live Build-Konfiguration", status="missing", risk="high", required_for_mvp=True, notes=["live-build config pending"], component_id="debian_live_build_config"),
        _row("ISO-Build-Skripte", status="missing", risk="high", required_for_mvp=True, notes=["template under scripts/rescue/"], component_id="iso_build_scripts"),
        _row("Boot-Menü (ISOLINUX/GRUB)", status="missing", risk="medium", required_for_mvp=True, notes=[], component_id="boot_menu"),
        _row("Offline-UI im Live-System", status="missing", risk="medium", required_for_mvp=True, notes=["local browser/kiosk optional"], component_id="offline_ui"),
        _row("WLAN-/Netzwerk-Assistent", status="missing", risk="medium", required_for_mvp=False, notes=["MVP: network status only"], component_id="wlan_assistant"),
        _row("SSH/Fernhilfe-Modus", status="missing", risk="medium", required_for_mvp=False, notes=["optional_readonly_help_mode"], component_id="ssh_remote_help"),
        _row("EFI-/Bootloader-Recovery", status="missing", risk="high", required_for_mvp=False, notes=["post_mvp_advisory"], component_id="efi_bootloader_recovery"),
        _row("fstab-/UUID-Recovery", status="missing", risk="high", required_for_mvp=False, notes=["detection_preview_only"], component_id="fstab_uuid_recovery"),
        _row("Provisioning-Layer", status="missing", risk="high", required_for_mvp=False, notes=[], component_id="provisioning_layer"),
        _row("ISO-Testpipeline", status="missing", risk="high", required_for_mvp=True, notes=["vm_and_laptop_matrix"], component_id="iso_test_pipeline"),
    ]
    partial = [
        _row("Network Status Surface", status="partial", risk="low", required_for_mvp=True, notes=["expose readonly status in live"], component_id="network_status"),
    ]

    body: dict[str, Any] = {
        "rescue_stick_component_inventory_schema_version": 1,
        "strict_mode": "setuphelfer_rescue_stick_preparation",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "components": existing + partial + missing,
        "counts": {
            "existing": len(existing),
            "partial": len(partial),
            "missing": len(missing),
            "planned": 0,
        },
    }
    status = "ok"
    werr = write_json_handoff(out_path, body, max_bytes=_MAX_BYTES)
    if werr:
        return _emit("blocked", body, wrote=False, warnings=[], errors=[werr])
    return _emit(status, body, wrote=True, warnings=[], errors=[])
