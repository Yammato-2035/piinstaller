from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Any

_base = Path(__file__).resolve().parent

_collector_spec = importlib.util.spec_from_file_location(
    "setuphelfer_inspect_collector_preflight",
    _base.parent / "inspect" / "collector.py",
)
if not (_collector_spec and _collector_spec.loader):
    raise ImportError("cannot load inspect collector for preflight routes")
_collector_mod = importlib.util.module_from_spec(_collector_spec)
sys.modules["setuphelfer_inspect_collector_preflight"] = _collector_mod
_collector_spec.loader.exec_module(_collector_mod)
collect_inspect_result = _collector_mod.collect_inspect_result

_pf_spec = importlib.util.spec_from_file_location("setuphelfer_preflight_backup", _base / "backup.py")
if not (_pf_spec and _pf_spec.loader):
    raise ImportError("cannot load preflight backup module")
_pf_mod = importlib.util.module_from_spec(_pf_spec)
_pf_spec.loader.exec_module(_pf_mod)
list_candidate_sources = _pf_mod.list_candidate_sources
create_backup_preview = _pf_mod.create_backup_preview
execute_backup_plan = _pf_mod.execute_backup_plan

router = APIRouter(prefix="/api/preflight", tags=["preflight"])




def _normalize_sources(payload: dict[str, object]) -> dict[str, object]:
    return {
        "code": payload.get("code") or "PREFLIGHT_SOURCE_FOUND",
        "sources": payload.get("sources") if isinstance(payload.get("sources"), list) else [],
        "warnings": payload.get("warnings") if isinstance(payload.get("warnings"), list) else [],
        "errors": payload.get("errors") if isinstance(payload.get("errors"), list) else [],
    }


def _normalize_preview(payload: dict[str, Any], target_device: str) -> dict[str, object]:
    return {
        "code": payload.get("code") or "PREFLIGHT_TARGET_BLOCKED",
        "plan_id": payload.get("plan_id"),
        "confirmation_token": payload.get("confirmation_token"),
        "target_device": payload.get("target_device") or target_device,
        "target_reason": payload.get("target_reason"),
        "requires_confirmation": bool(payload.get("requires_confirmation", False)),
        "sources": payload.get("sources") if isinstance(payload.get("sources"), list) else [],
        "warnings": payload.get("warnings") if isinstance(payload.get("warnings"), list) else [],
        "errors": payload.get("errors") if isinstance(payload.get("errors"), list) else [],
    }


def _normalize_execute(payload: dict[str, Any], plan_id: str) -> dict[str, object]:
    result: dict[str, Any] = {}
    for key in ("archive_path", "backup_code", "verify_code", "target_reason", "job_id"):
        if key in payload:
            result[key] = payload.get(key)
    return {
        "code": payload.get("code") or "PREFLIGHT_BACKUP_FAILED",
        "plan_id": payload.get("plan_id") or plan_id,
        "result": result,
        "details": payload.get("details") if isinstance(payload.get("details"), dict) else {},
        "errors": payload.get("errors") if isinstance(payload.get("errors"), list) else [],
    }
class PreviewRequest(BaseModel):
    target_device: str = Field(..., min_length=4)
    selected_source_ids: list[str] = Field(default_factory=list)


class ExecuteRequest(BaseModel):
    plan_id: str = Field(..., min_length=4)
    confirmation_token: str = Field(..., min_length=8)
    allow_empty_target: bool = False


@router.get("/sources")
async def get_preflight_sources() -> dict[str, object]:
    result = collect_inspect_result().model_dump()
    sources = list_candidate_sources(result)
    return _normalize_sources({"code": "PREFLIGHT_SOURCE_FOUND", "sources": sources})


@router.post("/backup/preview")
async def post_preflight_backup_preview(req: PreviewRequest) -> dict[str, object]:
    result = collect_inspect_result().model_dump()
    payload = create_backup_preview(
        target_device=req.target_device,
        inspect_result=result,
        selected_source_ids=req.selected_source_ids,
    )
    return _normalize_preview(payload, req.target_device)


@router.post("/backup/execute")
async def post_preflight_backup_execute(req: ExecuteRequest) -> dict[str, object]:
    result = collect_inspect_result().model_dump()
    payload = execute_backup_plan(
        plan_id=req.plan_id,
        confirmation_token=req.confirmation_token,
        inspect_result=result,
        allow_empty_target=req.allow_empty_target,
    )
    return _normalize_execute(payload, req.plan_id)
