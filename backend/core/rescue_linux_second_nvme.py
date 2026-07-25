"""Linux install on second NVMe — multi-distro plan, ISO check, gates.

No write to Windows NVMe. Bootloader target = Linux ESP only.
install_execute never runs destructive tools; returns handoff authorization only.
"""

from __future__ import annotations

import hashlib
import time
from typing import Any, Mapping

from core.rescue_linux_distro_profiles_v1 import (
  alias_to_profile_id,
  distro_install_allowed,
  get_distro_profile,
)
from core.rescue_linux_install_gate_v1 import evaluate_install_gate

CONTRACT_VERSION = 2
SCHEMA_VERSION = 2


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
  profile_id = alias_to_profile_id(distro) or distro
  meta = get_distro_profile(profile_id)
  if not meta:
    return {
      "schema_version": SCHEMA_VERSION,
      "status": "unknown_distro",
      "support_level": "experimental",
      "install_allowed": False,
      "distro": distro,
      "profile_id": profile_id,
    }
  sha_ok = bool(sha256_expected and sha256_actual and sha256_expected.lower() == sha256_actual.lower())
  status = "valid" if sha_ok and iso_path else "review_required"
  if sha256_expected and sha256_actual and not sha_ok:
    status = "corrupt"
  return {
    "schema_version": SCHEMA_VERSION,
    "contract_version": CONTRACT_VERSION,
    "status": status,
    "distro": distro,
    "profile_id": profile_id,
    "version": version,
    "iso_path": iso_path,
    "architecture": meta["arch"],
    "support_level": meta["support_level"],
    "sha256_ok": sha_ok,
    "signature_ok": signature_ok,
    "official_source": official_source,
    "install_allowed": status == "valid" and distro_install_allowed(profile_id),
  }


def build_linux_partition_plan(
  *,
  target_identity: Mapping[str, Any],
  root_gib: int = 200,
  efi_mib: int = 1024,
  encrypt_luks: bool = False,
  distro_profile_id: str = "linux_mint",
) -> dict[str, Any]:
  plan = {
    "schema_version": SCHEMA_VERSION,
    "contract_version": CONTRACT_VERSION,
    "distro_profile_id": distro_profile_id,
    "target_role": "linux",
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
    "partitionshelfer_required": True,
    "live_session_no_umstecken": True,
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
  operator_approval: bool = False,
  backup_verified: bool = False,
) -> dict[str, Any]:
  win_hash = str(windows_target.get("serial_hash") or "")
  lin_hash = str(linux_target.get("serial_hash") or "")
  profile_id = str(plan.get("distro_profile_id") or iso.get("profile_id") or "linux_mint")
  gate = evaluate_install_gate(
    distro_profile_id=profile_id,
    operator_approval=operator_approval,
    backup_verified=backup_verified,
    target_role="linux",
    windows_write_requested=False,
    iso_sha256_ok=bool(iso.get("sha256_ok") and iso.get("install_allowed")),
    disk_roles_bound=bool(win_hash and lin_hash and win_hash != lin_hash),
    live_session_continuous=True,
  )
  checks = {
    "machine_bound": bool(machine.get("gabriel_bound") or machine.get("expected_profile")),
    "not_developer_host": not bool(machine.get("is_developer_workstation")),
    "windows_postcheck": windows_postcheck_ok,
    "targets_distinct": bool(win_hash and lin_hash and win_hash != lin_hash),
    "iso_ok": iso.get("install_allowed") is True,
    "plan_linux_esp": plan.get("bootloader_target") == "linux_nvme_esp_only",
    "windows_write_blocked": plan.get("windows_nvme_write_allowed") is False,
    "linux_nvme_healthy": nvme_health_linux.get("install_allowed") is not False,
    "ac_power": ac_power,
    "approval_or_backup": gate.get("authorized") is True or operator_approval or backup_verified,
  }
  # Preflight ready for handoff planning even before approval — write still gated.
  planning_ok = all(
    v
    for k, v in checks.items()
    if k not in {"approval_or_backup", "machine_bound"}
  )
  return {
    "schema_version": SCHEMA_VERSION,
    "status": "ready" if planning_ok and gate.get("authorized") else ("planning_ok" if planning_ok else "blocked"),
    "checks": checks,
    "gate": gate,
    "write_allowed_windows": False,
    "write_allowed_linux": bool(gate.get("partitionshelfer_write_allowed")),
    "preflight_id": hashlib.sha256(f"{win_hash}:{lin_hash}:{plan.get('plan_hash')}".encode()).hexdigest()[:24],
    "expires_at_epoch": int(time.time()) + 3600,
    "plan_hash": plan.get("plan_hash"),
    "orchestration": "dev_laptop",
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
  now_epoch: int | None = None,
) -> dict[str, Any]:
  now = int(now_epoch if now_epoch is not None else time.time())
  errors: list[str] = []
  if preflight.get("status") not in {"ready"}:
    errors.append("preflight_not_ready")
  if not confirm_identity:
    errors.append("identity_confirmation_missing")
  if not confirm_destructive:
    errors.append("destructive_confirmation_missing")
  gate = preflight.get("gate") or {}
  if not gate.get("authorized"):
    errors.append("approval_or_backup_required")
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
      "errors": errors,
      "emergency_stop": any(
        e in {"target_serial_hash_changed", "machine_identity_changed"} for e in errors
      ),
    }
  return {
    "status": "handoff_authorized",
    "executed": False,
    "errors": [],
    "message": "Gates passed; physical Linux installer handoff authorized. No automatic wipe performed.",
    "windows_nvme_write_allowed": False,
    "bootloader_target": "linux_nvme_esp_only",
    "setuphelfer_bootstrap_required": True,
    "live_session_no_umstecken": True,
    "orchestration": "dev_laptop",
  }
