"""Linux install on second NVMe — plan, ISO check, gates (PI-RS-INSTALL-ASSISTANT-001).

No write to Windows NVMe. Bootloader target = Linux ESP only.
install_execute never runs destructive tools without dual operator confirmation and identity match.
"""

from __future__ import annotations

import hashlib
import time
from typing import Any, Mapping

from core.rescue_gabriel_ops_policy import authorize_linux_target_wipe

CONTRACT_VERSION = 1
SCHEMA_VERSION = 1

# Canonical profile ids (plan) + legacy ASUS aliases
SUPPORTED_DISTROS = {
    "linux_mint": {"support": "supported", "arch": "amd64", "capability": "preview"},
    "linux-mint": {"support": "supported", "arch": "amd64", "capability": "preview"},
    "ubuntu_server_lts": {"support": "preview", "arch": "amd64", "capability": "preview"},
    "ubuntu-lts": {"support": "preview", "arch": "amd64", "capability": "preview"},
    "ubuntu_server": {"support": "preview", "arch": "amd64", "capability": "preview"},
    "debian": {"support": "preview", "arch": "amd64", "capability": "preview"},
    "debian-stable": {"support": "preview", "arch": "amd64", "capability": "preview"},
}

DISTRO_ALIASES = {
    "linux-mint": "linux_mint",
    "ubuntu-lts": "ubuntu_server_lts",
    "debian-stable": "debian",
}


def normalize_distro_id(distro: str | None) -> str | None:
    if not distro:
        return None
    d = distro.strip()
    return DISTRO_ALIASES.get(d, d)


def check_linux_iso(
    *,
    distro: str | None,
    version: str | None,
    iso_path: str | None,
    sha256_expected: str | None,
    sha256_actual: str | None,
    signature_ok: bool | None = None,
    official_source: str | None = None,
) -> dict[str, Any]:
    if not distro:
        return {
            "schema_version": SCHEMA_VERSION,
            "status": "ready_for_distro_selection",
            "install_allowed": False,
        }
    distro_id = normalize_distro_id(distro) or distro
    meta = SUPPORTED_DISTROS.get(distro_id) or SUPPORTED_DISTROS.get(distro or "")
    if not meta:
        return {
            "schema_version": SCHEMA_VERSION,
            "status": "unknown_distro",
            "support_level": "experimental",
            "install_allowed": False,
            "distro": distro_id,
        }
    if not iso_path and not sha256_actual:
        return {
            "schema_version": SCHEMA_VERSION,
            "contract_version": CONTRACT_VERSION,
            "status": "missing",
            "distro": distro_id,
            "version": version,
            "iso_path": iso_path,
            "architecture": meta["arch"],
            "support_level": meta["support"],
            "capability": meta.get("capability", "preview"),
            "sha256_ok": False,
            "signature_ok": signature_ok,
            "official_source": official_source,
            "install_allowed": False,
        }
    sha_ok = bool(
        sha256_expected and sha256_actual and sha256_expected.lower() == sha256_actual.lower()
    )
    status = "valid" if sha_ok and iso_path else "review_required"
    if sha256_expected and sha256_actual and not sha_ok:
        status = "corrupt"
    # P0: only linux_mint is execute-preparable; others stay preview stubs
    install_allowed = (
        status == "valid" and meta["support"] == "supported" and distro_id == "linux_mint"
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "contract_version": CONTRACT_VERSION,
        "status": status,
        "distro": distro_id,
        "version": version,
        "iso_path": iso_path,
        "architecture": meta["arch"],
        "support_level": meta["support"],
        "capability": meta.get("capability", "preview"),
        "sha256_ok": sha_ok,
        "signature_ok": signature_ok,
        "official_source": official_source,
        "install_allowed": install_allowed,
    }


def build_linux_partition_plan(
    *,
    target_identity: Mapping[str, Any],
    root_gib: int = 200,
    efi_mib: int = 1024,
    encrypt_luks: bool = False,
    allow_windows_role_as_target: bool = False,
) -> dict[str, Any]:
    role = str(target_identity.get("intended_role") or "linux_target")
    if role in {"windows", "windows_system"} and not allow_windows_role_as_target:
        return {
            "schema_version": SCHEMA_VERSION,
            "contract_version": CONTRACT_VERSION,
            "status": "blocked",
            "error": "windows_role_forbidden_as_mint_target",
            "extra_gate_required": "allow_windows_role_as_target",
            "write_allowed": False,
            "windows_nvme_write_allowed": False,
        }
    plan = {
        "schema_version": SCHEMA_VERSION,
        "contract_version": CONTRACT_VERSION,
        "status": "planned",
        "target_role": "linux_target",
        "target_identity": {
            "serial_hash": target_identity.get("serial_hash"),
            "model": target_identity.get("model"),
            "size_bytes": target_identity.get("size_bytes"),
            "pci_path": target_identity.get("pci_address") or target_identity.get("pci_path"),
            "serial_masked": target_identity.get("serial_masked"),
            "identity_key": target_identity.get("identity_key"),
        },
        "layout": [
            {
                "number": 1,
                "purpose": "linux_efi",
                "size_mib": efi_mib,
                "filesystem": "fat32",
                "flags": ["esp"],
            },
            {
                "number": 2,
                "purpose": "root",
                "size_gib": root_gib,
                "filesystem": "ext4",
                "mountpoint": "/",
            },
            {
                "number": 3,
                "purpose": "home",
                "size": "remaining",
                "filesystem": "ext4",
                "mountpoint": "/home",
            },
        ],
        "swap": {"type": "swapfile", "partition": False},
        "luks2": bool(encrypt_luks),
        "bootloader_target": "linux_nvme_esp_only",
        "windows_nvme_write_allowed": False,
        "windows_esp_forbidden": True,
        "write_allowed": False,
        "partitionshelfer_write_allowed": False,
    }
    plan["plan_hash"] = hashlib.sha256(repr(sorted(plan.items())).encode()).hexdigest()
    return plan


def linux_install_preflight(
    *,
    machine: Mapping[str, Any],
    windows_postcheck_ok: bool,
    windows_target: Mapping[str, Any],
    linux_target: Mapping[str, Any],
    iso: Mapping[str, Any],
    plan: Mapping[str, Any],
    nvme_health_linux: Mapping[str, Any],
    ac_power: bool = True,
    backup_ack: bool = False,
) -> dict[str, Any]:
    win_hash = str(windows_target.get("serial_hash") or "")
    lin_hash = str(linux_target.get("serial_hash") or "")
    checks = {
        "machine_bound_or_generic_ok": bool(
            machine.get("gabriel_bound")
            or machine.get("expected_profile")
            or machine.get("machine_id")
        ),
        "not_developer_host": not bool(machine.get("is_developer_workstation")),
        "windows_postcheck": windows_postcheck_ok,
        "targets_distinct": bool(win_hash and lin_hash and win_hash != lin_hash),
        "iso_ok": iso.get("install_allowed") is True,
        "plan_linux_esp": plan.get("bootloader_target") == "linux_nvme_esp_only",
        "windows_write_blocked": plan.get("windows_nvme_write_allowed") is False,
        "linux_nvme_healthy": nvme_health_linux.get("install_allowed") is True,
        "ac_power": ac_power,
        "backup_ack": backup_ack,
    }
    ok = all(checks.values())
    return {
        "schema_version": SCHEMA_VERSION,
        "status": "ready" if ok else "blocked",
        "checks": checks,
        "write_allowed_windows": False,
        "write_allowed_linux": False,
        "execute": False,
        "preflight_id": hashlib.sha256(
            f"{win_hash}:{lin_hash}:{plan.get('plan_hash')}".encode()
        ).hexdigest()[:24],
        "expires_at_epoch": int(time.time()) + 3600,
        "plan_hash": plan.get("plan_hash"),
    }


def linux_install_execute_gate(
    *,
    preflight: Mapping[str, Any],
    confirm_identity: bool,
    confirm_destructive: bool,
    current_linux_serial_hash: str,
    expected_linux_serial_hash: str,
    current_machine_id: str,
    expected_machine_id: str,
    operator_phrase: str | None = None,
    expected_operator_phrase: str = "INSTALL LINUX TARGET",
    now_epoch: int | None = None,
    force_execute: bool = False,
    gabriel_ops_allowed: bool = False,
    authorize_linux_wipe: bool = False,
    linux_wipe_phrase: str | None = None,
) -> dict[str, Any]:
    """Authorize Mint handoff. Optional Gabriel linux_target wipe authorization.

    API never performs the wipe itself; when authorized it returns wipe_authorized=True
    for an operator/tooling handoff. Windows NVMe stays write-blocked.
    """
    _ = force_execute
    now = int(now_epoch if now_epoch is not None else time.time())
    errors: list[str] = []
    if preflight.get("status") != "ready":
        errors.append("preflight_not_ready")
    if not confirm_identity:
        errors.append("identity_confirmation_missing")
    if not confirm_destructive:
        errors.append("destructive_confirmation_missing")
    phrase = (operator_phrase or "").strip()
    if phrase != expected_operator_phrase:
        errors.append("operator_phrase_missing_or_mismatch")
    expires = int(preflight.get("expires_at_epoch") or 0)
    if expires and now > expires:
        errors.append("preflight_expired")
    if current_linux_serial_hash != expected_linux_serial_hash:
        errors.append("target_serial_hash_changed")
    if current_machine_id != expected_machine_id:
        errors.append("machine_identity_changed")
    if errors:
        return {
            "status": "blocked",
            "executed": False,
            "mode": "handoff",
            "errors": errors,
            "emergency_stop": any(
                e in {"target_serial_hash_changed", "machine_identity_changed"} for e in errors
            ),
            "windows_nvme_write_allowed": False,
            "wipe_authorized": False,
        }

    wipe_authorized = False
    wipe_detail: dict[str, Any] | None = None
    if authorize_linux_wipe:
        wipe_detail = authorize_linux_target_wipe(
            gabriel_ops=gabriel_ops_allowed,
            confirm_identity=confirm_identity,
            confirm_destructive=confirm_destructive,
            operator_phrase=str(linux_wipe_phrase or ""),
            linux_serial_hash=current_linux_serial_hash,
            expected_linux_serial_hash=expected_linux_serial_hash,
            windows_serial_hash="",
        )
        wipe_authorized = bool(wipe_detail.get("wipe_authorized"))
        if not wipe_authorized:
            return {
                "status": "blocked",
                "executed": False,
                "mode": "handoff",
                "errors": list(wipe_detail.get("errors") or ["linux_wipe_not_authorized"]),
                "windows_nvme_write_allowed": False,
                "wipe_authorized": False,
                "wipe": wipe_detail,
            }

    return {
        "status": "handoff_authorized",
        "executed": False,
        "mode": "handoff",
        "errors": [],
        "message": (
            "Gates passed; physical Linux Mint installer handoff authorized. "
            + (
                "Linux-target wipe authorized for Gabriel operator tooling."
                if wipe_authorized
                else "No automatic wipe performed."
            )
        ),
        "windows_nvme_write_allowed": False,
        "wipe_authorized": wipe_authorized,
        "gabriel_ops_allowed": gabriel_ops_allowed,
        "bootloader_target": "linux_nvme_esp_only",
        "handoff": {
            "installer": "official_linux_mint",
            "partition_plan_hash": preflight.get("plan_hash"),
            "preflight_id": preflight.get("preflight_id"),
            "wipe_authorized": wipe_authorized,
        },
        "wipe": wipe_detail,
    }


def post_install_verify(
    *,
    linux_target: Mapping[str, Any],
    windows_target: Mapping[str, Any],
    linux_bootable: bool,
    windows_unchanged: bool,
    evidence_paths: list[str] | None = None,
) -> dict[str, Any]:
    win_hash = str(windows_target.get("serial_hash") or "")
    lin_hash = str(linux_target.get("serial_hash") or "")
    ok = bool(
        linux_bootable
        and windows_unchanged
        and win_hash
        and lin_hash
        and win_hash != lin_hash
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "status": "verified" if ok else "incomplete",
        "linux_bootable": linux_bootable,
        "windows_nvme_unchanged": windows_unchanged,
        "targets_distinct": bool(win_hash and lin_hash and win_hash != lin_hash),
        "evidence_paths": list(evidence_paths or []),
        "write_allowed": False,
    }
