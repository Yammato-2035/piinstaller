"""
Rescue telemetry signing V1 — HMAC over canonical redacted JSON (mock-friendly).
"""

from __future__ import annotations

import hashlib
import hmac
import json
from typing import Any

SIGNING_VERSION = "telemetry.signing.v1"


def canonical_json(payload: dict[str, Any]) -> str:
  return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def payload_sha256(payload: dict[str, Any]) -> str:
  return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


def sign_payload_hmac(payload: dict[str, Any], *, secret: str, key_id: str = "mock") -> dict[str, Any]:
  digest = hmac.new(secret.encode("utf-8"), canonical_json(payload).encode("utf-8"), hashlib.sha256).hexdigest()
  return {
    "signing_version": SIGNING_VERSION,
    "attestation_mode": "hmac",
    "key_id": key_id,
    "payload_sha256": payload_sha256(payload),
    "signature": digest,
  }


def verify_payload_hmac(payload: dict[str, Any], signature: str, *, secret: str) -> bool:
  expected = hmac.new(secret.encode("utf-8"), canonical_json(payload).encode("utf-8"), hashlib.sha256).hexdigest()
  return hmac.compare_digest(expected, signature)
