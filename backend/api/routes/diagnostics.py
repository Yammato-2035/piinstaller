from __future__ import annotations

from fastapi import APIRouter, HTTPException

from core.diagnostics.runner import (
    catalog,
    diagnosis_by_id,
    get_evidence_sample,
    get_evidence_schema,
    run_diagnostics,
)
from core.diagnostics.models import (
    DiagnosticsAnalyzeRequest,
    DiagnosticsAnalyzeResponse,
    EvidenceSampleResponse,
)

router = APIRouter(prefix="/api/diagnostics", tags=["diagnostics"])


@router.post("/analyze", response_model=DiagnosticsAnalyzeResponse)
async def post_diagnostics_analyze(body: DiagnosticsAnalyzeRequest) -> DiagnosticsAnalyzeResponse:
    return run_diagnostics(body)


@router.get("/catalog")
async def get_diagnostics_catalog() -> dict:
    return {"items": catalog(), "count": len(catalog())}


@router.get("/evidence/schema")
async def get_diagnostics_evidence_schema() -> dict:
    return get_evidence_schema()


@router.get("/evidence/sample", response_model=EvidenceSampleResponse)
async def get_diagnostics_evidence_sample() -> EvidenceSampleResponse:
    return get_evidence_sample()


@router.get("/{diagnosis_id}")
async def get_diagnosis_by_id(diagnosis_id: str) -> dict:
    item = diagnosis_by_id(diagnosis_id)
    if item is None:
        raise HTTPException(status_code=404, detail="diagnosis_not_found")
    return item
