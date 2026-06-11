"""
Deploy governance router — plan-only POST routes via runner_api_facade (Phase D.5).

No runner_*.py imports, no execution, allowed_to_execute stays false (C.4/C.5).
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from deploy.runner_api_facade import build_plan_only_response

router = APIRouter(tags=["deploy-governance"])


class DeployRunnerNextPhaseGateRequest(BaseModel):
    placeholder: dict[str, Any] = Field(default_factory=dict)


class DeployVersionGovernanceStateRequest(BaseModel):
    previous_version: str = "1.5.0"
    strict_mode_phase: str = "laptop_failure_finalization_chain"
    phase_status: str = "completed"
    release_readiness: str = "internal_testing"
    completed_modules: list[str] = Field(default_factory=list)
    evidence_artifacts: list[str] = Field(default_factory=list)
    test_status: str = "green"
    changes: list[str] = Field(default_factory=list)
    explicit_overwrite: bool = False


class DeployVersionSourceOfTruthCheckRequest(BaseModel):
    explicit_overwrite: bool = False


@router.post("/runner/next-phase/gate")
async def post_deploy_runner_next_phase_gate(
    body: DeployRunnerNextPhaseGateRequest,
) -> dict[str, Any]:
    _ = body.placeholder or {}
    facade = build_plan_only_response(
        "runner_next_phase_gate",
        response_code="DEPLOY_RUNNER_NEXT_PHASE_GATE",
    )
    st = facade["status"]
    code = "DEPLOY_RUNNER_NEXT_PHASE_HOLD"
    if st == "ok":
        code = "DEPLOY_RUNNER_NEXT_PHASE_MANUAL_RUNTIME_ALLOWED"
    elif st == "blocked":
        code = "DEPLOY_RUNNER_NEXT_PHASE_BLOCKED"
    return {
        "code": code,
        "gate": facade,
        "warnings": list(facade.get("warnings") or []),
        "errors": list(facade.get("errors") or []),
    }


@router.post("/version-governance/state")
async def post_deploy_version_governance_state(
    body: DeployVersionGovernanceStateRequest,
) -> dict[str, Any]:
    _ = body
    facade = build_plan_only_response(
        "runner_version_governance",
        response_code="DEPLOY_VERSION_GOVERNANCE_STATE",
    )
    code = facade["code"]
    return {
        "code": code,
        "version_governance_state": facade,
        "warnings": list(facade.get("warnings") or []),
        "errors": list(facade.get("errors") or []),
    }


@router.post("/version-source-of-truth-check")
async def post_deploy_version_source_of_truth_check(
    body: DeployVersionSourceOfTruthCheckRequest,
) -> dict[str, Any]:
    _ = body
    facade = build_plan_only_response(
        "runner_version_source_of_truth_check",
        response_code="DEPLOY_VERSION_SOURCE_OF_TRUTH_CHECK",
    )
    return {
        "code": facade["code"],
        "version_source_of_truth_check": facade,
        "warnings": list(facade.get("warnings") or []),
        "errors": list(facade.get("errors") or []),
    }
