from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class InspectResult(BaseModel):
    system: dict[str, Any] = Field(default_factory=dict)
    storage: dict[str, Any] = Field(default_factory=dict)
    filesystems: dict[str, Any] = Field(default_factory=dict)
    boot: dict[str, Any] = Field(default_factory=dict)
    network: dict[str, Any] = Field(default_factory=dict)
    capabilities: dict[str, Any] = Field(default_factory=dict)
    warnings: list[dict[str, Any]] = Field(default_factory=list)
    errors: list[dict[str, Any]] = Field(default_factory=list)
    source_modules: list[str] = Field(default_factory=list)
    # Phase 2 (CIAO: Interpret + Advise) – nur aus Rohdaten abgeleitet, keine Aktionen
    classification: dict[str, Any] = Field(default_factory=dict)
    advice: dict[str, Any] = Field(default_factory=dict)
    # Write-Safety-Zusammenfassung (nur Auswertung, keine Schreibaktion)
    write_safety_summary: dict[str, Any] = Field(default_factory=dict)
