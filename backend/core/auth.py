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

# Merk-Termin (siehe PAKET-5-ANWENDEN.md / claude-code-handoff): Legacy-Fallback
# auf das alte, langlebige Session-Token (vor Access-/Refresh-Token-Trennung)
# ist eine bewusst befristete Übergangslösung, kein Dauerzustand. Nach diesem
# Datum: Fallback-Zweige in validate_session_token()/get_current_session()
# entfernen, sobald alle aktiven Companion-Geräte neu gepaart sind.
LEGACY_TOKEN_FALLBACK_REMOVAL_DATE = "2026-08-11"


def _warn_if_legacy_fallback_overdue() -> None:
    if datetime.now(timezone.utc).date().isoformat() > LEGACY_TOKEN_FALLBACK_REMOVAL_DATE:
        logger.warning(
            "Legacy-Session-Token-Fallback wird genutzt, obwohl der Merk-Termin "
            "%s überschritten ist — bitte prüfen, ob der Fallback entfernt werden kann.",
            LEGACY_TOKEN_FALLBACK_REMOVAL_DATE,
        )


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

    Paket 5 (E-09): Prüft zuerst den neuen kurzlebigen Access-Token, mit
    Legacy-Fallback auf das alte Session-Token — siehe get_current_session()
    für dieselbe Übergangslogik.

    Hinweis WebSocket-Langlebigkeit: Der Access-Token gilt nur ~5 Minuten,
    eine WS-Verbindung kann aber deutlich länger offen bleiben. Diese
    Funktion validiert nur beim Verbindungsaufbau — sie kappt keine
    laufende Verbindung, wenn der Access-Token zwischenzeitlich abläuft.
    Das ist ein bewusster Kompromiss (Reconnect-Komplexität vs. Nutzen);
    sicherheitsrelevante Aktionen laufen ohnehin über die REST-Endpunkte
    mit frischer Token-Prüfung, nicht über den WS-Kanal selbst.
    """
    if not token or not token.strip():
        return None

    from core.token_lifecycle import validate_access_token
    access_match = validate_access_token(token.strip())
    if access_match:
        session_id, device_id, role = access_match
        return SessionContext(session_id=session_id, device_id=device_id, role=role)

    # Legacy-Fallback (Schema v1/v2, vor Paket 5)
    _warn_if_legacy_fallback_overdue()
    token_hash = hash_token(token.strip())
    now_iso = datetime.now(timezone.utc).isoformat()
    conn = get_connection()
    try:
        cur = conn.execute(
            """SELECT s.id, s.device_id, s.expires_at, p.role
               FROM sessions s
               LEFT JOIN remote_device_profiles p ON p.device_id = s.device_id
               WHERE s.session_token_hash = ? AND COALESCE(s.revoked, 0) = 0""",
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

    Paket 5 (E-09): Prüft zuerst den neuen kurzlebigen Access-Token
    (siehe core/token_lifecycle.py). Fällt für eine Übergangszeit auf das
    alte, langlebige Session-Token zurück, damit bereits vor diesem Update
    gepairte Geräte nicht sofort ausgesperrt werden — Legacy-Pfad sollte
    entfernt werden, sobald alle aktiven Companion-Geräte neu gepaart sind
    (Empfehlung: Enddatum festlegen, siehe PAKET-5-ANWENDEN.md).
    """
    token = _get_token_from_request(request)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session-Token fehlt (Authorization: Bearer oder ?session=)",
        )

    from core.token_lifecycle import validate_access_token
    access_match = validate_access_token(token)
    if access_match:
        session_id, device_id, role = access_match
        return SessionContext(session_id=session_id, device_id=device_id, role=role)

    # Legacy-Fallback (Schema v1/v2, vor Paket 5) — siehe Docstring oben.
    _warn_if_legacy_fallback_overdue()
    token_hash = hash_token(token)
    now_iso = datetime.now(timezone.utc).isoformat()

    conn = get_connection()
    try:
        cur = conn.execute(
            """SELECT s.id, s.device_id, s.expires_at, p.role
               FROM sessions s
               LEFT JOIN remote_device_profiles p ON p.device_id = s.device_id
               WHERE s.session_token_hash = ? AND COALESCE(s.revoked, 0) = 0""",
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
               WHERE s.session_token_hash = ? AND s.expires_at >= ? AND COALESCE(s.revoked, 0) = 0""",
            (token_hash, now_iso),
        )
        row = cur.fetchone()
        if not row:
            return None
        return SessionContext(session_id=row[0], device_id=row[1], role=row[2] or "viewer")
    finally:
        conn.close()
