"""
Interpreter Phase 1 – regelbasiert, gekapselt.

INTERPRETER_VERSION erhöhen oder neue Datei interpret_v2.py bei größeren Änderungen.
Regeln: erste passende Regel gewinnt (Priorität = Reihenfolge in RULES_V1).
"""

from __future__ import annotations

import re
from typing import Callable, Optional

from models.diagnosis import DiagnosisInterpretRequest, DiagnosisRecord

INTERPRETER_VERSION = "v1"

RuleFn = Callable[[DiagnosisInterpretRequest], Optional[DiagnosisRecord]]


def _snapshot_source(req: DiagnosisInterpretRequest) -> dict:
    out = {
        "area": req.area,
        "event_type": req.event_type,
        "http_status": req.http_status,
        "api_status": req.api_status,
        "request_id": req.request_id,
        "message_excerpt": (req.message or "")[:400],
    }
    if req.extra:
        out["extra"] = dict(req.extra)
    return out


def _rule_firewall_sudo(req: DiagnosisInterpretRequest) -> Optional[DiagnosisRecord]:
    if req.area != "firewall":
        return None
    if req.api_status != "error":
        return None
    msg = (req.message or "").lower()
    if "sudo" in msg or req.extra.get("requires_sudo_password"):
        return DiagnosisRecord(
            interpreter_version=INTERPRETER_VERSION,
            diagnosis_id="firewall.sudo_required",
            diagnose_type="permission",
            severity="medium",
            confidence=0.9,
            title="Administratorrechte nötig",
            user_message=(
                "Für diese Firewall-Aktion wird ein gültiges Sudo-Passwort benötigt. "
                "Ohne Passwort kann die Regel nicht angewendet werden."
            ),
            technical_summary=req.message or "",
            suggested_actions=[
                "Sudo-Passwort erneut eingeben und Vorgang wiederholen.",
                "Prüfen, ob der Benutzer in der sudo-Gruppe ist.",
            ],
            quick_fix_available=False,
            source_event=_snapshot_source(req),
            area="firewall",
            beginner_safe=True,
            companion_mode="blocked",
        )
    return None


def _rule_firewall_port_conflict(req: DiagnosisInterpretRequest) -> Optional[DiagnosisRecord]:
    if req.area != "firewall":
        return None
    if req.api_status != "error":
        return None
    raw = req.message or ""
    low = raw.lower()
    patterns = (
        "could not add",
        "already exists",
        "bereits",
        "schon vorhanden",
        "address already in use",
        "bind",
        "belegt",
        "port.*in use",
    )
    if not any(re.search(p, low) for p in patterns):
        return None
    return DiagnosisRecord(
        interpreter_version=INTERPRETER_VERSION,
        diagnosis_id="firewall.rule_apply_failed_port",
        diagnose_type="configuration",
        severity="medium",
        confidence=0.72,
        title="Firewall-Regel nicht anwendbar",
        user_message=(
            "Die Firewall-Regel konnte nicht angewendet werden. "
            "Häufig ist der Zielport bereits von einem anderen Dienst belegt, "
            "oder eine ähnliche Regel existiert bereits."
        ),
        technical_summary=raw[:800],
        suggested_actions=[
            "Mit „Firewall-Regeln anzeigen“ prüfen, ob die Regel schon existiert.",
            "Prüfen, welcher Dienst den Port nutzt (z. B. Webserver, SSH).",
            "Bei Konflikten zuerst den Dienst oder die bestehende Regel anpassen.",
        ],
        quick_fix_available=False,
        source_event=_snapshot_source(req),
        area="firewall",
        beginner_safe=True,
        companion_mode="warning",
    )


def _rule_firewall_generic(req: DiagnosisInterpretRequest) -> Optional[DiagnosisRecord]:
    if req.area != "firewall":
        return None
    if req.api_status != "error":
        return None
    raw = req.message or ""
    if not raw.strip():
        return None
    return DiagnosisRecord(
        interpreter_version=INTERPRETER_VERSION,
        diagnosis_id="firewall.rule_apply_failed_generic",
        diagnose_type="security",
        severity="medium",
        confidence=0.55,
        title="Firewall-Regel fehlgeschlagen",
        user_message=(
            "Die Firewall konnte die Regel nicht setzen. "
            "Die genaue Ursache steht in den technischen Details – "
            "häufig helfen Syntax der Regel oder fehlende Rechte."
        ),
        technical_summary=raw[:800],
        suggested_actions=[
            "Technische Meldung lesen oder Support mit Protokoll kontaktieren.",
            "UFW-Status und bestehende Regeln im Sicherheitsbereich prüfen.",
        ],
        quick_fix_available=False,
        source_event=_snapshot_source(req),
        area="firewall",
        beginner_safe=True,
        companion_mode="caution",
    )


def _rule_system_backend_unreachable(req: DiagnosisInterpretRequest) -> Optional[DiagnosisRecord]:
    if req.area != "system":
        return None
    if req.event_type != "backend_unreachable":
        return None
    reason = (req.extra or {}).get("reason") or "other"
    if reason == "timeout":
        return DiagnosisRecord(
            interpreter_version=INTERPRETER_VERSION,
            diagnosis_id="system.backend_timeout",
            diagnose_type="connectivity",
            severity="high",
            confidence=0.85,
            title="Server antwortet zu langsam",
            user_message=(
                "Die Verbindung zum Setuphelfer-Server hat ein Zeitlimit erreicht. "
                "Das Gerät oder die Netzwerkverbindung ist möglicherweise überlastet oder nicht erreichbar."
            ),
            technical_summary=f"reason=timeout, message={req.message or ''}"[:500],
            suggested_actions=[
                "Netzwerk prüfen (LAN/WLAN, gleiches Subnetz).",
                "Server-Adresse in den Einstellungen kontrollieren.",
                "Später erneut versuchen; bei Pi: Strom und SD-Karte prüfen.",
            ],
            quick_fix_available=False,
            source_event=_snapshot_source(req),
            area="system",
            beginner_safe=True,
            companion_mode="warning",
        )
    if reason == "connection":
        return DiagnosisRecord(
            interpreter_version=INTERPRETER_VERSION,
            diagnosis_id="system.backend_connection",
            diagnose_type="connectivity",
            severity="high",
            confidence=0.88,
            title="Server nicht erreichbar",
            user_message=(
                "Es konnte keine Verbindung zum Setuphelfer-Server aufgebaut werden. "
                "Oft liegt es an falscher URL, gestopptem Dienst oder einer Firewall dazwischen."
            ),
            technical_summary=f"reason=connection, message={req.message or ''}"[:500],
            suggested_actions=[
                "Prüfen, ob der Dienst auf dem Zielgerät läuft.",
                "URL/Port in den Einstellungen mit der Anleitung abgleichen.",
                "Firewall zwischen PC und Gerät kurz prüfen (nicht dauerhaft abschalten).",
            ],
            quick_fix_available=False,
            source_event=_snapshot_source(req),
            area="system",
            beginner_safe=True,
            companion_mode="warning",
        )
    return DiagnosisRecord(
        interpreter_version=INTERPRETER_VERSION,
        diagnosis_id="system.backend_other",
        diagnose_type="connectivity",
        severity="medium",
        confidence=0.5,
        title="Unerwarteter Verbindungsfehler",
        user_message=(
            "Die Verbindung zum Server ist fehlgeschlagen. "
            "Bitte die Einstellungen und die Erreichbarkeit des Geräts prüfen."
        ),
        technical_summary=f"reason={reason}, message={req.message or ''}"[:500],
        suggested_actions=[
            "Einstellungen und Server-URL prüfen.",
            "Seite neu laden; bei anhaltendem Fehler Logs/Support nutzen.",
        ],
        quick_fix_available=False,
        source_event=_snapshot_source(req),
        area="system",
        beginner_safe=True,
        companion_mode="caution",
    )


def _rule_webserver_port_conflict(req: DiagnosisInterpretRequest) -> Optional[DiagnosisRecord]:
    """Erkennt typische Port-/Bind-Fehler bei Webserver-Start (80/443 u. a.). Regel v1 — nur Heuristik."""
    if req.area != "webserver":
        return None
    if req.event_type not in ("configure_failed", "api_error"):
        return None
    raw = req.message or ""
    low = raw.lower()
    patterns = (
        r"address already in use",
        r"eaddrinuse",
        r"already in use",
        r"port.+already",
        r"could not bind",
        r"unable to bind",
        r"bind failed",
        r"bind:.+address",
        r"socket.+in use",
        r"listen.+failed",
        r"\b:80\b",
        r"\b:443\b",
        r"\bport 80\b",
        r"\bport 443\b",
        r"\b98:\s*address",
        r"adresse.*bereits.*verwendung",
        r"port.*belegt",
    )
    if not any(re.search(p, low) for p in patterns):
        return None
    return DiagnosisRecord(
        interpreter_version=INTERPRETER_VERSION,
        diagnosis_id="webserver.port_conflict",
        diagnose_type="configuration",
        severity="high",
        confidence=0.72,
        title="Webserver konnte nicht starten (Port)",
        user_message=(
            "Der Webserver konnte nicht gestartet oder nicht neu geladen werden, "
            "weil der benötigte Netzwerk-Port sehr wahrscheinlich schon von einem anderen Programm genutzt wird. "
            "Typisch sind die Ports 80 (HTTP) und 443 (HTTPS), wenn bereits ein anderer Webserver oder Dienst darauf lauscht."
        ),
        technical_summary=raw[:800],
        suggested_actions=[
            "Unter „Übersicht“ prüfen, ob Nginx oder Apache bereits läuft oder ob ein anderer Dienst die Ports blockiert.",
            "Entweder den Konflikt beheben (anderen Dienst gezielt stoppen oder dessen Konfiguration anpassen) oder die Webserver-Einstellungen auf einen freien Port legen – das erfordert oft Erfahrung.",
            "Ohne geklärten Portkonflikt nicht wiederholt „Konfiguration anwenden“ ausführen; bei Unsicherheit Logs oder Dokumentation nutzen.",
        ],
        quick_fix_available=False,
        source_event=_snapshot_source(req),
        area="webserver",
        beginner_safe=True,
        companion_mode="warning",
    )


def _rule_backup_verify_failed(req: DiagnosisInterpretRequest) -> Optional[DiagnosisRecord]:
    if req.area != "backup_restore":
        return None
    if req.event_type != "verify_failed":
        return None
    if not (req.message or "").strip():
        return None
    return DiagnosisRecord(
        interpreter_version=INTERPRETER_VERSION,
        diagnosis_id="backup_restore.verify_failed_generic",
        diagnose_type="backup_restore",
        severity="high",
        confidence=0.65,
        title="Backup-Prüfung fehlgeschlagen",
        user_message=(
            "Die Überprüfung des Backups ist fehlgeschlagen. "
            "Das bedeutet nicht automatisch, dass eine Wiederherstellung möglich oder unmöglich ist – "
            "es wurde nur diese Prüfung nicht bestanden. "
            "Häufige Ursachen: beschädigtes oder unpassendes Archiv, falscher Pfad, fehlende Rechte "
            "oder Sicherheitsregeln des Systems."
        ),
        technical_summary=(req.message or "")[:800],
        suggested_actions=[
            "Keine Wiederherstellung starten, bevor die Ursache geklärt ist.",
            "Anderes Archiv wählen oder ein neues Backup erstellen und erneut prüfen.",
            "Pfad und Dateirechte prüfen; bei Unsicherheit Logs oder Support nutzen.",
        ],
        quick_fix_available=False,
        source_event=_snapshot_source(req),
        area="backup_restore",
        beginner_safe=True,
        companion_mode="warning",
    )


def _fallback(req: DiagnosisInterpretRequest) -> DiagnosisRecord:
    return DiagnosisRecord(
        interpreter_version=INTERPRETER_VERSION,
        diagnosis_id="unknown.generic",
        diagnose_type="unknown",
        severity="low",
        confidence=0.2,
        title="Keine spezifische Diagnose",
        user_message=(
            "Für diese Meldung liegt keine detaillierte Einordnung vor. "
            "Bitte technische Details prüfen oder Support kontaktieren."
        ),
        technical_summary=(req.message or "")[:800],
        suggested_actions=["Technische Zusammenfassung einblenden und manuell prüfen."],
        quick_fix_available=False,
        source_event=_snapshot_source(req),
        area=req.area or "unknown",
        beginner_safe=True,
        companion_mode="info",
    )


RULES_V1: tuple[RuleFn, ...] = (
    _rule_firewall_sudo,
    _rule_firewall_port_conflict,
    _rule_firewall_generic,
    _rule_webserver_port_conflict,
    _rule_system_backend_unreachable,
    _rule_backup_verify_failed,
)


def interpret_v1(req: DiagnosisInterpretRequest) -> DiagnosisRecord:
    for rule in RULES_V1:
        hit = rule(req)
        if hit is not None:
            return hit
    return _fallback(req)
