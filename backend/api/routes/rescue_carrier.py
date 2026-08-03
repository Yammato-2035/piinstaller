"""
Read-only / preview-only 64-GB carrier feasibility API.

PI-RS-HW-COMPAT-PROVISION-001 Phase 14 (carrier half). No partitioning, no
``dd``/``mkfs``/``parted``/``sfdisk``/``sgdisk``/``wipefs`` call exists here.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Body

from rescue.carrier_capacity_planner import compute_capacity_plan, get_real_carrier_size_bytes
from rescue.carrier_layout import evaluate_carrier_strategy

router = APIRouter(tags=["rescue-carrier"])


@router.get("/api/rescue/carrier/status")
async def get_carrier_status() -> dict[str, Any]:
    return {
        "strategy_decision": evaluate_carrier_strategy(),
        "note": "Kein Zielmedium ausgewaehlt. Fuer eine reale Kapazitaetspruefung /api/rescue/carrier/layout-preview mit device_path aufrufen.",
    }


@router.post("/api/rescue/carrier/layout-preview")
async def post_carrier_layout_preview(payload: dict[str, Any] = Body(default={})) -> dict[str, Any]:
    device_path = payload.get("device_path")
    include_optional_components = payload.get("include_optional_components") or []

    carrier_size_bytes = payload.get("carrier_size_bytes")
    if carrier_size_bytes is None and device_path:
        carrier_size_bytes = get_real_carrier_size_bytes(device_path)

    if carrier_size_bytes is None:
        return {
            "layout_status": "review_required",
            "warnings": ["no_carrier_size_bytes_available_provide_device_path_or_carrier_size_bytes"],
        }

    plan = compute_capacity_plan(
        carrier_size_bytes=carrier_size_bytes, include_optional_components=include_optional_components
    )
    plan["strategy_decision"] = evaluate_carrier_strategy()
    return plan


__all__ = ["router"]
