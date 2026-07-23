"""Remote lab job contract for ASUS_ROG_GABRIEL_LAB (PI-RS-ASUS-LAB-CONTROL-006).

Extends rescue_remote concepts: target-bound, expiry, nonce, audit — no parallel platform.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Mapping

from core.rescue_asus_lab_authorization import PROFILE_ID, evaluate_machine_identity_match
from core.rescue_bitlocker_mutation_guard import evaluate_bitlocker_command_gate

SCHEMA_VERSION = "1"
CONTRACT_VERSION = 1

JOB_STATES = (
    "created",
    "validated",
    "identity_confirmed",
    "preflight",
    "running",
    "waiting_for_reboot",
    "reconnected",
    "verifying",
    "success",
    "failed",
    "blocked",
    "cancelled",
)

RISK_CLASSES = frozenset({"read_only", "controlled", "destructive", "firmware"})
ACTION_TYPES = frozenset({"shell", "disk", "restore", "efi", "secure_boot", "firmware", "diagnostic"})


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def build_lab_job(
    *,
    action_type: str,
    risk_class: str,
    target_fingerprint: str,
    requested_by: str,
    authorization_profile_hash: str,
    command: str | None = None,
    parameters: Mapping[str, Any] | None = None,
    run_id: str | None = None,
    ttl_seconds: int = 3600,
    signing_key: bytes | None = None,
    bitlocker_mutation: bool = False,
) -> dict[str, Any]:
    if action_type not in ACTION_TYPES:
        raise ValueError("invalid_action_type")
    if risk_class not in RISK_CLASSES:
        raise ValueError("invalid_risk_class")
    if bitlocker_mutation:
        raise ValueError("bitlocker_mutation_forbidden")
    now = _utc_now()
    job_id = f"labjob-{now.strftime('%Y%m%dT%H%M%SZ')}-{secrets.token_hex(4)}"
    body = {
        "schema_version": SCHEMA_VERSION,
        "contract_version": CONTRACT_VERSION,
        "job_id": job_id,
        "run_id": run_id,
        "target_profile": PROFILE_ID,
        "target_fingerprint": target_fingerprint,
        "action_type": action_type,
        "command": command,
        "parameters": dict(parameters or {}),
        "risk_class": risk_class,
        "bitlocker_mutation": False,
        "created_at": _iso(now),
        "expires_at": _iso(now + timedelta(seconds=ttl_seconds)),
        "nonce": secrets.token_hex(16),
        "requested_by": requested_by,
        "authorization_profile_hash": authorization_profile_hash,
        "state": "created",
    }
    payload = json.dumps(body, sort_keys=True, separators=(",", ":")).encode("utf-8")
    key = signing_key or b"setuphelfer-lab-dev-only"
    body["signature"] = hmac.new(key, payload, hashlib.sha256).hexdigest()
    body["command_hash"] = hashlib.sha256((command or "").encode("utf-8")).hexdigest() if command else None
    return body


def validate_lab_job(
    job: Mapping[str, Any],
    *,
    observed_identity: Mapping[str, Any],
    seen_nonces: set[str] | None = None,
    signing_key: bytes | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    reasons: list[str] = []
    if str(job.get("target_profile") or "") != PROFILE_ID:
        reasons.append("wrong_target_profile")
    if job.get("bitlocker_mutation") is True:
        reasons.append("bitlocker_mutation_forbidden")
    if str(job.get("action_type") or "") not in ACTION_TYPES:
        reasons.append("invalid_action_type")
    if str(job.get("risk_class") or "") not in RISK_CLASSES:
        reasons.append("invalid_risk_class")

    expires = str(job.get("expires_at") or "")
    try:
        exp_dt = datetime.strptime(expires, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        if (now or _utc_now()) > exp_dt:
            reasons.append("job_expired")
    except ValueError:
        reasons.append("expires_at_invalid")

    nonce = str(job.get("nonce") or "")
    if not nonce:
        reasons.append("nonce_missing")
    if seen_nonces is not None and nonce in seen_nonces:
        reasons.append("nonce_replay")

    # Verify signature over body without signature/command_hash fields used at build time.
    unsigned = {k: v for k, v in job.items() if k not in {"signature", "command_hash"}}
    payload = json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode("utf-8")
    key = signing_key or b"setuphelfer-lab-dev-only"
    expected = hmac.new(key, payload, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, str(job.get("signature") or "")):
        reasons.append("signature_invalid")

    match = evaluate_machine_identity_match(observed=observed_identity)
    if not match.get("grants_usable"):
        reasons.append(f"identity_{match.get('match')}")
    if str(job.get("target_fingerprint") or "") and str(job.get("target_fingerprint")) != str(
        observed_identity.get("machine_id") or ""
    ):
        reasons.append("fingerprint_mismatch")

    if job.get("action_type") == "shell" and job.get("command"):
        bl = evaluate_bitlocker_command_gate(str(job.get("command")))
        if bl.get("blocked"):
            reasons.append("bitlocker_mutation_forbidden")

    ok = not reasons
    return {
        "ok": ok,
        "state": "validated" if ok else "blocked",
        "reasons": reasons,
        "identity_match": match.get("match"),
        "job_id": job.get("job_id"),
        "bitlocker_mutation": False,
    }
