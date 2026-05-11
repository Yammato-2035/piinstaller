from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

_base = Path(__file__).resolve().parent

_orch_spec = importlib.util.spec_from_file_location("setuphelfer_rescue_orchestrator", _base / "orchestrator.py")
if not (_orch_spec and _orch_spec.loader):
    raise ImportError("cannot load rescue orchestrator")
_orch_mod = importlib.util.module_from_spec(_orch_spec)
_orch_spec.loader.exec_module(_orch_mod)
preview_rescue_restore = _orch_mod.preview_rescue_restore
execute_rescue_restore = _orch_mod.execute_rescue_restore
validate_restored_target = _orch_mod.validate_restored_target
build_rescue_report = _orch_mod.build_rescue_report

router = APIRouter(prefix="/api/rescue", tags=["rescue-preview"])


class RescuePreviewRequest(BaseModel):
    backup_path: str = Field(..., min_length=3)
    target_device: str | None = None
    target_path: str | None = None
    preflight_plan_id: str | None = None
    encryption_key_hex: str | None = None




class PostRestoreValidateRequest(BaseModel):
    target_path: str = Field(..., min_length=3)

class RescueExecuteRequest(BaseModel):
    preview_id: str = Field(..., min_length=6)
    confirmation_token: str = Field(..., min_length=8)
    backup_path: str = Field(..., min_length=3)
    target_device: str | None = None
    target_path: str | None = None
    encryption_key_hex: str | None = None


@router.post("/preview")
async def post_rescue_preview(body: RescuePreviewRequest) -> dict[str, Any]:
    return preview_rescue_restore(body.model_dump())


@router.post("/execute")
async def post_rescue_execute(body: RescueExecuteRequest) -> dict[str, Any]:
    return execute_rescue_restore(body.model_dump())


@router.post("/post-restore/validate")
async def post_rescue_post_restore_validate(body: PostRestoreValidateRequest) -> dict[str, Any]:
    validation = validate_restored_target(body.target_path)
    status = str(validation.get("status") or "failed")
    code = "POST_RESTORE_FAILED"
    if status == "valid":
        code = "POST_RESTORE_VALID"
    elif status == "warning":
        code = "POST_RESTORE_WARNING"
    return {
        "code": code,
        "validation": validation,
        "warnings": validation.get("warnings", []),
        "errors": validation.get("errors", []),
    }


class RescueReportRequest(BaseModel):
    inspect_result: dict[str, Any] = Field(default_factory=dict)
    safety_summary: dict[str, Any] = Field(default_factory=dict)
    preflight_result: dict[str, Any] = Field(default_factory=dict)
    preview_result: dict[str, Any] = Field(default_factory=dict)
    execute_result: dict[str, Any] = Field(default_factory=dict)
    post_restore: dict[str, Any] = Field(default_factory=dict)
    boot_capability: dict[str, Any] = Field(default_factory=dict)
    boot_repair_plan: dict[str, Any] = Field(default_factory=dict)


RescueReportRequest.model_rebuild()


@router.post("/report")
async def post_rescue_report(body: RescueReportRequest) -> dict[str, Any]:
    report = build_rescue_report(
        inspect_result=body.inspect_result or {},
        safety_summary=body.safety_summary or {},
        preflight_result=body.preflight_result or {},
        preview_result=body.preview_result or {},
        execute_result=body.execute_result or {},
        post_restore=body.post_restore or {},
        boot_capability=body.boot_capability or {},
        boot_repair_plan=body.boot_repair_plan or {},
    )
    status = str(report.get("report_status") or "unknown")
    code = "RESCUE_REPORT_UNKNOWN"
    if status == "ok":
        code = "RESCUE_REPORT_OK"
    elif status == "warning":
        code = "RESCUE_REPORT_WARNING"
    elif status == "failed":
        code = "RESCUE_REPORT_FAILED"
    return {
        "code": code,
        "report": report,
        "warnings": report.get("warnings", []),
        "errors": report.get("errors", []),
    }
