"""
REST-Endpunkte für Remote-Sessions.
GET /api/sessions/me: aktuelle Session-Info (geschützt).
POST /api/sessions/refresh: Session verlängern (geschützt).
DELETE /api/sessions/me: Session beenden (geschützt).
"""

import logging
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Request, Depends

from core.auth import SessionContext, get_current_session
from core.settings import get_remote_settings
from models.session import SessionInfo
from storage.db import get_connection, audit_log_insert

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


def _session_ttl_seconds(request: Request) -> int:
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
            "SELECT expires_at FROM sessions WHERE id = ?",
            (session.session_id,),
        )
        row = cur.fetchone()
        expires_at = row[0] if row else ""
        return SessionInfo(
            session_id=session.session_id,
            device_id=session.device_id,
            role=session.role,
            expires_at=expires_at,
        )
    finally:
        conn.close()


@router.post("/refresh", response_model=SessionInfo)
async def sessions_refresh(
    request: Request,
    session: SessionContext = Depends(get_current_session),
):
    """Verlängert die Session um REMOTE_SESSION_TTL_SECONDS; refreshed_at wird aktualisiert."""
    ttl = _session_ttl_seconds(request)
    now_iso = datetime.now(timezone.utc).isoformat()
    new_expires = (datetime.now(timezone.utc) + timedelta(seconds=ttl)).isoformat()

    conn = get_connection()
    try:
        conn.execute(
            "UPDATE sessions SET expires_at = ?, refreshed_at = ? WHERE id = ?",
            (new_expires, now_iso, session.session_id),
        )
        conn.commit()
    finally:
        conn.close()

    try:
        audit_log_insert("session_refreshed", device_id=session.device_id, details=session.session_id)
    except Exception:
        pass
    return SessionInfo(
        session_id=session.session_id,
        device_id=session.device_id,
        role=session.role,
        expires_at=new_expires,
    )


@router.delete("/me")
async def sessions_revoke(session: SessionContext = Depends(get_current_session)):
    """Beendet die aktuelle Session (Token ungültig)."""
    conn = get_connection()
    try:
        conn.execute("DELETE FROM sessions WHERE id = ?", (session.session_id,))
        conn.commit()
    finally:
        conn.close()

    try:
        audit_log_insert("session_revoked", device_id=session.device_id, details=session.session_id)
    except Exception:
        pass
    return {"status": "success", "message": "Session beendet"}
