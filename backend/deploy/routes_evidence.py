"""
Deploy evidence router — plan-only POST routes via runner_api_facade (Phase D.4).

No runner_*.py imports, no execution, allowed_to_execute stays false (C.4/C.5/C.6).
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from deploy.runner_api_facade import build_plan_only_response

router = APIRouter(tags=["deploy-evidence"])


class DeployEvidencePlanOnlyRequest(BaseModel):
    explicit_overwrite: bool = False


@router.post("/legacy-identifier-inventory")
async def post_deploy_legacy_identifier_inventory(
    body: DeployEvidencePlanOnlyRequest,
) -> dict[str, Any]:
    _ = body
    facade = build_plan_only_response(
        "runner_legacy_identifier_inventory",
        response_code="DEPLOY_LEGACY_IDENTIFIER_INVENTORY",
    )
    return {
        "code": facade["code"],
        "legacy_identifier_inventory": facade,
        "warnings": list(facade.get("warnings") or []),
        "errors": list(facade.get("errors") or []),
    }


@router.post("/legacy-identifier-hotspot-analysis")
async def post_deploy_legacy_identifier_hotspot_analysis(
    body: DeployEvidencePlanOnlyRequest,
) -> dict[str, Any]:
    _ = body
    facade = build_plan_only_response(
        "runner_legacy_identifier_hotspot_analysis",
        response_code="DEPLOY_LEGACY_IDENTIFIER_HOTSPOT_ANALYSIS",
        decoupling_phase="c6",
    )
    return {
        "code": facade["code"],
        "legacy_identifier_hotspot_analysis": facade,
        "warnings": list(facade.get("warnings") or []),
        "errors": list(facade.get("errors") or []),
    }


@router.post("/setuphelfer-identifier-consistency-check")
async def post_deploy_setuphelfer_identifier_consistency_check(
    body: DeployEvidencePlanOnlyRequest,
) -> dict[str, Any]:
    _ = body
    facade = build_plan_only_response(
        "runner_setuphelfer_identifier_consistency_check",
        response_code="DEPLOY_SETUPHELFER_IDENTIFIER_CONSISTENCY_CHECK",
        decoupling_phase="c6",
    )
    return {
        "code": facade["code"],
        "setuphelfer_identifier_consistency_check": facade,
        "warnings": list(facade.get("warnings") or []),
        "errors": list(facade.get("errors") or []),
    }


@router.post("/runner/manual-runtime/result-validator-seal-index")
async def post_deploy_runner_manual_runtime_validator_seal_index(
    body: DeployEvidencePlanOnlyRequest,
) -> dict[str, Any]:
    _ = body
    facade = build_plan_only_response(
        "runner_manual_runtime_validator_seal_index",
        response_code="DEPLOY_RUNNER_MANUAL_RUNTIME_VALIDATOR_SEAL_INDEX",
        decoupling_phase="c6",
    )
    return {
        "code": facade["code"],
        "index": facade,
        "warnings": list(facade.get("warnings") or []),
        "errors": list(facade.get("errors") or []),
    }


@router.post("/runner/manual-runtime/evidence-timeline")
async def post_deploy_runner_manual_runtime_evidence_timeline(
    body: DeployEvidencePlanOnlyRequest,
) -> dict[str, Any]:
    _ = body
    facade = build_plan_only_response(
        "runner_manual_runtime_evidence_timeline",
        response_code="DEPLOY_RUNNER_MANUAL_RUNTIME_EVIDENCE_TIMELINE",
        decoupling_phase="c6",
    )
    return {
        "code": facade["code"],
        "timeline": facade,
        "warnings": list(facade.get("warnings") or []),
        "errors": list(facade.get("errors") or []),
    }


@router.post("/runner/manual-runtime/evidence-final-snapshot")
async def post_deploy_runner_manual_runtime_evidence_final_snapshot(
    body: DeployEvidencePlanOnlyRequest,
) -> dict[str, Any]:
    _ = body
    facade = build_plan_only_response(
        "runner_manual_runtime_evidence_final_snapshot",
        response_code="DEPLOY_RUNNER_MANUAL_RUNTIME_EVIDENCE_FINAL_SNAPSHOT",
        decoupling_phase="c6",
    )
    return {
        "code": facade["code"],
        "snapshot": facade,
        "warnings": list(facade.get("warnings") or []),
        "errors": list(facade.get("errors") or []),
    }
