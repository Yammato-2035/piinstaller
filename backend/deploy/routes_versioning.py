"""
Deploy versioning router — plan-only POST routes via runner_api_facade (Phase D.10).

No runner_*.py imports, no execution, allowed_to_execute stays false (C.4/M.1).
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from deploy.runner_api_facade import build_plan_only_response

router = APIRouter(tags=["deploy-versioning"])


class DeployVersioningPlanOnlyRequest(BaseModel):
    explicit_overwrite: bool = False


@router.post("/setuphelfer-runtime-identifier-migration")
async def post_deploy_setuphelfer_runtime_identifier_migration(
    body: DeployVersioningPlanOnlyRequest,
) -> dict[str, Any]:
    _ = body
    facade = build_plan_only_response(
        "runner_setuphelfer_runtime_identifier_migration",
        response_code="DEPLOY_SETUPHELFER_RUNTIME_IDENTIFIER_MIGRATION",
        decoupling_phase="d10",
    )
    return {
        "code": facade["code"],
        "setuphelfer_runtime_identifier_migration": facade,
        "warnings": list(facade.get("warnings") or []),
        "errors": list(facade.get("errors") or []),
    }


@router.post("/setuphelfer-safe-rewrite-plan")
async def post_deploy_setuphelfer_safe_rewrite_plan(
    body: DeployVersioningPlanOnlyRequest,
) -> dict[str, Any]:
    _ = body
    facade = build_plan_only_response(
        "runner_setuphelfer_safe_rewrite_plan",
        response_code="DEPLOY_SETUPHELFER_SAFE_REWRITE_PLAN",
        decoupling_phase="d10",
    )
    return {
        "code": facade["code"],
        "setuphelfer_safe_rewrite_plan": facade,
        "warnings": list(facade.get("warnings") or []),
        "errors": list(facade.get("errors") or []),
    }


@router.post("/runtime-identifier-elimination-targets")
async def post_deploy_runtime_identifier_elimination_targets(
    body: DeployVersioningPlanOnlyRequest,
) -> dict[str, Any]:
    _ = body
    facade = build_plan_only_response(
        "runner_setuphelfer_runtime_identifier_elimination",
        response_code="DEPLOY_RUNTIME_IDENTIFIER_ELIMINATION_TARGETS",
        decoupling_phase="d10",
    )
    return {
        "code": facade["code"],
        "runtime_identifier_elimination_targets": facade,
        "warnings": list(facade.get("warnings") or []),
        "errors": list(facade.get("errors") or []),
    }


@router.post("/runtime-identifier-elimination-plan")
async def post_deploy_runtime_identifier_elimination_plan(
    body: DeployVersioningPlanOnlyRequest,
) -> dict[str, Any]:
    _ = body
    facade = build_plan_only_response(
        "runner_setuphelfer_runtime_identifier_elimination",
        response_code="DEPLOY_RUNTIME_IDENTIFIER_ELIMINATION_PLAN",
        decoupling_phase="d10",
    )
    return {
        "code": facade["code"],
        "runtime_identifier_elimination_plan": facade,
        "warnings": list(facade.get("warnings") or []),
        "errors": list(facade.get("errors") or []),
    }


@router.post("/runtime-compatibility-alias-validation")
async def post_deploy_runtime_compatibility_alias_validation(
    body: DeployVersioningPlanOnlyRequest,
) -> dict[str, Any]:
    _ = body
    facade = build_plan_only_response(
        "runner_setuphelfer_runtime_identifier_elimination",
        response_code="DEPLOY_RUNTIME_COMPATIBILITY_ALIAS_VALIDATION",
        decoupling_phase="d10",
    )
    return {
        "code": facade["code"],
        "runtime_compatibility_alias_validation": facade,
        "warnings": list(facade.get("warnings") or []),
        "errors": list(facade.get("errors") or []),
    }


@router.post("/runtime-identifier-patch-bump-preparation")
async def post_deploy_runtime_identifier_patch_bump_preparation(
    body: DeployVersioningPlanOnlyRequest,
) -> dict[str, Any]:
    _ = body
    facade = build_plan_only_response(
        "runner_runtime_identifier_patch_bump_preparation",
        response_code="DEPLOY_RUNTIME_IDENTIFIER_PATCH_BUMP_PREPARATION",
        decoupling_phase="d10",
    )
    return {
        "code": facade["code"],
        "runtime_identifier_patch_bump_preparation": facade,
        "warnings": list(facade.get("warnings") or []),
        "errors": list(facade.get("errors") or []),
    }


@router.post("/legacy-runtime-safe-migration-recommendations")
async def post_deploy_legacy_runtime_safe_migration_recommendations(
    body: DeployVersioningPlanOnlyRequest,
) -> dict[str, Any]:
    _ = body
    facade = build_plan_only_response(
        "runner_legacy_runtime_compatibility_validation",
        response_code="DEPLOY_LEGACY_RUNTIME_SAFE_MIGRATION_RECOMMENDATIONS",
        decoupling_phase="d10",
    )
    return {
        "code": facade["code"],
        "legacy_runtime_safe_migration_recommendations": facade,
        "warnings": list(facade.get("warnings") or []),
        "errors": list(facade.get("errors") or []),
    }


@router.post("/legacy-upgrade-path-matrix")
async def post_deploy_legacy_upgrade_path_matrix(
    body: DeployVersioningPlanOnlyRequest,
) -> dict[str, Any]:
    _ = body
    facade = build_plan_only_response(
        "runner_legacy_runtime_compatibility_validation",
        response_code="DEPLOY_LEGACY_UPGRADE_PATH_MATRIX",
        decoupling_phase="d10",
    )
    return {
        "code": facade["code"],
        "legacy_upgrade_path_matrix": facade,
        "warnings": list(facade.get("warnings") or []),
        "errors": list(facade.get("errors") or []),
    }
