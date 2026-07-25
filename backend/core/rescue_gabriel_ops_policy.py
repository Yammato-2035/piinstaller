"""Gabriel ASUS ROG operator write/wipe policy (explicit operator authorization).

Windows NVMe (`windows_system`) stays write-blocked unless a separate
`WIPE WINDOWS SYSTEM` phrase is supplied. Stick USB updater writes are allowed
when gabriel ops are enabled.
"""

from __future__ import annotations

import re
from typing import Any, Mapping

CONTRACT_VERSION = 1

GABRIEL_OPS_CMDLINE = "setuphelfer_gabriel_ops_allowed=1"
INSTALL_ASSISTANT_CMDLINE = "setuphelfer_install_assistant=1"

LINUX_WIPE_PHRASE = "WIPE LINUX TARGET"
WINDOWS_WIPE_PHRASE = "WIPE WINDOWS SYSTEM"  # separate, never implied


def cmdline_has_flag(cmdline: str, flag: str) -> bool:
    return bool(re.search(rf"(?:^|\s){re.escape(flag)}(?:\s|$)", cmdline or ""))


def gabriel_ops_enabled(
    *,
    cmdline: str = "",
    machine: Mapping[str, Any] | None = None,
    operator_explicit: bool = False,
) -> bool:
    machine = machine or {}
    if operator_explicit:
        return True
    if cmdline_has_flag(cmdline, GABRIEL_OPS_CMDLINE):
        return True
    if bool(machine.get("gabriel_bound")) and str(machine.get("expected_profile") or "") in {
        "asus_rog_gabriel",
        "asus_rog",
    }:
        return True
    board = str(machine.get("board_name") or machine.get("board") or "").upper()
    product = str(machine.get("product_name") or machine.get("product") or "").upper()
    if "G513QM" in board or "G513QM" in product:
        return True
    return False


def gabriel_capabilities(
    *,
    cmdline: str = "",
    machine: Mapping[str, Any] | None = None,
    operator_explicit: bool = False,
) -> dict[str, Any]:
    enabled = gabriel_ops_enabled(
        cmdline=cmdline, machine=machine, operator_explicit=operator_explicit
    )
    return {
        "schema_version": 1,
        "contract_version": CONTRACT_VERSION,
        "gabriel_ops_enabled": enabled,
        "stick_write_allowed": enabled,
        "linux_target_write_allowed": enabled,
        "linux_target_wipe_allowed": enabled,
        "windows_system_write_allowed": False,
        "windows_system_wipe_allowed": False,
        "linux_install": "execute" if enabled else "preview",
        "linux_install_preview": True,
        "wipe": enabled,  # means linux_target wipe gate may open — not Windows
        "note": (
            "Operator authorized write/wipe on Gabriel ASUS ROG for linux_target + stick. "
            "Windows NVMe remains blocked without separate WIPE WINDOWS SYSTEM phrase."
        ),
    }


def authorize_linux_target_wipe(
    *,
    gabriel_ops: bool,
    confirm_identity: bool,
    confirm_destructive: bool,
    operator_phrase: str,
    linux_serial_hash: str,
    expected_linux_serial_hash: str,
    windows_serial_hash: str,
) -> dict[str, Any]:
    errors: list[str] = []
    if not gabriel_ops:
        errors.append("gabriel_ops_not_enabled")
    if not confirm_identity:
        errors.append("identity_confirmation_missing")
    if not confirm_destructive:
        errors.append("destructive_confirmation_missing")
    if (operator_phrase or "").strip() != LINUX_WIPE_PHRASE:
        errors.append("linux_wipe_phrase_missing_or_mismatch")
    if not linux_serial_hash or linux_serial_hash != expected_linux_serial_hash:
        errors.append("linux_target_hash_mismatch")
    if windows_serial_hash and windows_serial_hash == linux_serial_hash:
        errors.append("windows_and_linux_hash_collision")
    if errors:
        return {
            "status": "blocked",
            "wipe_authorized": False,
            "executed": False,
            "errors": errors,
            "windows_system_write_allowed": False,
        }
    return {
        "status": "wipe_authorized_linux_target",
        "wipe_authorized": True,
        "executed": False,
        "role": "linux_target",
        "errors": [],
        "windows_system_write_allowed": False,
        "message": (
            "Linux-target wipe authorized for Gabriel. Caller must re-check serial_hash "
            "immediately before any destructive tool. Windows NVMe remains blocked."
        ),
    }
