"""Beta registration server — private skeleton (lab-safe, no DB required)."""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Allow importing public contracts when submodule present
_ROOT = Path(__file__).resolve().parents[1]
_CONTRACTS = _ROOT.parent / "public-contracts" / "backend"
if _CONTRACTS.is_dir() and str(_CONTRACTS) not in sys.path:
    sys.path.insert(0, str(_CONTRACTS.parent.parent / "backend"))
    sys.path.insert(0, str(_CONTRACTS.parent.parent))

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

try:
    from core.beta_agreement_gate_v1 import gate_upload
    from core.beta_stick_registration_contract_v1 import upload_blocked_for_stick, validate_stick_registry_entry
except ImportError:
    gate_upload = None  # type: ignore[misc, assignment]
    upload_blocked_for_stick = None  # type: ignore[misc, assignment]
    validate_stick_registry_entry = None  # type: ignore[misc, assignment]

app = FastAPI(title="Setuphelfer Beta Registration", version="0.1.0-beta")


class RegisterBody(BaseModel):
    email_hash: str = Field(..., min_length=8)
    mfa_method: str = "totp"


class UploadPermissionBody(BaseModel):
    stick_id: str
    agreement_valid: bool = False
    stick_status: str = "active"
    machine_fingerprint: str | None = None


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "beta-registration", "version": "0.1.0-beta"}


@app.get("/public/v1/beta/status")
def public_status() -> dict:
    return {
        "status": "beta_open",
        "registration_open": True,
        "mfa_required": True,
        "email_verification_required": True,
    }


@app.post("/public/v1/beta/register")
def register(body: RegisterBody) -> dict:
    return {"status": "pending_email_verification", "mfa_setup_required": True}


@app.post("/internal/v1/sticks/check-upload-permission")
def check_upload_permission(
    body: UploadPermissionBody,
    authorization: str | None = Header(default=None),
) -> dict:
    token = os.environ.get("BR_INTERNAL_API_TOKEN", "")
    if token and authorization != f"Bearer {token}":
        raise HTTPException(status_code=401, detail="unauthorized")
    if upload_blocked_for_stick and upload_blocked_for_stick(body.stick_status)[0]:
        return {"upload_allowed": False, "quarantine_required": True, "reason": body.stick_status}
    if gate_upload:
        gate = gate_upload(
            agreement_status="valid" if body.agreement_valid else "missing",
            telemetry_consent=True,
            mfa_enabled=True,
            email_verified=True,
        )
        return {
            "upload_allowed": gate["allowed"],
            "quarantine_required": gate.get("mode") == "quarantine",
            "reason_code": gate.get("reason"),
        }
    return {"upload_allowed": body.agreement_valid, "quarantine_required": not body.agreement_valid}


def create_app() -> FastAPI:
    return app
