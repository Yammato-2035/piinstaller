"""
WebSocket-Endpunkt für Live-Events (Eventbus).
WS /api/ws?session=TOKEN — Session-Validierung; nur berechtigte Sessions erhalten Events.
Sauberes Disconnect-/Cleanup-Handling.
"""

import json
import logging
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from core.auth import validate_session_token
from core.eventbus import get_eventbus

logger = logging.getLogger(__name__)

router = APIRouter(tags=["ws"])

# WebSocket close code: 4401 = Unauthorized (application-level)
WS_CLOSE_UNAUTHORIZED = 4401


@router.websocket("/api/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket-Verbindung: Query-Parameter session=TOKEN erforderlich.
    Bei ungültiger/abgelaufener Session: Schließen mit Code 4401.
    Nach Accept: Verbindung im Eventbus registriert; bei Disconnect wird entfernt (kein Memory-Leak).
    """
    query = websocket.query_params
    token = query.get("session") if query else None
    session = validate_session_token(token) if token else None
    if not session:
        await websocket.close(code=WS_CLOSE_UNAUTHORIZED, reason="Session fehlt oder ungültig")
        return

    await websocket.accept()
    eventbus = get_eventbus()
    conn_id = eventbus.add(websocket, session.session_id)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                msg = json.loads(data) if data.strip() else {}
                if isinstance(msg, dict) and msg.get("type") == "subscribe":
                    topics = msg.get("topics")
                    if isinstance(topics, list):
                        await eventbus.subscribe(conn_id, {str(t) for t in topics})
            except (json.JSONDecodeError, TypeError):
                pass
    except WebSocketDisconnect:
        logger.debug("WebSocket client disconnected conn_id=%s", conn_id[:8] if conn_id else "")
    except Exception as e:
        logger.warning("WebSocket error: %s", e)
    finally:
        await eventbus.remove(conn_id)
