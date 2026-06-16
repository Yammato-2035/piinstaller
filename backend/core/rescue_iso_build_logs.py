"""
Read-only Rescue-ISO-Build-Logs für das Development Dashboard.

Filtert große live-build-Ausgaben auf relevante Zeilen und liefert strukturierte Events.
Keine Build-Ausführung, kein sudo.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from core.rescue_iso_build_state import (
    _extract_last_error,
    _read_recent_lines,
    _redact_line,
    _repo_root,
    resolve_rescue_iso_paths,
)

LogFilter = Literal["all", "important", "errors", "summary"]

_VALID_FILTERS: frozenset[str] = frozenset({"all", "important", "errors", "summary"})

_IMPORTANT_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"^START ", re.I),
    re.compile(r"LB_EXIT=", re.I),
    re.compile(r"^OK:", re.I),
    re.compile(r"OK: setuphelfer live user baked", re.I),
    re.compile(r"CHROOT_STALE", re.I),
    re.compile(r"POLICY_GUARD", re.I),
    re.compile(r"Post-build squashfs validation", re.I),
    re.compile(r"LIVE_LOGIN_USER_GAP|INTEGRATION_GAP|SYSTEMD_|DBUS_GAP|LOGIN_HINT_GAP|KEYBOARD_LOCALE_GAP", re.I),
    re.compile(r"skipping\s+.+, already done", re.I),
    re.compile(r"\blb_chroot\b|\blb_binary\b|\blb_source\b", re.I),
    re.compile(r"^P: (Begin|Saving|Configuring|Deconfiguring|Executing)", re.I),
    re.compile(r"^=== ", re.I),
    re.compile(r"RESCUE-BUILD-|blocked_requires_operator", re.I),
    re.compile(r"sha256|binary\.hybrid\.iso", re.I),
    re.compile(r"summary written to", re.I),
)

_ERROR_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\b(E:|ERROR|failed|Fehler|MISSING:|blocked)\b", re.I),
    re.compile(r"_GAP:", re.I),
    re.compile(r"LB_EXIT=(?!0\b)", re.I),
    re.compile(r"tar failed", re.I),
    re.compile(r"isohybrid: not found", re.I),
    re.compile(r"CHROOT_STALE_CODE|RESCUE-ISO-SQUASHFS-VALIDATION-", re.I),
)

_EVENT_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("build_started", re.compile(r"^START ", re.I)),
    ("policy_guard", re.compile(r"POLICY_GUARD_STATUS=", re.I)),
    ("chroot_stale", re.compile(r"CHROOT_STALE:", re.I)),
    ("auto_clean", re.compile(r"\./auto/clean", re.I)),
    ("stage_skipped", re.compile(r"skipping\s+([^,]+), already done", re.I)),
    ("squashfs_validation", re.compile(r"Post-build squashfs validation", re.I)),
    ("validator_ok", re.compile(r"^OK: rescue ISO squashfs", re.I)),
    ("live_user_baked", re.compile(r"OK: setuphelfer live user baked", re.I)),
    ("validator_gap", re.compile(r"_GAP:", re.I)),
    ("lb_exit", re.compile(r"LB_EXIT=(\d+)", re.I)),
    ("summary_written", re.compile(r"summary written to", re.I)),
    ("build_error", re.compile(r"\b(E:|ERROR|failed|Fehler)\b", re.I)),
)


def _resolve_latest_log_path(*, repo_root: Path | None = None) -> Path:
    runtime_root = (repo_root or _repo_root()).resolve(strict=False)
    paths = resolve_rescue_iso_paths(repo_root=runtime_root)
    return Path(str(paths["logs_path"])).resolve(strict=False) / "latest.log"


def _read_all_lines(path: Path) -> list[str]:
    if not path.is_file():
        return []
    try:
        raw = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    return [_redact_line(line.rstrip("\n")) for line in raw.splitlines()]


def _line_matches(patterns: tuple[re.Pattern[str], ...], line: str) -> bool:
    return any(p.search(line) for p in patterns)


def filter_log_lines(lines: list[str], mode: LogFilter) -> list[str]:
    if mode == "all":
        return list(lines)
    if mode == "errors":
        return [line for line in lines if _line_matches(_ERROR_PATTERNS, line)]
    if mode == "important":
        return [line for line in lines if _line_matches(_IMPORTANT_PATTERNS, line) or _line_matches(_ERROR_PATTERNS, line)]
    return []


def extract_log_events(lines: list[str], *, max_events: int = 80) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for index, line in enumerate(lines):
        for event_type, pattern in _EVENT_PATTERNS:
            match = pattern.search(line)
            if not match:
                continue
            detail = match.group(1).strip() if match.lastindex else None
            events.append(
                {
                    "type": event_type,
                    "line_no": index + 1,
                    "text": line[:500],
                    "detail": detail,
                }
            )
            break
    return events[-max_events:]


def _build_in_progress(lines: list[str], *, mtime_age_seconds: float | None) -> bool:
    if not lines:
        return False
    tail = "\n".join(lines[-40:])
    if re.search(r"LB_EXIT=\d+", tail):
        return False
    if mtime_age_seconds is not None and mtime_age_seconds > 7200:
        return False
    return bool(re.search(r"\blb_(chroot|binary|build)\b|^P: Begin", tail, re.I | re.M))


def read_rescue_iso_build_logs(
    *,
    repo_root: Path | None = None,
    log_filter: str = "important",
    tail: int = 500,
    offset_from_end: int = 0,
) -> dict[str, Any]:
    mode: LogFilter = log_filter if log_filter in _VALID_FILTERS else "important"
    tail = max(20, min(int(tail), 5000))
    offset_from_end = max(0, int(offset_from_end))

    log_path = _resolve_latest_log_path(repo_root=repo_root)
    all_lines = _read_all_lines(log_path)
    total_lines = len(all_lines)

    file_size_bytes: int | None = None
    last_modified: str | None = None
    mtime_age_seconds: float | None = None
    if log_path.is_file():
        try:
            stat = log_path.stat()
            file_size_bytes = int(stat.st_size)
            last_modified = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat()
            mtime_age_seconds = max(0.0, datetime.now(tz=timezone.utc).timestamp() - stat.st_mtime)
        except OSError:
            pass

    window_end = max(0, total_lines - offset_from_end)
    window_start = max(0, window_end - tail)
    window_lines = all_lines[window_start:window_end]

    if mode == "summary":
        filtered = []
        events = extract_log_events(all_lines)
    else:
        filtered = filter_log_lines(window_lines, mode)
        events = extract_log_events(all_lines)

    last_lb_exit: str | None = None
    for line in reversed(all_lines):
        match = re.search(r"LB_EXIT=(\d+)", line)
        if match:
            last_lb_exit = match.group(1)
            break

    skipped_stages: list[str] = []
    for line in all_lines:
        match = re.search(r"skipping\s+([^,]+), already done", line, re.I)
        if match:
            stage = match.group(1).strip()
            if stage not in skipped_stages:
                skipped_stages.append(stage)

    return {
        "status": "success",
        "code": "DEV_DASHBOARD_RESCUE_ISO_LOGS_OK",
        "filter": mode,
        "log_file": str(log_path),
        "log_file_exists": log_path.is_file(),
        "total_lines": total_lines,
        "file_size_bytes": file_size_bytes,
        "last_modified": last_modified,
        "window_start_line": window_start + 1 if total_lines else 0,
        "window_end_line": window_end if total_lines else 0,
        "returned_lines": len(filtered) if mode != "summary" else 0,
        "lines": filtered if mode != "summary" else [],
        "events": events,
        "last_error": _extract_last_error(all_lines[-400:]),
        "last_lb_exit": last_lb_exit,
        "build_in_progress": _build_in_progress(all_lines, mtime_age_seconds=mtime_age_seconds),
        "skipped_stages": skipped_stages[-20:],
        "read_only": True,
    }


def read_rescue_iso_build_log_download(*, repo_root: Path | None = None) -> dict[str, Any]:
    log_path = _resolve_latest_log_path(repo_root=repo_root)
    lines = _read_all_lines(log_path)
    return {
        "status": "success",
        "code": "DEV_DASHBOARD_RESCUE_ISO_LOG_DOWNLOAD_OK",
        "log_file": str(log_path),
        "total_lines": len(lines),
        "content": "\n".join(lines) + ("\n" if lines else ""),
        "read_only": True,
    }
