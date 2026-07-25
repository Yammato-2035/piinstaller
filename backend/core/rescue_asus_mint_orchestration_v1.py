"""
ASUS ROG Mint-on-second-NVMe orchestration plan — Dev-Laptop driven, stick executes under gates.

No destructive I/O. Builds a dry-run orchestration bundle for the live stick session.
"""

from __future__ import annotations

from typing import Any, Mapping

from core.rescue_linux_distro_profiles_v1 import list_distro_profiles
from core.rescue_linux_install_diagnosis_v1 import classify_install_diagnosis
from core.rescue_linux_second_nvme import (
  build_linux_partition_plan,
  check_linux_iso,
  linux_install_preflight,
)
from core.rescue_nvme_install_target import normalize_nvme_entry

ORCH_SCHEMA = "asus-mint-second-nvme-orchestration.v1"


def build_asus_mint_orchestration_plan(
  *,
  windows_disk: Mapping[str, Any],
  linux_disk: Mapping[str, Any],
  iso_path: str | None = None,
  sha256_expected: str | None = None,
  sha256_actual: str | None = None,
  operator_approval: bool = False,
  backup_verified: bool = False,
  assessment_issue_codes: list[str] | None = None,
  bios_compare: Mapping[str, Any] | None = None,
  secure_boot: str | None = None,
  machine: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
  win = normalize_nvme_entry(windows_disk)
  lin = normalize_nvme_entry(linux_disk)
  win["intended_role"] = "windows"
  lin["intended_role"] = "linux"

  iso = check_linux_iso(
    distro="linux_mint",
    version=None,
    iso_path=iso_path,
    sha256_expected=sha256_expected,
    sha256_actual=sha256_actual,
  )
  plan = build_linux_partition_plan(target_identity=lin, distro_profile_id="linux_mint")
  diagnosis = classify_install_diagnosis(
    bios_compare=dict(bios_compare or {}),
    assessment_issue_codes=assessment_issue_codes,
    secure_boot=secure_boot,
    iso_sha256_ok=iso.get("sha256_ok"),
    disk_roles_bound=bool(win.get("serial_hash") and lin.get("serial_hash") and win["serial_hash"] != lin["serial_hash"]),
    nvme_count=2,
  )
  preflight = linux_install_preflight(
    machine=machine or {"expected_profile": "asus_rog_gabriel"},
    windows_postcheck_ok=True,
    windows_target=win,
    linux_target=lin,
    iso=iso,
    plan=plan,
    nvme_health_linux={"install_allowed": True},
    operator_approval=operator_approval,
    backup_verified=backup_verified,
  )
  return {
    "schema_version": ORCH_SCHEMA,
    "track": "asus_rog_second_nvme_mint",
    "orchestration": "dev_laptop",
    "live_session_no_umstecken": True,
    "distro_profiles_available": list_distro_profiles(include_planned=True),
    "selected_distro": "linux_mint",
    "windows_target": {k: win[k] for k in ("serial_hash", "serial_masked", "model", "size_bytes", "identity_key", "intended_role")},
    "linux_target": {k: lin[k] for k in ("serial_hash", "serial_masked", "model", "size_bytes", "identity_key", "intended_role")},
    "iso": iso,
    "partition_plan": plan,
    "diagnosis": diagnosis,
    "preflight": preflight,
    "setuphelfer_bootstrap": {
      "required": True,
      "components": ["setuphelfer_client", "telemetry_client_contract", "rescue_evidence_hooks"],
      "secrets_forbidden": True,
    },
    "cloud": {
      "telemetry_server": "private_github_and_ionos",
      "diagnostics_server": "private_github_and_ionos",
      "public_repo_contracts_only": True,
    },
    "execute": {
      "allowed": False,
      "reason": "operator_physical_handoff_required",
      "partitionshelfer_write_allowed": bool(preflight.get("write_allowed_linux")),
    },
  }
