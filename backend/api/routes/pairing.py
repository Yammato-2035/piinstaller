"""
REST-Endpunkte für Pairing (QR-Code-Kopplung).
POST /api/pairing/create: Ticket anlegen, QR-Payload zurückgeben.
POST /api/pairing/claim: Einmal-Token einlösen (nur einmal, innerhalb TTL); Replay-Schutz durch status=claimed.
"""

import logging
import secrets
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse

from core.settings import get_remote_settings
from core.qr import build_pairing_payload, iso_expires_at
from models.pairing import PairingClaimRequest, PairingCreateResponse, PairingClaimResponse
from storage.db import get_connection, hash_token, audit_log_insert

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/pairing", tags=["pairing"])


def _get_remote_config(request: Request) -> dict[str, Any]:
    """Liefert die Remote-Konfiguration aus app.state (von app.py gesetzt)."""
    settings = getattr(request.app.state, "app_settings", None) or {}
    return get_remote_settings(settings)


def _get_device_id(request: Request) -> str:
    """Liefert die Geräte-ID des Pi (von app.py gesetzt)."""
    return getattr(request.app.state, "device_id", "") or "unknown-device"


@router.post("/create", response_model=PairingCreateResponse)
async def pairing_create(request: Request):
    """
    Erstellt ein Pairing-Ticket und liefert den QR-Payload.
    Pairing-Token wird nur gehashed in der DB gespeichert; Klartext nur im Response für die QR-Anzeige.
    """
    config = _get_remote_config(request)
    if not config.get("REMOTE_FEATURE_ENABLED"):
        raise HTTPException(status_code=403, detail="Remote-Companion ist deaktiviert")

    device_id = _get_device_id(request)
    ttl = int(config.get("REMOTE_PAIRING_TTL_SECONDS") or 300)
    base_url = (config.get("REMOTE_BASE_URL") or "").strip() or (config.get("REMOTE_PUBLIC_HOST") or "").strip()
    if not base_url and request.url:
        base_url = str(request.url.replace(path="", query=""))

    ticket_id = str(uuid.uuid4())
    pair_token = secrets.token_urlsafe(32)
    ticket_hash = hash_token(pair_token)
    created_at = datetime.now(timezone.utc).isoformat()
    expires_at = iso_expires_at(ttl)

    conn = get_connection()
    try:
        conn.execute(
            """INSERT INTO pairing_tickets (id, ticket_hash, created_at, expires_at, device_name, status)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (ticket_id, ticket_hash, created_at, expires_at, None, "pending"),
        )
        conn.commit()
    finally:
        conn.close()

    payload = build_pairing_payload(
        host=base_url or "unknown",
        device_id=device_id,
        pair_token=pair_token,
        expires_at=expires_at,
    )
    return PairingCreateResponse(ticket_id=ticket_id, payload=payload, expires_at=expires_at)


@router.post("/claim", response_model=PairingClaimResponse)
async def pairing_claim(body: PairingClaimRequest, request: Request):
    """
    Löst ein Pairing-Ticket ein (einmalig, innerhalb TTL).
    Replay-Schutz: Nach erfolgreichem Claim wird status=claimed gesetzt; erneuter Aufruf mit gleichem Token schlägt fehl.
    """
    config = _get_remote_config(request)
    if not config.get("REMOTE_FEATURE_ENABLED"):
        raise HTTPException(status_code=403, detail="Remote-Companion ist deaktiviert")

    pair_token = (body.pair_token or "").strip()
    if not pair_token:
        raise HTTPException(status_code=400, detail="pair_token fehlt")

    ticket_hash = hash_token(pair_token)
    now_iso = datetime.now(timezone.utc).isoformat()

    conn = get_connection()
    try:
        cur = conn.execute(
            """SELECT id, status, expires_at FROM pairing_tickets WHERE ticket_hash = ?""",
            (ticket_hash,),
        )
        row = cur.fetchone()
        if not row:
            logger.warning("Pairing claim: unbekannter oder ungültiger Token")
            return PairingClaimResponse(success=False, message="Ungültiges oder abgelaufenes Ticket")
        ticket_id, status, expires_at = row

        if status != "pending":
            logger.warning("Pairing claim: Ticket bereits verwendet (Replay?) ticket_id=%s", ticket_id)
            return PairingClaimResponse(success=False, message="Ticket wurde bereits verwendet")

        if expires_at < now_iso:
            conn.execute("UPDATE pairing_tickets SET status = ? WHERE id = ?", ("expired", ticket_id))
            conn.commit()
            return PairingClaimResponse(success=False, message="Ticket abgelaufen")

        conn.execute("UPDATE pairing_tickets SET status = ? WHERE id = ?", ("claimed", ticket_id))
        device_id = (body.device_id or "").strip() or str(uuid.uuid4())
        device_name = (body.device_name or "").strip() or None
        profile_id = str(uuid.uuid4())
        conn.execute(
            """INSERT OR REPLACE INTO remote_device_profiles (id, device_id, name, role, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (profile_id, device_id, device_name, "viewer", now_iso, now_iso),
        )
        session_ttl = int(config.get("REMOTE_SESSION_TTL_SECONDS") or 86400)
        session_id = str(uuid.uuid4())
        session_token = secrets.token_urlsafe(32)
        session_token_hash = hash_token(session_token)
        session_expires_at = iso_expires_at(session_ttl)
        conn.execute(
            """INSERT INTO sessions (id, session_token_hash, device_id, created_at, expires_at, refreshed_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (session_id, session_token_hash, device_id, now_iso, session_expires_at, None),
        )
        conn.commit()
    finally:
        conn.close()

    try:
        audit_log_insert("session_created", device_id=device_id, details=f"ticket_id={ticket_id}")
    except Exception:
        pass
    logger.info("Pairing claim erfolgreich device_id=%s ticket_id=%s", device_id, ticket_id)
    return PairingClaimResponse(
        success=True,
        message="Gerät erfolgreich gekoppelt",
        ticket_id=ticket_id,
        session_token=session_token,
    )
