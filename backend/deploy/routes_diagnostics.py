"""
Deploy diagnostics router — plan-only POST routes via runner_api_facade (Phase D.8).

No runner_*.py imports, no execution, allowed_to_execute stays false.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from deploy.runner_api_facade import build_plan_only_response

router = APIRouter(tags=["deploy-diagnostics"])


class DeployDiagnosticsPlanOnlyRequest(BaseModel):
    explicit_overwrite: bool = False


@router.post("/runner/manual-runtime/failure-injection-matrix")
async def post_deploy_runner_manual_runtime_failure_injection_matrix(
    body: DeployDiagnosticsPlanOnlyRequest,
) -> dict[str, Any]:
    _ = body
    facade = build_plan_only_response(
        "runner_manual_runtime_failure_injection_matrix",
        response_code="DEPLOY_RUNNER_MANUAL_RUNTIME_FAILURE_INJECTION_MATRIX",
        decoupling_phase="d8",
    )
    return {
        "code": facade["code"],
        "matrix": facade,
        "warnings": list(facade.get("warnings") or []),
        "errors": list(facade.get("errors") or []),
    }


@router.post("/runner/manual-runtime/failure-execution-preview")
async def post_deploy_runner_manual_runtime_failure_execution_preview(
    body: DeployDiagnosticsPlanOnlyRequest,
) -> dict[str, Any]:
    _ = body
    facade = build_plan_only_response(
        "runner_manual_runtime_failure_execution_preview",
        response_code="DEPLOY_RUNNER_MANUAL_RUNTIME_FAILURE_EXECUTION_PREVIEW",
        decoupling_phase="d8",
    )
    return {
        "code": facade["code"],
        "preview": facade,
        "warnings": list(facade.get("warnings") or []),
        "errors": list(facade.get("errors") or []),
    }


@router.post("/runner/manual-runtime/failure-operator-checklists")
async def post_deploy_runner_manual_runtime_failure_operator_checklists(
    body: DeployDiagnosticsPlanOnlyRequest,
) -> dict[str, Any]:
    _ = body
    facade = build_plan_only_response(
        "runner_manual_runtime_failure_operator_checklists",
        response_code="DEPLOY_RUNNER_MANUAL_RUNTIME_FAILURE_OPERATOR_CHECKLISTS",
        decoupling_phase="d8",
    )
    return {
        "code": facade["code"],
        "checklists": facade,
        "warnings": list(facade.get("warnings") or []),
        "errors": list(facade.get("errors") or []),
    }


@router.post("/runner/manual-runtime/failure-test-sessions")
async def post_deploy_runner_manual_runtime_failure_test_sessions(
    body: DeployDiagnosticsPlanOnlyRequest,
) -> dict[str, Any]:
    _ = body
    facade = build_plan_only_response(
        "runner_manual_runtime_failure_test_sessions",
        response_code="DEPLOY_RUNNER_MANUAL_RUNTIME_FAILURE_TEST_SESSIONS",
        decoupling_phase="d8",
    )
    return {
        "code": facade["code"],
        "sessions": facade,
        "warnings": list(facade.get("warnings") or []),
        "errors": list(facade.get("errors") or []),
    }


@router.post("/runner/manual-runtime/failure-readiness-gate")
async def post_deploy_runner_manual_runtime_failure_readiness_gate(
    body: DeployDiagnosticsPlanOnlyRequest,
) -> dict[str, Any]:
    _ = body
    facade = build_plan_only_response(
        "runner_manual_runtime_failure_readiness_gate",
        response_code="DEPLOY_RUNNER_MANUAL_RUNTIME_FAILURE_READINESS_GATE",
        decoupling_phase="d8",
    )
    return {
        "code": facade["code"],
        "readiness": facade,
        "warnings": list(facade.get("warnings") or []),
        "errors": list(facade.get("errors") or []),
    }


@router.post("/runtime-identifier-zero-state-verification")
async def post_deploy_runtime_identifier_zero_state_verification(
    body: DeployDiagnosticsPlanOnlyRequest,
) -> dict[str, Any]:
    _ = body
    facade = build_plan_only_response(
        "runner_runtime_identifier_zero_state_verification",
        response_code="DEPLOY_RUNTIME_IDENTIFIER_ZERO_STATE_VERIFICATION",
        decoupling_phase="d8",
    )
    return {
        "code": facade["code"],
        "runtime_identifier_zero_state_verification": facade,
        "warnings": list(facade.get("warnings") or []),
        "errors": list(facade.get("errors") or []),
    }
