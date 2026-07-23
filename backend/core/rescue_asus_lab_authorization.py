"""ASUS Gabriel lab authorization — machine-bound grants (PI-RS-ASUS-LAB-CONTROL-006).

Never activates on MSI, developer ASUS, or unknown fingerprints.
BitLocker mutation is always denied.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any, Mapping, Sequence

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


DESTRUCTIVE_ACTIONS = frozenset(
    {
        "disk_delete",
        "repartition",
        "internal_restore",
        "windows_efi_change",
        "secure_boot_key_management",
        "bios_flash",
        "mint_install",
    }
)


def evaluate_disk_fingerprint_gate(
    *,
    observed_disks: Sequence[Mapping[str, Any]] | None,
    profile: Mapping[str, Any] | None = None,
    required_role: str | None = None,
) -> dict[str, Any]:
    """Match expected NVMe identity hashes. Device names alone never pass."""
    prof = dict(profile or load_lab_target_profile())
    expected = [
        d
        for d in (prof.get("expected_internal_disks") or [])
        if isinstance(d, dict)
    ]
    observed = [d for d in (observed_disks or []) if isinstance(d, Mapping)]
    reasons: list[str] = []
    role_hits: dict[str, bool] = {}

    for exp in expected:
        role = str(exp.get("role") or "")
        want = str(exp.get("nvme_identity_hash") or "")
        if not role or not want:
            continue
        hit = any(
            str(obs.get("nvme_identity_hash") or obs.get("identity_hash") or "") == want
            for obs in observed
        )
        role_hits[role] = hit
        if not hit:
            reasons.append(f"disk_fingerprint_miss:{role}")

    if required_role and not role_hits.get(required_role):
        reasons.append(f"required_role_miss:{required_role}")

    # Reject obvious rescue-stick / SETUP_LOGS labels if presented as internal.
    for obs in observed:
        label = str(obs.get("label") or obs.get("fs_label") or "").upper()
        if label in {"SETUP_LOGS", "SETUPHELFER", "SETUPHELFER_LOGS"}:
            reasons.append("rescue_stick_excluded")

    ok = not reasons and (bool(role_hits) if expected else True)
    return {
        "schema_version": SCHEMA_VERSION,
        "ok": ok,
        "role_hits": role_hits,
        "reasons": reasons,
        "confirmed_required": any(not bool(d.get("confirmed")) for d in expected),
    }


def assert_action_allowed(
    *,
    match_result: Mapping[str, Any],
    action: str,
    bitlocker_mutation: bool = False,
    observed_disks: Sequence[Mapping[str, Any]] | None = None,
    required_disk_role: str | None = None,
    profile: Mapping[str, Any] | None = None,
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
        "diagnostic": None,
    }
    if action == "diagnostic":
        return {"ok": True, "blocked_reason": None, "action": action, "match": MATCH_EXACT}
    key = mapping.get(action)
    if key is None:
        return {"ok": False, "blocked_reason": "unknown_action", "action": action}
    if not auth.get(key):
        return {"ok": False, "blocked_reason": f"grant_missing:{key}", "action": action}

    if action in DESTRUCTIVE_ACTIONS:
        role = required_disk_role
        if role is None and action == "mint_install":
            role = "linux_lab_nvme"
        disk_gate = evaluate_disk_fingerprint_gate(
            observed_disks=observed_disks,
            profile=profile,
            required_role=role,
        )
        if disk_gate.get("confirmed_required"):
            return {
                "ok": False,
                "blocked_reason": "disk_roles_unconfirmed",
                "action": action,
                "match": match_result.get("match"),
                "disk_gate": disk_gate,
            }
        if not disk_gate.get("ok"):
            return {
                "ok": False,
                "blocked_reason": "disk_fingerprint_mismatch",
                "action": action,
                "match": match_result.get("match"),
                "disk_gate": disk_gate,
            }

    return {"ok": True, "blocked_reason": None, "action": action, "match": MATCH_EXACT}
