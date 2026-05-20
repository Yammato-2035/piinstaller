"""Optional E-Mail notifications after successful backup jobs (no failure on SMTP errors)."""

from __future__ import annotations

import os
import re
import smtplib
import ssl
from dataclasses import dataclass
from email.message import EmailMessage
from typing import Any, Literal

SMTP_SECURITY_MODES = frozenset({"starttls", "ssl", "none"})
SmtpSecurity = Literal["starttls", "ssl", "none"]

__all__ = [
    "EmailNotificationResult",
    "NotificationConfig",
    "build_backup_failure_body",
    "build_backup_failure_subject",
    "build_backup_success_body",
    "build_backup_success_subject",
    "load_notification_config",
    "mask_email_address",
    "maybe_send_backup_failure_email",
    "maybe_send_backup_success_email",
    "notification_status_fields",
    "should_notify_backup_failure",
    "should_notify_backup_success",
]


def _env_bool(name: str, default: bool = False) -> bool:
    raw = (os.environ.get(name) or "").strip().lower()
    if not raw:
        return default
    return raw in ("1", "true", "yes", "on")


def _env_str(name: str) -> str:
    return (os.environ.get(name) or "").strip()


def normalize_smtp_security(value: str | None, *, port: int, smtp_starttls: bool) -> SmtpSecurity:
    """Resolve encryption mode; legacy smtp_starttls + port 465 heuristics when security unset."""
    raw = (value or "").strip().lower()
    if raw in SMTP_SECURITY_MODES:
        return raw  # type: ignore[return-value]
    if port == 465:
        return "ssl"
    if smtp_starttls:
        return "starttls"
    return "none"


@dataclass(frozen=True)
class NotificationConfig:
    email_enabled: bool
    email_to: str
    email_from: str
    smtp_host: str
    smtp_port: int
    smtp_username: str
    smtp_password: str
    smtp_security: SmtpSecurity
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
    starttls = _env_bool("SETUPHELFER_NOTIFY_SMTP_STARTTLS", default=True)
    security = normalize_smtp_security(
        _env_str("SETUPHELFER_NOTIFY_SMTP_SECURITY"),
        port=port,
        smtp_starttls=starttls,
    )
    return NotificationConfig(
        email_enabled=_env_bool("SETUPHELFER_NOTIFY_EMAIL_ENABLED"),
        email_to=_env_str("SETUPHELFER_NOTIFY_EMAIL_TO"),
        email_from=_env_str("SETUPHELFER_NOTIFY_EMAIL_FROM"),
        smtp_host=_env_str("SETUPHELFER_NOTIFY_SMTP_HOST"),
        smtp_port=port,
        smtp_username=_env_str("SETUPHELFER_NOTIFY_SMTP_USERNAME"),
        smtp_password=_env_str("SETUPHELFER_NOTIFY_SMTP_PASSWORD"),
        smtp_security=security,
        smtp_starttls=security == "starttls",
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


def should_notify_backup_failure(
    *,
    status: str,
    code: str,
    config: NotificationConfig | None = None,
) -> bool:
    cfg = config or load_notification_config()
    if not cfg.email_enabled or not cfg.notify_on_backup_failure:
        return False
    st = (status or "").strip().lower()
    if st in ("error", "failed"):
        return True
    c = (code or "").strip().lower()
    return c in (
        "backup.failed",
        "backup.blocked_package_activity",
        "backup.write_io_error",
        "backup.inhibit_failed",
        "backup.failed_manifest_missing",
    )


def build_backup_failure_subject(job_id: str) -> str:
    jid = (job_id or "").strip() or "unknown"
    return f"Setuphelfer — Backup fehlgeschlagen ({jid})"


def build_backup_failure_body(
    *,
    job_id: str,
    status_code: str,
    backup_type: str = "",
    backup_profile: str = "",
    target_path: str = "",
    target_device: str = "",
    diagnosis_id: str = "",
    abort_reason: str = "",
    archive_path: str = "",
    partial_path: str = "",
    partial_deleted: bool | None = None,
    final_archive_exists: bool | None = None,
    runtime_seconds: int | None = None,
    bytes_written: int | None = None,
    tar_return_code: int | None = None,
    tar_warning_classification: str = "",
    error_excerpt: str = "",
    next_step: str = "",
) -> str:
    lines = [
        "Setuphelfer — Backup fehlgeschlagen",
        "",
        f"Job-ID: {job_id or '—'}",
        f"Status/Code: {status_code or '—'}",
    ]
    if diagnosis_id:
        lines.append(f"Diagnose: {diagnosis_id}")
    if abort_reason:
        lines.append(f"Abbruchgrund: {abort_reason}")
    if backup_type:
        lines.append(f"Backup-Typ: {backup_type}")
    if backup_profile:
        lines.append(f"Profil: {backup_profile}")
    if target_path:
        lines.append(f"Zielverzeichnis: {target_path}")
    if target_device:
        lines.append(f"Zielgerät: {target_device}")
    if runtime_seconds is not None:
        lines.append(f"Laufzeit: {runtime_seconds} s")
    if bytes_written is not None:
        lines.append(f"Bytes geschrieben: {bytes_written}")
    if final_archive_exists is not None:
        lines.append(f"Finales Archiv: {'ja' if final_archive_exists else 'nein'}")
    if partial_path:
        lines.append(f"Partial: {partial_path}")
    if partial_deleted is not None:
        lines.append(f"Partial gelöscht: {'ja' if partial_deleted else 'nein'}")
    if tar_return_code is not None:
        lines.append(f"tar_return_code: {tar_return_code}")
    if tar_warning_classification:
        lines.append(f"tar_warning_classification: {tar_warning_classification}")
    if error_excerpt:
        lines.append("")
        lines.append("Fehlerkern:")
        lines.append(error_excerpt[:800])
    lines.extend(
        [
            "",
            "Hinweis: Kein Restore ohne Verify Deep und finales Archiv.",
            next_step or "Nächster Schritt: Ursache beheben, Partial ggf. bereinigen, erneut testen.",
            "",
            "— Setuphelfer (automatische Benachrichtigung)",
        ]
    )
    return "\n".join(lines)


def send_backup_failure_email(
    *,
    job_id: str,
    status_code: str,
    backup_type: str = "",
    backup_profile: str = "",
    target_path: str = "",
    target_device: str = "",
    diagnosis_id: str = "",
    abort_reason: str = "",
    archive_path: str = "",
    partial_path: str = "",
    partial_deleted: bool | None = None,
    final_archive_exists: bool | None = None,
    runtime_seconds: int | None = None,
    bytes_written: int | None = None,
    tar_return_code: int | None = None,
    tar_warning_classification: str = "",
    error_excerpt: str = "",
    next_step: str = "",
    config: NotificationConfig | None = None,
    smtp_send: Any | None = None,
) -> EmailNotificationResult:
    cfg = config or load_notification_config()
    if not cfg.email_enabled:
        return EmailNotificationResult(status="skipped_disabled")
    if not cfg.email_fully_configured():
        return EmailNotificationResult(status="skipped_not_configured")

    masked = mask_email_address(cfg.email_to)
    subject = build_backup_failure_subject(job_id)
    body = build_backup_failure_body(
        job_id=job_id,
        status_code=status_code,
        backup_type=backup_type,
        backup_profile=backup_profile,
        target_path=target_path,
        target_device=target_device,
        diagnosis_id=diagnosis_id,
        abort_reason=abort_reason,
        archive_path=archive_path,
        partial_path=partial_path,
        partial_deleted=partial_deleted,
        final_archive_exists=final_archive_exists,
        runtime_seconds=runtime_seconds,
        bytes_written=bytes_written,
        tar_return_code=tar_return_code,
        tar_warning_classification=tar_warning_classification,
        error_excerpt=error_excerpt,
        next_step=next_step,
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
        err = _safe_smtp_error_message(exc)
        return EmailNotificationResult(status="failed", error=err, recipient_masked=masked)


def maybe_send_backup_failure_email(
    *,
    job_id: str,
    status: str,
    status_code: str,
    backup_type: str = "",
    backup_profile: str = "",
    target_path: str = "",
    target_device: str = "",
    diagnosis_id: str = "",
    abort_reason: str = "",
    archive_path: str = "",
    partial_path: str = "",
    partial_deleted: bool | None = None,
    final_archive_exists: bool | None = None,
    runtime_seconds: int | None = None,
    bytes_written: int | None = None,
    tar_return_code: int | None = None,
    tar_warning_classification: str = "",
    error_excerpt: str = "",
    next_step: str = "",
    config: NotificationConfig | None = None,
    smtp_send: Any | None = None,
) -> EmailNotificationResult:
    cfg = config or load_notification_config()
    if not should_notify_backup_failure(status=status, code=status_code, config=cfg):
        if not cfg.email_enabled:
            return EmailNotificationResult(status="skipped_disabled")
        if not cfg.email_fully_configured():
            return EmailNotificationResult(status="skipped_not_configured")
        return EmailNotificationResult(status="skipped_not_applicable")

    return send_backup_failure_email(
        job_id=job_id,
        status_code=status_code,
        backup_type=backup_type,
        backup_profile=backup_profile,
        target_path=target_path,
        target_device=target_device,
        diagnosis_id=diagnosis_id,
        abort_reason=abort_reason,
        archive_path=archive_path,
        partial_path=partial_path,
        partial_deleted=partial_deleted,
        final_archive_exists=final_archive_exists,
        runtime_seconds=runtime_seconds,
        bytes_written=bytes_written,
        tar_return_code=tar_return_code,
        tar_warning_classification=tar_warning_classification,
        error_excerpt=error_excerpt,
        next_step=next_step,
        config=cfg,
        smtp_send=smtp_send,
    )


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
        err = _safe_smtp_error_message(exc)
        return EmailNotificationResult(status="failed", error=err, recipient_masked=masked)


def _safe_smtp_error_message(exc: BaseException) -> str:
    text = str(exc)
    text = re.sub(r"(?i)(password|passwd|credential)[^\s]*", "[redacted]", text)
    text = re.sub(r"(?i)(auth[^\s]*\s*[:=]\s*)\S+", r"\1[redacted]", text)
    return text[:300]


def _smtp_login_and_send(smtp: smtplib.SMTP, cfg: NotificationConfig, msg: EmailMessage) -> None:
    if cfg.smtp_username:
        smtp.login(cfg.smtp_username, cfg.smtp_password)
    smtp.send_message(msg)


def _smtp_send_default(cfg: NotificationConfig, msg: EmailMessage) -> None:
    timeout = 60
    tls_context = ssl.create_default_context()
    if cfg.smtp_security == "ssl":
        with smtplib.SMTP_SSL(
            cfg.smtp_host,
            cfg.smtp_port,
            timeout=timeout,
            context=tls_context,
        ) as smtp:
            _smtp_login_and_send(smtp, cfg, msg)
        return
    with smtplib.SMTP(cfg.smtp_host, cfg.smtp_port, timeout=timeout) as smtp:
        if cfg.smtp_security == "starttls":
            smtp.starttls(context=tls_context)
        _smtp_login_and_send(smtp, cfg, msg)


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
        "notification_error_class": (result.error or "")[:120] if result.error else None,
        "notification_status": result.status,
        "notification_email_to_configured": bool(c.email_to),
        "notification_email_recipient_masked": result.recipient_masked
        or (mask_email_address(c.email_to) if c.email_to else None),
    }
