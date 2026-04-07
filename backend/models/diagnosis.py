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

LocalizationModel = Literal["legacy", "key_v1"]


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
    """Ausgabe Interpreter → Frontend. Serialisierbar, später erweiterbar.

    **Zwei Schichten (Übergang):**
    - ``localization_model == \"legacy\"``: ``title``, ``user_message``, ``suggested_actions`` sind
      freie Texte (historisch oft Deutsch). ``schema_version`` typisch ``\"1\"``.
    - ``localization_model == \"key_v1\"``: Zielmodell – Frontend übersetzt über ``*_key``-Felder;
      Legacy-Textfelder enthalten kurze EN-Fallbacks; ``schema_version`` typisch ``\"2\"``.

    Stabiler Code: ``diagnosis_code`` entspricht bei neuen Records ``diagnosis_id`` (Punkt-Notation).
    """

    schema_version: str = Field(default="1", description="1 = Legacy-Form, 2 = keyed + Legacy-Fallbacks")
    interpreter_version: str = Field(..., description="Interpreter-Version, z. B. v2")

    diagnosis_id: str = Field(..., description="Stabile ID (gleichbedeutend mit diagnosis_code bei key_v1)")
    diagnose_type: DiagnoseType
    severity: Severity
    confidence: float = Field(ge=0.0, le=1.0, description="0–1, wie sicher die Einordnung ist")

    title: str
    user_message: str
    technical_summary: str = ""
    suggested_actions: list[str] = Field(default_factory=list)
    quick_fix_available: bool = False

    localization_model: LocalizationModel = Field(
        default="legacy",
        description="legacy = Freitext; key_v1 = i18n-Keys im Frontend",
    )
    diagnosis_code: Optional[str] = Field(
        default=None,
        description="Stabiler Code (bei key_v1 i. d. R. = diagnosis_id)",
    )
    module: Optional[str] = Field(default=None, description="Modulkürzel, meist = area")
    event: Optional[str] = Field(default=None, description="Auslöser / event_type der Anfrage")

    title_key: Optional[str] = Field(default=None, description="i18n-Key für Titel (key_v1)")
    user_message_key: Optional[str] = Field(default=None, description="i18n-Key Nutzerzusammenfassung")
    technical_summary_key: Optional[str] = Field(
        default=None,
        description="Optional: statischer i18n-Key; Rohdaten bleiben in technical_summary",
    )
    suggested_action_keys: Optional[list[str]] = Field(
        default=None,
        description="i18n-Keys für Empfehlungen (Reihenfolge = Anzeige)",
    )

    docs_refs: list[str] = Field(default_factory=list, description="Pfade/Anker zur technischen Doku")
    faq_refs: list[str] = Field(default_factory=list)
    kb_refs: list[str] = Field(default_factory=list)
    evidence: Optional[dict[str, Any]] = Field(default=None, description="Strukturierte Belege (optional)")
    question_path: Optional[list[str]] = Field(
        default=None,
        description="Optional: geführte Diagnose / Entscheidungspfad (IDs)",
    )

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
                "schema_version": "2",
                "interpreter_version": "v2",
                "diagnosis_id": "webserver.port_conflict",
                "diagnosis_code": "webserver.port_conflict",
                "localization_model": "key_v1",
                "title_key": "diagnosis.codes.webserver.port_conflict.title",
                "user_message_key": "diagnosis.codes.webserver.port_conflict.user_summary",
                "suggested_action_keys": [
                    "diagnosis.codes.webserver.port_conflict.actions.check_overview",
                ],
                "diagnose_type": "configuration",
                "severity": "high",
                "confidence": 0.72,
                "title": "Web server port conflict",
                "user_message": "Port likely in use.",
                "technical_summary": "nginx: bind :443 …",
                "suggested_actions": ["Check overview", "Resolve conflict"],
                "docs_refs": ["docs/architecture/diagnosis_localization.md"],
                "quick_fix_available": False,
                "source_event": {"area": "webserver"},
                "area": "webserver",
                "beginner_safe": True,
                "companion_mode": "warning",
            }
        }
