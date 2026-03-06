"""
Pydantic-Modelle für Pairing-Tickets (QR-Pairing).
DB: pairing_tickets; Token nur als Hash speichern.
Status: pending | claimed | expired.
"""

from typing import Literal, Optional
from pydantic import BaseModel, Field

PairingTicketStatus = Literal["pending", "claimed", "expired"]


class PairingTicketCreate(BaseModel):
    """Daten zum Anlegen eines Pairing-Tickets (intern; Token wird gehashed)."""
    id: str = Field(..., description="Eindeutige Ticket-ID (z. B. UUID)")
    ticket_hash: str = Field(..., description="SHA256-Hash des Einmal-Tokens, nie Klartext")
    created_at: str = Field(..., description="ISO-8601 Zeitstempel")
    expires_at: str = Field(..., description="ISO-8601 Ablaufzeit")
    device_name: Optional[str] = Field(None, description="Optionale Anzeige des Gerätenamens")
    status: PairingTicketStatus = Field("pending", description="pending | claimed | expired")


class PairingTicketRow(BaseModel):
    """Eine Zeile aus pairing_tickets (z. B. für Abfragen)."""
    id: str
    ticket_hash: str
    created_at: str
    expires_at: str
    device_name: Optional[str] = None
    status: PairingTicketStatus = "pending"

    class Config:
        from_attributes = True


class PairingClaimRequest(BaseModel):
    """Request-Body für POST /api/pairing/claim."""
    pair_token: str = Field(..., description="Einmal-Token aus dem QR-Payload")
    device_id: Optional[str] = Field(None, description="Stabile Geräte-Kennung vom Client")
    device_name: Optional[str] = Field(None, description="Anzeigename des Geräts")


class PairingCreateResponse(BaseModel):
    """Response für POST /api/pairing/create: QR-Payload für das Smartphone."""
    ticket_id: str = Field(..., description="Eindeutige Ticket-ID")
    payload: dict = Field(..., description="QR-Payload (v, host, device_id, pair_token, expires_at, scope)")
    expires_at: str = Field(..., description="ISO-8601 Ablaufzeit")


class PairingClaimResponse(BaseModel):
    """Response für POST /api/pairing/claim."""
    success: bool = Field(..., description="Claim erfolgreich")
    message: str = Field("", description="Hinweistext")
    ticket_id: Optional[str] = Field(None, description="Ticket-ID bei Erfolg")
    session_token: Optional[str] = Field(None, description="Session-Token bei Erfolg (nur einmal zurückgegeben)")
