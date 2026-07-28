"""
REST-Endpunkte für Remote-Sessions.
GET /api/sessions/me: aktuelle Session-Info (geschützt).
POST /api/sessions/refresh: Refresh-Token gegen neues Access-/Refresh-Token-Paar tauschen (Paket 5, E-09).
DELETE /api/sessions/me: Session beenden (geschützt).
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status

from core.auth import SessionContext, get_current_session
from core.settings import get_remote_settings
from core.token_lifecycle import rotate_with_refresh_token
from models.session import SessionInfo, RefreshRequest, RefreshResponse
from storage.db import get_connection, audit_log_insert

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


def _refresh_ttl_seconds(request) -> int:
    """TTL aus App-Settings."""
    settings = getattr(request.app.state, "app_settings", None) or {}
    config = get_remote_settings(settings)
    return int(config.get("REMOTE_SESSION_TTL_SECONDS") or 86400)


@router.get("/me", response_model=SessionInfo)
async def sessions_me(session: SessionContext = Depends(get_current_session)):
    """Liefert die aktuelle Session-Info (device_id, role, expires_at)."""
    conn = get_connection()
    try:
        cur = conn.execute(
            "SELECT access_expires_at FROM sessions WHERE id = ?",
            (session.session_id,),
        )
        row = cur.fetchone()
        expires_at = row[0] if row and row[0] else ""
        return SessionInfo(
            session_id=session.session_id,
            device_id=session.device_id,
            role=session.role,
            expires_at=expires_at,
        )
    finally:
        conn.close()


@router.post("/refresh", response_model=RefreshResponse)
async def sessions_refresh(request: Request, body: RefreshRequest):
    """
    Tauscht einen gültigen Refresh-Token gegen ein neues Access-/Refresh-
    Token-Paar (Paket 5, E-09). Der alte Refresh-Token wird dabei ungültig
    (Rotation). Wird ein bereits rotierter Refresh-Token erneut vorgelegt,
    wird das als Diebstahlsignal gewertet: die Session wird revoked und
    diese Anfrage schlägt fehl — das Gerät muss neu gepaart werden.

    Bewusst OHNE get_current_session-Dependency: Der Access-Token kann zu
    diesem Zeitpunkt bereits abgelaufen sein (das ist der Normalfall, dafür
    existiert dieser Endpunkt ja) — validiert wird ausschließlich der
    mitgesendete Refresh-Token.
    """
    ttl = _refresh_ttl_seconds(request)
    pair = rotate_with_refresh_token(body.refresh_token, refresh_ttl_seconds=ttl)
    if pair is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh-Token ungültig, abgelaufen oder bereits verwendet — bitte neu pairen.",
        )
    try:
        audit_log_insert("session_refreshed", device_id=None, details=pair.session_id)
    except Exception:
        pass
    return RefreshResponse(
        access_token=pair.access_token,
        access_expires_at=pair.access_expires_at,
        refresh_token=pair.refresh_token,
        refresh_expires_at=pair.refresh_expires_at,
    )


@router.delete("/me")
async def sessions_revoke(session: SessionContext = Depends(get_current_session)):
    """Beendet die aktuelle Session (Token ungültig)."""
    conn = get_connection()
    try:
        conn.execute("UPDATE sessions SET revoked = 1 WHERE id = ?", (session.session_id,))
        conn.commit()
    finally:
        conn.close()

    try:
        audit_log_insert("session_revoked", device_id=session.device_id, details=session.session_id)
    except Exception:
        pass
    return {"status": "success", "message": "Session beendet"}
