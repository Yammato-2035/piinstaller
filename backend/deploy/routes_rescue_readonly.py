"""
Deploy rescue readonly router — plan-only rescue POST routes (Phase D.13).

First safe slice: early rescue plan/gate routes only. No execute, no USB write, no ISO build.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from deploy.runner_rescue_debian_live_build_plan import build_rescue_debian_live_build_plan
from deploy.runner_rescue_live_os_base_decision import build_rescue_live_os_base_decision
from deploy.runner_rescue_mvp_scope_gate import build_rescue_mvp_scope_gate
from deploy.runner_rescue_stick_component_inventory import build_rescue_stick_component_inventory

router = APIRouter(tags=["deploy-rescue-readonly"])


class DeployRescueReadonlyOverwriteRequest(BaseModel):
    explicit_overwrite: bool = False


@router.post("/rescue/live-os-base-decision")
async def post_deploy_rescue_live_os_base_decision(
    body: DeployRescueReadonlyOverwriteRequest,
) -> dict[str, Any]:
    res = build_rescue_live_os_base_decision(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(res.get("rescue_live_os_base_decision_status") or "blocked")
    code = "DEPLOY_RESCUE_LIVE_OS_BASE_DECISION_BLOCKED"
    if st == "ok":
        code = "DEPLOY_RESCUE_LIVE_OS_BASE_DECISION_OK"
    elif st == "review_required":
        code = "DEPLOY_RESCUE_LIVE_OS_BASE_DECISION_REVIEW_REQUIRED"
    return {
        "code": code,
        "rescue_live_os_base_decision": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
    }


@router.post("/rescue/component-inventory")
async def post_deploy_rescue_component_inventory(
    body: DeployRescueReadonlyOverwriteRequest,
) -> dict[str, Any]:
    res = build_rescue_stick_component_inventory(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(res.get("rescue_stick_component_inventory_status") or "blocked")
    code = "DEPLOY_RESCUE_COMPONENT_INVENTORY_BLOCKED"
    if st == "ok":
        code = "DEPLOY_RESCUE_COMPONENT_INVENTORY_OK"
    elif st == "review_required":
        code = "DEPLOY_RESCUE_COMPONENT_INVENTORY_REVIEW_REQUIRED"
    return {
        "code": code,
        "rescue_stick_component_inventory": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
    }


@router.post("/rescue/mvp-scope-gate")
async def post_deploy_rescue_mvp_scope_gate(
    body: DeployRescueReadonlyOverwriteRequest,
) -> dict[str, Any]:
    res = build_rescue_mvp_scope_gate(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(res.get("rescue_mvp_scope_gate_status") or "blocked")
    code = "DEPLOY_RESCUE_MVP_SCOPE_GATE_BLOCKED"
    if st == "ok":
        code = "DEPLOY_RESCUE_MVP_SCOPE_GATE_OK"
    elif st == "review_required":
        code = "DEPLOY_RESCUE_MVP_SCOPE_GATE_REVIEW_REQUIRED"
    return {
        "code": code,
        "rescue_mvp_scope_gate": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
    }


@router.post("/rescue/debian-live-build-plan")
async def post_deploy_rescue_debian_live_build_plan(
    body: DeployRescueReadonlyOverwriteRequest,
) -> dict[str, Any]:
    res = build_rescue_debian_live_build_plan(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(res.get("rescue_debian_live_build_plan_status") or "blocked")
    code = "DEPLOY_RESCUE_DEBIAN_LIVE_BUILD_PLAN_BLOCKED"
    if st == "ok":
        code = "DEPLOY_RESCUE_DEBIAN_LIVE_BUILD_PLAN_OK"
    elif st == "review_required":
        code = "DEPLOY_RESCUE_DEBIAN_LIVE_BUILD_PLAN_REVIEW_REQUIRED"
    return {
        "code": code,
        "rescue_debian_live_build_plan": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
    }
