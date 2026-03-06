"""
Pydantic-Schemas für Eventbus-Events (WebSocket).
Unterstützte Eventtypen: module.state.changed, log.line, job.progress, tuner.now_playing, sync.status.changed.
"""

from typing import Any, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field


# Bekannte Topic-/Eventtypen (eine Quelle der Wahrheit für Sender und Empfänger)
EVENT_TOPICS = (
    "module.state.changed",
    "log.line",
    "job.progress",
    "tuner.now_playing",
    "tuner.volume_changed",
    "sync.status.changed",
)


class EventMessage(BaseModel):
    """Nachricht, die über den Eventbus an WebSocket-Clients gesendet wird."""
    type: str = Field(..., description="Topic / Eventtyp")
    topic: str = Field(..., description="Gleich wie type, für Kompatibilität")
    payload: Optional[dict[str, Any]] = Field(None, description="Event-Payload")
    ts: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat(), description="ISO-8601 Zeitstempel")

    class Config:
        # payload kann beliebige Struktur haben
        extra = "allow"
