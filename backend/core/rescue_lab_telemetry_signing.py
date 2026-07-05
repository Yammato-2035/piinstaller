"""
PI-RS-TEL-001 — HMAC-v2 signing for Rescue Stick lab telemetry (TEL-012 compatible).
"""

from __future__ import annotations

import hashlib
import hmac
import json
import time
import uuid
from typing import Any

HMAC_HEADER_TIMESTAMP = "X-Setuphelfer-Timestamp"
HMAC_HEADER_SIGNATURE = "X-Setuphelfer-Signature"
HMAC_HEADER_CLIENT_ID = "X-Setuphelfer-Client-Id"
HMAC_HEADER_NONCE = "X-Setuphelfer-Nonce"


def build_nonce() -> str:
    return str(uuid.uuid4())


def build_timestamp() -> str:
    return str(int(time.time()))


def canonical_json_bytes(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def wire_json_bytes(payload: dict[str, Any]) -> bytes:
    """Serialization used for TEL-012 ingest body and signature (matches server tests)."""
    return json.dumps(payload, ensure_ascii=False).encode("utf-8")


def sign_hmac_v2(payload: dict[str, Any], secret: str, nonce: str, timestamp: str, *, canonical: bool = True) -> str:
    raw = canonical_json_bytes(payload) if canonical else wire_json_bytes(payload)
    message = f"{timestamp}.{nonce}.".encode("utf-8") + raw
    return hmac.new(secret.encode("utf-8"), message, hashlib.sha256).hexdigest()


def build_hmac_headers(client_id: str, payload: dict[str, Any], secret: str) -> dict[str, str]:
    nonce = build_nonce()
    timestamp = build_timestamp()
    signature = sign_hmac_v2(payload, secret, nonce, timestamp, canonical=False)
    return {
        HMAC_HEADER_TIMESTAMP: timestamp,
        HMAC_HEADER_SIGNATURE: signature,
        HMAC_HEADER_CLIENT_ID: client_id,
        HMAC_HEADER_NONCE: nonce,
        "Content-Type": "application/json",
    }
