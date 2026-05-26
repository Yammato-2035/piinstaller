from __future__ import annotations

import smtplib
import ssl
from email.message import EmailMessage
from typing import Any

from core.notification_events import _sanitize_text
from core.notification_service import NotificationConfig, mask_email_address
from core.notification_settings import classify_smtp_error, load_effective_notification_config


def _smtp_send(cfg: NotificationConfig, msg: EmailMessage, smtp_send: Any | None = None) -> None:
    if smtp_send is not None:
        smtp_send(cfg, msg)
        return
    timeout = 60
    tls_context = ssl.create_default_context()
    if cfg.smtp_security == "ssl":
        with smtplib.SMTP_SSL(
            cfg.smtp_host,
            cfg.smtp_port,
            timeout=timeout,
            context=tls_context,
        ) as smtp:
            if cfg.smtp_username:
                smtp.login(cfg.smtp_username, cfg.smtp_password)
            smtp.send_message(msg)
        return
    with smtplib.SMTP(cfg.smtp_host, cfg.smtp_port, timeout=timeout) as smtp:
        if cfg.smtp_security == "starttls":
            smtp.starttls(context=tls_context)
        if cfg.smtp_username:
            smtp.login(cfg.smtp_username, cfg.smtp_password)
        smtp.send_message(msg)


def current_email_status() -> dict[str, Any]:
    cfg = load_effective_notification_config()
    recipient = mask_email_address(cfg.email_to) if cfg.email_to else None
    if not cfg.email_enabled:
        return {
            "status": "disabled",
            "configured": False,
            "enabled": False,
            "recipient_masked": recipient,
        }
    configured = bool(cfg.email_fully_configured() and cfg.smtp_password)
    return {
        "status": "ready" if configured else "not_configured",
        "configured": configured,
        "enabled": True,
        "recipient_masked": recipient,
    }


def _build_email_subject(event: dict[str, Any]) -> str:
    title = _sanitize_text(event.get("title") or event.get("event_type") or "Notification")
    severity = str(event.get("severity") or "info").upper()
    return f"Setuphelfer [{severity}] {title}"


def _build_email_body(event: dict[str, Any]) -> str:
    lines = [
        f"Titel: {_sanitize_text(event.get('title')) or '—'}",
        f"Bereich: {_sanitize_text(event.get('area')) or '—'}",
        f"Event-Typ: {_sanitize_text(event.get('event_type')) or '—'}",
        f"Severity: {_sanitize_text(event.get('severity')) or '—'}",
        "",
        _sanitize_text(event.get("message")) or "Keine Nachricht",
        "",
        "Technische Zusammenfassung:",
        _sanitize_text(event.get("technical_summary")) or "—",
    ]
    evidence_paths = event.get("evidence_paths") if isinstance(event.get("evidence_paths"), list) else []
    if evidence_paths:
        lines.extend(["", "Evidence:"])
        lines.extend(f"- {_sanitize_text(item)}" for item in evidence_paths[:10])
    lines.extend(["", "— Setuphelfer Notification"])
    return "\n".join(lines)


def send_email_for_event(event: dict[str, Any], smtp_send: Any | None = None) -> dict[str, Any]:
    body = dict(event)
    cfg = load_effective_notification_config()
    recipient = mask_email_address(cfg.email_to) if cfg.email_to else None
    body["email_recipient_masked"] = recipient
    body["email_error"] = None
    body["email_error_class"] = None

    if not bool(body.get("email_requested", True)):
        body["email_status"] = "disabled"
        return body
    if not cfg.email_enabled:
        body["email_status"] = "disabled"
        return body
    if not cfg.email_fully_configured() or not cfg.smtp_password:
        body["email_status"] = "not_configured"
        return body

    msg = EmailMessage()
    msg["Subject"] = _build_email_subject(body)
    msg["From"] = cfg.email_from
    msg["To"] = cfg.email_to
    msg.set_content(_build_email_body(body))

    try:
        _smtp_send(cfg, msg, smtp_send=smtp_send)
        body["email_status"] = "sent"
        return body
    except Exception as exc:
        error = _sanitize_text(str(exc))[:300]
        body["email_status"] = "failed"
        body["email_error"] = error
        body["email_error_class"] = classify_smtp_error(error)
        return body
