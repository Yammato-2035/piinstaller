"""ASUS Gabriel lab authorization — machine-bound grants (PI-RS-ASUS-LAB-CONTROL-006).

Never activates on MSI, developer ASUS, or unknown fingerprints.
BitLocker mutation is always denied.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any, Mapping

import yaml

from core.rescue_machine_identity_profiles import (
    PROFILE_ASUS_ROG_GABRIEL,
    is_known_developer_asus,
)

PROFILE_ID = "ASUS_ROG_GABRIEL_LAB"
SCHEMA_VERSION = 1
CONTRACT_VERSION = 1

DEFAULT_PROFILE_PATH = Path(__file__).resolve().parents[2] / "config" / "lab-targets" / "asus-rog-gabriel.yaml"

MATCH_EXACT = "exact_match"
MATCH_PARTIAL = "partial_match"
MATCH_MISMATCH = "mismatch"
MATCH_UNKNOWN = "unknown"


def load_lab_target_profile(path: Path | None = None) -> dict[str, Any]:
    p = path or DEFAULT_PROFILE_PATH
    data = yaml.safe_load(p.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("lab_target_profile_invalid")
    return data


def profile_authorization_hash(profile: Mapping[str, Any]) -> str:
    auth = profile.get("authorization") if isinstance(profile.get("authorization"), dict) else {}
    blob = f"{profile.get('profile_id')}|{profile.get('machine_id')}|{sorted(auth.items())}"
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def evaluate_machine_identity_match(
    *,
    observed: Mapping[str, Any],
    profile: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Compare observed identity to ASUS_ROG_GABRIEL_LAB profile."""
    prof = dict(profile or load_lab_target_profile())
    reasons: list[str] = []
    board = str(observed.get("board_name") or "")
    product = str(observed.get("product_name") or "")
    manufacturer = str(observed.get("manufacturer") or observed.get("sys_vendor") or "")
    machine_id = str(observed.get("machine_id") or "")
    uuid_hash = str(observed.get("system_uuid_hash") or "")

    if is_known_developer_asus({"board_name": board, "product_name": product}):
        return {
            "schema_version": SCHEMA_VERSION,
            "match": MATCH_MISMATCH,
            "profile_id": PROFILE_ID,
            "reasons": ["developer_asus_blocked"],
            "grants_usable": False,
        }

    msi_markers = ("MSI", "MICRO-STAR")
    if any(m in manufacturer.upper() for m in msi_markers):
        return {
            "schema_version": SCHEMA_VERSION,
            "match": MATCH_MISMATCH,
            "profile_id": PROFILE_ID,
            "reasons": ["msi_not_asus_lab"],
            "grants_usable": False,
        }

    checks = {
        "manufacturer": "ASUS" in manufacturer.upper(),
        "board_g513qm": "G513QM" in board.upper() or "G513QM" in product.upper(),
        "machine_id": bool(machine_id) and machine_id == str(prof.get("machine_id") or ""),
        "system_uuid_hash": bool(uuid_hash)
        and uuid_hash == str(prof.get("system_uuid_hash") or ""),
    }
    for key, ok in checks.items():
        if not ok:
            reasons.append(f"fail:{key}")

    if not machine_id and not uuid_hash and not (checks["board_g513qm"] and checks["manufacturer"]):
        match = MATCH_UNKNOWN
    elif checks["board_g513qm"] and checks["manufacturer"] and checks["machine_id"] and checks["system_uuid_hash"]:
        match = MATCH_EXACT
    elif checks["board_g513qm"] and checks["manufacturer"]:
        match = MATCH_PARTIAL
    elif not machine_id and not uuid_hash:
        match = MATCH_UNKNOWN
    else:
        match = MATCH_MISMATCH

    grants = match == MATCH_EXACT
    return {
        "schema_version": SCHEMA_VERSION,
        "contract_version": CONTRACT_VERSION,
        "match": match,
        "profile_id": PROFILE_ID,
        "expected_profile": PROFILE_ASUS_ROG_GABRIEL,
        "checks": checks,
        "reasons": reasons,
        "grants_usable": grants,
        "authorization": dict(prof.get("authorization") or {}) if grants else {"bitlocker_mutation": False},
        "authorization_profile_hash": profile_authorization_hash(prof),
        "bitlocker_mutation": False,
    }


def assert_action_allowed(
    *,
    match_result: Mapping[str, Any],
    action: str,
    bitlocker_mutation: bool = False,
) -> dict[str, Any]:
    """Gate a lab action. BitLocker mutation always blocked."""
    if bitlocker_mutation or action.startswith("bitlocker_"):
        return {
            "ok": False,
            "blocked_reason": "bitlocker_mutation_forbidden",
            "action": action,
            "match": match_result.get("match"),
        }
    if not match_result.get("grants_usable"):
        return {
            "ok": False,
            "blocked_reason": "identity_grants_unavailable",
            "action": action,
            "match": match_result.get("match"),
        }
    auth = match_result.get("authorization") if isinstance(match_result.get("authorization"), dict) else {}
    mapping = {
        "bios_flash": "bios_flash",
        "disk_delete": "disk_delete",
        "repartition": "repartition",
        "internal_restore": "internal_restore",
        "windows_efi_change": "windows_efi_change",
        "secure_boot_key_management": "secure_boot_key_management",
        "shell": "unrestricted_shell",
        "mint_install": "mint_install_linux_lab_nvme",
    }
    key = mapping.get(action)
    if key is None:
        return {"ok": False, "blocked_reason": "unknown_action", "action": action}
    if not auth.get(key):
        return {"ok": False, "blocked_reason": f"grant_missing:{key}", "action": action}
    return {"ok": True, "blocked_reason": None, "action": action, "match": MATCH_EXACT}
