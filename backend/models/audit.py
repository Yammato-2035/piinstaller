"""
Pydantic-Modelle für Remote-Audit-Log.
DB: audit_log.
"""

from typing import Optional
from pydantic import BaseModel, Field


class AuditLogCreate(BaseModel):
    """Daten zum Eintragen eines Audit-Eintrags."""
    event_type: str = Field(..., description="z. B. pairing_used, session_created, action_invoked")
    device_id: Optional[str] = Field(None, description="Verknüpftes Gerät falls vorhanden")
    details: Optional[str] = Field(None, description="JSON oder Klartext-Details")
    created_at: str = Field(..., description="ISO-8601")


class AuditLogRow(BaseModel):
    """Eine Zeile aus audit_log."""
    id: int
    event_type: str
    device_id: Optional[str] = None
    details: Optional[str] = None
    created_at: str

    class Config:
        from_attributes = True
