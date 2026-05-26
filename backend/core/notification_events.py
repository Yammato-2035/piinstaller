from __future__ import annotations

import json
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

UTC = timezone.utc

VALID_SEVERITIES = frozenset({"info", "warning", "error", "critical"})
VALID_EMAIL_STATUSES = frozenset({"not_configured", "queued", "sent", "failed", "disabled"})
VALID_AREAS = frozenset({"rescue", "runtime", "deploy", "backup", "restore", "packaging", "dev_dashboard"})
REQUIRED_EVENT_TYPES = frozenset(
    {
        "rescue_iso_build_failed",
        "rescue_iso_build_success",
        "rescue_usb_write_blocked",
        "rescue_usb_write_started",
        "rescue_usb_write_failed",
        "rescue_usb_write_success",
        "runtime_gate_failed",
        "deploy_helper_failed",
        "deploy_helper_success",
        "backup_failed",
        "backup_success",
        "restore_blocked",
        "restore_failed",
        "restore_success",
    }
)
REQUIRED_FIELDS = (
    "event_id",
    "created_at",
    "severity",
    "area",
    "event_type",
    "title",
    "message",
    "technical_summary",
    "evidence_paths",
    "dashboard_visible",
    "email_requested",
    "email_status",
    "email_error",
    "acknowledged",
)
_SUMMARY_REL = Path("docs/evidence/runtime-results/rescue/controlled_iso_build_latest_summary.json")
_DEFAULT_RESCUE_EVIDENCE_PATHS = [
    "docs/evidence/rescue/RESCUE_CONTROLLED_ISO_BUILD_RESULT.md",
    "docs/evidence/rescue/RESCUE_USB_WRITE_RESULT.md",
    "docs/evidence/rescue/RESCUE_ISO_RSVG_FAILURE_ANALYSIS.md",
    "docs/evidence/runtime-results/rescue/controlled_iso_build_latest_summary.json",
    "docs/evidence/runtime-results/rescue/controlled_usb_write_latest_summary.json",
    "docs/roadmap/STATUS_MATRIX.md",
]
_SECRET_PATTERNS = (
    re.compile(r"(?i)\b(password|passwd|secret|token|api[_-]?key|smtp_password)\b\s*[:=]\s*\S+"),
    re.compile(r"(?i)\bauthorization\s*[:=]\s*\S+"),
)


def _now_iso() -> str:
    return datetime.now(tz=UTC).isoformat()


def _sanitize_text(value: Any) -> str:
    text = str(value or "").strip()
    for pattern in _SECRET_PATTERNS:
        text = pattern.sub("[redacted]", text)
    text = re.sub(r"(?i)(password|passwd|secret|token|api[_-]?key)\s*[:=]\s*\S+", r"\1=[redacted]", text)
    return text[:4000]


def _sanitize_evidence_paths(values: Any) -> list[str]:
    if not isinstance(values, list):
        return []
    out: list[str] = []
    for item in values:
        text = str(item or "").strip()
        if not text:
            continue
        out.append(text[:500])
    return out[:20]


def normalize_area(area: str | None) -> str:
    raw = str(area or "").strip().lower().replace("-", "_")
    if raw == "devdashboard":
        raw = "dev_dashboard"
    return raw if raw in VALID_AREAS else "runtime"


def rescue_failure_source_key(summary: dict[str, Any]) -> str:
    primary_error = _sanitize_text(summary.get("primary_error") or summary.get("last_error"))
    updated_at = str(summary.get("updated_at") or "")
    exit_code = summary.get("last_exit_code")
    return f"rescue_iso_build_failed:{exit_code}:{primary_error}:{updated_at}"


def coerce_notification_event(event: dict[str, Any]) -> dict[str, Any]:
    body = {
        "event_id": str(event.get("event_id") or uuid.uuid4().hex),
        "created_at": str(event.get("created_at") or _now_iso()),
        "severity": str(event.get("severity") or "info").strip().lower(),
        "area": normalize_area(str(event.get("area") or "")),
        "event_type": str(event.get("event_type") or "notification_event").strip(),
        "title": _sanitize_text(event.get("title")),
        "message": _sanitize_text(event.get("message")),
        "technical_summary": _sanitize_text(event.get("technical_summary")),
        "evidence_paths": _sanitize_evidence_paths(event.get("evidence_paths")),
        "dashboard_visible": bool(event.get("dashboard_visible", True)),
        "email_requested": bool(event.get("email_requested", True)),
        "email_status": str(
            event.get("email_status")
            or ("disabled" if not bool(event.get("email_requested", True)) else "not_configured")
        ).strip(),
        "email_error": _sanitize_text(event.get("email_error")) or None,
        "acknowledged": bool(event.get("acknowledged", False)),
    }
    if "source_state_key" in event:
        body["source_state_key"] = _sanitize_text(event.get("source_state_key"))
    if "email_recipient_masked" in event:
        body["email_recipient_masked"] = _sanitize_text(event.get("email_recipient_masked")) or None
    if "email_error_class" in event:
        body["email_error_class"] = _sanitize_text(event.get("email_error_class")) or None
    if "classification" in event:
        body["classification"] = _sanitize_text(event.get("classification")) or None
    if "next_action" in event:
        body["next_action"] = _sanitize_text(event.get("next_action")) or None
    validate_notification_event(body)
    return body


def validate_notification_event(event: dict[str, Any]) -> None:
    missing = [field for field in REQUIRED_FIELDS if field not in event]
    if missing:
        raise ValueError(f"notification_event_missing_fields:{','.join(missing)}")
    if str(event.get("severity") or "") not in VALID_SEVERITIES:
        raise ValueError("notification_event_invalid_severity")
    if str(event.get("email_status") or "") not in VALID_EMAIL_STATUSES:
        raise ValueError("notification_event_invalid_email_status")
    if str(event.get("area") or "") not in VALID_AREAS:
        raise ValueError("notification_event_invalid_area")
    if not isinstance(event.get("evidence_paths"), list):
        raise ValueError("notification_event_invalid_evidence_paths")
    blob = json.dumps(
        {
            "title": event.get("title"),
            "message": event.get("message"),
            "technical_summary": event.get("technical_summary"),
            "email_error": event.get("email_error"),
        },
        ensure_ascii=False,
    )
    if "[redacted]" not in blob:
        for pattern in _SECRET_PATTERNS:
            if pattern.search(blob):
                raise ValueError("notification_event_contains_secret")


def load_rescue_summary(repo_root: Path) -> dict[str, Any] | None:
    path = (repo_root / _SUMMARY_REL).resolve(strict=False)
    try:
        if not path.is_file():
            return None
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return raw if isinstance(raw, dict) else None


def rescue_summary_indicates_failure(summary: dict[str, Any] | None) -> bool:
    if not isinstance(summary, dict):
        return False
    raw_status = str(summary.get("status") or "").strip().lower()
    dashboard_status = str(summary.get("dashboard_status_after_failure") or (summary.get("dashboard_state") or {}).get("status") or "").strip().lower()
    exit_code = summary.get("last_exit_code")
    primary_error = _sanitize_text(summary.get("primary_error") or summary.get("last_error"))
    iso_found = bool(summary.get("iso_found"))
    return (
        raw_status in {"failed", "blocked", "error"}
        or dashboard_status == "red"
        or (isinstance(exit_code, int) and exit_code != 0)
        or (not iso_found and "rsvg" in primary_error.lower())
    )


def build_rescue_iso_failure_event(
    summary: dict[str, Any],
    *,
    evidence_paths: list[str] | None = None,
) -> dict[str, Any]:
    exit_code = summary.get("last_exit_code")
    primary_error = _sanitize_text(summary.get("primary_error") or summary.get("last_error"))
    iso_found = bool(summary.get("iso_found"))
    next_action = _sanitize_text(
        summary.get("next_required_action")
        or (summary.get("dashboard_state") or {}).get("next_operator_action", {}).get("type")
        or "fix_missing_rsvg_or_remove_rsvg_dependency"
    )
    dashboard_status = _sanitize_text(
        summary.get("dashboard_status_after_failure") or (summary.get("dashboard_state") or {}).get("status") or "red"
    )
    technical_summary = (
        f"LB_EXIT={exit_code}; primary_error={primary_error}; iso_found={str(iso_found).lower()}; "
        f"dashboard_status_after_failure={dashboard_status}; next_required_action={next_action}; "
        f"usb_write_started={str(bool(summary.get('usb_write_started'))).lower()}"
    )
    message = (
        f"LB_EXIT={exit_code}; rsvg fehlt; keine ISO erzeugt; USB nicht gestartet; "
        f"naechste erforderliche Aktion: {next_action}"
    )
    return coerce_notification_event(
        {
            "created_at": str(summary.get("updated_at") or _now_iso()),
            "severity": "error",
            "area": "rescue",
            "event_type": "rescue_iso_build_failed",
            "title": "Rescue ISO Build fehlgeschlagen",
            "message": message,
            "technical_summary": technical_summary,
            "evidence_paths": evidence_paths or list(_DEFAULT_RESCUE_EVIDENCE_PATHS),
            "dashboard_visible": True,
            "email_requested": True,
            "email_status": "not_configured",
            "email_error": None,
            "acknowledged": False,
            "source_state_key": rescue_failure_source_key(summary),
        }
    )
