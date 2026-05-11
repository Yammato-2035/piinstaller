"""
Pydantic-Schemas für Remote-Modul-Widgets (UI-Bausteine der Modulansicht).
"""

from typing import Any, Optional
from pydantic import BaseModel, Field


class WidgetDescriptor(BaseModel):
    """Beschreibung eines Widgets (z. B. StatusCard, VolumeSlider)."""
    id: str = Field(..., description="Eindeutige Widget-ID")
    type: str = Field(..., description="Widget-Typ: StatusCard, PresetGrid, VolumeSlider, EqControl, LogViewer, …")
    label: Optional[str] = Field(None, description="Anzeige-Label")
    config: Optional[dict[str, Any]] = Field(None, description="Optionale Konfiguration (z. B. min/max für Slider)")
