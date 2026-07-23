"""BIOS capability inventory and change contract (no undocumentierte NVRAM writes)."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

SCHEMA_VERSION = 1
CONTRACT_VERSION = 1

# Conservative known-controllable surfaces for ASUS ROG lab; write_supported only when method exists.
DEFAULT_CAPABILITIES: tuple[dict[str, Any], ...] = (
    {
        "setting": "BootOrder",
        "read_method": "efibootmgr -v",
        "write_method": "efibootmgr -o",
        "write_supported": True,
        "requires_reboot": True,
        "requires_firmware_ui": False,
        "rollback_supported": True,
        "bitlocker_recovery_risk": False,
    },
    {
        "setting": "BootNext",
        "read_method": "efibootmgr -v",
        "write_method": "efibootmgr -n",
        "write_supported": True,
        "requires_reboot": True,
        "requires_firmware_ui": False,
        "rollback_supported": True,
        "bitlocker_recovery_risk": False,
    },
    {
        "setting": "SecureBoot",
        "read_method": "efivarfs SecureBoot",
        "write_method": "firmware_setup_ui_or_mokutil",
        "write_supported": False,
        "requires_reboot": True,
        "requires_firmware_ui": True,
        "rollback_supported": True,
        "bitlocker_recovery_risk": True,
    },
    {
        "setting": "SetupMode",
        "read_method": "efivarfs SetupMode",
        "write_method": "firmware_setup_ui",
        "write_supported": False,
        "requires_reboot": True,
        "requires_firmware_ui": True,
        "rollback_supported": True,
        "bitlocker_recovery_risk": True,
    },
    {
        "setting": "TPM_fTPM",
        "read_method": "sysfs/tpm + firmware inventory",
        "write_method": "firmware_setup_ui",
        "write_supported": False,
        "requires_reboot": True,
        "requires_firmware_ui": True,
        "rollback_supported": False,
        "bitlocker_recovery_risk": True,
    },
    {
        "setting": "VMD_RAID_AHCI",
        "read_method": "unknown_until_probed",
        "write_method": "firmware_setup_ui",
        "write_supported": False,
        "requires_reboot": True,
        "requires_firmware_ui": True,
        "rollback_supported": True,
        "bitlocker_recovery_risk": False,
    },
    {
        "setting": "FastBoot",
        "read_method": "unknown_until_probed",
        "write_method": "firmware_setup_ui",
        "write_supported": False,
        "requires_reboot": True,
        "requires_firmware_ui": True,
        "rollback_supported": True,
        "bitlocker_recovery_risk": False,
    },
)


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def build_capability_inventory(
    *,
    observed: Mapping[str, Any] | None = None,
    capabilities: Sequence[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    obs = dict(observed or {})
    items: list[dict[str, Any]] = []
    for cap in capabilities or DEFAULT_CAPABILITIES:
        setting = str(cap.get("setting") or "")
        current = obs.get(setting)
        items.append(
            {
                "setting": setting,
                "current_value": current if current is not None else "unknown",
                "allowed_values": list(cap.get("allowed_values") or []),
                "read_method": cap.get("read_method"),
                "write_method": cap.get("write_method"),
                "write_supported": bool(cap.get("write_supported")),
                "requires_reboot": bool(cap.get("requires_reboot")),
                "requires_firmware_ui": bool(cap.get("requires_firmware_ui")),
                "rollback_supported": bool(cap.get("rollback_supported")),
                "bitlocker_recovery_risk": bool(cap.get("bitlocker_recovery_risk")),
            }
        )
    return {
        "schema_version": SCHEMA_VERSION,
        "contract_version": CONTRACT_VERSION,
        "profile_id": "ASUS_ROG_GABRIEL_LAB",
        "generated_at": utc_now(),
        "settings": items,
        "note": "write_supported=false means firmware UI checklist only — no invented raw NVRAM writes",
    }


def build_bios_change_contract(
    *,
    change_id: str,
    setting: str,
    old_value: str,
    new_value: str,
    reason: str,
    write_method: str,
    requires_reboot: bool = True,
    rollback_value: str | None = None,
    write_supported: bool = False,
    bitlocker_recovery_risk: bool = True,
    operator_presence_required: bool | None = None,
) -> dict[str, Any]:
    if not write_supported and "firmware_setup_ui" not in write_method and "efibootmgr" not in write_method:
        raise ValueError("unsupported_bios_write_method")
    if old_value == new_value:
        raise ValueError("noop_bios_change")
    op_required = (
        operator_presence_required
        if operator_presence_required is not None
        else (not write_supported or "firmware_setup_ui" in write_method)
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "contract_version": CONTRACT_VERSION,
        "change_id": change_id,
        "machine_profile": "ASUS_ROG_GABRIEL_LAB",
        "setting": setting,
        "old_value": old_value,
        "new_value": new_value,
        "reason": reason,
        "write_method": write_method,
        "risk_class": "firmware_config",
        "bitlocker_mutation": False,
        "bitlocker_recovery_risk": bool(bitlocker_recovery_risk),
        "requires_reboot": bool(requires_reboot),
        "rollback_value": rollback_value if rollback_value is not None else old_value,
        "preflight_status": "ready" if write_supported or op_required else "blocked",
        "operator_presence_required": bool(op_required),
        "one_change_per_run": True,
    }


def validate_change_against_inventory(
    change: Mapping[str, Any],
    inventory: Mapping[str, Any],
) -> dict[str, Any]:
    setting = str(change.get("setting") or "")
    items = inventory.get("settings") if isinstance(inventory.get("settings"), list) else []
    match = next((i for i in items if isinstance(i, dict) and i.get("setting") == setting), None)
    reasons: list[str] = []
    if match is None:
        reasons.append("setting_not_in_inventory")
    else:
        if change.get("write_method") and match.get("write_supported") is False:
            if "firmware_setup_ui" not in str(change.get("write_method")):
                reasons.append("write_not_supported_without_firmware_ui")
        if match.get("bitlocker_recovery_risk") and not change.get("bitlocker_recovery_risk"):
            reasons.append("bitlocker_recovery_risk_must_be_true")
    if change.get("bitlocker_mutation") is True:
        reasons.append("bitlocker_mutation_forbidden")
    if not change.get("rollback_value"):
        reasons.append("rollback_value_required")
    return {"ok": not reasons, "reasons": reasons, "setting": setting}


def write_inventory(path: Path, inventory: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dict(inventory), indent=2) + "\n", encoding="utf-8")
