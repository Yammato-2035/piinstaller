"""
Session-Authentifizierung für Remote-Companion.
Extrahiert Session-Token (Bearer oder query), validiert gegen DB (Hash, Ablauf), liefert Session-Kontext inkl. Rolle.
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from fastapi import Request, HTTPException, status

from storage.db import get_connection, hash_token

logger = logging.getLogger(__name__)


@dataclass
class SessionContext:
    """Kontext einer gültigen Session (nach Validierung)."""
    session_id: str
    device_id: str
    role: str  # viewer | controller | admin | sync


def validate_session_token(token: str) -> Optional[SessionContext]:
    """
    Validiert einen Session-Token (z. B. aus WebSocket query) und liefert SessionContext oder None.
    Für WebSocket: Token aus query ?session= übergeben; bei None/ungültig Verbindung ablehnen.
    """
    if not token or not token.strip():
        return None
    token_hash = hash_token(token.strip())
    now_iso = datetime.now(timezone.utc).isoformat()
    conn = get_connection()
    try:
        cur = conn.execute(
            """SELECT s.id, s.device_id, s.expires_at, p.role
               FROM sessions s
               LEFT JOIN remote_device_profiles p ON p.device_id = s.device_id
               WHERE s.session_token_hash = ?""",
            (token_hash,),
        )
        row = cur.fetchone()
        if not row:
            return None
        session_id, device_id, expires_at, role = row
        if expires_at < now_iso:
            return None
        return SessionContext(session_id=session_id, device_id=device_id, role=role or "viewer")
    finally:
        conn.close()


def _get_token_from_request(request: Request) -> Optional[str]:
    """Entnimmt Session-Token aus Authorization: Bearer oder query ?session=."""
    auth = request.headers.get("Authorization")
    if auth and auth.lower().startswith("bearer "):
        return auth[7:].strip()
    q = request.query_params.get("session") if request.query_params else None
    if q and isinstance(q, str) and q.strip():
        return q.strip()
    return None


async def get_current_session(request: Request) -> SessionContext:
    """
    FastAPI-Dependency: Liefert gültige Session oder 401.
    Ungültige/abgelaufene Sessions werden sauber abgewiesen.
    """
    token = _get_token_from_request(request)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session-Token fehlt (Authorization: Bearer oder ?session=)",
        )
    token_hash = hash_token(token)
    now_iso = datetime.now(timezone.utc).isoformat()

    conn = get_connection()
    try:
        cur = conn.execute(
            """SELECT s.id, s.device_id, s.expires_at, p.role
               FROM sessions s
               LEFT JOIN remote_device_profiles p ON p.device_id = s.device_id
               WHERE s.session_token_hash = ?""",
            (token_hash,),
        )
        row = cur.fetchone()
        if not row:
            logger.warning("Session validation: unbekannter oder ungültiger Token")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Ungültige Session")
        session_id, device_id, expires_at, role = row
        if expires_at < now_iso:
            logger.info("Session abgelaufen session_id=%s", session_id)
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session abgelaufen")
        role = role or "viewer"
        return SessionContext(session_id=session_id, device_id=device_id, role=role)
    finally:
        conn.close()


async def get_optional_session(request: Request) -> Optional[SessionContext]:
    """Dependency: Liefert Session oder None (für Endpoints, die mit und ohne Session funktionieren)."""
    token = _get_token_from_request(request)
    if not token:
        return None
    token_hash = hash_token(token)
    now_iso = datetime.now(timezone.utc).isoformat()
    conn = get_connection()
    try:
        cur = conn.execute(
            """SELECT s.id, s.device_id, p.role FROM sessions s
               LEFT JOIN remote_device_profiles p ON p.device_id = s.device_id
               WHERE s.session_token_hash = ? AND s.expires_at >= ?""",
            (token_hash, now_iso),
        )
        row = cur.fetchone()
        if not row:
            return None
        return SessionContext(session_id=row[0], device_id=row[1], role=row[2] or "viewer")
    finally:
        conn.close()
