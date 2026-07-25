"""
Linux install execute gate — Freigabe OR Backup+Verify required.

No destructive I/O. Returns authorization status only.
"""

from __future__ import annotations

from typing import Any

from core.rescue_linux_distro_profiles_v1 import distro_install_allowed


GATE_SCHEMA = "linux-install-gate.v1"


def evaluate_install_gate(
  *,
  distro_profile_id: str,
  operator_approval: bool,
  backup_verified: bool,
  target_role: str,
  windows_write_requested: bool = False,
  iso_sha256_ok: bool = False,
  disk_roles_bound: bool = False,
  live_session_continuous: bool = True,
) -> dict[str, Any]:
  """
  Execute authorization for Installationsassistent + Partitionshelfer.

  Allowed when (operator_approval OR backup_verified) AND other hard checks.
  """
  blockers: list[str] = []
  if not distro_install_allowed(distro_profile_id):
    blockers.append("distro_not_supported_yet")
  if windows_write_requested or target_role == "windows":
    blockers.append("windows_nvme_write_forbidden")
  if target_role not in {"linux", "linux_target"}:
    blockers.append("target_role_invalid")
  if not disk_roles_bound:
    blockers.append("disk_roles_not_bound")
  if not iso_sha256_ok:
    blockers.append("iso_sha256_required")
  if not live_session_continuous:
    blockers.append("live_session_interrupted_umstecken")
  if not operator_approval and not backup_verified:
    blockers.append("approval_or_backup_required")

  authorized = not blockers
  return {
    "schema_version": GATE_SCHEMA,
    "distro_profile_id": distro_profile_id,
    "authorized": authorized,
    "executed": False,
    "mode": "handoff_only" if authorized else "blocked",
    "approval_path": (
      "operator_approval"
      if operator_approval
      else ("backup_verified" if backup_verified else "none")
    ),
    "blockers": blockers,
    "partitionshelfer_write_allowed": authorized,
    "windows_nvme_write_allowed": False,
    "message_de": (
      "Handoff freigegeben — keine automatische Destruktion."
      if authorized
      else "Installation blockiert — siehe blockers."
    ),
  }
