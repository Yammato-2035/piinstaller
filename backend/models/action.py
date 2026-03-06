"""
Pydantic-Schemas für Remote-Modul-Aktionen.
"""

from typing import Any, Optional
from pydantic import BaseModel, Field


class ActionDescriptor(BaseModel):
    """Beschreibung einer ausführbaren Aktion eines Moduls."""
    id: str = Field(..., description="Eindeutige Action-ID (z. B. set_volume, play_preset)")
    label: str = Field(..., description="Anzeige-Label")
    description: Optional[str] = Field(None, description="Kurzbeschreibung")
    params_schema: Optional[dict[str, Any]] = Field(None, description="Optionale JSON-Schema für das Payload")


class ActionInvocation(BaseModel):
    """Request-Body für POST /api/modules/{module_id}/actions/{action_id}."""
    payload: Optional[dict[str, Any]] = Field(default_factory=dict, description="Action-spezifische Parameter")


class ActionResult(BaseModel):
    """Response für Modul-Aktionen."""
    success: bool = Field(..., description="Aktion erfolgreich")
    message: Optional[str] = Field(None, description="Hinweis oder Fehlermeldung")
    data: Optional[dict[str, Any]] = Field(None, description="Optionale Rückgabedaten")
