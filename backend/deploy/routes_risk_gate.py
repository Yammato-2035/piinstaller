"""
Deploy risk-gate router — read-only GET routes via runner_api_facade (Phase D.3).

No runner_*.py imports, no execution, allowed_to_execute stays false (C.4).
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from deploy.runner_api_facade import (
    build_runner_risk_gate_summary,
    get_runner_risk_gate_decision,
    list_runner_never_auto,
    list_runner_operator_required,
    list_runner_plan_allowed,
)

router = APIRouter(prefix="/runners", tags=["deploy-runners-risk-gate"])


@router.get("/risk-gate/summary")
async def get_deploy_runners_risk_gate_summary() -> dict[str, Any]:
    return build_runner_risk_gate_summary()


@router.get("/risk-gate/operator-required")
async def get_deploy_runners_operator_required() -> dict[str, Any]:
    return list_runner_operator_required()


@router.get("/risk-gate/never-auto")
async def get_deploy_runners_never_auto() -> dict[str, Any]:
    return list_runner_never_auto()


@router.get("/risk-gate/plan-allowed")
async def get_deploy_runners_plan_allowed() -> dict[str, Any]:
    return list_runner_plan_allowed()


@router.get("/{runner_id}/risk-gate")
async def get_deploy_runner_risk_gate(runner_id: str) -> dict[str, Any]:
    return get_runner_risk_gate_decision(runner_id)
