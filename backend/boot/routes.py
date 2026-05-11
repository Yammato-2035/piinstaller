from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from boot.capability import check_boot_capability
from boot.repair_plan import generate_boot_repair_plan
from boot.repair_execute import create_boot_repair_session, execute_boot_repair

router = APIRouter(prefix="/api/boot", tags=["boot-capability"])


class BootCapabilityRequest(BaseModel):
    target_path: str = Field(..., min_length=3)


BootCapabilityRequest.model_rebuild()


@router.post("/capability")
async def post_boot_capability(body: BootCapabilityRequest) -> dict[str, Any]:
    capability = check_boot_capability(body.target_path)
    status = str(capability.get("status") or "boot_unknown")
    code = "BOOT_CAPABILITY_UNKNOWN"
    if status == "boot_likely":
        code = "BOOT_CAPABILITY_LIKELY"
    elif status == "boot_warning":
        code = "BOOT_CAPABILITY_WARNING"
    elif status == "boot_failed":
        code = "BOOT_CAPABILITY_FAILED"
    return {
        "code": code,
        "capability": capability,
        "warnings": capability.get("warnings", []),
        "errors": capability.get("errors", []),
    }


class BootRepairPlanRequest(BaseModel):
    target_path: str = Field(..., min_length=3)
    inspect: dict[str, Any] = Field(default_factory=dict)
    post_verify: dict[str, Any] = Field(default_factory=dict)
    boot_capability: dict[str, Any] = Field(default_factory=dict)


BootRepairPlanRequest.model_rebuild()


@router.post("/repair/plan")
async def post_boot_repair_plan(body: BootRepairPlanRequest) -> dict[str, Any]:
    plan = generate_boot_repair_plan(
        target_path=body.target_path,
        inspect_result=body.inspect or {},
        post_verify=body.post_verify or {},
        boot_capability=body.boot_capability or {},
    )
    status = str(plan.get("plan_status") or "not_applicable")
    code = "BOOT_REPAIR_PLAN_NOT_APPLICABLE"
    if status == "ok":
        code = "BOOT_REPAIR_PLAN_OK"
    elif status == "review_required":
        code = "BOOT_REPAIR_PLAN_REVIEW_REQUIRED"
    return {
        "code": code,
        "plan": plan,
        "warnings": [],
        "errors": [],
    }


class BootRepairSessionRequest(BaseModel):
    target_path: str = Field(..., min_length=3)
    selected_action_code: str = Field(..., min_length=3)
    inspect: dict[str, Any] = Field(default_factory=dict)
    post_verify: dict[str, Any] = Field(default_factory=dict)
    boot_capability: dict[str, Any] = Field(default_factory=dict)
    boot_repair_plan: dict[str, Any] = Field(default_factory=dict)


class BootRepairExecuteRequest(BaseModel):
    repair_session_id: str = Field(..., min_length=6)
    confirmation_token: str = Field(..., min_length=8)
    action_code: str = Field(..., min_length=3)
    target_path: str = Field(..., min_length=3)


BootRepairSessionRequest.model_rebuild()
BootRepairExecuteRequest.model_rebuild()


@router.post("/repair/session")
async def post_boot_repair_session(body: BootRepairSessionRequest) -> dict[str, Any]:
    return create_boot_repair_session(
        target_path=body.target_path,
        selected_action_code=body.selected_action_code,
        inspect_result=body.inspect or {},
        post_verify=body.post_verify or {},
        boot_capability=body.boot_capability or {},
        boot_repair_plan=body.boot_repair_plan or {},
    )


@router.post("/repair/execute")
async def post_boot_repair_execute(body: BootRepairExecuteRequest) -> dict[str, Any]:
    return execute_boot_repair(body.model_dump())
