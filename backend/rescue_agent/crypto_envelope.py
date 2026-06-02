from __future__ import annotations

import base64
import hashlib
import json
import secrets


def build_encrypted_envelope(
    *,
    plaintext_report: dict,
    session_id: str,
    agent_id: str,
    sender_public_key: str,
    recipient_key_id: str,
    created_at: str,
    allow_unencrypted_fallback: bool = False,
) -> dict:
    if allow_unencrypted_fallback:
        raise ValueError("unencrypted_fallback_blocked")
    if not recipient_key_id:
        raise ValueError("recipient_key_id_missing")
    report_json = json.dumps(plaintext_report, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    key_material = f"{sender_public_key}:{recipient_key_id}:{session_id}:{agent_id}".encode("utf-8")
    digest = hashlib.sha256(key_material + report_json.encode("utf-8")).digest()
    ciphertext = base64.b64encode(digest).decode("ascii")
    return {
        "envelope_version": "1.0",
        "alg": "X25519-Ed25519-AEAD",
        "sender_public_key": sender_public_key,
        "recipient_key_id": recipient_key_id,
        "nonce": secrets.token_hex(12),
        "ciphertext": ciphertext,
        "aad": {"session_id": session_id, "agent_id": agent_id, "created_at": created_at},
    }

