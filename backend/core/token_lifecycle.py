"""
Access-/Refresh-Token-Lebenszyklus für Remote-Companion (Paket 5, E-09).

Ersetzt das bisherige Modell (ein einziger Token, 24h gültig, im
localStorage) durch:

  - Access-Token: kurzlebig (Standard 5 Minuten), wird bei jeder
    API-/WebSocket-Anfrage verwendet. Diebstahl (z.B. via XSS) hat nur
    einen sehr kurzen Zeitraum Wirkung.
  - Refresh-Token: länger gültig (Standard = REMOTE_SESSION_TTL_SECONDS,
    Default 24h), wird NUR gegen einen neuen Access-Token eingetauscht.
    Bei jeder Nutzung wird der Refresh-Token rotiert (alter wird
    ungültig, neuer ausgegeben).
  - Reuse-Detection: Wird ein bereits rotierter (also nicht mehr aktueller,
    aber als "previous" bekannter) Refresh-Token erneut vorgelegt, ist das
    ein starkes Diebstahl-Signal — die gesamte Session wird sofort revoked
    und muss neu gepaart werden.

Alle Tokens werden ausschließlich gehashed gespeichert (siehe hash_token),
Klartext nur in der jeweiligen API-Response.
"""
from __future__ import annotations

import logging
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional

from storage.db import get_connection, hash_token

logger = logging.getLogger(__name__)

DEFAULT_ACCESS_TOKEN_TTL_SECONDS = 300  # 5 Minuten


@dataclass
class TokenPair:
    session_id: str
    access_token: str
    access_expires_at: str
    refresh_token: str
    refresh_expires_at: str


def _iso_expires_at(ttl_seconds: int) -> str:
    return (datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)).isoformat()


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def issue_token_pair(
    session_id: str,
    *,
    refresh_ttl_seconds: int,
    access_ttl_seconds: int = DEFAULT_ACCESS_TOKEN_TTL_SECONDS,
) -> TokenPair:
    """Erzeugt ein neues Access-/Refresh-Token-Paar und schreibt es (gehasht)
    in die bestehende Session-Zeile. Wird sowohl beim initialen Pairing-Claim
    als auch bei jeder Rotation aufgerufen."""
    access_token = secrets.token_urlsafe(32)
    refresh_token = secrets.token_urlsafe(32)
    access_expires_at = _iso_expires_at(access_ttl_seconds)
    refresh_expires_at = _iso_expires_at(refresh_ttl_seconds)

    conn = get_connection()
    try:
        cur = conn.execute("SELECT COALESCE(revoked, 0) FROM sessions WHERE id = ?", (session_id,))
        row = cur.fetchone()
        if row is not None and row[0]:
            raise ValueError(f"Session {session_id} ist revoked — keine neuen Tokens ausstellbar.")

        conn.execute(
            """UPDATE sessions
               SET access_token_hash = ?, access_expires_at = ?,
                   previous_refresh_token_hash = refresh_token_hash,
                   refresh_token_hash = ?, refresh_expires_at = ?,
                   refreshed_at = ?
               WHERE id = ?""",
            (
                hash_token(access_token), access_expires_at,
                hash_token(refresh_token), refresh_expires_at,
                _now_iso(), session_id,
            ),
        )
        conn.commit()
    finally:
        conn.close()

    return TokenPair(
        session_id=session_id,
        access_token=access_token,
        access_expires_at=access_expires_at,
        refresh_token=refresh_token,
        refresh_expires_at=refresh_expires_at,
    )


def validate_access_token(token: str) -> Optional[tuple[str, str, str]]:
    """Prüft einen Access-Token. Gibt (session_id, device_id, role) zurück
    oder None bei ungültig/abgelaufen/revoked."""
    if not token or not token.strip():
        return None
    token_hash = hash_token(token.strip())
    now_iso = _now_iso()
    conn = get_connection()
    try:
        cur = conn.execute(
            """SELECT s.id, s.device_id, p.role
               FROM sessions s
               LEFT JOIN remote_device_profiles p ON p.device_id = s.device_id
               WHERE s.access_token_hash = ? AND s.access_expires_at >= ?
                     AND COALESCE(s.revoked, 0) = 0""",
            (token_hash, now_iso),
        )
        row = cur.fetchone()
        if not row:
            return None
        return row[0], row[1], (row[2] or "viewer")
    finally:
        conn.close()


def rotate_with_refresh_token(token: str, *, refresh_ttl_seconds: int) -> Optional[TokenPair]:
    """Tauscht einen gültigen Refresh-Token gegen ein neues Token-Paar.

    Reuse-Detection: Wenn der vorgelegte Token mit
    previous_refresh_token_hash übereinstimmt (also bereits einmal rotiert
    wurde), wird das als Diebstahlsignal gewertet — die Session wird
    revoked und None zurückgegeben, unabhängig vom aktuellen Refresh-Token.
    """
    if not token or not token.strip():
        return None
    token_hash = hash_token(token.strip())
    now_iso = _now_iso()

    conn = get_connection()
    try:
        cur = conn.execute(
            """SELECT id, refresh_token_hash, refresh_expires_at, previous_refresh_token_hash
               FROM sessions
               WHERE COALESCE(revoked, 0) = 0
                     AND (refresh_token_hash = ? OR previous_refresh_token_hash = ?)""",
            (token_hash, token_hash),
        )
        rows = cur.fetchall()
        match_current = None
        match_reuse = None
        for session_id, current_hash, expires_at, previous_hash in rows:
            if current_hash == token_hash:
                match_current = (session_id, expires_at)
            elif previous_hash == token_hash:
                match_reuse = session_id

        if match_reuse is not None:
            logger.warning(
                "SICHERHEITSALARM: Wiederverwendung eines rotierten Refresh-Tokens "
                "erkannt (session_id=%s) — Session wird revoked.", match_reuse,
            )
            conn.execute("UPDATE sessions SET revoked = 1 WHERE id = ?", (match_reuse,))
            conn.commit()
            return None

        if match_current is None:
            return None
        session_id, expires_at = match_current
        if expires_at < now_iso:
            return None
    finally:
        conn.close()

    return issue_token_pair(session_id, refresh_ttl_seconds=refresh_ttl_seconds)
