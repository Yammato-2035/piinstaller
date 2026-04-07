"""
Interpreter – regelbasiert, gekapselt.

INTERPRETER_VERSION bei ausgabe-relevanten Änderungen erhöhen.
Regeln: erste passende Regel gewinnt (Priorität = Reihenfolge in RULES_V1).

Übergang: Firewall-Regeln noch ``localization_model=legacy`` (Freitexte);
Webserver-Port, Backup-Verify, System-Backend und generischer Fallback nutzen ``key_v1``
(siehe docs/architecture/diagnosis_localization.md).
"""

from __future__ import annotations

import re
from typing import Any, Callable, Optional

from models.diagnosis import DiagnosisInterpretRequest, DiagnosisRecord

INTERPRETER_VERSION = "v2"

RuleFn = Callable[[DiagnosisInterpretRequest], Optional[DiagnosisRecord]]


def _keyed_record(
    *,
    diagnosis_id: str,
    diagnose_type: str,
    severity: str,
    confidence: float,
    area: str,
    event: str,
    companion_mode: str,
    technical_summary: str,
    source_event: dict,
    title_key: str,
    user_message_key: str,
    suggested_action_keys: list[str],
    title_fallback_en: str,
    user_message_fallback_en: str,
    suggested_actions_fallback_en: list[str],
    docs_refs: Optional[list[str]] = None,
    faq_refs: Optional[list[str]] = None,
    kb_refs: Optional[list[str]] = None,
    evidence: Optional[dict[str, Any]] = None,
    question_path: Optional[list[str]] = None,
) -> DiagnosisRecord:
    """key_v1: i18n über Frontend-Keys; Legacy-Felder = kurze EN-Fallbacks."""
    return DiagnosisRecord(
        schema_version="2",
        interpreter_version=INTERPRETER_VERSION,
        diagnosis_id=diagnosis_id,
        diagnosis_code=diagnosis_id,
        localization_model="key_v1",
        module=area,
        event=event,
        title_key=title_key,
        user_message_key=user_message_key,
        technical_summary_key=None,
        suggested_action_keys=suggested_action_keys,
        docs_refs=list(docs_refs or []),
        faq_refs=list(faq_refs or []),
        kb_refs=list(kb_refs or []),
        evidence=evidence,
        question_path=question_path,
        diagnose_type=diagnose_type,  # type: ignore[arg-type]
        severity=severity,  # type: ignore[arg-type]
        confidence=confidence,
        title=title_fallback_en,
        user_message=user_message_fallback_en,
        technical_summary=technical_summary,
        suggested_actions=list(suggested_actions_fallback_en),
        quick_fix_available=False,
        source_event=source_event,
        area=area,
        beginner_safe=True,
        companion_mode=companion_mode,  # type: ignore[arg-type]
    )


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
    step_keys = [
        "diagnosis.codes.system.shared.actions.check_network",
        "diagnosis.codes.system.shared.actions.check_server_url",
        "diagnosis.codes.system.shared.actions.retry_or_logs",
    ]
    if reason == "timeout":
        return _keyed_record(
            diagnosis_id="system.backend_timeout",
            diagnose_type="connectivity",
            severity="high",
            confidence=0.85,
            area="system",
            event=req.event_type,
            companion_mode="warning",
            technical_summary=f"reason=timeout, message={req.message or ''}"[:500],
            source_event=_snapshot_source(req),
            title_key="diagnosis.codes.system.backend_timeout.title",
            user_message_key="diagnosis.codes.system.backend_timeout.user_summary",
            suggested_action_keys=step_keys,
            title_fallback_en="Server timed out",
            user_message_fallback_en="The connection hit a timeout; the device or network may be overloaded or unreachable.",
            suggested_actions_fallback_en=[
                "Check LAN/WLAN and same subnet.",
                "Verify server URL in settings.",
                "Retry later; on Pi check power and storage.",
            ],
            docs_refs=["docs/architecture/diagnose_companion.md", "docs/user/QUICKSTART.md"],
            evidence={"reason": "timeout"},
        )
    if reason == "connection":
        return _keyed_record(
            diagnosis_id="system.backend_connection",
            diagnose_type="connectivity",
            severity="high",
            confidence=0.88,
            area="system",
            event=req.event_type,
            companion_mode="warning",
            technical_summary=f"reason=connection, message={req.message or ''}"[:500],
            source_event=_snapshot_source(req),
            title_key="diagnosis.codes.system.backend_connection.title",
            user_message_key="diagnosis.codes.system.backend_connection.user_summary",
            suggested_action_keys=step_keys,
            title_fallback_en="Server unreachable",
            user_message_fallback_en="No TCP connection; wrong URL, stopped service, or a firewall in between.",
            suggested_actions_fallback_en=[
                "Check whether the service runs on the target device.",
                "Match URL/port with the setup guide.",
                "Briefly review firewall rules between machines (do not disable permanently).",
            ],
            docs_refs=["docs/architecture/diagnose_companion.md", "docs/user/QUICKSTART.md"],
            evidence={"reason": "connection"},
        )
    return _keyed_record(
        diagnosis_id="system.backend_other",
        diagnose_type="connectivity",
        severity="medium",
        confidence=0.5,
        area="system",
        event=req.event_type,
        companion_mode="caution",
        technical_summary=f"reason={reason}, message={req.message or ''}"[:500],
        source_event=_snapshot_source(req),
        title_key="diagnosis.codes.system.backend_other.title",
        user_message_key="diagnosis.codes.system.backend_other.user_summary",
        suggested_action_keys=step_keys,
        title_fallback_en="Unexpected connection error",
        user_message_fallback_en="Connection failed; verify settings and device reachability.",
        suggested_actions_fallback_en=[
            "Check settings and server URL.",
            "Reload the page; if it persists use logs or support.",
        ],
        docs_refs=["docs/architecture/diagnose_companion.md"],
        evidence={"reason": str(reason)},
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
    ev: dict[str, Any] = {}
    if req.extra.get("server_type"):
        ev["server_type"] = req.extra.get("server_type")
    return _keyed_record(
        diagnosis_id="webserver.port_conflict",
        diagnose_type="configuration",
        severity="high",
        confidence=0.72,
        area="webserver",
        event=req.event_type,
        companion_mode="warning",
        technical_summary=raw[:800],
        source_event=_snapshot_source(req),
        title_key="diagnosis.codes.webserver.port_conflict.title",
        user_message_key="diagnosis.codes.webserver.port_conflict.user_summary",
        suggested_action_keys=[
            "diagnosis.codes.webserver.port_conflict.actions.check_overview",
            "diagnosis.codes.webserver.port_conflict.actions.resolve_binding",
            "diagnosis.codes.webserver.port_conflict.actions.avoid_repeat_apply",
        ],
        title_fallback_en="Web server could not start (port)",
        user_message_fallback_en=(
            "The web server likely failed to bind because TCP port 80/443 (or another required port) "
            "is already in use by another service."
        ),
        suggested_actions_fallback_en=[
            "Check the overview whether nginx/apache or another service already uses the port.",
            "Stop or reconfigure the conflicting service, or use a free port (advanced).",
            "Do not re-run apply until the conflict is understood; check logs or docs.",
        ],
        docs_refs=[
            "docs/architecture/diagnose_companion.md",
            "docs/architecture/diagnosis_localization.md",
        ],
        evidence=ev or None,
    )


def _rule_backup_verify_failed(req: DiagnosisInterpretRequest) -> Optional[DiagnosisRecord]:
    if req.area != "backup_restore":
        return None
    if req.event_type != "verify_failed":
        return None
    if not (req.message or "").strip():
        return None
    ev: dict[str, Any] = {}
    if req.extra.get("verify_mode") is not None:
        ev["verify_mode"] = req.extra.get("verify_mode")
    if req.extra.get("backup_file") is not None:
        ev["backup_file"] = req.extra.get("backup_file")
    return _keyed_record(
        diagnosis_id="backup_restore.verify_failed_generic",
        diagnose_type="backup_restore",
        severity="high",
        confidence=0.65,
        area="backup_restore",
        event=req.event_type,
        companion_mode="warning",
        technical_summary=(req.message or "")[:800],
        source_event=_snapshot_source(req),
        title_key="diagnosis.codes.backup_restore.verify_failed_generic.title",
        user_message_key="diagnosis.codes.backup_restore.verify_failed_generic.user_summary",
        suggested_action_keys=[
            "diagnosis.codes.backup_restore.verify_failed_generic.actions.no_restore_until_clear",
            "diagnosis.codes.backup_restore.verify_failed_generic.actions.retry_new_archive",
            "diagnosis.codes.backup_restore.verify_failed_generic.actions.check_path_rights",
        ],
        title_fallback_en="Backup verification failed",
        user_message_fallback_en=(
            "Verification did not pass. That does not strictly prove restore will fail or succeed—only that this check failed."
        ),
        suggested_actions_fallback_en=[
            "Do not start a restore until the cause is clear.",
            "Pick another archive or create a new backup and verify again.",
            "Check path and permissions; use logs or support if unsure.",
        ],
        docs_refs=["docs/architecture/diagnose_companion.md", "docs/backup-restore-realtest.md"],
        evidence=ev or None,
    )


def _fallback(req: DiagnosisInterpretRequest) -> DiagnosisRecord:
    return _keyed_record(
        diagnosis_id="unknown.generic",
        diagnose_type="unknown",
        severity="low",
        confidence=0.2,
        area=req.area or "unknown",
        event=req.event_type,
        companion_mode="info",
        technical_summary=(req.message or "")[:800],
        source_event=_snapshot_source(req),
        title_key="diagnosis.codes.unknown.generic.title",
        user_message_key="diagnosis.codes.unknown.generic.user_summary",
        suggested_action_keys=["diagnosis.codes.unknown.generic.actions.expand_technical"],
        title_fallback_en="No specific diagnosis",
        user_message_fallback_en="No detailed classification for this message; inspect technical details or contact support.",
        suggested_actions_fallback_en=["Expand the technical summary and review manually."],
        docs_refs=["docs/architecture/diagnosis_localization.md"],
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
