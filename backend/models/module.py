"""
Pydantic-Schemas für Remote-Module (Modulvertrag / Registry).
"""

from typing import List, Optional
from pydantic import BaseModel, Field

from .widget import WidgetDescriptor
from .action import ActionDescriptor


class ModuleDescriptor(BaseModel):
    """Öffentliche Beschreibung eines Moduls (für GET /api/modules, GET /api/modules/{id})."""
    id: str = Field(..., description="Eindeutige Modul-ID (z. B. sabrina-tuner, pi-installer)")
    name: str = Field(..., description="Anzeigename")
    description: Optional[str] = Field(None, description="Kurzbeschreibung")
    widgets: List[WidgetDescriptor] = Field(default_factory=list, description="Unterstützte Widgets für die UI")
    actions: List[ActionDescriptor] = Field(default_factory=list, description="Verfügbare Aktionen")
