"""Telemetry server beta.0.1 — private skeleton. No remote command routes."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

FORBIDDEN_PREFIXES = (
    "/execute", "/command", "/shell", "/remote-help", "/fix",
    "/apply", "/write", "/mount", "/wipe", "/restore",
)

app = FastAPI(title="Setuphelfer Telemetry Server", version="0.1.0-beta")


def _load_contract_required_keys() -> set[str]:
    schema_path = Path(__file__).resolve().parents[2] / "public-contracts" / "docs" / "architecture" / "telemetry_rescue_beta_v2.schema.json"
    if not schema_path.is_file():
        return {"schema_version", "event_id", "stick", "privacy"}
    data = json.loads(schema_path.read_text(encoding="utf-8"))
    return set(data.get("required") or [])


@app.get("/health")
@app.get("/v1/telemetry/health")
def health() -> dict:
    return {"status": "ok", "service": "telemetry-server", "version": "0.1.0-beta"}


@app.post("/v1/telemetry/rescue/dry-run")
@app.post("/v1/telemetry/rescue/ingest")
async def ingest(request: Request) -> JSONResponse:
    path = request.url.path
    for prefix in FORBIDDEN_PREFIXES:
        if path.startswith(prefix):
            return JSONResponse(status_code=403, content={"error": "forbidden_route"})
    try:
        payload: dict[str, Any] = await request.json()
    except Exception:
        return JSONResponse(status_code=422, content={"accepted": False, "status": "rejected_schema"})
    if payload.get("schema_version") != "telemetry.rescue.beta.v2":
        return JSONResponse(status_code=422, content={"accepted": False, "status": "rejected_schema"})
    privacy = payload.get("privacy") or {}
    for key in ("contains_ip", "contains_mac", "contains_email", "contains_secrets"):
        if privacy.get(key) is True:
            return JSONResponse(status_code=422, content={"accepted": False, "status": "rejected_privacy"})
    if path.endswith("/dry-run"):
        return JSONResponse(status_code=200, content={"accepted": True, "status": "dry_run_ok", "event_id": payload.get("event_id")})
    beta = payload.get("beta") or {}
    if not beta.get("upload_allowed"):
        return JSONResponse(status_code=202, content={
            "accepted": False,
            "status": "quarantine_pending_agreement",
            "diagnostics_forwarded": False,
            "learning_export_allowed": False,
        })
    return JSONResponse(status_code=200, content={
        "accepted": True,
        "status": "accepted",
        "event_id": payload.get("event_id"),
        "redaction_applied": True,
        "diagnostics_forwarded": True,
        "learning_export_allowed": True,
        "message_de": "Akzeptiert",
        "message_en": "Accepted",
    })
