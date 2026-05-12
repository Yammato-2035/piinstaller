"""
Pydantic-Modelle für Remote-Geräteprofile (gekoppelte Geräte).
DB: remote_device_profiles.
"""

from pydantic import BaseModel, Field


class RemoteDeviceProfileCreate(BaseModel):
    """Daten zum Anlegen/Aktualisieren eines Geräteprofils."""
    id: str = Field(..., description="Eindeutige ID (z. B. UUID)")
    device_id: str = Field(..., description="Stabile Geräte-Kennung (z. B. vom Client)")
    name: str | None = Field(None, description="Anzeigename")
    role: str = Field("viewer", description="Rolle: viewer, controller, admin, sync")
    created_at: str = Field(..., description="ISO-8601")
    updated_at: str = Field(..., description="ISO-8601")


class RemoteDeviceProfileRow(BaseModel):
    """Eine Zeile aus remote_device_profiles."""
    id: str
    device_id: str
    name: str | None
    role: str
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True
