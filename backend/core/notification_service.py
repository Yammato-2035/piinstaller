"""Optional E-Mail notifications after successful backup jobs (no failure on SMTP errors)."""

from __future__ import annotations

import os
import re
import smtplib
from dataclasses import dataclass
from email.message import EmailMessage
from typing import Any, Mapping

__all__ = [
    "EmailNotificationResult",
    "NotificationConfig",
    "build_backup_success_body",
    "build_backup_success_subject",
    "load_notification_config",
    "mask_email_address",
    "maybe_send_backup_success_email",
    "notification_status_fields",
    "should_notify_backup_success",
]


def _env_bool(name: str, default: bool = False) -> bool:
    raw = (os.environ.get(name) or "").strip().lower()
    if not raw:
        return default
    return raw in ("1", "true", "yes", "on")


def _env_str(name: str) -> str:
    return (os.environ.get(name) or "").strip()


@dataclass(frozen=True)
class NotificationConfig:
    email_enabled: bool
    email_to: str
    email_from: str
    smtp_host: str
    smtp_port: int
    smtp_username: str
    smtp_password: str
    smtp_starttls: bool
    notify_on_backup_success: bool
    notify_on_backup_failure: bool

    def email_fully_configured(self) -> bool:
        return bool(
            self.email_to
            and self.email_from
            and self.smtp_host
            and self.smtp_port > 0
        )


@dataclass(frozen=True)
class EmailNotificationResult:
    status: str
    error: str | None = None
    recipient_masked: str | None = None

    @property
    def sent(self) -> bool:
        return self.status == "sent"


def load_notification_config() -> NotificationConfig:
    port_raw = _env_str("SETUPHELFER_NOTIFY_SMTP_PORT") or "587"
    try:
        port = int(port_raw)
    except ValueError:
        port = 587
    return NotificationConfig(
        email_enabled=_env_bool("SETUPHELFER_NOTIFY_EMAIL_ENABLED"),
        email_to=_env_str("SETUPHELFER_NOTIFY_EMAIL_TO"),
        email_from=_env_str("SETUPHELFER_NOTIFY_EMAIL_FROM"),
        smtp_host=_env_str("SETUPHELFER_NOTIFY_SMTP_HOST"),
        smtp_port=port,
        smtp_username=_env_str("SETUPHELFER_NOTIFY_SMTP_USERNAME"),
        smtp_password=_env_str("SETUPHELFER_NOTIFY_SMTP_PASSWORD"),
        smtp_starttls=_env_bool("SETUPHELFER_NOTIFY_SMTP_STARTTLS", default=True),
        notify_on_backup_success=_env_bool("SETUPHELFER_NOTIFY_ON_BACKUP_SUCCESS", default=True),
        notify_on_backup_failure=_env_bool("SETUPHELFER_NOTIFY_ON_BACKUP_FAILURE", default=False),
    )


def mask_email_address(address: str) -> str:
    """Mask local part for status/logs, e.g. v***@example.com."""
    addr = (address or "").strip()
    if "@" not in addr:
        return "***" if addr else ""
    local, _, domain = addr.partition("@")
    if not local:
        return f"***@{domain}"
    if len(local) == 1:
        masked_local = f"{local}***"
    else:
        masked_local = f"{local[0]}***"
    return f"{masked_local}@{domain}"


def should_notify_backup_success(
    *,
    code: str,
    verify_deep_ok: bool | None,
    backup_integrity_status: str | None,
    config: NotificationConfig | None = None,
) -> bool:
    cfg = config or load_notification_config()
    if not cfg.email_enabled or not cfg.notify_on_backup_success:
        return False
    if code == "backup.success":
        return True
    if code == "backup.success_with_warnings":
        return bool(verify_deep_ok is True and backup_integrity_status == "verified")
    return False


def build_backup_success_subject(job_id: str) -> str:
    jid = (job_id or "").strip() or "unknown"
    return f"Setuphelfer Backup erfolgreich: {jid}"


def build_backup_success_body(
    *,
    job_id: str,
    status_code: str,
    backup_type: str = "",
    backup_profile: str = "",
    target_path: str = "",
    archive_path: str = "",
    manifest_hash: str = "",
    verify_deep_ok: bool | None = None,
    verify_deep_message_key: str | None = None,
    runtime_seconds: int | None = None,
    bytes_written: int | None = None,
    warning_status: str | None = None,
    warnings_summary: str | None = None,
) -> str:
    lines = [
        "Setuphelfer — Backup erfolgreich abgeschlossen",
        "",
        f"Job-ID: {job_id or '—'}",
        f"Status: {status_code or '—'}",
    ]
    if backup_type:
        lines.append(f"Backup-Typ: {backup_type}")
    if backup_profile:
        lines.append(f"Profil: {backup_profile}")
    if target_path:
        lines.append(f"Zielverzeichnis: {target_path}")
    if archive_path:
        lines.append(f"Archiv: {archive_path}")
    if manifest_hash:
        lines.append(f"SHA256 (Payload): {manifest_hash}")
    if verify_deep_ok is not None:
        lines.append(f"Verify Deep: {'ok' if verify_deep_ok else 'failed'}")
    if verify_deep_message_key:
        lines.append(f"Verify-Key: {verify_deep_message_key}")
    if runtime_seconds is not None:
        lines.append(f"Laufzeit: {runtime_seconds} s")
    if bytes_written is not None:
        lines.append(f"Bytes geschrieben: {bytes_written}")
    if warning_status:
        lines.append(f"Warnstatus: {warning_status}")
    if warnings_summary:
        lines.append(f"Hinweise: {warnings_summary}")
    lines.extend(["", "— Setuphelfer (automatische Benachrichtigung)"])
    return "\n".join(lines)


def send_backup_success_email(
    *,
    job_id: str,
    status_code: str,
    backup_type: str = "",
    backup_profile: str = "",
    target_path: str = "",
    archive_path: str = "",
    manifest_hash: str = "",
    verify_deep_ok: bool | None = None,
    verify_deep_message_key: str | None = None,
    runtime_seconds: int | None = None,
    bytes_written: int | None = None,
    warning_status: str | None = None,
    warnings_summary: str | None = None,
    config: NotificationConfig | None = None,
    smtp_send: Any | None = None,
) -> EmailNotificationResult:
    """
    Send success notification. Never raises to caller; returns structured result.
    """
    cfg = config or load_notification_config()
    if not cfg.email_enabled:
        return EmailNotificationResult(status="skipped_disabled")
    if not cfg.email_fully_configured():
        return EmailNotificationResult(status="skipped_not_configured")

    masked = mask_email_address(cfg.email_to)
    subject = build_backup_success_subject(job_id)
    body = build_backup_success_body(
        job_id=job_id,
        status_code=status_code,
        backup_type=backup_type,
        backup_profile=backup_profile,
        target_path=target_path,
        archive_path=archive_path,
        manifest_hash=manifest_hash,
        verify_deep_ok=verify_deep_ok,
        verify_deep_message_key=verify_deep_message_key,
        runtime_seconds=runtime_seconds,
        bytes_written=bytes_written,
        warning_status=warning_status,
        warnings_summary=warnings_summary,
    )
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = cfg.email_from
    msg["To"] = cfg.email_to
    msg.set_content(body)

    try:
        if smtp_send is not None:
            smtp_send(cfg, msg)
        else:
            _smtp_send_default(cfg, msg)
        return EmailNotificationResult(status="sent", recipient_masked=masked)
    except Exception as exc:
        err = re.sub(r"(?i)(password|passwd|auth|credential)[^\s]*", "[redacted]", str(exc))[:300]
        return EmailNotificationResult(status="failed", error=err, recipient_masked=masked)


def _smtp_send_default(cfg: NotificationConfig, msg: EmailMessage) -> None:
    with smtplib.SMTP(cfg.smtp_host, cfg.smtp_port, timeout=60) as smtp:
        if cfg.smtp_starttls:
            smtp.starttls()
        if cfg.smtp_username:
            smtp.login(cfg.smtp_username, cfg.smtp_password)
        smtp.send_message(msg)


def maybe_send_backup_success_email(
    *,
    job_id: str,
    status_code: str,
    backup_type: str = "",
    backup_profile: str = "",
    target_path: str = "",
    archive_path: str = "",
    manifest_hash: str = "",
    verify_deep_ok: bool | None = None,
    backup_integrity_status: str | None = None,
    verify_deep_message_key: str | None = None,
    runtime_seconds: int | None = None,
    bytes_written: int | None = None,
    warning_status: str | None = None,
    warnings: Any = None,
    config: NotificationConfig | None = None,
    smtp_send: Any | None = None,
) -> EmailNotificationResult:
    if not should_notify_backup_success(
        code=status_code,
        verify_deep_ok=verify_deep_ok,
        backup_integrity_status=backup_integrity_status,
        config=config,
    ):
        cfg = config or load_notification_config()
        if not cfg.email_enabled:
            return EmailNotificationResult(status="skipped_disabled")
        if not cfg.email_fully_configured():
            return EmailNotificationResult(status="skipped_not_configured")
        return EmailNotificationResult(status="skipped_not_applicable")

    warn_summary = None
    if warnings:
        if isinstance(warnings, list):
            kinds = []
            for w in warnings[:5]:
                if isinstance(w, dict):
                    kinds.append(str(w.get("kind") or w.get("classification") or "warning"))
                else:
                    kinds.append(str(w))
            warn_summary = ", ".join(kinds) if kinds else None
        else:
            warn_summary = str(warnings)[:200]

    return send_backup_success_email(
        job_id=job_id,
        status_code=status_code,
        backup_type=backup_type,
        backup_profile=backup_profile,
        target_path=target_path,
        archive_path=archive_path,
        manifest_hash=manifest_hash,
        verify_deep_ok=verify_deep_ok,
        verify_deep_message_key=verify_deep_message_key,
        runtime_seconds=runtime_seconds,
        bytes_written=bytes_written,
        warning_status=warning_status,
        warnings_summary=warn_summary,
        config=config,
        smtp_send=smtp_send,
    )


def notification_status_fields(
    cfg: NotificationConfig | None,
    result: EmailNotificationResult,
) -> dict[str, Any]:
    c = cfg or load_notification_config()
    return {
        "notification_email_enabled": c.email_enabled,
        "notification_email_status": result.status,
        "notification_email_sent": result.sent,
        "notification_email_error": (result.error or "")[:300] if result.error else None,
        "notification_email_to_configured": bool(c.email_to),
        "notification_email_recipient_masked": result.recipient_masked
        or (mask_email_address(c.email_to) if c.email_to else None),
    }
