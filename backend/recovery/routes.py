from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from recovery.minimal_plan import generate_recovery_minimal_plan
from recovery.minimal_execute import create_recovery_minimal_session, execute_recovery_minimal
from recovery.activation_plan import generate_recovery_activation_plan
from recovery.activation_execute import create_recovery_activation_session, execute_recovery_activation

router = APIRouter(prefix="/api/recovery", tags=["recovery-minimal-plan"])


class RecoveryMinimalPlanRequest(BaseModel):
    target_path: str = Field(..., min_length=3)
    inspect_result: dict[str, Any] = Field(default_factory=dict)
    boot_capability: dict[str, Any] = Field(default_factory=dict)
    post_restore: dict[str, Any] = Field(default_factory=dict)
    safety_summary: dict[str, Any] = Field(default_factory=dict)


RecoveryMinimalPlanRequest.model_rebuild()


@router.post("/minimal/plan")
async def post_recovery_minimal_plan(body: RecoveryMinimalPlanRequest) -> dict[str, Any]:
    plan = generate_recovery_minimal_plan(
        target_path=body.target_path,
        inspect_result=body.inspect_result or {},
        boot_capability=body.boot_capability or {},
        post_restore=body.post_restore or {},
        safety_summary=body.safety_summary or {},
    )
    status = str(plan.get("plan_status") or "not_applicable")
    code = "RECOVERY_MINIMAL_PLAN_NOT_APPLICABLE"
    if status == "ok":
        code = "RECOVERY_MINIMAL_PLAN_OK"
    elif status == "review_required":
        code = "RECOVERY_MINIMAL_PLAN_REVIEW_REQUIRED"
    elif status == "blocked":
        code = "RECOVERY_MINIMAL_PLAN_BLOCKED"
    return {
        "code": code,
        "plan": plan,
        "warnings": plan.get("warnings", []),
        "errors": plan.get("errors", []),
    }


class RecoveryMinimalSessionRequest(BaseModel):
    target_path: str = Field(..., min_length=3)
    selected_steps: list[str] = Field(default_factory=list)
    plan: dict[str, Any] = Field(default_factory=dict)


class RecoveryMinimalExecuteRequest(BaseModel):
    session_id: str = Field(..., min_length=6)
    confirmation_token: str = Field(..., min_length=8)
    target_path: str = Field(..., min_length=3)
    plan: dict[str, Any] = Field(default_factory=dict)


RecoveryMinimalSessionRequest.model_rebuild()
RecoveryMinimalExecuteRequest.model_rebuild()


@router.post("/minimal/session")
async def post_recovery_minimal_session(body: RecoveryMinimalSessionRequest) -> dict[str, Any]:
    return create_recovery_minimal_session(body.model_dump())


@router.post("/minimal/execute")
async def post_recovery_minimal_execute(body: RecoveryMinimalExecuteRequest) -> dict[str, Any]:
    return execute_recovery_minimal(body.model_dump())


class RecoveryActivationPlanRequest(BaseModel):
    target_path: str = Field(..., min_length=3)
    inspect_result: dict[str, Any] = Field(default_factory=dict)
    post_restore: dict[str, Any] = Field(default_factory=dict)
    boot_capability: dict[str, Any] = Field(default_factory=dict)
    recovery_minimal_plan: dict[str, Any] = Field(default_factory=dict)
    safety_summary: dict[str, Any] = Field(default_factory=dict)


RecoveryActivationPlanRequest.model_rebuild()


@router.post("/activation/plan")
async def post_recovery_activation_plan(body: RecoveryActivationPlanRequest) -> dict[str, Any]:
    plan = generate_recovery_activation_plan(
        target_path=body.target_path,
        inspect_result=body.inspect_result or {},
        post_restore=body.post_restore or {},
        boot_capability=body.boot_capability or {},
        recovery_minimal_plan=body.recovery_minimal_plan or {},
        safety_summary=body.safety_summary or {},
    )
    status = str(plan.get("plan_status") or "not_applicable")
    code = "RECOVERY_ACTIVATION_PLAN_NOT_APPLICABLE"
    if status == "ok":
        code = "RECOVERY_ACTIVATION_PLAN_OK"
    elif status == "review_required":
        code = "RECOVERY_ACTIVATION_PLAN_REVIEW_REQUIRED"
    elif status == "blocked":
        code = "RECOVERY_ACTIVATION_PLAN_BLOCKED"
    return {
        "code": code,
        "plan": plan,
        "warnings": plan.get("warnings", []),
        "errors": plan.get("errors", []),
    }


class RecoveryActivationSessionRequest(BaseModel):
    target_path: str = Field(..., min_length=3)
    selected_steps: list[str] = Field(default_factory=list)
    plan: dict[str, Any] = Field(default_factory=dict)


class RecoveryActivationExecuteRequest(BaseModel):
    activation_session_id: str = Field(..., min_length=6)
    confirmation_token: str = Field(..., min_length=8)
    target_path: str = Field(..., min_length=3)
    plan: dict[str, Any] = Field(default_factory=dict)
    ssh_public_key: str = Field(default="", max_length=8192)
    allow_lan_backend_bind: bool = False


RecoveryActivationSessionRequest.model_rebuild()
RecoveryActivationExecuteRequest.model_rebuild()


@router.post("/activation/session")
async def post_recovery_activation_session(body: RecoveryActivationSessionRequest) -> dict[str, Any]:
    return create_recovery_activation_session(body.model_dump())


@router.post("/activation/execute")
async def post_recovery_activation_execute(body: RecoveryActivationExecuteRequest) -> dict[str, Any]:
    return execute_recovery_activation(body.model_dump())
