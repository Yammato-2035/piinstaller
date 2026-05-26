"""Read/write /etc/setuphelfer/notification.env for backup e-mail settings (no secrets in API responses)."""

from __future__ import annotations

import logging
import os
import re
import tempfile
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

from core.install_paths import get_config_dir, get_state_dir
from core.notification_service import (
    EmailNotificationResult,
    NotificationConfig,
    SMTP_SECURITY_MODES,
    load_notification_config,
    normalize_smtp_security,
    send_backup_success_email,
)

NOTIFICATION_ENV_FILENAME = "notification.env"
TEST_META_FILENAME = "notification_email_test_meta.json"

ENV_KEYS = {
    "enabled": "SETUPHELFER_NOTIFY_EMAIL_ENABLED",
    "on_backup_success": "SETUPHELFER_NOTIFY_ON_BACKUP_SUCCESS",
    "on_backup_failure": "SETUPHELFER_NOTIFY_ON_BACKUP_FAILURE",
    "email_to": "SETUPHELFER_NOTIFY_EMAIL_TO",
    "email_from": "SETUPHELFER_NOTIFY_EMAIL_FROM",
    "smtp_host": "SETUPHELFER_NOTIFY_SMTP_HOST",
    "smtp_port": "SETUPHELFER_NOTIFY_SMTP_PORT",
    "smtp_username": "SETUPHELFER_NOTIFY_SMTP_USERNAME",
    "smtp_password": "SETUPHELFER_NOTIFY_SMTP_PASSWORD",
    "smtp_starttls": "SETUPHELFER_NOTIFY_SMTP_STARTTLS",
    "smtp_security": "SETUPHELFER_NOTIFY_SMTP_SECURITY",
}

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def notification_env_path() -> Path:
    return get_config_dir() / NOTIFICATION_ENV_FILENAME


def notification_test_meta_path() -> Path:
    return get_state_dir() / TEST_META_FILENAME


def parse_env_file(path: Path) -> dict[str, str]:
    """Parse KEY=value lines; never raises (invalid UTF-8, I/O, malformed lines)."""
    if not path.is_file():
        return {}
    try:
        raw = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return {}
    out: dict[str, str] = {}
    for line in raw.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        key = k.strip()
        if not key:
            continue
        out[key] = v.strip()
    return out


def _bool_to_env(value: bool) -> str:
    return "true" if value else "false"


def _env_to_bool(raw: str | None, default: bool = False) -> bool:
    if raw is None or not str(raw).strip():
        return default
    return str(raw).strip().lower() in ("1", "true", "yes", "on")


def validate_email_field(value: str, field: str) -> None:
    v = (value or "").strip()
    if not v:
        raise ValueError(f"{field} ist erforderlich")
    if not _EMAIL_RE.match(v):
        raise ValueError(f"{field} ist keine gültige E-Mail-Adresse")


def validate_port(port: int) -> None:
    if not isinstance(port, int) or port < 1 or port > 65535:
        raise ValueError("smtp_port muss zwischen 1 und 65535 liegen")


def classify_smtp_error(error: str | None) -> str | None:
    if not error:
        return None
    low = error.lower()
    if (
        "554" in low
        and "5.7.0" in low
        and (
            "limit on the number of allowed outgoing messages was exceeded" in low
            or "outgoing message limit exceeded" in low
            or "sending limit exceeded" in low
            or "rate limit" in low
            or "quota" in low
        )
    ):
        return "notification.email.provider_limit_exceeded"
    if (
        "535" in low
        or "badcredentials" in low
        or "username and" in low
        or "authentication" in low
        or "smtpauthenticationerror" in low
    ):
        return "smtp_auth_failed"
    if (
        "ssl" in low
        or "tls" in low
        or "certificate" in low
        or "wrap_socket" in low
        or "sslerror" in low
    ):
        return "smtp_tls_failed"
    if "connection refused" in low or "timed out" in low or "gaierror" in low or "connect" in low:
        return "smtp_connection_failed"
    return "smtp_send_failed"


def config_from_env_map(env: dict[str, str]) -> NotificationConfig:
    port_raw = env.get(ENV_KEYS["smtp_port"], "587")
    try:
        port = int(port_raw)
    except ValueError:
        port = 587
    starttls = _env_to_bool(env.get(ENV_KEYS["smtp_starttls"]), default=True)
    security = normalize_smtp_security(
        env.get(ENV_KEYS["smtp_security"]),
        port=port,
        smtp_starttls=starttls,
    )
    return NotificationConfig(
        email_enabled=_env_to_bool(env.get(ENV_KEYS["enabled"])),
        email_to=(env.get(ENV_KEYS["email_to"]) or "").strip(),
        email_from=(env.get(ENV_KEYS["email_from"]) or "").strip(),
        smtp_host=(env.get(ENV_KEYS["smtp_host"]) or "").strip(),
        smtp_port=port,
        smtp_username=(env.get(ENV_KEYS["smtp_username"]) or "").strip(),
        smtp_password=(env.get(ENV_KEYS["smtp_password"]) or "").strip(),
        smtp_security=security,
        smtp_starttls=security == "starttls",
        notify_on_backup_success=_env_to_bool(env.get(ENV_KEYS["on_backup_success"]), default=True),
        notify_on_backup_failure=_env_to_bool(env.get(ENV_KEYS["on_backup_failure"]), default=False),
    )


def load_effective_notification_config() -> NotificationConfig:
    """Prefer notification.env on disk, then process environment."""
    path = notification_env_path()
    if path.is_file():
        return config_from_env_map(parse_env_file(path))
    return load_notification_config()


def apply_env_file_to_process(path: Path | None = None) -> None:
    p = path or notification_env_path()
    for k, v in parse_env_file(p).items():
        os.environ[k] = v


def read_test_meta() -> dict[str, Any]:
    p = notification_test_meta_path()
    if not p.is_file():
        return {}
    try:
        import json

        data = json.loads(p.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def write_test_meta(status: str, error_class: str | None = None) -> None:
    import json
    from datetime import datetime, timezone

    p = notification_test_meta_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "last_test_status": status,
        "last_test_error_class": error_class,
        "last_test_at": datetime.now(timezone.utc).isoformat(),
    }
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    os.replace(tmp, p)


def build_public_settings() -> dict[str, Any]:
    """Public notification UI state; never raises (no secrets in return value)."""
    try:
        return _build_public_settings_impl()
    except Exception as exc:
        logger.warning("build_public_settings failed: %s", type(exc).__name__, exc_info=True)
        p = notification_env_path()
        return {
            "enabled": False,
            "on_backup_success": True,
            "on_backup_failure": False,
            "email_to": "",
            "email_from": "",
            "smtp_host": "",
            "smtp_port": 587,
            "smtp_username": "",
            "smtp_security": "starttls",
            "smtp_starttls": True,
            "smtp_password_set": False,
            "configured": False,
            "env_path": str(p),
            "env_writable": can_write_notification_env_direct(),
            "last_test_status": "unknown",
            "last_test_error_class": "settings_read_failed",
        }


def _build_public_settings_impl() -> dict[str, Any]:
    cfg = load_effective_notification_config()
    meta = read_test_meta()
    configured = cfg.email_fully_configured() and bool(cfg.smtp_password or False)
    if cfg.email_fully_configured() and cfg.smtp_password:
        configured = True
    elif cfg.email_fully_configured():
        # host/user/to/from ok; password may exist on disk but empty in parsed cfg
        env_map = parse_env_file(notification_env_path())
        configured = bool((env_map.get(ENV_KEYS["smtp_password"]) or "").strip())

    return {
        "enabled": cfg.email_enabled,
        "on_backup_success": cfg.notify_on_backup_success,
        "on_backup_failure": cfg.notify_on_backup_failure,
        "email_to": cfg.email_to,
        "email_from": cfg.email_from,
        "smtp_host": cfg.smtp_host,
        "smtp_port": cfg.smtp_port,
        "smtp_username": cfg.smtp_username,
        "smtp_security": cfg.smtp_security,
        "smtp_starttls": cfg.smtp_starttls,
        "smtp_password_set": bool((parse_env_file(notification_env_path()).get(ENV_KEYS["smtp_password"]) or "").strip()),
        "configured": configured,
        "env_path": str(notification_env_path()),
        "env_writable": can_write_notification_env_direct(),
        "last_test_status": meta.get("last_test_status") or "unknown",
        "last_test_error_class": meta.get("last_test_error_class"),
    }


def can_write_notification_env_direct() -> bool:
    """True when notification.env can be created/updated without sudo (ReadWritePaths + Unix perms)."""
    path = notification_env_path()
    if path.exists() and os.access(path, os.W_OK):
        return True
    parent = path.parent
    return parent.is_dir() and os.access(parent, os.W_OK)


def serialize_env_lines(env_map: dict[str, str]) -> str:
    lines = [
        "# Setuphelfer backup notification (managed via API/UI; do not commit)",
        "",
    ]
    order = [
        ENV_KEYS["enabled"],
        ENV_KEYS["on_backup_success"],
        ENV_KEYS["on_backup_failure"],
        ENV_KEYS["email_to"],
        ENV_KEYS["email_from"],
        ENV_KEYS["smtp_host"],
        ENV_KEYS["smtp_port"],
        ENV_KEYS["smtp_username"],
        ENV_KEYS["smtp_password"],
        ENV_KEYS["smtp_security"],
        ENV_KEYS["smtp_starttls"],
    ]
    for key in order:
        if key in env_map:
            lines.append(f"{key}={env_map[key]}")
    return "\n".join(lines) + "\n"


def merge_settings_payload(payload: dict[str, Any]) -> tuple[dict[str, str], list[str]]:
    """Return merged env map and validation errors."""
    errors: list[str] = []
    path = notification_env_path()
    current = parse_env_file(path) if path.is_file() else {}

    enabled = bool(payload.get("enabled", _env_to_bool(current.get(ENV_KEYS["enabled"]))))
    on_success = bool(
        payload.get(
            "on_backup_success",
            _env_to_bool(current.get(ENV_KEYS["on_backup_success"]), default=True),
        )
    )
    on_failure = bool(
        payload.get(
            "on_backup_failure",
            _env_to_bool(current.get(ENV_KEYS["on_backup_failure"]), default=False),
        )
    )

    email_to = str(payload.get("email_to", current.get(ENV_KEYS["email_to"], ""))).strip()
    email_from = str(payload.get("email_from", current.get(ENV_KEYS["email_from"], ""))).strip()
    smtp_host = str(payload.get("smtp_host", current.get(ENV_KEYS["smtp_host"], ""))).strip()
    smtp_username = str(payload.get("smtp_username", current.get(ENV_KEYS["smtp_username"], ""))).strip()

    try:
        port = int(payload.get("smtp_port", current.get(ENV_KEYS["smtp_port"], 587)))
        validate_port(port)
    except (TypeError, ValueError) as e:
        errors.append(str(e))
        port = 587

    smtp_starttls_legacy = bool(
        payload.get(
            "smtp_starttls",
            _env_to_bool(current.get(ENV_KEYS["smtp_starttls"]), default=True),
        )
    )
    security_raw = payload.get("smtp_security")
    if security_raw is not None:
        security = str(security_raw).strip().lower()
        if security not in SMTP_SECURITY_MODES:
            errors.append("smtp_security muss starttls, ssl oder none sein")
            security = normalize_smtp_security(
                current.get(ENV_KEYS["smtp_security"]),
                port=port,
                smtp_starttls=smtp_starttls_legacy,
            )
    else:
        security = normalize_smtp_security(
            current.get(ENV_KEYS["smtp_security"]),
            port=port,
            smtp_starttls=smtp_starttls_legacy,
        )

    if port == 465 and security == "starttls":
        errors.append(
            "Port 465 erwartet smtp_security=ssl (implizites TLS). "
            "Für STARTTLS typischerweise Port 587."
        )
    if port == 587 and security == "ssl":
        errors.append(
            "Port 587 mit smtp_security=ssl ist unüblich; für STARTTLS smtp_security=starttls wählen."
        )

    new_password = payload.get("smtp_password")
    if new_password is not None and str(new_password).strip():
        password = str(new_password).strip()
    else:
        password = (current.get(ENV_KEYS["smtp_password"]) or "").strip()

    if enabled or email_to or smtp_host:
        for label, val, field in (
            ("email_to", email_to, "email_to"),
            ("email_from", email_from, "email_from"),
        ):
            try:
                if val:
                    validate_email_field(val, field)
            except ValueError as e:
                errors.append(str(e))

    env_map = {
        ENV_KEYS["enabled"]: _bool_to_env(enabled),
        ENV_KEYS["on_backup_success"]: _bool_to_env(on_success),
        ENV_KEYS["on_backup_failure"]: _bool_to_env(on_failure),
        ENV_KEYS["email_to"]: email_to,
        ENV_KEYS["email_from"]: email_from,
        ENV_KEYS["smtp_host"]: smtp_host,
        ENV_KEYS["smtp_port"]: str(port),
        ENV_KEYS["smtp_username"]: smtp_username,
        ENV_KEYS["smtp_password"]: password,
        ENV_KEYS["smtp_security"]: security,
        ENV_KEYS["smtp_starttls"]: _bool_to_env(security == "starttls"),
    }
    return env_map, errors


def write_notification_env_atomic(env_map: dict[str, str]) -> None:
    path = notification_env_path()
    content = serialize_env_lines(env_map)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix="notification.env.", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(content)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp_name, path)
        try:
            os.chmod(path, 0o660)
        except OSError:
            pass
    finally:
        if os.path.exists(tmp_name):
            try:
                os.unlink(tmp_name)
            except OSError:
                pass


def staging_path() -> Path:
    return get_state_dir() / ".notification.env.staging"


def write_notification_env_via_staging(env_map: dict[str, str]) -> Path:
    staging = staging_path()
    staging.parent.mkdir(parents=True, exist_ok=True)
    content = serialize_env_lines(env_map)
    fd, tmp = tempfile.mkstemp(prefix="notification.staging.", dir=str(staging.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(content)
            fh.flush()
            os.fsync(fh.fileno())
        os.chmod(tmp, 0o600)
        os.replace(tmp, staging)
    finally:
        if os.path.exists(tmp):
            try:
                os.unlink(tmp)
            except OSError:
                pass
    return staging


def operator_install_commands(staging: Path) -> list[str]:
    dest = notification_env_path()
    return [
        "# Drop-in (ReadWritePaths) — siehe packaging/.../notification-env.conf.example",
        "sudo cp packaging/systemd/setuphelfer-backend.service.d/notification-env.conf.example "
        "/etc/systemd/system/setuphelfer-backend.service.d/notification-env.conf",
        f"sudo install -o root -g setuphelfer -m 660 {staging} {dest}",
        "sudo systemctl daemon-reload",
        "sudo systemctl restart setuphelfer-backend.service",
    ]


def save_notification_settings(
    payload: dict[str, Any],
    *,
    sudo_install: Any | None = None,
) -> dict[str, Any]:
    """
    sudo_install: callable(staging_path) -> bool when direct write is not allowed.
    """
    env_map, errors = merge_settings_payload(payload)
    if errors:
        return {"status": "error", "message": "; ".join(errors), "validation_errors": errors}

    if can_write_notification_env_direct():
        try:
            write_notification_env_atomic(env_map)
            apply_env_file_to_process()
            return {"status": "success", "write_status": "written", "message": "Einstellungen gespeichert"}
        except OSError as e:
            return {
                "status": "error",
                "write_status": "write_failed",
                "message": "Speichern fehlgeschlagen (Dateisystem / Rechte).",
                "error_class": type(e).__name__,
            }

    staging = write_notification_env_via_staging(env_map)
    if sudo_install is not None:
        if sudo_install(staging):
            try:
                staging.unlink(missing_ok=True)
            except OSError:
                pass
            apply_env_file_to_process()
            return {
                "status": "success",
                "write_status": "written_via_sudo",
                "message": "Einstellungen gespeichert (Administrator)",
            }
        return {
            "status": "error",
            "write_status": "sudo_install_failed",
            "message": (
                "Speichern mit Administratorrechten fehlgeschlagen "
                "(sudo ist im Backend-Dienst durch NoNewPrivileges blockiert)"
            ),
            "operator_commands": operator_install_commands(staging),
        }

    return {
        "status": "error",
        "write_status": "requires_operator_write",
        "message": (
            "notification.env ist nicht beschreibbar. Drop-in mit ReadWritePaths=/etc/setuphelfer "
            "installieren und Dienst neu starten (siehe operator_commands)."
        ),
        "operator_commands": operator_install_commands(staging),
    }


def run_notification_test_email(
    *,
    smtp_send: Any | None = None,
) -> dict[str, Any]:
    cfg = load_effective_notification_config()
    if not cfg.email_enabled:
        write_test_meta("skipped_disabled")
        return {
            "status": "skipped_disabled",
            "error_class": None,
            "message": "E-Mail-Benachrichtigungen sind deaktiviert",
            "email_to": cfg.email_to,
        }
    if not cfg.email_fully_configured() or not cfg.smtp_password:
        write_test_meta("skipped_not_configured")
        return {
            "status": "skipped_not_configured",
            "error_class": None,
            "message": "SMTP ist nicht vollständig konfiguriert",
            "email_to": cfg.email_to,
        }

    result: EmailNotificationResult = send_backup_success_email(
        job_id="notification-ui-test",
        status_code="backup.success",
        backup_type="test",
        backup_profile="settings-test",
        target_path="/media/setuphelfer/br001",
        archive_path="/selftest/no-real-archive.tar.gz",
        manifest_hash="notification-ui-test",
        verify_deep_ok=True,
        config=cfg,
        smtp_send=smtp_send,
    )
    err_class = classify_smtp_error(result.error)
    if result.sent:
        write_test_meta("sent")
        return {
            "status": "sent",
            "error_class": None,
            "message": "Testmail wurde gesendet",
            "email_to": cfg.email_to,
        }
    write_test_meta("failed", err_class)
    return {
        "status": "failed",
        "error_class": err_class,
        "message": "Testmail konnte nicht gesendet werden",
        "email_to": cfg.email_to,
    }
