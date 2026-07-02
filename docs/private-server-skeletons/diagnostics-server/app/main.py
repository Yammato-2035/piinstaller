"""Diagnostics / hardware DB server beta.0.1 — private skeleton."""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

PII_KEYS = frozenset({"email", "phone", "ip", "mac", "account_id"})

app = FastAPI(title="Setuphelfer Diagnostics Server", version="0.1.0-beta")


def _has_pii(obj: Any) -> bool:
    if isinstance(obj, dict):
        for k, v in obj.items():
            if str(k).lower() in PII_KEYS:
                return True
            if _has_pii(v):
                return True
    elif isinstance(obj, list):
        return any(_has_pii(i) for i in obj)
    return False


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "diagnostics-server", "version": "0.1.0-beta"}


@app.post("/v1/learning/import")
async def learning_import(request: Request) -> JSONResponse:
    try:
        payload = await request.json()
    except Exception:
        return JSONResponse(status_code=400, content={"import_status": "rejected_schema"})
    if _has_pii(payload):
        return JSONResponse(status_code=422, content={"import_status": "rejected_pii", "review_required": True})
    return JSONResponse(status_code=200, content={
        "import_status": "accepted",
        "review_required": True,
        "hardware_key": payload.get("hardware_key", "unknown"),
    })
