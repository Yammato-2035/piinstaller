from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Any

from core.dev_dashboard import _effective_workspace_root
from core.eventbus import publish_fire_and_forget
from core.install_paths import get_install_profile, get_state_dir
from core.notification_email import current_email_status, send_email_for_event
from core.notification_events import (
    build_rescue_iso_failure_event,
    coerce_notification_event,
    load_rescue_summary,
    rescue_failure_source_key,
    rescue_summary_indicates_failure,
)
from core.notification_settings import classify_smtp_error

_LOCK = threading.Lock()
_NOTIFICATION_DIR_REL = Path("docs/evidence/runtime-results/notifications")
_RUNTIME_NOTIFICATION_DIR = Path("notifications")
_EVENTS_FILENAME = "notification_events.jsonl"
_SUMMARY_FILENAME = "notification_latest_summary.json"


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent


def _workspace_root() -> Path:
    repo = _repo_root().resolve(strict=False)
    try:
        return _effective_workspace_root(repo).resolve(strict=False)
    except OSError:
        return repo


def _notification_dir(root: Path | None = None) -> Path:
    if root is not None:
        base = root.resolve(strict=False)
        if base.name == _NOTIFICATION_DIR_REL.name:
            return base
        return (base / _NOTIFICATION_DIR_REL).resolve(strict=False)
    if get_install_profile() == "opt":
        return (get_state_dir() / _RUNTIME_NOTIFICATION_DIR).resolve(strict=False)
    return (_workspace_root() / _NOTIFICATION_DIR_REL).resolve(strict=False)


def _events_path(notification_dir: Path | None = None) -> Path:
    return (_notification_dir(notification_dir) / _EVENTS_FILENAME).resolve(strict=False)


def _summary_path(notification_dir: Path | None = None) -> Path:
    return (_notification_dir(notification_dir) / _SUMMARY_FILENAME).resolve(strict=False)


def _repo_rel(root: Path, path: Path) -> str:
    try:
        return path.resolve(strict=False).relative_to(root.resolve(strict=False)).as_posix()
    except (OSError, ValueError):
        return str(path)


def _write_json(path: Path, body: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(body, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    tmp.replace(path)


def _append_event(path: Path, event: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False) + "\n")


def _normalize_historical_event(event: dict[str, Any]) -> dict[str, Any]:
    body = dict(event)
    email_error = str(body.get("email_error") or "")
    derived = classify_smtp_error(email_error)
    current = str(body.get("classification") or body.get("email_error_class") or "").strip() or None
    if derived == "notification.email.provider_limit_exceeded":
        body["email_error_class"] = derived
        body["classification"] = derived
        body["next_action"] = str(body.get("next_action") or "check_smtp_provider_limit_or_wait")
        body["email_error"] = "554 5.7.0 outgoing message limit exceeded"
    elif current and not body.get("classification"):
        body["classification"] = current
    return body


def _read_events(notification_dir: Path | None = None) -> list[dict[str, Any]]:
    path = _events_path(notification_dir)
    if not path.is_file():
        return []
    events: list[dict[str, Any]] = []
    try:
        with path.open(encoding="utf-8") as handle:
            for line in handle:
                raw = line.strip()
                if not raw:
                    continue
                try:
                    item = json.loads(raw)
                except json.JSONDecodeError:
                    continue
                if isinstance(item, dict):
                    events.append(_normalize_historical_event(item))
    except OSError:
        return []
    events.sort(key=lambda item: str(item.get("created_at") or ""), reverse=True)
    return events


def _publish_event(event: dict[str, Any]) -> None:
    payload = {
        "module": "dev_dashboard.notifications",
        "event_id": event.get("event_id"),
        "event_type": event.get("event_type"),
        "severity": event.get("severity"),
        "title": event.get("title"),
        "message": event.get("message"),
        "email_status": event.get("email_status"),
    }
    publish_fire_and_forget("module.state.changed", payload)


def _summary_status(events: list[dict[str, Any]], email: dict[str, Any]) -> str:
    if events:
        return "green"
    if email.get("status") in {"not_configured", "disabled"}:
        return "yellow"
    return "gray"


def _effective_email_summary(events: list[dict[str, Any]], base_email: dict[str, Any]) -> dict[str, Any]:
    email = dict(base_email)
    status = str(base_email.get("status") or "unknown")
    severity = "green" if status == "ready" else ("yellow" if status == "not_configured" else "gray")
    classification = None
    next_action = None
    relevant = next(
        (
            item
            for item in events
            if item.get("email_requested") or str(item.get("email_status") or "") not in {"", "disabled"}
        ),
        None,
    )
    if relevant is not None:
        event_status = str(relevant.get("email_status") or status)
        classification = relevant.get("classification") or relevant.get("email_error_class")
        next_action = relevant.get("next_action")
        if event_status == "sent":
            status = "sent"
            severity = "green"
        elif event_status == "not_configured":
            status = "not_configured"
            severity = "yellow"
        elif event_status == "failed" and classification == "notification.email.provider_limit_exceeded":
            status = "provider_limit"
            severity = "yellow"
            next_action = str(next_action or "check_smtp_provider_limit_or_wait")
        elif event_status == "failed":
            status = "failed"
            severity = "yellow"
            next_action = str(next_action or "inspect_smtp_error")
        elif event_status == "disabled":
            status = "disabled"
            severity = "gray"
        email["last_delivery_status"] = event_status
        email["last_delivery_event_type"] = relevant.get("event_type")
    email["status"] = status
    email["severity"] = severity
    email["classification"] = classification
    email["next_action"] = next_action
    return email


def _build_notification_summary(
    workspace_root: Path,
    notification_dir: Path,
    *,
    sync_rescue: bool,
) -> dict[str, Any]:
    if sync_rescue:
        sync_rescue_failure_notification(workspace_root=workspace_root, notification_dir=notification_dir)
    events = _read_events(notification_dir)
    email = _effective_email_summary(events, current_email_status())
    latest = events[0] if events else None
    return {
        "status": _summary_status(events, email),
        "generated_at": latest.get("created_at") if latest else None,
        "event_count": len(events),
        "last_event": latest,
        "dashboard": {
            "status": "green" if events else "yellow",
            "visible_event_count": len([item for item in events if item.get("dashboard_visible")]),
        },
        "email": email,
        "events_path": _repo_rel(workspace_root, _events_path(notification_dir)),
        "summary_path": _repo_rel(workspace_root, _summary_path(notification_dir)),
    }


def build_notification_summary(
    *,
    workspace_root: Path | None = None,
    notification_dir: Path | None = None,
) -> dict[str, Any]:
    ws_root = (workspace_root or _workspace_root()).resolve(strict=False)
    notif_dir = _notification_dir(notification_dir)
    return _build_notification_summary(ws_root, notif_dir, sync_rescue=True)


def emit_notification_event(
    event: dict[str, Any],
    *,
    smtp_send: Any | None = None,
    workspace_root: Path | None = None,
    notification_dir: Path | None = None,
) -> dict[str, Any]:
    ws_root = (workspace_root or _workspace_root()).resolve(strict=False)
    notif_dir = _notification_dir(notification_dir)
    with _LOCK:
        body = coerce_notification_event(event)
        body = send_email_for_event(body, smtp_send=smtp_send)
        _append_event(_events_path(notif_dir), body)
        _write_json(_summary_path(notif_dir), _build_notification_summary(ws_root, notif_dir, sync_rescue=False))
    _publish_event(body)
    return body


def list_notification_events(
    limit: int = 50,
    *,
    workspace_root: Path | None = None,
    notification_dir: Path | None = None,
) -> dict[str, Any]:
    ws_root = (workspace_root or _workspace_root()).resolve(strict=False)
    notif_dir = _notification_dir(notification_dir)
    sync_rescue_failure_notification(workspace_root=ws_root, notification_dir=notif_dir)
    events = _read_events(notif_dir)[: max(1, int(limit or 50))]
    email = _effective_email_summary(_read_events(notif_dir), current_email_status())
    return {
        "status": _summary_status(events, email),
        "event_count": len(_read_events(notif_dir)),
        "events": events,
        "email": email,
        "events_path": _repo_rel(ws_root, _events_path(notif_dir)),
    }


def sync_rescue_failure_notification(
    *,
    workspace_root: Path | None = None,
    notification_dir: Path | None = None,
) -> dict[str, Any] | None:
    ws_root = (workspace_root or _workspace_root()).resolve(strict=False)
    notif_dir = _notification_dir(notification_dir)
    summary = load_rescue_summary(ws_root)
    if not rescue_summary_indicates_failure(summary):
        return None
    assert summary is not None
    source_key = rescue_failure_source_key(summary)
    events = _read_events(notif_dir)
    for item in events:
        if item.get("event_type") == "rescue_iso_build_failed" and item.get("source_state_key") == source_key:
            _write_json(_summary_path(notif_dir), _build_notification_summary(ws_root, notif_dir, sync_rescue=False))
            return item
    event = build_rescue_iso_failure_event(summary)
    return emit_notification_event(event, workspace_root=ws_root, notification_dir=notif_dir)
