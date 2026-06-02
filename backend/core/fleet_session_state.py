"""Host-seitige Fleet-Session-State für lokale Lab-/QEMU-Smokes (Phase 1, read-only UI)."""

from __future__ import annotations

import json
import os
import socket
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

UTC = timezone.utc

FLEET_SESSIONS_REL = Path("docs/evidence/runtime-results/dev-dashboard")
JSONL_NAME = "fleet_sessions.jsonl"
LATEST_NAME = "fleet_sessions_latest.json"

SESSION_TYPES = frozenset({"local_qemu_smoke", "local_agent_smoke", "local_manual_lab"})
STATUSES = frozenset(
    {
        "queued",
        "starting",
        "proxy_starting",
        "proxy_ready",
        "qemu_starting",
        "booting",
        "autopilot_waiting",
        "guest_report_seen",
        "serial_active",
        "serial_empty",
        "timeout_warning",
        "timeout",
        "failed",
        "success",
        "cancelled",
        "unknown",
    }
)
TERMINAL_STATUSES = frozenset({"timeout", "failed", "success", "cancelled"})
RUNNING_STATUSES = STATUSES - TERMINAL_STATUSES - frozenset({"unknown", "queued"})
SEVERITIES = frozenset({"info", "warning", "error"})
AGENT_STATES = frozenset({"alive", "booting", "checking", "degraded", "stalled", "finished"})

FORBIDDEN_ROUTE_FRAGMENTS = (
    "/execute",
    "/start",
    "/stop",
    "/revive",
    "/control",
    "/ssh",
    "/remote",
)


class FleetSessionError(Exception):
    def __init__(self, code: str, errors: list[str] | None = None) -> None:
        super().__init__(code)
        self.code = code
        self.errors = errors or [code]


def _repo_root(repo_root: Path | None = None) -> Path:
    if repo_root is not None:
        return repo_root.resolve()
    return Path(__file__).resolve().parent.parent.parent


def fleet_sessions_storage_dir(repo_root: Path | None = None) -> Path:
    return _repo_root(repo_root) / FLEET_SESSIONS_REL


def _jsonl_path(repo_root: Path | None = None) -> Path:
    return fleet_sessions_storage_dir(repo_root) / JSONL_NAME


def _latest_path(repo_root: Path | None = None) -> Path:
    return fleet_sessions_storage_dir(repo_root) / LATEST_NAME


def utc_now_iso() -> str:
    return datetime.now(tz=UTC).replace(microsecond=0).isoformat()


def _parse_iso(ts: str | None) -> datetime | None:
    if not ts:
        return None
    try:
        if ts.endswith("Z"):
            ts = ts[:-1] + "+00:00"
        return datetime.fromisoformat(ts)
    except ValueError:
        return None


def _validate_id(value: str, field: str) -> str:
    s = (value or "").strip()
    if not s or len(s) > 128:
        raise FleetSessionError("FLEET_SESSION_BLOCKED_INVALID_PAYLOAD", [f"invalid_{field}"])
    for bad in ("..", "/", "\\", "\0"):
        if bad in s:
            raise FleetSessionError("FLEET_SESSION_BLOCKED_INVALID_PAYLOAD", [f"invalid_{field}"])
    if s.startswith("."):
        raise FleetSessionError("FLEET_SESSION_BLOCKED_INVALID_PAYLOAD", [f"invalid_{field}"])
    return s


def _ensure_under_repo(path: Path, repo: Path) -> Path:
    if path.is_symlink():
        raise FleetSessionError("FLEET_SESSION_BLOCKED_INVALID_PAYLOAD", ["symlink_blocked"])
    try:
        resolved = path.resolve()
    except OSError as exc:
        raise FleetSessionError("FLEET_SESSION_BLOCKED_INVALID_PAYLOAD", ["path_resolve_failed"]) from exc
    repo_s = str(repo.resolve())
    res_s = str(resolved)
    if res_s != repo_s and not res_s.startswith(repo_s + os.sep):
        raise FleetSessionError("FLEET_SESSION_BLOCKED_INVALID_PAYLOAD", ["path_traversal"])
    return resolved


def _atomic_write_json(path: Path, data: dict[str, Any] | list[Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.parent.is_symlink():
        raise FleetSessionError("FLEET_SESSION_BLOCKED_INVALID_PAYLOAD", ["symlink_blocked"])
    tmp = path.with_name(path.name + ".tmp")
    if tmp.exists() and tmp.is_symlink():
        raise FleetSessionError("FLEET_SESSION_BLOCKED_INVALID_PAYLOAD", ["symlink_blocked"])
    content = json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    tmp.write_text(content, encoding="utf-8")
    os.replace(tmp, path)


def _append_jsonl(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n"
    with path.open("a", encoding="utf-8") as fh:
        fh.write(line)


def _default_host_block() -> dict[str, Any]:
    return {
        "hostname": socket.gethostname(),
        "user": os.environ.get("USER") or os.environ.get("LOGNAME") or "unknown",
        "has_kvm": Path("/dev/kvm").exists(),
        "kvm_enabled": False,
    }


def _default_session_shell(
    *,
    session_id: str,
    run_id: str,
    session_type: str,
    label: str,
) -> dict[str, Any]:
    now = utc_now_iso()
    return {
        "session_id": session_id,
        "run_id": run_id,
        "session_type": session_type,
        "created_at": now,
        "updated_at": now,
        "started_at": now,
        "finished_at": None,
        "status": "starting",
        "severity": "info",
        "label": label,
        "host": _default_host_block(),
        "qemu": {
            "pid": None,
            "iso_path": "",
            "proxy_port": 8001,
            "timeout_seconds": 900,
            "acceleration": "unknown",
            "exit_code": None,
        },
        "guest": {
            "report_seen": False,
            "guest_node_id": None,
            "guest_smoke_status": None,
            "dev_server_report_new": False,
        },
        "serial": {
            "path": "",
            "exists": False,
            "size_bytes": 0,
            "last_size_change_at": None,
        },
        "heartbeat": {
            "last_heartbeat_at": now,
            "age_seconds": 0,
            "healthy": True,
            "stalled": False,
            "stall_reason": "",
        },
        "agent_state": "booting",
        "evidence_paths": [],
        "findings": [],
        "errors": [],
    }


def _deep_merge(base: dict[str, Any], patch: dict[str, Any]) -> dict[str, Any]:
    out = dict(base)
    for key, val in patch.items():
        if isinstance(val, dict) and isinstance(out.get(key), dict):
            out[key] = _deep_merge(out[key], val)
        else:
            out[key] = val
    return out


def _sanitize_evidence_paths(paths: list[Any], repo: Path) -> list[str]:
    out: list[str] = []
    for raw in paths or []:
        s = str(raw).strip()
        if not s:
            continue
        p = Path(s)
        if p.is_absolute():
            try:
                rel = _ensure_under_repo(p, repo).relative_to(repo.resolve())
                out.append(str(rel))
            except FleetSessionError:
                continue
        else:
            try:
                _ensure_under_repo((repo / s).resolve(), repo)
                out.append(s.lstrip("/"))
            except FleetSessionError:
                continue
    return out


def _validate_payload(payload: dict[str, Any], repo: Path, *, partial: bool = False) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise FleetSessionError("FLEET_SESSION_BLOCKED_INVALID_PAYLOAD", ["payload_not_object"])

    cleaned: dict[str, Any] = {}
    if "session_type" in payload or not partial:
        st = str(payload.get("session_type") or "local_qemu_smoke")
        if st not in SESSION_TYPES:
            raise FleetSessionError("FLEET_SESSION_BLOCKED_INVALID_PAYLOAD", ["invalid_session_type"])
        cleaned["session_type"] = st

    if "status" in payload:
        status = str(payload["status"])
        if status not in STATUSES:
            raise FleetSessionError("FLEET_SESSION_BLOCKED_INVALID_PAYLOAD", ["invalid_status"])
        cleaned["status"] = status

    if "severity" in payload:
        sev = str(payload["severity"])
        if sev not in SEVERITIES:
            raise FleetSessionError("FLEET_SESSION_BLOCKED_INVALID_PAYLOAD", ["invalid_severity"])
        cleaned["severity"] = sev

    for key in ("label", "run_id"):
        if key in payload and payload[key] is not None:
            cleaned[key] = _validate_id(str(payload[key]), key)

    if "session_id" in payload and payload["session_id"] is not None:
        cleaned["session_id"] = _validate_id(str(payload["session_id"]), "session_id")

    for block in ("host", "qemu", "guest", "serial", "heartbeat"):
        if block in payload and isinstance(payload[block], dict):
            cleaned[block] = payload[block]
    if "agent_state" in payload:
        state = str(payload.get("agent_state") or "").strip().lower()
        if state not in AGENT_STATES:
            raise FleetSessionError("FLEET_SESSION_BLOCKED_INVALID_PAYLOAD", ["invalid_agent_state"])
        cleaned["agent_state"] = state

    if "evidence_paths" in payload and isinstance(payload["evidence_paths"], list):
        cleaned["evidence_paths"] = _sanitize_evidence_paths(payload["evidence_paths"], repo)

    for key in ("findings", "errors"):
        if key in payload and isinstance(payload[key], list):
            cleaned[key] = [str(x) for x in payload[key][:50]]

    forbidden_keys = ("token", "secret", "password", "api_key", "private_key")
    raw = json.dumps(payload, default=str).lower()
    for fk in forbidden_keys:
        if fk in raw:
            raise FleetSessionError("FLEET_SESSION_BLOCKED_INVALID_PAYLOAD", [f"forbidden_field:{fk}"])

    return cleaned


def _load_latest_index(repo_root: Path | None = None) -> dict[str, dict[str, Any]]:
    path = _latest_path(repo_root)
    if not path.is_file() or path.is_symlink():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
    sessions = data.get("sessions") if isinstance(data, dict) else None
    if not isinstance(sessions, dict):
        return {}
    return {str(k): v for k, v in sessions.items() if isinstance(v, dict)}


def _save_latest_index(sessions: dict[str, dict[str, Any]], repo_root: Path | None = None) -> None:
    payload = {
        "updated_at": utc_now_iso(),
        "sessions": sessions,
    }
    _atomic_write_json(_latest_path(repo_root), payload)


def _persist_session(session: dict[str, Any], repo_root: Path | None = None) -> None:
    repo = _repo_root(repo_root)
    sid = _validate_id(str(session.get("session_id") or ""), "session_id")
    session["session_id"] = sid
    session["updated_at"] = utc_now_iso()
    _append_jsonl(_jsonl_path(repo_root), session)
    index = _load_latest_index(repo_root)
    index[sid] = session
    _save_latest_index(index, repo_root)


def _compute_heartbeat_age(session: dict[str, Any], now: datetime | None = None) -> int:
    now = now or datetime.now(tz=UTC)
    hb = session.get("heartbeat") if isinstance(session.get("heartbeat"), dict) else {}
    last = _parse_iso(str(hb.get("last_heartbeat_at") or session.get("updated_at") or ""))
    if not last:
        return 0
    if last.tzinfo is None:
        last = last.replace(tzinfo=UTC)
    return max(0, int((now - last).total_seconds()))


def _apply_serial_observation(session: dict[str, Any], now: datetime | None = None) -> None:
    serial = session.setdefault("serial", {})
    path_s = str(serial.get("path") or "")
    size = 0
    exists = False
    if path_s:
        p = Path(path_s)
        if p.is_file() and not p.is_symlink():
            exists = True
            try:
                size = p.stat().st_size
            except OSError:
                size = 0
    prev_size = int(serial.get("size_bytes") or 0)
    serial["exists"] = exists
    serial["size_bytes"] = size
    if size > 0 and size != prev_size:
        serial["last_size_change_at"] = utc_now_iso()
        if session.get("status") in ("booting", "qemu_starting", "starting"):
            session["status"] = "serial_active"

    started = _parse_iso(str(session.get("started_at") or ""))
    now = now or datetime.now(tz=UTC)
    elapsed = 0
    if started:
        if started.tzinfo is None:
            started = started.replace(tzinfo=UTC)
        elapsed = int((now - started).total_seconds())

    if exists and size == 0 and elapsed >= 120 and session.get("status") not in TERMINAL_STATUSES:
        session["status"] = "serial_empty"
        findings = list(session.get("findings") or [])
        if "serial_empty" not in findings:
            findings.append("serial_empty")
        session["findings"] = findings
        session["severity"] = "warning"


def _apply_stale_rules(session: dict[str, Any], now: datetime | None = None) -> None:
    if session.get("status") in TERMINAL_STATUSES:
        return
    now = now or datetime.now(tz=UTC)
    age = _compute_heartbeat_age(session, now)
    hb = session.setdefault("heartbeat", {})
    hb["age_seconds"] = age
    timeout_s = int((session.get("qemu") or {}).get("timeout_seconds") or 900)

    findings = list(session.get("findings") or [])
    if age > 60:
        hb["healthy"] = False
        hb["stalled"] = age > 180
        if "heartbeat_delayed" not in findings:
            findings.append("heartbeat_delayed")
        session["severity"] = "warning"
    else:
        hb["healthy"] = True
        hb["stalled"] = False

    if age > 180 and session.get("status") in RUNNING_STATUSES:
        session["status"] = "timeout_warning"
        if "timeout_warning" not in findings:
            findings.append("timeout_warning")

    if age > timeout_s + 60:
        session["status"] = "timeout"
        session["finished_at"] = session.get("finished_at") or utc_now_iso()
        hb["stall_reason"] = "heartbeat_exceeded_timeout_window"
        session["severity"] = "error"

    session["findings"] = findings


def create_fleet_session(payload: dict[str, Any], *, repo_root: Path | None = None) -> dict[str, Any]:
    repo = _repo_root(repo_root)
    cleaned = _validate_payload(payload, repo)
    run_id = _validate_id(str(cleaned.get("run_id") or payload.get("run_id") or ""), "run_id")
    session_type = cleaned.get("session_type") or "local_qemu_smoke"
    session_id = cleaned.get("session_id") or _validate_id(f"fleet-{run_id}", "session_id")
    label = str(cleaned.get("label") or payload.get("label") or "QEMU Developer ISO Smoke")

    session = _default_session_shell(
        session_id=session_id,
        run_id=run_id,
        session_type=session_type,
        label=label,
    )
    session = _deep_merge(session, cleaned)
    session["run_id"] = run_id
    session["session_id"] = session_id
    if cleaned.get("status"):
        session["status"] = cleaned["status"]
    if payload.get("evidence_paths"):
        session["evidence_paths"] = _sanitize_evidence_paths(payload.get("evidence_paths"), repo)
    _apply_serial_observation(session)
    _apply_stale_rules(session)
    _persist_session(session, repo_root)
    return {"code": "FLEET_SESSION_CREATED", "session": session}


def update_fleet_session(session_id: str, patch: dict[str, Any], *, repo_root: Path | None = None) -> dict[str, Any]:
    repo = _repo_root(repo_root)
    sid = _validate_id(session_id, "session_id")
    index = _load_latest_index(repo_root)
    session = index.get(sid)
    if not session:
        raise FleetSessionError("FLEET_SESSION_NOT_FOUND", ["session_not_found"])
    cleaned = _validate_payload(patch, repo, partial=True)
    session = _deep_merge(session, cleaned)
    if patch.get("evidence_paths"):
        session["evidence_paths"] = _sanitize_evidence_paths(
            list(session.get("evidence_paths") or []) + list(patch.get("evidence_paths") or []),
            repo,
        )
    _apply_serial_observation(session)
    _apply_stale_rules(session)
    _persist_session(session, repo_root)
    return {"code": "FLEET_SESSION_UPDATED", "session": session}


def heartbeat_fleet_session(
    session_id: str,
    patch: dict[str, Any] | None = None,
    *,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    repo = _repo_root(repo_root)
    sid = _validate_id(session_id, "session_id")
    index = _load_latest_index(repo_root)
    session = index.get(sid)
    if not session:
        raise FleetSessionError("FLEET_SESSION_NOT_FOUND", ["session_not_found"])
    if session.get("status") in TERMINAL_STATUSES:
        return {"code": "FLEET_SESSION_HEARTBEAT_OK", "session": session}

    now = utc_now_iso()
    hb_patch = {"heartbeat": {"last_heartbeat_at": now}}
    session = _deep_merge(session, hb_patch)
    if patch:
        hb_status = str(patch.get("status") or "").strip().lower()
        if hb_status == "running":
            patch = dict(patch)
            patch.pop("status", None)
            patch.setdefault("agent_state", "alive")
        cleaned = _validate_payload(patch, repo, partial=True)
        session = _deep_merge(session, cleaned)
    _apply_serial_observation(session)
    _apply_stale_rules(session)
    _persist_session(session, repo_root)
    return {"code": "FLEET_SESSION_HEARTBEAT_OK", "session": session}


def finish_fleet_session(
    session_id: str,
    status: str,
    patch: dict[str, Any] | None = None,
    *,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    repo = _repo_root(repo_root)
    sid = _validate_id(session_id, "session_id")
    st = str(status)
    if st not in STATUSES:
        raise FleetSessionError("FLEET_SESSION_BLOCKED_INVALID_PAYLOAD", ["invalid_status"])

    index = _load_latest_index(repo_root)
    session = index.get(sid)
    if not session:
        raise FleetSessionError("FLEET_SESSION_NOT_FOUND", ["session_not_found"])

    finish_patch: dict[str, Any] = {
        "status": st,
        "finished_at": utc_now_iso(),
    }
    if patch:
        finish_patch.update(_validate_payload(patch, repo, partial=True))

    qemu = session.setdefault("qemu", {})
    exit_code = (patch or {}).get("qemu", {}).get("exit_code") if patch else None
    if exit_code is None and patch and "qemu_exit_code" in patch:
        exit_code = patch.get("qemu_exit_code")
    if exit_code is not None:
        qemu["exit_code"] = int(exit_code)
        if int(exit_code) == 124:
            finish_patch["status"] = "timeout"
            finish_patch.setdefault("findings", [])
            if isinstance(finish_patch.get("findings"), list):
                fins = list(finish_patch["findings"])
            else:
                fins = list(session.get("findings") or [])
            if "qemu_timeout_124" not in fins:
                fins.append("qemu_timeout_124")
            finish_patch["findings"] = fins
            finish_patch["severity"] = "error"

    session = _deep_merge(session, finish_patch)
    if patch and patch.get("guest"):
        guest = session.setdefault("guest", {})
        gpatch = patch["guest"]
        if gpatch.get("report_seen"):
            session["status"] = st if st in TERMINAL_STATUSES else "guest_report_seen"
        guest.update(gpatch)

    if not session.get("guest", {}).get("report_seen") and st in ("failed", "timeout", "review_required"):
        findings = list(session.get("findings") or [])
        if "guest_report_missing" not in findings:
            findings.append("guest_report_missing")
        session["findings"] = findings
        if session.get("severity") != "error":
            session["severity"] = "warning"

    _apply_serial_observation(session)
    _persist_session(session, repo_root)
    return {"code": "FLEET_SESSION_FINISHED", "session": session}


def get_fleet_session(session_id: str, *, repo_root: Path | None = None) -> dict[str, Any]:
    sid = _validate_id(session_id, "session_id")
    index = _load_latest_index(repo_root)
    session = index.get(sid)
    if not session:
        raise FleetSessionError("FLEET_SESSION_NOT_FOUND", ["session_not_found"])
    _apply_serial_observation(session)
    _apply_stale_rules(session)
    return {"code": "FLEET_SESSION_OK", "session": session}


def list_fleet_sessions(
    *,
    limit: int = 50,
    include_finished: bool = True,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    limit = max(1, min(int(limit), 200))
    index = _load_latest_index(repo_root)
    sessions = list(index.values())

    def sort_key(s: dict[str, Any]) -> tuple[str, str]:
        return (str(s.get("updated_at") or s.get("created_at") or ""), str(s.get("session_id") or ""))

    sessions.sort(key=sort_key, reverse=True)
    if not include_finished:
        sessions = [s for s in sessions if s.get("status") not in TERMINAL_STATUSES]

    stale = detect_stale_sessions(repo_root=repo_root)
    return {
        "code": "FLEET_SESSION_LIST_OK",
        "sessions": sessions[:limit],
        "count": len(sessions[:limit]),
        "stale_summary": stale.get("summary", {}),
    }


def build_fleet_session_summary(*, repo_root: Path | None = None) -> dict[str, Any]:
    index = _load_latest_index(repo_root)
    sessions = list(index.values())
    active = [s for s in sessions if s.get("status") not in TERMINAL_STATUSES]
    terminal = [s for s in sessions if s.get("status") in TERMINAL_STATUSES]
    warnings = sum(1 for s in sessions if s.get("severity") == "warning")
    errors = sum(1 for s in sessions if s.get("severity") == "error")
    return {
        "code": "FLEET_SESSION_SUMMARY_OK",
        "total": len(sessions),
        "active_count": len(active),
        "finished_count": len(terminal),
        "warning_count": warnings,
        "error_count": errors,
        "latest_active": active[:5],
        "generated_at": utc_now_iso(),
    }


def detect_stale_sessions(*, now: datetime | None = None, repo_root: Path | None = None) -> dict[str, Any]:
    now = now or datetime.now(tz=UTC)
    index = _load_latest_index(repo_root)
    updated: list[str] = []
    for sid, session in list(index.items()):
        before = session.get("status")
        _apply_serial_observation(session, now)
        _apply_stale_rules(session, now)
        if session.get("status") != before:
            _persist_session(session, repo_root)
            updated.append(sid)
    summary = build_fleet_session_summary(repo_root=repo_root)
    return {"summary": summary, "updated_session_ids": updated}


def fleet_sessions_enabled() -> bool:
    try:
        from core.install_profile import get_install_profile_state

        return get_install_profile_state().fleet_sessions_enabled
    except Exception:
        pass
    env = os.environ.get("SETUPHELFER_FLEET_SESSIONS_ENABLED", "").strip().lower()
    if env in ("0", "false", "no"):
        return False
    if env in ("1", "true", "yes"):
        return True
    try:
        from devserver.config import load_dev_server_config

        cfg = load_dev_server_config()
        if cfg.enabled and cfg.mode == "local_lab":
            return True
    except Exception:
        pass
    try:
        from core.install_paths import is_dev_mode

        return is_dev_mode()
    except Exception:
        return False


def assert_fleet_write_allowed() -> None:
    if not fleet_sessions_enabled():
        raise FleetSessionError("FLEET_SESSION_BLOCKED_INVALID_PAYLOAD", ["fleet_sessions_disabled"])


def assert_no_forbidden_routes(path: str) -> None:
    low = path.lower()
    for frag in FORBIDDEN_ROUTE_FRAGMENTS:
        if frag in low:
            raise FleetSessionError("FLEET_SESSION_BLOCKED_INVALID_PAYLOAD", [f"forbidden_route:{frag}"])
