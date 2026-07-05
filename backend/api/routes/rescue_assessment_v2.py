"""
Rescue Assessment V2 API routes — read-only diagnostics and telemetry dry-run.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from core.rescue_master_assessment_bundle_v1 import build_master_assessment_bundle_v1
from core.rescue_network_connectivity_v2 import build_network_connectivity_v2
from core.rescue_repair_advice_engine_v1 import build_safe_action_plan
from core.rescue_system_assessment_v2 import build_system_assessment_v2
from core.rescue_telemetry_connectivity_v1 import build_telemetry_connectivity_v1
from core.rescue_telemetry_upload_v1 import upload_telemetry_payload_v1

router = APIRouter(tags=["rescue-assessment-v2"])


class TelemetryUploadRequest(BaseModel):
  payload: dict[str, Any] = Field(default_factory=dict)
  mode: str = "dry_run_local"
  stick_verified: bool = False
  agreement_valid: bool = False


@router.get("/system-assessment-v2")
async def get_system_assessment_v2() -> dict[str, Any]:
  return build_system_assessment_v2()


@router.get("/network-connectivity-v2")
async def get_network_connectivity_v2() -> dict[str, Any]:
  return build_network_connectivity_v2()


@router.get("/telemetry-connectivity-v1")
async def get_telemetry_connectivity_v1() -> dict[str, Any]:
  return build_telemetry_connectivity_v1()


@router.get("/safe-action-plan-v1")
async def get_safe_action_plan_v1() -> dict[str, Any]:
  assessment = build_system_assessment_v2()
  return build_safe_action_plan(
    assessment.get("issue_codes") or [],
    assessment.get("recommendation_codes"),
  )


@router.get("/master-assessment-bundle-v1")
async def get_master_assessment_bundle_v1() -> dict[str, Any]:
  return build_master_assessment_bundle_v1()


@router.post("/telemetry/upload-v1")
async def post_telemetry_upload_v1(body: TelemetryUploadRequest) -> dict[str, Any]:
  return upload_telemetry_payload_v1(
    body.payload,
    mode=body.mode,
    stick_verified=body.stick_verified,
    agreement_valid=body.agreement_valid,
    signing_secret=None,
  )
