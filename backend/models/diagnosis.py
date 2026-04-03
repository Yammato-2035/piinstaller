"""
Diagnose- und Companion-Datenmodell (API + Interpreter).

schema_version: erhöhen bei inkompatiblen Feldänderungen.
"""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, Field

# Erlaubte Companion-/Präsentationsmodi (Abstimmung mit UI-Ampel)
CompanionMode = Literal[
    "info",
    "caution",
    "warning",
    "blocked",
    "recommendation",
    "guided_step",
]

DiagnoseType = Literal[
    "connectivity",
    "permission",
    "configuration",
    "security",
    "backup_restore",
    "service",
    "unknown",
]

Severity = Literal["info", "low", "medium", "high", "critical"]


class DiagnosisInterpretRequest(BaseModel):
    """Eingabe für POST /api/diagnosis/interpret."""

    area: str = Field(..., description="Modul/Bereich, z. B. firewall, system, backup_restore")
    event_type: str = Field(
        ...,
        description="Technischer Ereignistyp, z. B. api_error, backend_unreachable, verify_failed",
    )
    message: Optional[str] = Field(None, description="Roh-Fehlermeldung oder gekürzter Text")
    http_status: Optional[int] = None
    api_status: Optional[str] = Field(None, description="Body-Feld status bei HTTP 200")
    request_id: Optional[str] = None
    extra: dict[str, Any] = Field(default_factory=dict)


class DiagnosisRecord(BaseModel):
    """Ausgabe Interpreter → Frontend. Serialisierbar, später erweiterbar."""

    schema_version: str = Field(default="1", description="Schema-Version des Records")
    interpreter_version: str = Field(..., description="Interpreter-Version, z. B. v1")

    diagnosis_id: str = Field(..., description="Stabile ID für i18n/Telemetrie")
    diagnose_type: DiagnoseType
    severity: Severity
    confidence: float = Field(ge=0.0, le=1.0, description="0–1, wie sicher die Einordnung ist")

    title: str
    user_message: str
    technical_summary: str = ""
    suggested_actions: list[str] = Field(default_factory=list)
    quick_fix_available: bool = False

    source_event: dict[str, Any] = Field(
        default_factory=dict,
        description="Anonymisierte Kopie der Eingabekontexte",
    )
    area: str
    beginner_safe: bool = True
    companion_mode: CompanionMode = "recommendation"

    class Config:
        json_schema_extra = {
            "example": {
                "schema_version": "1",
                "interpreter_version": "v1",
                "diagnosis_id": "firewall.rule_apply_failed_port",
                "diagnose_type": "configuration",
                "severity": "medium",
                "confidence": 0.75,
                "title": "Firewall-Regel",
                "user_message": "Die Regel konnte nicht angewendet werden.",
                "technical_summary": "ufw stderr: ...",
                "suggested_actions": ["Port prüfen", "Bestehende Regeln anzeigen"],
                "quick_fix_available": False,
                "source_event": {"area": "firewall"},
                "area": "firewall",
                "beginner_safe": True,
                "companion_mode": "warning",
            }
        }
