"""
Eventbus / Topic-System für WebSocket: Connection-Manager und Publish.
Events werden nur an berechtigte Sessions (verbundene Clients) gesendet.
Sauberes Disconnect-/Cleanup-Handling; keine hängenden Subscriptions.
"""

import asyncio
import logging
import uuid
from typing import Any, Dict, List, Optional, Set, Tuple

from fastapi import WebSocket

from models.events import EVENT_TOPICS, EventMessage

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    Verwaltet WebSocket-Verbindungen und Topic-Subscriptions.
    Pro Verbindung: connection_id, websocket, session_id, subscribed topics.
    Bei Disconnect: Entfernen aus der Registry (Cleanup, kein Memory-Leak).
    """

    def __init__(self) -> None:
        self._connections: Dict[str, Tuple[WebSocket, str, Set[str]]] = {}  # conn_id -> (ws, session_id, topics)
        self._lock = asyncio.Lock()

    def add(self, websocket: WebSocket, session_id: str, topics: Set[str] = None) -> str:
        """
        Registriert eine neue Verbindung. Topics optional; Default: alle EVENT_TOPICS.
        Gibt connection_id zurück (für spätere remove/subscribe).
        """
        conn_id = str(uuid.uuid4())
        subs = set(topics) if topics is not None else set(EVENT_TOPICS)
        self._connections[conn_id] = (websocket, session_id, subs)
        logger.info("WS connection added conn_id=%s session_id=%s", conn_id[:8], session_id[:8])
        return conn_id

    async def remove(self, connection_id: str) -> None:
        """Entfernt eine Verbindung (z. B. bei Disconnect). Cleanup."""
        async with self._lock:
            self._connections.pop(connection_id, None)
        logger.debug("WS connection removed conn_id=%s", connection_id[:8] if connection_id else "")

    async def subscribe(self, connection_id: str, topics: Set[str]) -> None:
        """Fügt Topics zur Subscription einer Verbindung hinzu."""
        async with self._lock:
            if connection_id in self._connections:
                ws, sid, subs = self._connections[connection_id]
                subs.update(topics)

    async def unsubscribe(self, connection_id: str, topics: Set[str]) -> None:
        """Entfernt Topics aus der Subscription."""
        async with self._lock:
            if connection_id in self._connections:
                _, _, subs = self._connections[connection_id]
                subs -= topics

    async def publish(self, topic: str, payload: Any = None) -> None:
        """
        Sendet ein Event an alle Verbindungen, die topic abonniert haben.
        Bei Sendefehler (z. B. getrennte Verbindung) wird die Verbindung entfernt.
        Lock nur kurz; Sends außerhalb des Locks, um Blockierung zu vermeiden.
        """
        msg = EventMessage(type=topic, topic=topic, payload=payload or {})
        try:
            body = msg.model_dump_json()
        except Exception:
            body = '{"type":"%s","topic":"%s","payload":{},"ts":""}' % (topic, topic)
        to_send: List[Tuple[WebSocket, str]] = []
        async with self._lock:
            for conn_id, (ws, _session_id, subs) in list(self._connections.items()):
                if topic in subs:
                    to_send.append((ws, body))
        for ws, body_str in to_send:
            try:
                await ws.send_text(body_str)
            except Exception as e:
                logger.debug("WS send failed: %s", e)
                async with self._lock:
                    to_remove = [cid for cid, (w, _, _) in self._connections.items() if w == ws]
                    for cid in to_remove:
                        self._connections.pop(cid, None)


# Singleton für die App
_manager: Optional[ConnectionManager] = None


def publish_fire_and_forget(topic: str, payload: Any = None) -> None:
    """
    Fire-and-forget Eventbus-Publish (async aus sync Kontext).
    AUDIT-FIX (D-003): Zentraler Helper, Dublette in pi_installer_service/sabrina_tuner_service entfernt.
    """
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            eb = get_eventbus()
            loop.create_task(eb.publish(topic, payload or {}))
    except Exception as e:
        logger.debug("Eventbus publish %s: %s", topic, e)


def get_eventbus() -> ConnectionManager:
    """Liefert den globalen ConnectionManager (Eventbus)."""
    global _manager
    if _manager is None:
        _manager = ConnectionManager()
    return _manager
