"""
Deploy registry router — read-only GET routes via runner_api_facade (Phase D.2).

No runner_*.py imports, no execution, no writes.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from deploy.runner_api_facade import (
    build_runner_catalog,
    build_runner_catalog_summary,
    build_runner_policy_warnings,
    get_runner_empty_result,
    get_runner_registry_entry,
)

router = APIRouter(prefix="/runners", tags=["deploy-runners-registry"])


@router.get("/catalog")
async def get_deploy_runners_catalog() -> dict[str, Any]:
    return build_runner_catalog()


@router.get("/summary")
async def get_deploy_runners_summary() -> dict[str, Any]:
    return build_runner_catalog_summary()


@router.get("/policy-warnings")
async def get_deploy_runners_policy_warnings() -> dict[str, Any]:
    return build_runner_policy_warnings()


@router.get("/{runner_id}/empty-result")
async def get_deploy_runner_empty_result(runner_id: str) -> dict[str, Any]:
    return get_runner_empty_result(runner_id)


@router.get("/{runner_id}")
async def get_deploy_runner_registry_entry(runner_id: str) -> dict[str, Any]:
    return get_runner_registry_entry(runner_id)
