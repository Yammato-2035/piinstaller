"""
GNU tar stderr/exit-code classification for Setuphelfer backups (BR-001 forensics).

Design: tar exit 1 is not automatically success or failure. Downgrade from hard
failure requires volatile-only warnings AND a final archive with SHA256 + verify_deep.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any

__all__ = [
    "TarWarningClassification",
    "classify_tar_run",
    "classification_to_job_status_fields",
    "decide_tar_nonzero_job_outcome",
    "parse_tar_stderr_lines",
    "path_is_critical_for_tar_warning",
    "path_is_volatile_for_tar_warning",
]


class TarWarningClassification(StrEnum):
    TAR_OK = "TAR_OK"
    TAR_LIVE_FILE_CHANGED_ONLY = "TAR_LIVE_FILE_CHANGED_ONLY"
    TAR_SOCKET_IGNORED_ONLY = "TAR_SOCKET_IGNORED_ONLY"
    TAR_VOLATILE_WARNINGS_ONLY = "TAR_VOLATILE_WARNINGS_ONLY"
    TAR_CRITICAL_WARNING = "TAR_CRITICAL_WARNING"
    TAR_IO_ERROR = "TAR_IO_ERROR"
    TAR_PERMISSION_CRITICAL = "TAR_PERMISSION_CRITICAL"
    TAR_FATAL = "TAR_FATAL"


_CRITICAL_PREFIXES = (
    "/etc/",
    "/etc",
    "/boot/",
    "/boot",
    "/usr/",
    "/var/lib/dpkg/",
    "/var/lib/apt/",
)

_VOLATILE_PREFIXES = (
    "/var/tmp/",
    "/var/tmp",
    "/var/cache/",
    "/var/cache",
    "/var/log/journal/",
    "/tmp/",
)

_VOLATILE_GLOBS = (
    re.compile(r"^/home/[^/]+/\.cache/"),
    re.compile(r"^/home/[^/]+/\.local/share/Trash/"),
    re.compile(r"^/root/\.gnupg/S\."),
    re.compile(r"^/home/[^/]+/\.docker/desktop/.*\.sock$"),
    re.compile(r"^/home/[^/]+/\.var/app/.*/cache/.*SingletonSocket$"),
    re.compile(r"^/home/[^/]+/\.cache/ibus/dbus-"),
)

_RE_FILE_CHANGED = re.compile(
    r"file changed as we read it|Datei hat sich beim Lesen geändert",
    re.IGNORECASE,
)
_RE_SOCKET_IGNORED = re.compile(r"socket ignored|Socket ignoriert", re.IGNORECASE)
_RE_IO = re.compile(r"input/output error|Ein-/Ausgabefehler", re.IGNORECASE)
_RE_NO_SPACE = re.compile(r"no space left on device|Kein Speicherplatz", re.IGNORECASE)
_RE_EOF = re.compile(r"unexpected eof|Unerwartetes Dateiende", re.IGNORECASE)
_RE_PERM = re.compile(r"permission denied|Keine Berechtigung", re.IGNORECASE)
_RE_TAR_PATH = re.compile(r"^tar:\s+([^:]+):")


@dataclass(frozen=True)
class TarStderrEvent:
    kind: str
    path: str | None
    line: str


@dataclass
class TarClassificationResult:
    classification: TarWarningClassification
    tar_exit_code: int
    events: list[TarStderrEvent] = field(default_factory=list)
    volatile_paths: list[str] = field(default_factory=list)
    critical_paths: list[str] = field(default_factory=list)
    io_errors_found: bool = False
    critical_errors_found: bool = False
    allows_warning_downgrade: bool = False
    operational_success_allowed: bool = False
    no_archive_created: bool = True
    downgrade_blockers: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "classification": self.classification.value,
            "tar_exit_code": self.tar_exit_code,
            "volatile_paths_detected": list(self.volatile_paths),
            "critical_paths_detected": list(self.critical_paths),
            "io_errors_found": self.io_errors_found,
            "critical_errors_found": self.critical_errors_found,
            "allows_warning_downgrade": self.allows_warning_downgrade,
            "operational_success_allowed": self.operational_success_allowed,
            "no_archive_created": self.no_archive_created,
            "downgrade_blockers": list(self.downgrade_blockers),
            "events": [{"kind": e.kind, "path": e.path, "line": e.line} for e in self.events],
        }


def path_is_critical_for_tar_warning(path: str) -> bool:
    p = (path or "").strip()
    if not p.startswith("/"):
        return False
    for pref in _CRITICAL_PREFIXES:
        if p == pref.rstrip("/") or p.startswith(pref):
            return True
    return False


def path_is_volatile_for_tar_warning(path: str) -> bool:
    p = (path or "").strip()
    if not p.startswith("/"):
        return False
    for pref in _VOLATILE_PREFIXES:
        if p == pref.rstrip("/") or p.startswith(pref):
            return True
    return any(rx.match(p) for rx in _VOLATILE_GLOBS)


def parse_tar_stderr_lines(stderr_text: str) -> list[TarStderrEvent]:
    events: list[TarStderrEvent] = []
    for raw in (stderr_text or "").splitlines():
        line = raw.strip()
        if not line or not line.startswith("tar:"):
            continue
        m = _RE_TAR_PATH.match(line)
        path = m.group(1).strip() if m else None
        if _RE_IO.search(line):
            events.append(TarStderrEvent("io_error", path, line))
        elif _RE_NO_SPACE.search(line):
            events.append(TarStderrEvent("no_space", path, line))
        elif _RE_EOF.search(line):
            events.append(TarStderrEvent("unexpected_eof", path, line))
        elif _RE_PERM.search(line):
            events.append(TarStderrEvent("permission_denied", path, line))
        elif _RE_FILE_CHANGED.search(line):
            events.append(TarStderrEvent("file_changed", path, line))
        elif _RE_SOCKET_IGNORED.search(line):
            events.append(TarStderrEvent("socket_ignored", path, line))
        elif path:
            events.append(TarStderrEvent("other", path, line))
    return events


def _has_fatal_blob(stderr_text: str) -> tuple[bool, bool]:
    blob = (stderr_text or "").lower()
    io = "input/output error" in blob or "ein-/ausgabefehler" in blob
    if io:
        return True, True
    if "no space left on device" in blob or "kein speicherplatz" in blob:
        return True, False
    if "unexpected eof" in blob or "unerwartetes dateiende" in blob:
        return True, False
    if "wrote only" in blob and "byte" in blob:
        return True, True
    return False, io


def classify_tar_run(
    *,
    tar_exit_code: int,
    stderr_text: str = "",
    final_archive_path: str | Path | None = None,
    final_archive_exists: bool | None = None,
    sha256_verified: bool | None = None,
    verify_deep_ok: bool | None = None,
) -> TarClassificationResult:
    events = parse_tar_stderr_lines(stderr_text)
    volatile_paths: list[str] = []
    critical_paths: list[str] = []
    has_file_changed = False
    has_socket_only = True
    has_non_volatile_warning = False

    fatal, io_found = _has_fatal_blob(stderr_text)
    res = TarClassificationResult(
        classification=TarWarningClassification.TAR_FATAL,
        tar_exit_code=tar_exit_code,
        events=events,
        io_errors_found=io_found,
    )

    archive_exists = False
    if final_archive_exists is not None:
        archive_exists = bool(final_archive_exists)
    elif final_archive_path is not None:
        p = Path(final_archive_path)
        archive_exists = p.is_file() and p.stat().st_size > 0
    res.no_archive_created = not archive_exists

    if tar_exit_code == 0 and not fatal:
        res.classification = TarWarningClassification.TAR_OK
        res.no_archive_created = not archive_exists if final_archive_path is not None else res.no_archive_created
        _apply_post_verify(res, archive_exists, sha256_verified, verify_deep_ok)
        return res

    if fatal:
        res.classification = (
            TarWarningClassification.TAR_IO_ERROR if io_found else TarWarningClassification.TAR_FATAL
        )
        res.critical_errors_found = True
        _apply_post_verify(res, archive_exists, sha256_verified, verify_deep_ok)
        return res

    for ev in events:
        if ev.kind in {"no_space", "unexpected_eof"}:
            res.classification = TarWarningClassification.TAR_FATAL
            res.critical_errors_found = True
            _apply_post_verify(res, archive_exists, sha256_verified, verify_deep_ok)
            return res
        if ev.kind == "permission_denied" and ev.path:
            if path_is_critical_for_tar_warning(ev.path):
                critical_paths.append(ev.path)
                res.classification = TarWarningClassification.TAR_PERMISSION_CRITICAL
                res.critical_errors_found = True
                res.critical_paths = list(dict.fromkeys(critical_paths))
                _apply_post_verify(res, archive_exists, sha256_verified, verify_deep_ok)
                return res
            has_non_volatile_warning = True
        if ev.kind == "file_changed" and ev.path:
            has_file_changed = True
            if path_is_critical_for_tar_warning(ev.path):
                critical_paths.append(ev.path)
            elif path_is_volatile_for_tar_warning(ev.path):
                volatile_paths.append(ev.path)
            else:
                has_non_volatile_warning = True
                critical_paths.append(ev.path)
        if ev.kind == "socket_ignored" and ev.path:
            if path_is_volatile_for_tar_warning(ev.path) or path_is_critical_for_tar_warning(ev.path) is False:
                volatile_paths.append(ev.path)
            else:
                has_socket_only = False
                critical_paths.append(ev.path)
        if ev.kind == "other" and ev.path:
            has_non_volatile_warning = True

    res.volatile_paths = list(dict.fromkeys(volatile_paths))
    res.critical_paths = list(dict.fromkeys(critical_paths))

    if critical_paths and any(
        ev.kind == "file_changed" and ev.path in critical_paths for ev in events
    ):
        res.classification = TarWarningClassification.TAR_CRITICAL_WARNING
        res.critical_errors_found = True
        _apply_post_verify(res, archive_exists, sha256_verified, verify_deep_ok)
        return res

    if has_non_volatile_warning or any(ev.kind == "other" for ev in events):
        res.classification = TarWarningClassification.TAR_FATAL
        res.critical_errors_found = True
        _apply_post_verify(res, archive_exists, sha256_verified, verify_deep_ok)
        return res

    socket_events = [e for e in events if e.kind == "socket_ignored"]
    file_events = [e for e in events if e.kind == "file_changed"]

    if file_events and not socket_events and not critical_paths:
        all_volatile_fc = all(e.path and path_is_volatile_for_tar_warning(e.path) for e in file_events)
        if all_volatile_fc:
            res.classification = TarWarningClassification.TAR_LIVE_FILE_CHANGED_ONLY
        else:
            res.classification = TarWarningClassification.TAR_FATAL
            res.critical_errors_found = True
    elif socket_events and not file_events and not critical_paths:
        all_volatile_sk = all(e.path and path_is_volatile_for_tar_warning(e.path) for e in socket_events)
        if all_volatile_sk:
            res.classification = TarWarningClassification.TAR_SOCKET_IGNORED_ONLY
        else:
            res.classification = TarWarningClassification.TAR_FATAL
    elif (socket_events or file_events) and not critical_paths:
        only_volatile = True
        for e in socket_events + file_events:
            if not e.path or not path_is_volatile_for_tar_warning(e.path):
                only_volatile = False
                break
        res.classification = (
            TarWarningClassification.TAR_VOLATILE_WARNINGS_ONLY
            if only_volatile
            else TarWarningClassification.TAR_FATAL
        )
        if not only_volatile:
            res.critical_errors_found = True
    elif tar_exit_code != 0:
        res.classification = TarWarningClassification.TAR_FATAL
        if tar_exit_code != 0 and not events:
            res.critical_errors_found = True

    _apply_post_verify(res, archive_exists, sha256_verified, verify_deep_ok)
    return res


def _apply_post_verify(
    res: TarClassificationResult,
    archive_exists: bool,
    sha256_verified: bool | None,
    verify_deep_ok: bool | None,
) -> None:
    volatile_only = res.classification in {
        TarWarningClassification.TAR_LIVE_FILE_CHANGED_ONLY,
        TarWarningClassification.TAR_SOCKET_IGNORED_ONLY,
        TarWarningClassification.TAR_VOLATILE_WARNINGS_ONLY,
    }
    res.allows_warning_downgrade = volatile_only and not res.critical_errors_found and not res.io_errors_found
    blockers: list[str] = []
    if res.no_archive_created:
        blockers.append("no_final_archive")
    if sha256_verified is not True:
        blockers.append("sha256_not_verified")
    if verify_deep_ok is not True:
        blockers.append("verify_deep_not_ok")
    if res.critical_errors_found:
        blockers.append("critical_errors")
    if res.io_errors_found:
        blockers.append("io_errors")
    res.downgrade_blockers = blockers
    res.operational_success_allowed = res.allows_warning_downgrade and not blockers


def classification_to_job_status_fields(result: TarClassificationResult) -> dict[str, Any]:
    """Stable job/status.json fields for runner and API consumers."""
    return {
        "tar_warning_classification": result.classification.value,
        "tar_warning_downgrade_allowed": result.allows_warning_downgrade,
        "operational_success_allowed": result.operational_success_allowed,
        "final_archive_required": True,
        "sha256_required": True,
        "verify_deep_required": True,
        "volatile_warning_paths": list(result.volatile_paths),
        "fatal_patterns_found": bool(result.critical_errors_found or result.io_errors_found),
        "tar_downgrade_blockers": list(result.downgrade_blockers),
    }


def decide_tar_nonzero_job_outcome(
    *,
    tar_exit_code: int,
    stderr_text: str,
    partial_exists: bool,
    partial_bytes: int,
    final_archive_exists: bool,
    finalize_attempted: bool,
    finalize_ok: bool,
    sha256_verified: bool,
    verify_deep_ok: bool,
) -> dict[str, Any]:
    """
    Pure decision for runner integration (unit-tested without live tar).

    Never returns plain success without integrity chain when tar_exit_code != 0.
    """
    cls = classify_tar_run(
        tar_exit_code=tar_exit_code,
        stderr_text=stderr_text,
        final_archive_exists=final_archive_exists,
        sha256_verified=sha256_verified if final_archive_exists else None,
        verify_deep_ok=verify_deep_ok if final_archive_exists else None,
    )
    fields = classification_to_job_status_fields(cls)
    out: dict[str, Any] = {
        **fields,
        "classification": cls.classification.value,
        "allows_warning_downgrade": cls.allows_warning_downgrade,
    }

    if cls.classification in {
        TarWarningClassification.TAR_IO_ERROR,
        TarWarningClassification.TAR_FATAL,
    } or cls.io_errors_found:
        out.update(
            status="error",
            code="backup.failed",
            severity="error",
            abort_reason="tar_failed",
        )
        return out

    if cls.classification == TarWarningClassification.TAR_PERMISSION_CRITICAL:
        out.update(
            status="error",
            code="backup.failed",
            severity="error",
            abort_reason="tar_failed",
        )
        return out

    if cls.classification == TarWarningClassification.TAR_CRITICAL_WARNING:
        out.update(
            status="error",
            code="backup.failed",
            severity="error",
            abort_reason="tar_failed",
        )
        return out

    if not cls.allows_warning_downgrade:
        out.update(
            status="error",
            code="backup.failed",
            severity="error",
            abort_reason="tar_failed",
        )
        return out

    if not final_archive_exists:
        if not partial_exists or partial_bytes <= 0:
            abort = "tar_volatile_warning_without_final_archive"
        elif finalize_attempted and not finalize_ok:
            abort = "tar_volatile_finalize_failed"
        else:
            abort = "tar_volatile_warning_without_final_archive"
        out.update(
            status="error",
            code="backup.warning_not_promoted",
            severity="error",
            abort_reason=abort,
            partial_deleted=True,
        )
        return out

    if not sha256_verified:
        out.update(
            status="error",
            code="backup.warning_not_promoted",
            severity="error",
            abort_reason="tar_volatile_sha256_failed",
            partial_deleted=False,
        )
        return out

    if not verify_deep_ok:
        out.update(
            status="error",
            code="backup.warning_not_promoted",
            severity="error",
            abort_reason="tar_volatile_verify_deep_failed",
            partial_deleted=False,
        )
        return out

    if cls.operational_success_allowed:
        out.update(
            status="success",
            code="backup.success_with_warnings",
            severity="success",
            warning_status="completed_with_warnings",
            backup_integrity_status="verified",
            abort_reason=None,
            warnings=[
                {
                    "kind": "tar_volatile_warnings",
                    "classification": cls.classification.value,
                    "paths": list(cls.volatile_paths)[:50],
                }
            ],
            partial_deleted=False,
        )
        return out

    out.update(
        status="error",
        code="backup.warning_not_promoted",
        severity="error",
        abort_reason="tar_volatile_warning_without_final_archive",
        partial_deleted=not final_archive_exists,
    )
    return out
