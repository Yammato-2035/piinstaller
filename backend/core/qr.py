"""
QR-Payload für Pairing: einheitliches Format für den Inhalt des QR-Codes.
Das Frontend kodiert diesen Payload als QR; das Smartphone scannt und sendet pair_token beim Claim.
"""

from typing import Any
from datetime import datetime, timezone, timedelta


PAIRING_PAYLOAD_VERSION = 1
PAIRING_SCOPE = "remote"


def build_pairing_payload(
    *,
    host: str,
    device_id: str,
    pair_token: str,
    expires_at: str,
    scope: str = PAIRING_SCOPE,
    v: int = PAIRING_PAYLOAD_VERSION,
) -> dict[str, Any]:
    """
    Baut den QR-Payload für Pairing.
    pair_token: Einmal-Klartext-Token (wird nur hier und beim Claim verwendet; in der DB nur Hash).
    """
    return {
        "v": v,
        "host": host,
        "device_id": device_id,
        "pair_token": pair_token,
        "expires_at": expires_at,
        "scope": scope,
    }


def iso_expires_at(ttl_seconds: int) -> str:
    """Liefert expires_at als ISO-8601 (UTC) für jetzt + ttl_seconds."""
    when = datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)
    return when.isoformat()
