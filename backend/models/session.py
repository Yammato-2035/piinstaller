"""
Pydantic-Modelle für Remote-Sessions.
DB: sessions; Session-Token nur als Hash speichern.
"""

from typing import Optional
from pydantic import BaseModel, Field


class SessionCreate(BaseModel):
    """Daten zum Anlegen einer Session (intern; Token wird gehashed)."""
    id: str = Field(..., description="Eindeutige Session-ID")
    session_token_hash: str = Field(..., description="SHA256-Hash des Session-Tokens, nie Klartext")
    device_id: str = Field(..., description="Verknüpftes Gerät (remote_device_profiles.device_id)")
    created_at: str = Field(..., description="ISO-8601")
    expires_at: str = Field(..., description="ISO-8601 Ablauf")
    refreshed_at: Optional[str] = Field(None, description="ISO-8601 letztes Refresh")


class SessionRow(BaseModel):
    """Eine Zeile aus sessions."""
    id: str
    session_token_hash: str
    device_id: str
    created_at: str
    expires_at: str
    refreshed_at: Optional[str] = None

    class Config:
        from_attributes = True


class SessionInfo(BaseModel):
    """Response für GET /api/sessions/me."""
    session_id: str = Field(..., description="Session-ID")
    device_id: str = Field(..., description="Geräte-Kennung")
    role: str = Field(..., description="Rolle: viewer, controller, admin, sync")
    expires_at: str = Field(..., description="ISO-8601 Ablauf")
