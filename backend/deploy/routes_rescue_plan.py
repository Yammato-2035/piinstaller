"""
Deploy rescue plan router — plan-only rescue POST routes (Phase D.14).

Debian-live inputs, dry-build orchestration, and build-sandbox preparation plans.
No execute, no USB write, no ISO build.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from deploy.runner_rescue_build_sandbox_preparation import (
    build_rescue_build_cleanup_plan,
    build_rescue_build_sandbox_final_gate,
    build_rescue_build_sandbox_root,
    build_rescue_overlay_workspace_plan,
    build_rescue_sandbox_config_copy_plan,
    build_rescue_sandbox_runtime_copy_plan,
    validate_rescue_build_sandbox_safety,
)
from deploy.runner_rescue_debian_live_build_inputs import (
    build_debian_live_bootloader_templates,
    build_debian_live_build_inputs_final_gate,
    build_debian_live_config_structure,
    build_debian_live_hook_templates,
    build_debian_live_includes_ch_root,
    build_debian_live_package_lists,
    validate_debian_live_build_inputs_safety,
)
from deploy.runner_rescue_dry_build_orchestration import (
    build_rescue_dry_build_final_gate,
    build_rescue_dry_build_input_resolution,
    build_rescue_dry_build_stage_graph,
    build_rescue_package_resolution_plan,
    simulate_rescue_dry_build_execution,
    validate_rescue_build_order,
    validate_rescue_dry_build_safety,
)

router = APIRouter(tags=["deploy-rescue-plan"])


class DeployRescuePlanOverwriteRequest(BaseModel):
    explicit_overwrite: bool = False


@router.post("/rescue/debian-live/config-structure")
async def post_deploy_rescue_debian_live_config_structure(body: DeployRescuePlanOverwriteRequest) -> dict[str, Any]:
    res = build_debian_live_config_structure(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(res.get("rescue_debian_live_config_structure_status") or "blocked")
    code = "DEPLOY_RESCUE_DEBIAN_LIVE_CONFIG_STRUCTURE_BLOCKED"
    if st == "ok":
        code = "DEPLOY_RESCUE_DEBIAN_LIVE_CONFIG_STRUCTURE_OK"
    elif st == "review_required":
        code = "DEPLOY_RESCUE_DEBIAN_LIVE_CONFIG_STRUCTURE_REVIEW_REQUIRED"
    return {
        "code": code,
        "rescue_debian_live_config_structure": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
    }


@router.post("/rescue/debian-live/package-lists")
async def post_deploy_rescue_debian_live_package_lists(body: DeployRescuePlanOverwriteRequest) -> dict[str, Any]:
    res = build_debian_live_package_lists(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(res.get("rescue_debian_live_package_lists_status") or "blocked")
    code = "DEPLOY_RESCUE_DEBIAN_LIVE_PACKAGE_LISTS_BLOCKED"
    if st == "ok":
        code = "DEPLOY_RESCUE_DEBIAN_LIVE_PACKAGE_LISTS_OK"
    elif st == "review_required":
        code = "DEPLOY_RESCUE_DEBIAN_LIVE_PACKAGE_LISTS_REVIEW_REQUIRED"
    return {
        "code": code,
        "rescue_debian_live_package_lists": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
    }


@router.post("/rescue/debian-live/includes-chroot")
async def post_deploy_rescue_debian_live_includes_ch_root(body: DeployRescuePlanOverwriteRequest) -> dict[str, Any]:
    res = build_debian_live_includes_ch_root(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(res.get("rescue_debian_live_includes_chroot_status") or "blocked")
    code = "DEPLOY_RESCUE_DEBIAN_LIVE_INCLUDES_CHROOT_BLOCKED"
    if st == "ok":
        code = "DEPLOY_RESCUE_DEBIAN_LIVE_INCLUDES_CHROOT_OK"
    elif st == "review_required":
        code = "DEPLOY_RESCUE_DEBIAN_LIVE_INCLUDES_CHROOT_REVIEW_REQUIRED"
    return {
        "code": code,
        "rescue_debian_live_includes_chroot": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
    }


@router.post("/rescue/debian-live/bootloader-templates")
async def post_deploy_rescue_debian_live_bootloader_templates(body: DeployRescuePlanOverwriteRequest) -> dict[str, Any]:
    res = build_debian_live_bootloader_templates(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(res.get("rescue_debian_live_bootloader_templates_status") or "blocked")
    code = "DEPLOY_RESCUE_DEBIAN_LIVE_BOOTLOADER_TEMPLATES_BLOCKED"
    if st == "ok":
        code = "DEPLOY_RESCUE_DEBIAN_LIVE_BOOTLOADER_TEMPLATES_OK"
    elif st == "review_required":
        code = "DEPLOY_RESCUE_DEBIAN_LIVE_BOOTLOADER_TEMPLATES_REVIEW_REQUIRED"
    return {
        "code": code,
        "rescue_debian_live_bootloader_templates": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
    }


@router.post("/rescue/debian-live/hook-templates")
async def post_deploy_rescue_debian_live_hook_templates(body: DeployRescuePlanOverwriteRequest) -> dict[str, Any]:
    res = build_debian_live_hook_templates(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(res.get("rescue_debian_live_hook_templates_status") or "blocked")
    code = "DEPLOY_RESCUE_DEBIAN_LIVE_HOOK_TEMPLATES_BLOCKED"
    if st == "ok":
        code = "DEPLOY_RESCUE_DEBIAN_LIVE_HOOK_TEMPLATES_OK"
    elif st == "review_required":
        code = "DEPLOY_RESCUE_DEBIAN_LIVE_HOOK_TEMPLATES_REVIEW_REQUIRED"
    return {
        "code": code,
        "rescue_debian_live_hook_templates": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
    }


@router.post("/rescue/debian-live/input-safety")
async def post_deploy_rescue_debian_live_input_safety(body: DeployRescuePlanOverwriteRequest) -> dict[str, Any]:
    res = validate_debian_live_build_inputs_safety(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(res.get("rescue_debian_live_build_inputs_safety_status") or "blocked")
    code = "DEPLOY_RESCUE_DEBIAN_LIVE_INPUT_SAFETY_BLOCKED"
    if st == "ok":
        code = "DEPLOY_RESCUE_DEBIAN_LIVE_INPUT_SAFETY_OK"
    elif st == "review_required":
        code = "DEPLOY_RESCUE_DEBIAN_LIVE_INPUT_SAFETY_REVIEW_REQUIRED"
    return {
        "code": code,
        "rescue_debian_live_build_inputs_safety": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
    }


@router.post("/rescue/debian-live/final-gate")
async def post_deploy_rescue_debian_live_final_gate(body: DeployRescuePlanOverwriteRequest) -> dict[str, Any]:
    res = build_debian_live_build_inputs_final_gate(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(res.get("rescue_debian_live_build_inputs_final_gate_status") or "blocked")
    code = "DEPLOY_RESCUE_DEBIAN_LIVE_FINAL_GATE_BLOCKED"
    if st == "ready":
        code = "DEPLOY_RESCUE_DEBIAN_LIVE_FINAL_GATE_READY"
    elif st == "review_required":
        code = "DEPLOY_RESCUE_DEBIAN_LIVE_FINAL_GATE_REVIEW_REQUIRED"
    return {
        "code": code,
        "rescue_debian_live_build_inputs_final_gate": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
    }


@router.post("/rescue/dry-build/stage-graph")
async def post_deploy_rescue_dry_build_stage_graph(body: DeployRescuePlanOverwriteRequest) -> dict[str, Any]:
    res = build_rescue_dry_build_stage_graph(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(res.get("rescue_dry_build_stage_graph_status") or "blocked")
    code = "DEPLOY_RESCUE_DRY_BUILD_STAGE_GRAPH_BLOCKED"
    if st == "ok":
        code = "DEPLOY_RESCUE_DRY_BUILD_STAGE_GRAPH_OK"
    elif st == "review_required":
        code = "DEPLOY_RESCUE_DRY_BUILD_STAGE_GRAPH_REVIEW_REQUIRED"
    return {
        "code": code,
        "rescue_dry_build_stage_graph": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
    }


@router.post("/rescue/dry-build/input-resolution")
async def post_deploy_rescue_dry_build_input_resolution(body: DeployRescuePlanOverwriteRequest) -> dict[str, Any]:
    res = build_rescue_dry_build_input_resolution(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(res.get("rescue_dry_build_input_resolution_status") or "blocked")
    code = "DEPLOY_RESCUE_DRY_BUILD_INPUT_RESOLUTION_BLOCKED"
    if st == "ok":
        code = "DEPLOY_RESCUE_DRY_BUILD_INPUT_RESOLUTION_OK"
    elif st == "review_required":
        code = "DEPLOY_RESCUE_DRY_BUILD_INPUT_RESOLUTION_REVIEW_REQUIRED"
    return {
        "code": code,
        "rescue_dry_build_input_resolution": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
    }


@router.post("/rescue/dry-build/package-resolution")
async def post_deploy_rescue_dry_build_package_resolution(body: DeployRescuePlanOverwriteRequest) -> dict[str, Any]:
    res = build_rescue_package_resolution_plan(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(res.get("rescue_dry_build_package_resolution_status") or "blocked")
    code = "DEPLOY_RESCUE_DRY_BUILD_PACKAGE_RESOLUTION_BLOCKED"
    if st == "ok":
        code = "DEPLOY_RESCUE_DRY_BUILD_PACKAGE_RESOLUTION_OK"
    elif st == "review_required":
        code = "DEPLOY_RESCUE_DRY_BUILD_PACKAGE_RESOLUTION_REVIEW_REQUIRED"
    return {
        "code": code,
        "rescue_dry_build_package_resolution": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
    }


@router.post("/rescue/dry-build/build-order-validation")
async def post_deploy_rescue_dry_build_build_order_validation(body: DeployRescuePlanOverwriteRequest) -> dict[str, Any]:
    res = validate_rescue_build_order(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(res.get("rescue_dry_build_build_order_validation_status") or "blocked")
    code = "DEPLOY_RESCUE_DRY_BUILD_BUILD_ORDER_VALIDATION_BLOCKED"
    if st == "ok":
        code = "DEPLOY_RESCUE_DRY_BUILD_BUILD_ORDER_VALIDATION_OK"
    elif st == "review_required":
        code = "DEPLOY_RESCUE_DRY_BUILD_BUILD_ORDER_VALIDATION_REVIEW_REQUIRED"
    return {
        "code": code,
        "rescue_dry_build_build_order_validation": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
    }


@router.post("/rescue/dry-build/execution-simulation")
async def post_deploy_rescue_dry_build_execution_simulation(body: DeployRescuePlanOverwriteRequest) -> dict[str, Any]:
    res = simulate_rescue_dry_build_execution(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(res.get("rescue_dry_build_execution_simulation_status") or "blocked")
    code = "DEPLOY_RESCUE_DRY_BUILD_EXECUTION_SIMULATION_BLOCKED"
    if st == "ok":
        code = "DEPLOY_RESCUE_DRY_BUILD_EXECUTION_SIMULATION_OK"
    elif st == "review_required":
        code = "DEPLOY_RESCUE_DRY_BUILD_EXECUTION_SIMULATION_REVIEW_REQUIRED"
    return {
        "code": code,
        "rescue_dry_build_execution_simulation": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
    }


@router.post("/rescue/dry-build/final-gate")
async def post_deploy_rescue_dry_build_final_gate(body: DeployRescuePlanOverwriteRequest) -> dict[str, Any]:
    res = build_rescue_dry_build_final_gate(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(res.get("rescue_dry_build_final_gate_status") or "blocked")
    code = "DEPLOY_RESCUE_DRY_BUILD_FINAL_GATE_BLOCKED"
    if st == "ready":
        code = "DEPLOY_RESCUE_DRY_BUILD_FINAL_GATE_READY"
    elif st == "review_required":
        code = "DEPLOY_RESCUE_DRY_BUILD_FINAL_GATE_REVIEW_REQUIRED"
    return {
        "code": code,
        "rescue_dry_build_final_gate": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
    }


@router.post("/rescue/dry-build/safety-validation")
async def post_deploy_rescue_dry_build_safety_validation(body: DeployRescuePlanOverwriteRequest) -> dict[str, Any]:
    res = validate_rescue_dry_build_safety(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(res.get("rescue_dry_build_safety_validation_status") or "blocked")
    code = "DEPLOY_RESCUE_DRY_BUILD_SAFETY_VALIDATION_BLOCKED"
    if st == "ok":
        code = "DEPLOY_RESCUE_DRY_BUILD_SAFETY_VALIDATION_OK"
    elif st == "review_required":
        code = "DEPLOY_RESCUE_DRY_BUILD_SAFETY_VALIDATION_REVIEW_REQUIRED"
    return {
        "code": code,
        "rescue_dry_build_safety_validation": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
    }


@router.post("/rescue/build-sandbox/root")
async def post_deploy_rescue_build_sandbox_root(body: DeployRescuePlanOverwriteRequest) -> dict[str, Any]:
    res = build_rescue_build_sandbox_root(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(res.get("rescue_build_sandbox_root_status") or "blocked")
    code = "DEPLOY_RESCUE_BUILD_SANDBOX_ROOT_BLOCKED"
    if st == "ok":
        code = "DEPLOY_RESCUE_BUILD_SANDBOX_ROOT_OK"
    elif st == "review_required":
        code = "DEPLOY_RESCUE_BUILD_SANDBOX_ROOT_REVIEW_REQUIRED"
    return {
        "code": code,
        "rescue_build_sandbox_root": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
    }


@router.post("/rescue/build-sandbox/config-copy-plan")
async def post_deploy_rescue_build_sandbox_config_copy_plan(body: DeployRescuePlanOverwriteRequest) -> dict[str, Any]:
    res = build_rescue_sandbox_config_copy_plan(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(res.get("rescue_build_sandbox_config_copy_plan_status") or "blocked")
    code = "DEPLOY_RESCUE_BUILD_SANDBOX_CONFIG_COPY_PLAN_BLOCKED"
    if st == "ok":
        code = "DEPLOY_RESCUE_BUILD_SANDBOX_CONFIG_COPY_PLAN_OK"
    elif st == "review_required":
        code = "DEPLOY_RESCUE_BUILD_SANDBOX_CONFIG_COPY_PLAN_REVIEW_REQUIRED"
    return {
        "code": code,
        "rescue_build_sandbox_config_copy_plan": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
    }


@router.post("/rescue/build-sandbox/runtime-copy-plan")
async def post_deploy_rescue_build_sandbox_runtime_copy_plan(body: DeployRescuePlanOverwriteRequest) -> dict[str, Any]:
    res = build_rescue_sandbox_runtime_copy_plan(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(res.get("rescue_build_sandbox_runtime_copy_plan_status") or "blocked")
    code = "DEPLOY_RESCUE_BUILD_SANDBOX_RUNTIME_COPY_PLAN_BLOCKED"
    if st == "ok":
        code = "DEPLOY_RESCUE_BUILD_SANDBOX_RUNTIME_COPY_PLAN_OK"
    elif st == "review_required":
        code = "DEPLOY_RESCUE_BUILD_SANDBOX_RUNTIME_COPY_PLAN_REVIEW_REQUIRED"
    return {
        "code": code,
        "rescue_build_sandbox_runtime_copy_plan": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
    }


@router.post("/rescue/build-sandbox/overlay-workspace-plan")
async def post_deploy_rescue_build_sandbox_overlay_workspace_plan(body: DeployRescuePlanOverwriteRequest) -> dict[str, Any]:
    res = build_rescue_overlay_workspace_plan(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(res.get("rescue_build_sandbox_overlay_workspace_plan_status") or "blocked")
    code = "DEPLOY_RESCUE_BUILD_SANDBOX_OVERLAY_WORKSPACE_PLAN_BLOCKED"
    if st == "ok":
        code = "DEPLOY_RESCUE_BUILD_SANDBOX_OVERLAY_WORKSPACE_PLAN_OK"
    elif st == "review_required":
        code = "DEPLOY_RESCUE_BUILD_SANDBOX_OVERLAY_WORKSPACE_PLAN_REVIEW_REQUIRED"
    return {
        "code": code,
        "rescue_build_sandbox_overlay_workspace_plan": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
    }


@router.post("/rescue/build-sandbox/cleanup-plan")
async def post_deploy_rescue_build_sandbox_cleanup_plan(body: DeployRescuePlanOverwriteRequest) -> dict[str, Any]:
    res = build_rescue_build_cleanup_plan(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(res.get("rescue_build_cleanup_plan_status") or "blocked")
    code = "DEPLOY_RESCUE_BUILD_SANDBOX_CLEANUP_PLAN_BLOCKED"
    if st == "ok":
        code = "DEPLOY_RESCUE_BUILD_SANDBOX_CLEANUP_PLAN_OK"
    elif st == "review_required":
        code = "DEPLOY_RESCUE_BUILD_SANDBOX_CLEANUP_PLAN_REVIEW_REQUIRED"
    return {
        "code": code,
        "rescue_build_cleanup_plan": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
    }


@router.post("/rescue/build-sandbox/safety-validation")
async def post_deploy_rescue_build_sandbox_safety_validation(body: DeployRescuePlanOverwriteRequest) -> dict[str, Any]:
    res = validate_rescue_build_sandbox_safety(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(res.get("rescue_build_sandbox_safety_validation_status") or "blocked")
    code = "DEPLOY_RESCUE_BUILD_SANDBOX_SAFETY_VALIDATION_BLOCKED"
    if st == "ok":
        code = "DEPLOY_RESCUE_BUILD_SANDBOX_SAFETY_VALIDATION_OK"
    elif st == "review_required":
        code = "DEPLOY_RESCUE_BUILD_SANDBOX_SAFETY_VALIDATION_REVIEW_REQUIRED"
    return {
        "code": code,
        "rescue_build_sandbox_safety_validation": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
    }


@router.post("/rescue/build-sandbox/final-gate")
async def post_deploy_rescue_build_sandbox_final_gate(body: DeployRescuePlanOverwriteRequest) -> dict[str, Any]:
    res = build_rescue_build_sandbox_final_gate(explicit_overwrite=bool(body.explicit_overwrite))
    st = str(res.get("rescue_build_sandbox_final_gate_status") or "blocked")
    code = "DEPLOY_RESCUE_BUILD_SANDBOX_FINAL_GATE_BLOCKED"
    if st == "ready":
        code = "DEPLOY_RESCUE_BUILD_SANDBOX_FINAL_GATE_READY"
    elif st == "review_required":
        code = "DEPLOY_RESCUE_BUILD_SANDBOX_FINAL_GATE_REVIEW_REQUIRED"
    return {
        "code": code,
        "rescue_build_sandbox_final_gate": res,
        "warnings": list(res.get("warnings") or []),
        "errors": list(res.get("errors") or []),
    }
