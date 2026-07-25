"""
Rescue Linux install API — distro profiles, diagnosis, ASUS orchestration dry-run.
No destructive execute.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from core.rescue_asus_mint_orchestration_v1 import build_asus_mint_orchestration_plan
from core.rescue_linux_distro_profiles_v1 import list_distro_profiles
from core.rescue_linux_install_diagnosis_v1 import classify_install_diagnosis
from core.rescue_linux_install_gate_v1 import evaluate_install_gate

router = APIRouter(tags=["rescue-linux-install"])


class InstallGateBody(BaseModel):
  distro_profile_id: str = "linux_mint"
  operator_approval: bool = False
  backup_verified: bool = False
  target_role: str = "linux"
  iso_sha256_ok: bool = False
  disk_roles_bound: bool = False
  live_session_continuous: bool = True
  windows_write_requested: bool = False


class DiagnosisBody(BaseModel):
  bios_compare: dict[str, Any] = Field(default_factory=dict)
  assessment_issue_codes: list[str] = Field(default_factory=list)
  secure_boot: str | None = None
  iso_sha256_ok: bool | None = None
  disk_roles_bound: bool = False
  nvme_count: int = 0


class AsusOrchBody(BaseModel):
  windows_disk: dict[str, Any]
  linux_disk: dict[str, Any]
  iso_path: str | None = None
  sha256_expected: str | None = None
  sha256_actual: str | None = None
  operator_approval: bool = False
  backup_verified: bool = False
  assessment_issue_codes: list[str] = Field(default_factory=list)
  bios_compare: dict[str, Any] = Field(default_factory=dict)
  secure_boot: str | None = None
  machine: dict[str, Any] = Field(default_factory=dict)


@router.get("/linux-install/distro-profiles")
async def get_linux_distro_profiles() -> dict[str, Any]:
  return {
    "schema_version": "linux-distro-profiles.v1",
    "debian_live_is_stick_runtime": True,
    "profiles": list_distro_profiles(include_planned=True),
  }


@router.post("/linux-install/gate")
async def post_linux_install_gate(body: InstallGateBody) -> dict[str, Any]:
  return evaluate_install_gate(**body.model_dump())


@router.post("/linux-install/diagnosis")
async def post_linux_install_diagnosis(body: DiagnosisBody) -> dict[str, Any]:
  return classify_install_diagnosis(**body.model_dump())


@router.post("/linux-install/asus-mint-orchestration")
async def post_asus_mint_orchestration(body: AsusOrchBody) -> dict[str, Any]:
  return build_asus_mint_orchestration_plan(**body.model_dump())
