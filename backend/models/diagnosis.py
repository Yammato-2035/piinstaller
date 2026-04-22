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

# Rescue-/Read-only-Diagnose (Ampel, nur Codes — Texte im Frontend i18n)
RescueRiskLevel = Literal["green", "yellow", "red"]


class RescueFinding(BaseModel):
    """Einzelbefund der Rescue-Analyse; keine Freitexte, nur Codes + Evidence."""

    code: str = Field(..., description="Stabiler i18n-Code, z. B. rescue.storage.duplicate_uuid")
    area: str = Field(
        ...,
        description="Kategorie: storage | smart | filesystem | boot | network",
    )
    risk_level: RescueRiskLevel = Field(..., description="Ampel pro Befund")
    evidence: dict[str, Any] = Field(default_factory=dict, description="Strukturierte Rohdaten (ohne UI-Text)")


class RescueAnalyzeResponse(BaseModel):
    """Antwort von GET /api/rescue/analyze und CLI-Report."""

    status: Literal["ok", "error"] = "ok"
    risk_level: RescueRiskLevel
    findings: list[RescueFinding] = Field(default_factory=list)
    devices: list[dict[str, Any]] = Field(default_factory=list)
    boot_status: dict[str, Any] = Field(default_factory=dict)
    network_status: dict[str, Any] = Field(default_factory=dict)
    generated_at: str = Field(..., description="UTC ISO8601")


RestoreDryRunMode = Literal["analyze_only", "dryrun"]

RestoreDecision = Literal[
    "proceed_possible",
    "proceed_with_explicit_risk_ack",
    "do_not_restore",
    "recommend_data_recovery_first",
    "recommend_new_target_disk",
]


class RestoreDryRunRequest(BaseModel):
    """POST /api/rescue/restore-dryrun — keine Secrets im Klartext; nur Flags."""

    backup_file: str = Field(..., description="Absoluter Pfad zu .tar.gz unter erlaubten Wurzeln")
    target_device: Optional[str] = Field(None, description="Optional: Whole-Disk-Blockgerät für Kapazitäts-/Layout-Vergleich")
    mode: RestoreDryRunMode = Field(default="dryrun", description="analyze_only = kein Sandbox-Extract")
    encryption_key_available: bool = Field(
        default=False,
        description="True wenn Nutzer angibt, einen Schlüssel parat zu haben (kein Schlüsselübertrag)",
    )


class RestoreDryRunResponse(BaseModel):
    """Antwort Restore-Dry-Run — nur strukturierte Codes in findings/recommended_actions."""

    status: Literal["ok", "error"] = "ok"
    restore_risk_level: RescueRiskLevel
    restore_decision: RestoreDecision
    backup_assessment: dict[str, Any] = Field(default_factory=dict)
    target_assessment: dict[str, Any] = Field(default_factory=dict)
    dryrun: dict[str, Any] = Field(default_factory=dict)
    bootability: dict[str, Any] = Field(default_factory=dict)
    findings: list[RescueFinding] = Field(default_factory=list)
    recommended_actions: list[str] = Field(default_factory=list, description="Nur stabile Aktions-Codes")
    report_paths: dict[str, str] = Field(default_factory=dict)
    generated_at: str = Field(..., description="UTC ISO8601")
    dry_run_token: Optional[str] = Field(
        default=None,
        description="Einmal-Token für POST /api/rescue/restore (nur wenn allow_restore)",
    )
    allow_restore: bool = Field(
        default=False,
        description="True nur bei erfolgreichem Modus dryrun + DRYRUN_OK + kein RED-Entscheid",
    )
    session_id: str = Field(
        default="",
        description="Server-Session: DB-Session bei authentifizierter API, sonst servergenerierte Korrelations-ID",
    )


RestoreResultCode = Literal[
    "RESTORE_SUCCESS",
    "RESTORE_SUCCESS_WITH_WARNINGS",
    "RESTORE_PARTIAL",
    "RESTORE_FAILED",
    "RESTORE_BLOCKED",
]


class RescueRestoreRequest(BaseModel):
    """POST /api/rescue/restore — kontrollierter Restore (Phase 3)."""

    session_id: str = Field(
        ...,
        min_length=4,
        description="Muss exakt der session_id aus dem zugehörigen Dry-Run entsprechen (Session-Bindung)",
    )
    backup_id: str = Field(
        ...,
        description="Absoluter Pfad zum Backup-Archiv (entspricht Dry-Run backup_file)",
    )
    restore_target_directory: str = Field(
        ...,
        description="Leeres/aufbereitetes Zielverzeichnis unter erlaubtem Live-Restore-Präfix",
    )
    target_device: Optional[str] = Field(
        None,
        description="Muss mit Dry-Run target_device übereinstimmen (optional)",
    )
    dry_run_token: str = Field(..., description="Token aus RestoreDryRunResponse")
    confirmation: bool = Field(..., description="Muss true sein")
    risk_acknowledged: bool = Field(default=False, description="Bei YELLOW-Zwang true")
    target_confirmation_text: str = Field(
        ...,
        description="Gerätename (basename) oder RESTORE_NO_BLOCK_DEVICE",
    )
    encryption_key_hex: Optional[str] = Field(
        default=None,
        description="Optional: 64 Hex-Zeichen (32 Byte) für SHB1-AES-Archive — nicht loggen",
    )
    perform_boot_repair: bool = Field(
        default=False,
        description="Bootloader/initramfs-Schritte nur auf Ziel (nicht auf laufendes System)",
    )


class RescueRestoreResponse(BaseModel):
    """Antwort echter Restore — Codes in warnings, kein Freitext."""

    status: Literal["ok", "error"] = "ok"
    result: RestoreResultCode
    warnings: list[str] = Field(default_factory=list)
    log_path: str = Field(default="", description="Pfad zum Append-Log")
    bootable: bool = Field(default=False)
    codes: list[str] = Field(default_factory=list, description="Zusätzliche Status-/Fehlercodes")


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

    risk_level: Optional[RescueRiskLevel] = Field(
        default=None,
        description="Optional: Ampel (green|yellow|red) für Rescue-/übergreifende Darstellung",
    )

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
