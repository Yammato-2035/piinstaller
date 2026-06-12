"""
Deploy runtime router — read-only / plan-only POST routes via runner_api_facade (Phase D.11).

No runner_*.py imports, no execution, no runtime changes, allowed_to_execute stays false.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from deploy.runner_api_facade import build_plan_only_response

router = APIRouter(tags=["deploy-runtime"])


class DeployRuntimePlanOnlyRequest(BaseModel):
    explicit_overwrite: bool = False


@router.post("/runner/release/readiness")
async def post_deploy_runner_release_readiness(
    body: DeployRuntimePlanOnlyRequest,
) -> dict[str, Any]:
    _ = body
    facade = build_plan_only_response(
        "runner_release_readiness",
        response_code="DEPLOY_RUNNER_RELEASE_READINESS",
        decoupling_phase="d11",
    )
    return {
        "code": facade["code"],
        "readiness": facade,
        "warnings": list(facade.get("warnings") or []),
        "errors": list(facade.get("errors") or []),
    }


@router.post("/runner/lab-readiness/unblock-plan")
async def post_deploy_runner_lab_readiness_unblock_plan(
    body: DeployRuntimePlanOnlyRequest,
) -> dict[str, Any]:
    _ = body
    facade = build_plan_only_response(
        "runner_lab_readiness_plan",
        response_code="DEPLOY_RUNNER_LAB_UNBLOCK_PLAN",
        decoupling_phase="d11",
    )
    return {
        "code": facade["code"],
        "plan": facade,
        "warnings": list(facade.get("warnings") or []),
        "errors": list(facade.get("errors") or []),
    }


@router.post("/runner/lab-readiness/status")
async def post_deploy_runner_lab_readiness_status(
    body: DeployRuntimePlanOnlyRequest,
) -> dict[str, Any]:
    _ = body
    facade = build_plan_only_response(
        "runner_lab_readiness_status",
        response_code="DEPLOY_RUNNER_LAB_READINESS_STATUS",
        decoupling_phase="d11",
    )
    return {
        "code": facade["code"],
        "status": facade,
        "warnings": list(facade.get("warnings") or []),
        "errors": list(facade.get("errors") or []),
    }


@router.post("/runner/runtime-runbook/bundle")
async def post_deploy_runner_runtime_runbook_bundle(
    body: DeployRuntimePlanOnlyRequest,
) -> dict[str, Any]:
    _ = body
    facade = build_plan_only_response(
        "runner_runtime_runbook_bundle",
        response_code="DEPLOY_RUNNER_RUNTIME_RUNBOOK_BUNDLE",
        decoupling_phase="d11",
    )
    return {
        "code": facade["code"],
        "bundle": facade,
        "warnings": list(facade.get("warnings") or []),
        "errors": list(facade.get("errors") or []),
    }


@router.post("/runner/runtime-runbook/export")
async def post_deploy_runner_runtime_runbook_export(
    body: DeployRuntimePlanOnlyRequest,
) -> dict[str, Any]:
    _ = body
    facade = build_plan_only_response(
        "runner_runtime_runbook_export",
        response_code="DEPLOY_RUNNER_RUNTIME_RUNBOOK_EXPORT",
        decoupling_phase="d11",
    )
    return {
        "code": facade["code"],
        "export": facade,
        "warnings": list(facade.get("warnings") or []),
        "errors": list(facade.get("errors") or []),
    }


@router.post("/runner/runtime-results/validate")
async def post_deploy_runner_runtime_results_validate(
    body: DeployRuntimePlanOnlyRequest,
) -> dict[str, Any]:
    _ = body
    facade = build_plan_only_response(
        "runner_runtime_result_validator",
        response_code="DEPLOY_RUNNER_RUNTIME_RESULTS_VALIDATE",
        decoupling_phase="d11",
    )
    return {
        "code": facade["code"],
        "validation": facade,
        "warnings": list(facade.get("warnings") or []),
        "errors": list(facade.get("errors") or []),
    }


@router.post("/runner/lab-readiness/acceptance")
async def post_deploy_runner_lab_readiness_acceptance(
    body: DeployRuntimePlanOnlyRequest,
) -> dict[str, Any]:
    _ = body
    facade = build_plan_only_response(
        "runner_lab_acceptance_aggregator",
        response_code="DEPLOY_RUNNER_LAB_ACCEPTANCE",
        decoupling_phase="d11",
    )
    return {
        "code": facade["code"],
        "acceptance": facade,
        "warnings": list(facade.get("warnings") or []),
        "errors": list(facade.get("errors") or []),
    }


@router.post("/runner/lab-phase/consolidation")
async def post_deploy_runner_lab_phase_consolidation(
    body: DeployRuntimePlanOnlyRequest,
) -> dict[str, Any]:
    _ = body
    facade = build_plan_only_response(
        "runner_lab_phase_consolidation",
        response_code="DEPLOY_RUNNER_LAB_PHASE_CONSOLIDATION",
        decoupling_phase="d11",
    )
    return {
        "code": facade["code"],
        "consolidation": facade,
        "warnings": list(facade.get("warnings") or []),
        "errors": list(facade.get("errors") or []),
    }
