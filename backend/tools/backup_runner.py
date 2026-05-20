#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

import argparse
import atexit
import hashlib
import json
import os
import shlex
import shutil
import signal
import subprocess
import tarfile
import threading
import time
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

import psutil

from core.backup_archive_options import (
    PROFILE_FULL_EXPERT,
    build_full_root_tar_command,
)
from core.backup_progress import merge_progress_optional, quick_target_preflight
from core.backup_tar_warning_classification import (
    classification_to_job_status_fields,
    classify_tar_run,
    decide_tar_nonzero_job_outcome,
)
from core.backup_telemetry import sync_status_telemetry
from core.notification_settings import load_effective_notification_config
from core.notification_service import (
    maybe_send_backup_failure_email,
    maybe_send_backup_success_email,
    notification_status_fields,
)

# Status-Herzschlag während teurer Finalisierung (SHA256 / Manifest-Rewrite)
_FINALIZE_PROGRESS_INTERVAL_S = 30.0
_FINALIZE_HASH_PROGRESS_BYTES = 4 * 1024 * 1024

# Volles tar-stderr: /var/log/setuphelfer/backup-<job_id>.log; Kopf/Schwanz nur im RAM.
STDERR_LOG_DIR = Path("/var/log/setuphelfer")
STDERR_HEAD_MAX_BYTES = 8192
STDERR_TAIL_MAX_LINES = 20


STOP_REQUESTED = False
CHILD_PROC: subprocess.Popen[str] | None = None
STATUS_FINAL_WRITTEN = False
_EVIDENCE_CTX: dict[str, Any] | None = None
_EVIDENCE_COLLECTED = False


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def _status_path(status_dir: Path, job_id: str) -> Path:
    return status_dir / job_id / "status.json"


def _job_path(status_dir: Path, job_id: str) -> Path:
    return status_dir / job_id / "job.json"


def _tar_stderr_log_path(job_id: str) -> Path:
    return STDERR_LOG_DIR / f"backup-{job_id}.log"


def _reap_child_returncode(proc: subprocess.Popen[str] | None) -> None:
    if proc and proc.returncode is None:
        try:
            proc.wait(timeout=120)
        except Exception:
            pass


def _child_exit_code(proc: subprocess.Popen[str] | None) -> int:
    if proc is None:
        return -1
    rc = proc.returncode
    return rc if rc is not None else -1


def _load_job_json(status_dir: Path, job_id: str) -> dict[str, Any]:
    p = _job_path(status_dir, job_id)
    if not p.exists():
        return {}
    try:
        data = json.loads(p.read_text(encoding="utf-8") or "{}")
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _write_status(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, path)


def _update_status(path: Path, state: dict[str, Any], **kwargs: Any) -> None:
    state.update(kwargs)
    sync_status_telemetry(state)
    _write_status(path, state)


def _detect_active_package_operations() -> list[dict[str, Any]]:
    from core.package_activity import detect_active_package_operations

    return detect_active_package_operations()


def _cleanup_partial(partial_path: str) -> bool:
    p = Path(partial_path)
    existed = p.exists()
    try:
        if existed:
            p.unlink()
    except Exception:
        pass
    return existed and not p.exists()


def _stderr_indicates_target_write_io_error(head_text: str, tail_text: str) -> bool:
    """True if tar/gzip stderr suggests EIO / short-write on the backup archive stream (BACKUP-IO-ERROR-050)."""
    blob = f"{head_text or ''}\n{tail_text or ''}".lower()
    if "input/output error" in blob:
        return True
    if "wrote only" in blob and "byte" in blob:
        return True
    return False


def _read_full_tar_stderr(head_text: str, tail_text: str, stderr_log_path: Path | None) -> str:
    chunks = [head_text or "", tail_text or ""]
    if stderr_log_path and stderr_log_path.is_file():
        try:
            chunks.append(stderr_log_path.read_text(encoding="utf-8", errors="replace"))
        except OSError:
            pass
    return "\n".join(chunks)


def _runner_verify_deep(archive_path: str | Path) -> tuple[bool, str | None]:
    import tempfile

    from modules.backup_verify import verify_deep

    with tempfile.TemporaryDirectory(prefix="setuphelfer-runner-vd-") as td:
        ok, key, _details = verify_deep(
            str(archive_path),
            verify_checksums=True,
            strict_archive_manifest=False,
            try_loop_mount_image=False,
            extract_root=td,
        )
        return bool(ok), (str(key) if key else None)


def _cleanup_archive(path: str | Path) -> None:
    try:
        Path(path).unlink(missing_ok=True)
    except OSError:
        pass


def _publish_tar_nonzero_failure(
    status_file: Path,
    status: dict[str, Any],
    *,
    partial_path: str,
    rc: int,
    stderr_excerpt: str,
    stderr_tail: str,
    stderr_log_path: Path | None,
    tar_class_fields: dict[str, Any],
    outcome: dict[str, Any],
) -> int:
    partial_deleted = bool(outcome.get("partial_deleted"))
    if partial_deleted:
        partial_deleted = _cleanup_partial(partial_path)
    _skip = {
        "status",
        "code",
        "severity",
        "abort_reason",
        "partial_deleted",
        "classification",
        "allows_warning_downgrade",
    }
    _skip |= set(tar_class_fields.keys())
    final_code = str(outcome.get("code") or "backup.failed")
    _update_status(
        status_file,
        status,
        status=str(outcome.get("status") or "error"),
        code=final_code,
        severity=str(outcome.get("severity") or "error"),
        diagnosis_id=None,
        abort_reason=outcome.get("abort_reason"),
        backup_finished_at=_now_iso(),
        stderr_excerpt=stderr_excerpt,
        stderr_tail=stderr_tail,
        subprocess_returncode=rc,
        tar_stderr_log=str(stderr_log_path) if stderr_log_path else None,
        suspend_guard_active=False,
        partial_deleted=partial_deleted,
        final_archive_exists=False,
        last_error_code=final_code,
        last_error_message=stderr_excerpt[:500] if stderr_excerpt else None,
        last_status_message=f"Backup fehlgeschlagen ({outcome.get('abort_reason') or 'tar_failed'})",
        **tar_class_fields,
        **{k: v for k, v in outcome.items() if k not in _skip},
    )
    _attach_backup_failure_notification(
        status_file,
        status,
        job_id=str(status.get("job_id") or ""),
        code=final_code,
        stderr_excerpt=stderr_excerpt,
        tar_return_code=rc,
    )
    _mark_terminal()
    return 1


def _sha256_file(path: str | Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _throttled_finalize_progress(
    progress: Callable[[str, int], None] | None,
    *,
    phase: str,
    processed: int,
    state: dict[str, Any],
) -> None:
    """Ruft progress(phase, processed) höchstens alle _FINALIZE_PROGRESS_INTERVAL_S auf — plus beim Phasenwechsel."""
    if progress is None:
        return
    now = time.monotonic()
    prev_phase = state.get("phase") or ""
    if phase != prev_phase:
        state["phase"] = phase
        state["t"] = now
        progress(phase, processed)
        return
    if now - float(state.get("t") or 0.0) >= _FINALIZE_PROGRESS_INTERVAL_S:
        state["t"] = now
        progress(phase, processed)


def _sha256_archive_payload(
    archive_path: str | Path,
    *,
    progress: Callable[[str, int], None] | None = None,
    progress_state: dict[str, Any] | None = None,
) -> str:
    """
    Deterministischer Integritäts-Hash über Archivinhalt ohne MANIFEST.json,
    damit der Hash stabil bleibt, obwohl das Manifest den Hash selbst trägt.

    Streamt Member-Inhalte in konstanten Chunks; optional progress(phase, bytes_processed).
    """
    st: dict[str, Any] = progress_state if progress_state is not None else {"t": 0.0, "phase": ""}
    try:
        total_est = Path(archive_path).stat().st_size
    except OSError:
        total_est = 0
    processed = 0
    _throttled_finalize_progress(progress, phase="finalizing_hash", processed=processed, state=st)
    h = hashlib.sha256()
    since_emit = 0
    with tarfile.open(archive_path, "r:*") as tf:
        for member in tf.getmembers():
            arc = (member.name or "").lstrip("./")
            if arc == "MANIFEST.json":
                continue
            h.update(arc.encode("utf-8", errors="ignore"))
            h.update(b"\0")
            h.update(str(member.type).encode("ascii", errors="ignore"))
            h.update(b"\0")
            h.update(str(member.size).encode("ascii", errors="ignore"))
            h.update(b"\0")
            if member.isfile():
                fobj = tf.extractfile(member)
                if fobj is not None:
                    for chunk in iter(lambda: fobj.read(1024 * 1024), b""):
                        if not chunk:
                            break
                        h.update(chunk)
                        processed += len(chunk)
                        since_emit += len(chunk)
                        if since_emit >= _FINALIZE_HASH_PROGRESS_BYTES:
                            since_emit = 0
                            _throttled_finalize_progress(
                                progress, phase="finalizing_hash", processed=processed, state=st
                            )
            elif member.issym() or member.islnk():
                h.update((member.linkname or "").encode("utf-8", errors="ignore"))
    _throttled_finalize_progress(progress, phase="finalizing_hash", processed=max(processed, total_est), state=st)
    return h.hexdigest()


def _rewrite_manifest_in_archive(
    archive_path: str | Path,
    manifest_payload: dict[str, Any],
    *,
    progress: Callable[[str, int], None] | None = None,
    progress_state: dict[str, Any] | None = None,
) -> tuple[bool, str | None]:
    path = Path(archive_path)
    tmp = path.with_suffix(path.suffix + ".manifest-tmp")
    manifest_tmp = path.parent / f".{path.name}.MANIFEST.json"
    st: dict[str, Any] = progress_state if progress_state is not None else {"t": 0.0, "phase": ""}
    processed = 0
    try:
        manifest_tmp.write_text(json.dumps(manifest_payload, ensure_ascii=False, indent=2), encoding="utf-8")
        _throttled_finalize_progress(progress, phase="finalizing_manifest", processed=0, state=st)
        with tarfile.open(path, "r:gz") as src, tarfile.open(tmp, "w:gz") as dst:
            dst.add(manifest_tmp, arcname="MANIFEST.json")
            for m in src.getmembers():
                arc = (m.name or "").lstrip("./")
                if arc == "MANIFEST.json":
                    continue
                if m.isdir() or m.issym():
                    dst.addfile(m)
                else:
                    fobj = src.extractfile(m)
                    dst.addfile(m, fobj)
                    if m.isfile():
                        processed += int(getattr(m, "size", 0) or 0)
                        _throttled_finalize_progress(
                            progress, phase="finalizing_manifest", processed=processed, state=st
                        )
        os.replace(tmp, path)
    except Exception as e:
        try:
            if tmp.exists():
                tmp.unlink()
        except Exception:
            pass
        return False, str(e)
    finally:
        try:
            if manifest_tmp.exists():
                manifest_tmp.unlink()
        except Exception:
            pass
    return True, None


def _kill_child_group() -> None:
    global CHILD_PROC
    proc = CHILD_PROC
    if not proc:
        return
    try:
        pgid = os.getpgid(proc.pid)
        os.killpg(pgid, signal.SIGTERM)
    except Exception:
        try:
            proc.terminate()
        except Exception:
            pass
    try:
        proc.wait(timeout=5)
    except Exception:
        try:
            pgid = os.getpgid(proc.pid)
            os.killpg(pgid, signal.SIGKILL)
        except Exception:
            pass


def _on_signal(signum: int, frame: Any) -> None:
    global STOP_REQUESTED
    STOP_REQUESTED = True
    _kill_child_group()


def _try_collect_evidence(status_file: Path, status: dict[str, Any]) -> None:
    try:
        from tools.backup_evidence_collector import collect_backup_job_evidence
    except ImportError:
        from backup_evidence_collector import collect_backup_job_evidence

    jid = str(status.get("job_id") or "").strip()
    if not jid:
        return
    status_dir = status_file.parent.parent
    un = str(status.get("unit_name") or f"setuphelfer-backup@{jid}.service")
    us = str(status.get("unit_scope") or "system")
    bd = str(status.get("backup_dir") or "").strip() or None
    collect_backup_job_evidence(jid, status_dir=status_dir, unit_name=un, unit_scope=us, backup_dir=bd)


def _mark_terminal() -> None:
    global STATUS_FINAL_WRITTEN, _EVIDENCE_CTX, _EVIDENCE_COLLECTED
    STATUS_FINAL_WRITTEN = True
    if _EVIDENCE_CTX and not _EVIDENCE_COLLECTED:
        _EVIDENCE_COLLECTED = True
        try:
            _try_collect_evidence(_EVIDENCE_CTX["status_file"], _EVIDENCE_CTX["status"])
        except Exception:
            pass
        _EVIDENCE_CTX = None


def _write_cancel_final(
    status_file: Path,
    state: dict[str, Any],
    partial_path: str,
    manifest_tmp_path: str,
    *,
    abort_reason: str,
) -> None:
    """Finale Cancel-Zeilen in status.json (SIGTERM / systemctl stop)."""
    global STATUS_FINAL_WRITTEN
    _cleanup_partial(partial_path)
    try:
        Path(manifest_tmp_path).unlink(missing_ok=True)
    except Exception:
        pass
    partial_gone = not Path(partial_path).exists()
    _update_status(
        status_file,
        state,
        status="cancelled",
        code="backup.cancelled",
        severity="info",
        diagnosis_id="BACKUP-CANCEL-001",
        backup_finished_at=_now_iso(),
        abort_reason=abort_reason,
        archive_path=None,
        partial_path=None,
        manifest_tmp_path=None,
        suspend_guard_active=False,
        partial_deleted=partial_gone,
        progress_optional=None,
    )
    _mark_terminal()


def _cancel_if_stop_requested(
    status_file: Path,
    state: dict[str, Any],
    partial_path: str,
    manifest_tmp_path: str,
) -> bool:
    """True = Cancel geschrieben, main soll mit 0 beenden."""
    if not STOP_REQUESTED:
        return False
    _write_cancel_final(
        status_file,
        state,
        partial_path,
        manifest_tmp_path,
        abort_reason="user_cancel",
    )
    return True


def _full_inner_tar_command(partial_path: str, backup_dir_resolved: str) -> str:
    """Legacy: vollständiger Root-Backup-Befehl wie zuvor (Profil ``full-expert``)."""
    cmd, _meta = build_full_root_tar_command(
        partial_path, backup_dir_resolved, profile=PROFILE_FULL_EXPERT
    )
    return cmd


def _run_tar_pipeline_from_preflight(
    status_file: Path,
    status: dict[str, Any],
    partial_path: str,
    manifest_tmp_path: str,
    archive_path: str,
    manifest_payload: dict[str, Any],
    inner_tar_cmd: str,
    progress_ctx: dict[str, Any] | None = None,
) -> int:
    """Gemeinsame Pipeline: Preflight (Paket/Inhibit), inhibit-wrap, Monitor, Manifest, finalize — ohne Data-/Full-Tar zu vermischen."""
    global CHILD_PROC, _EVIDENCE_CTX, _EVIDENCE_COLLECTED
    _EVIDENCE_CTX = {"status_file": status_file, "status": status}
    _EVIDENCE_COLLECTED = False

    if _cancel_if_stop_requested(status_file, status, partial_path, manifest_tmp_path):
        return 0

    active_pkg = _detect_active_package_operations()
    if active_pkg:
        _update_status(
            status_file,
            status,
            status="error",
            code="backup.blocked_package_activity",
            severity="error",
            diagnosis_id="UPDATE-CONFLICT-041",
            abort_reason="package_activity_detected_preflight",
            backup_finished_at=_now_iso(),
            active_package_processes=active_pkg[:10],
            partial_deleted=_cleanup_partial(partial_path),
        )
        _mark_terminal()
        return 1

    inhibit = shutil.which("systemd-inhibit")
    if not inhibit:
        _update_status(
            status_file,
            status,
            status="error",
            code="backup.inhibit_failed",
            severity="error",
            diagnosis_id="SYSTEMD-INHIBIT-042",
            abort_reason="inhibit_not_available",
            backup_finished_at=_now_iso(),
            inhibit_available=False,
            inhibit_error="systemd-inhibit binary not found",
            suspend_guard_active=False,
            partial_deleted=_cleanup_partial(partial_path),
        )
        _mark_terminal()
        return 1
    if not os.access(inhibit, os.X_OK):
        _update_status(
            status_file,
            status,
            status="error",
            code="backup.inhibit_failed",
            severity="error",
            diagnosis_id="SYSTEMD-INHIBIT-042",
            abort_reason="inhibit_not_executable",
            backup_finished_at=_now_iso(),
            inhibit_available=True,
            inhibit_error="systemd-inhibit is not executable",
            suspend_guard_active=False,
            partial_deleted=_cleanup_partial(partial_path),
        )
        _mark_terminal()
        return 1

    if _cancel_if_stop_requested(status_file, status, partial_path, manifest_tmp_path):
        return 0

    guarded_cmd = (
        f"{shlex.quote(inhibit)} --what=sleep --why='Setuphelfer Backup läuft' --mode=block "
        f"sh -c {shlex.quote(inner_tar_cmd)}"
    )
    drain_collect: dict[str, Any] = {
        "head_parts": [],
        "hlen": 0,
        "tail": deque(maxlen=STDERR_TAIL_MAX_LINES),
    }
    stderr_log_fh: Any | None = None
    stderr_log_path: Path | None = None
    jid = str(status.get("job_id") or "").strip() or "unknown"
    try:
        STDERR_LOG_DIR.mkdir(parents=True, exist_ok=True)
        stderr_log_path = _tar_stderr_log_path(jid)
        stderr_log_fh = open(stderr_log_path, "w", encoding="utf-8", errors="replace")
    except OSError:
        stderr_log_path = None
        stderr_log_fh = None

    log_status_kw: dict[str, Any] = {"inhibit_available": True, "suspend_guard_active": True}
    if stderr_log_path is not None:
        log_status_kw["tar_stderr_log"] = str(stderr_log_path)
    _update_status(status_file, status, **log_status_kw)

    if _cancel_if_stop_requested(status_file, status, partial_path, manifest_tmp_path):
        if stderr_log_fh:
            try:
                stderr_log_fh.close()
            except OSError:
                pass
        return 0

    def _drain_stderr_worker() -> None:
        proc = CHILD_PROC
        if not proc or not proc.stderr:
            return
        lbuf = ""
        try:
            while True:
                chunk = proc.stderr.read(4096)
                if not chunk:
                    break
                if stderr_log_fh:
                    try:
                        stderr_log_fh.write(chunk)
                        stderr_log_fh.flush()
                    except OSError:
                        pass
                hlen: int = drain_collect["hlen"]
                if hlen < STDERR_HEAD_MAX_BYTES:
                    take = chunk[: STDERR_HEAD_MAX_BYTES - hlen]
                    drain_collect["head_parts"].append(take)
                    drain_collect["hlen"] = hlen + len(take)
                lbuf += chunk
                while "\n" in lbuf:
                    line, lbuf = lbuf.split("\n", 1)
                    drain_collect["tail"].append(line)
            if lbuf:
                drain_collect["tail"].append(lbuf)
        finally:
            if stderr_log_fh:
                try:
                    stderr_log_fh.close()
                except OSError:
                    pass

    CHILD_PROC = subprocess.Popen(
        ["sh", "-c", guarded_cmd],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
        preexec_fn=os.setsid,
    )
    stderr_thread = threading.Thread(target=_drain_stderr_worker, name="setuphelfer-tar-stderr", daemon=True)
    stderr_thread.start()

    def _join_stderr_and_reap() -> tuple[str, str, int]:
        _reap_child_returncode(CHILD_PROC)
        stderr_thread.join(timeout=600)
        ht = "".join(drain_collect["head_parts"])[:STDERR_HEAD_MAX_BYTES]
        tt = "\n".join(list(drain_collect["tail"]))
        return ht, tt, _child_exit_code(CHILD_PROC)

    start_monotonic = time.monotonic()
    if progress_ctx is not None:
        progress_ctx["start_monotonic"] = start_monotonic
        warns = list(progress_ctx.get("profile_warnings") or [])
        notes = progress_ctx.get("preflight_notes") or []
        if isinstance(notes, list):
            warns.extend([f"preflight:{n}" for n in notes[:8]])
        po = merge_progress_optional(
            status.get("progress_optional"),
            phase="preflight",
            bytes_current=0,
            bytes_total_estimate=progress_ctx.get("bytes_total_estimate"),
            start_monotonic=start_monotonic,
            compression_method=str(
                progress_ctx.get("compression_method")
                or (status.get("compression_detail") or {}).get("compression_engine")
                or "gzip"
            ),
            current_operation="package_and_inhibit_ok",
            target_mount=progress_ctx.get("target_mount"),
            target_free_bytes=progress_ctx.get("target_free_bytes"),
            warning_codes=warns,
            health_flags={"compression_detail": status.get("compression_detail") or {}},
            throughput_state=progress_ctx["throughput_state"],
        )
        _update_status(
            status_file,
            status,
            progress_optional=po,
            compression_method=str(progress_ctx.get("compression_method") or "gzip"),
        )
    while True:
        if STOP_REQUESTED:
            _kill_child_group()
            _join_stderr_and_reap()
            _write_cancel_final(
                status_file,
                status,
                partial_path,
                manifest_tmp_path,
                abort_reason="user_cancel",
            )
            return 0
        pkg_now = _detect_active_package_operations()
        if pkg_now:
            _kill_child_group()
            head_text_p, tail_text_p, rc_pkg = _join_stderr_and_reap()
            _te_p = tail_text_p.strip()
            excerpt_tail_p = _te_p[-300:] if len(_te_p) > 300 else _te_p
            _update_status(
                status_file,
                status,
                status="error",
                code="backup.blocked_package_activity",
                severity="error",
                diagnosis_id="UPDATE-CONFLICT-041",
                abort_reason="package_activity_detected_runtime",
                backup_finished_at=_now_iso(),
                active_package_processes=pkg_now[:10],
                suspend_guard_active=False,
                partial_deleted=_cleanup_partial(partial_path),
                subprocess_returncode=rc_pkg,
                stderr_tail=tail_text_p,
                stderr_excerpt=excerpt_tail_p,
                tar_stderr_log=str(stderr_log_path) if stderr_log_path else None,
                final_archive_exists=False,
                last_error_code="backup.blocked_package_activity",
                last_status_message="Backup blockiert: Paketaktivität",
            )
            _attach_backup_failure_notification(
                status_file,
                status,
                job_id=str(status.get("job_id") or ""),
                code="backup.blocked_package_activity",
                stderr_excerpt=excerpt_tail_p,
                tar_return_code=rc_pkg,
            )
            _mark_terminal()
            return 1
        if CHILD_PROC.poll() is not None:
            break
        try:
            if Path(partial_path).exists():
                size = Path(partial_path).stat().st_size
            else:
                size = 0
        except Exception:
            size = 0
        if progress_ctx is not None:
            pc = progress_ctx
            sm = float(pc.get("start_monotonic") or start_monotonic)
            warns = list(pc.get("profile_warnings") or [])
            po = merge_progress_optional(
                status.get("progress_optional"),
                phase="archiving",
                bytes_current=size,
                bytes_total_estimate=pc.get("bytes_total_estimate"),
                start_monotonic=sm,
                compression_method=str(pc.get("compression_method") or "gzip"),
                current_operation="tar_create_stream",
                target_mount=pc.get("target_mount"),
                target_free_bytes=pc.get("target_free_bytes"),
                warning_codes=warns,
                health_flags={"compression_detail": status.get("compression_detail") or {}},
                throughput_state=pc["throughput_state"],
            )
            po["running_for_s"] = int(time.monotonic() - start_monotonic)
            _update_status(status_file, status, progress_optional=po)
        else:
            _update_status(
                status_file,
                status,
                progress_optional={
                    "bytes_current": size,
                    "running_for_s": int(time.monotonic() - start_monotonic),
                },
            )
        time.sleep(0.5)

    if STOP_REQUESTED:
        _join_stderr_and_reap()
        _write_cancel_final(
            status_file,
            status,
            partial_path,
            manifest_tmp_path,
            abort_reason="user_cancel",
        )
        return 0

    head_text, tail_text, rc = _join_stderr_and_reap()
    _te = tail_text.strip()
    stderr_excerpt_tail = _te[-300:] if len(_te) > 300 else _te
    inhibit_failed = "failed to inhibit" in head_text.lower() or "access denied" in head_text.lower()
    if STOP_REQUESTED:
        _write_cancel_final(
            status_file,
            status,
            partial_path,
            manifest_tmp_path,
            abort_reason="user_cancel",
        )
        return 0

    stderr_blob = _read_full_tar_stderr(head_text, tail_text, stderr_log_path)
    tar_cls = classify_tar_run(tar_exit_code=rc, stderr_text=stderr_blob)
    tar_class_fields = classification_to_job_status_fields(tar_cls)
    volatile_tar_finalize = False

    if inhibit_failed:
        _update_status(
            status_file,
            status,
            status="error",
            code="backup.inhibit_failed",
            severity="error",
            diagnosis_id="SYSTEMD-INHIBIT-042",
            abort_reason="inhibit_failed",
            backup_finished_at=_now_iso(),
            inhibit_available=True,
            inhibit_error=head_text.strip()[:300],
            suspend_guard_active=False,
            partial_deleted=_cleanup_partial(partial_path),
            subprocess_returncode=rc,
            stderr_tail=tail_text,
            stderr_excerpt=stderr_excerpt_tail,
            tar_stderr_log=str(stderr_log_path) if stderr_log_path else None,
            **tar_class_fields,
        )
        _mark_terminal()
        return 1

    if _stderr_indicates_target_write_io_error(head_text, tail_text):
        _update_status(
            status_file,
            status,
            status="error",
            code="backup.write_io_error",
            severity="error",
            diagnosis_id="BACKUP-IO-ERROR-050",
            abort_reason="target_write_io_error",
            backup_finished_at=_now_iso(),
            stderr_excerpt=stderr_excerpt_tail,
            stderr_tail=tail_text,
            subprocess_returncode=rc,
            tar_stderr_log=str(stderr_log_path) if stderr_log_path else None,
            suspend_guard_active=False,
            partial_deleted=False,
            **tar_class_fields,
        )
        _mark_terminal()
        return 1

    if rc != 0:
        try:
            _partial_stat = Path(partial_path).stat()
            _partial_exists = True
            _partial_bytes = int(_partial_stat.st_size)
        except OSError:
            _partial_exists = False
            _partial_bytes = 0
        if tar_cls.allows_warning_downgrade and _partial_exists and _partial_bytes > 0:
            volatile_tar_finalize = True
        else:
            _outcome = decide_tar_nonzero_job_outcome(
                tar_exit_code=rc,
                stderr_text=stderr_blob,
                partial_exists=_partial_exists,
                partial_bytes=_partial_bytes,
                final_archive_exists=False,
                finalize_attempted=False,
                finalize_ok=False,
                sha256_verified=False,
                verify_deep_ok=False,
            )
            return _publish_tar_nonzero_failure(
                status_file,
                status,
                partial_path=partial_path,
                rc=rc,
                stderr_excerpt=stderr_excerpt_tail,
                stderr_tail=tail_text,
                stderr_log_path=stderr_log_path,
                tar_class_fields=tar_class_fields,
                outcome=_outcome,
            )

    if rc == 0 or volatile_tar_finalize:
        completed_at = _now_iso()
        finalize_prog_state: dict[str, Any] = {"t": 0.0, "phase": ""}

        def _finalize_emit(phase: str, proc_bytes: int) -> None:
            try:
                psz = Path(partial_path).stat().st_size
            except OSError:
                psz = 0
            now_m = time.monotonic()
            merged = dict(status.get("progress_optional") or {})
            merged.update(
                {
                    "bytes_current": psz,
                    "running_for_s": int(now_m - start_monotonic),
                    "finalize_phase": phase,
                    "finalize_bytes_processed": proc_bytes,
                    "phase": "finalizing",
                }
            )
            _update_status(status_file, status, progress_optional=merged)

        if STOP_REQUESTED:
            _write_cancel_final(
                status_file,
                status,
                partial_path,
                manifest_tmp_path,
                abort_reason="user_cancel",
            )
            return 0
        try:
            current_size = Path(partial_path).stat().st_size
        except Exception:
            current_size = 0
        payload_hash = _sha256_archive_payload(
            partial_path,
            progress=_finalize_emit,
            progress_state=finalize_prog_state,
        )
        manifest_payload.update(
            {
                "completed_at": completed_at,
                "archive_size": str(current_size),
                "hash": f"sha256:{payload_hash}",
            }
        )
        ok_manifest = False
        manifest_err: str | None = None
        for _attempt in range(3):
            if STOP_REQUESTED:
                _write_cancel_final(
                    status_file,
                    status,
                    partial_path,
                    manifest_tmp_path,
                    abort_reason="user_cancel",
                )
                return 0
            ok_manifest, manifest_err = _rewrite_manifest_in_archive(
                partial_path,
                manifest_payload,
                progress=_finalize_emit,
                progress_state=finalize_prog_state,
            )
            if ok_manifest:
                break
        if not ok_manifest:
            if volatile_tar_finalize:
                _outcome = decide_tar_nonzero_job_outcome(
                    tar_exit_code=rc,
                    stderr_text=stderr_blob,
                    partial_exists=True,
                    partial_bytes=current_size,
                    final_archive_exists=False,
                    finalize_attempted=True,
                    finalize_ok=False,
                    sha256_verified=False,
                    verify_deep_ok=False,
                )
                return _publish_tar_nonzero_failure(
                    status_file,
                    status,
                    partial_path=partial_path,
                    rc=rc,
                    stderr_excerpt=stderr_excerpt_tail,
                    stderr_tail=tail_text,
                    stderr_log_path=stderr_log_path,
                    tar_class_fields=tar_class_fields,
                    outcome=_outcome,
                )
            _update_status(
                status_file,
                status,
                status="error",
                code="backup.failed_manifest_missing",
                severity="error",
                diagnosis_id="BACKUP-MANIFEST-001",
                abort_reason="manifest_embed_failed",
                backup_finished_at=_now_iso(),
                suspend_guard_active=False,
                partial_deleted=_cleanup_partial(partial_path),
                manifest_error=str(manifest_err or "")[:300],
                subprocess_returncode=0,
                tar_stderr_log=str(stderr_log_path) if stderr_log_path else None,
            )
            _mark_terminal()
            return 1
        if STOP_REQUESTED:
            _write_cancel_final(
                status_file,
                status,
                partial_path,
                manifest_tmp_path,
                abort_reason="user_cancel",
            )
            return 0
        _finalize_emit("renaming", current_size)
        ok_rename = False
        rename_error = ""
        try:
            os.replace(partial_path, archive_path)
            ok_rename = True
        except Exception as e:
            rename_error = str(e)
        if ok_rename:
            asz = Path(archive_path).stat().st_size if Path(archive_path).exists() else 0
            merged_ok = dict(status.get("progress_optional") or {})
            merged_ok.update(
                {
                    "bytes_current": asz,
                    "running_for_s": int(time.monotonic() - start_monotonic),
                    "finalize_phase": "complete",
                    "finalize_bytes_processed": asz,
                    "phase": "completed",
                }
            )
            if volatile_tar_finalize:
                vd_ok, vd_key = _runner_verify_deep(archive_path)
                _outcome = decide_tar_nonzero_job_outcome(
                    tar_exit_code=rc,
                    stderr_text=stderr_blob,
                    partial_exists=True,
                    partial_bytes=current_size,
                    final_archive_exists=True,
                    finalize_attempted=True,
                    finalize_ok=True,
                    sha256_verified=bool(payload_hash),
                    verify_deep_ok=vd_ok,
                )
                if str(_outcome.get("code")) == "backup.success_with_warnings":
                    _update_status(
                        status_file,
                        status,
                        status="success",
                        code="backup.success_with_warnings",
                        severity="success",
                        warning_status="completed_with_warnings",
                        backup_integrity_status="verified",
                        diagnosis_id=None,
                        abort_reason=None,
                        backup_finished_at=_now_iso(),
                        suspend_guard_active=False,
                        partial_deleted=not Path(partial_path).exists(),
                        archive_path=archive_path,
                        partial_path=partial_path,
                        progress_optional=merged_ok,
                        manifest_hash=f"sha256:{payload_hash}",
                        subprocess_returncode=rc,
                        tar_stderr_log=str(stderr_log_path) if stderr_log_path else None,
                        verify_deep_ok=vd_ok,
                        verify_deep_message_key=vd_key,
                        warnings=_outcome.get("warnings"),
                        **tar_class_fields,
                    )
                    _attach_backup_success_notification(
                        status_file,
                        status,
                        job_id=str(status.get("job_id") or ""),
                        code="backup.success_with_warnings",
                        backup_type=str(status.get("backup_type") or ""),
                        backup_profile=str(
                            (status.get("compression_detail") or {}).get("profile_normalized")
                            or status.get("backup_profile")
                            or ""
                        ),
                        backup_dir=str(status.get("backup_dir") or ""),
                        archive_path=archive_path,
                        manifest_hash=f"sha256:{payload_hash}",
                        verify_deep_ok=vd_ok,
                        backup_integrity_status="verified",
                        verify_deep_message_key=vd_key,
                        warning_status="completed_with_warnings",
                        warnings=_outcome.get("warnings"),
                    )
                    try:
                        Path(manifest_tmp_path).unlink(missing_ok=True)
                    except Exception:
                        pass
                    _mark_terminal()
                    return 0
                _cleanup_archive(archive_path)
                if "partial_deleted" in _outcome and _outcome.get("partial_deleted"):
                    _cleanup_partial(partial_path)
                return _publish_tar_nonzero_failure(
                    status_file,
                    status,
                    partial_path=partial_path,
                    rc=rc,
                    stderr_excerpt=stderr_excerpt_tail,
                    stderr_tail=tail_text,
                    stderr_log_path=stderr_log_path,
                    tar_class_fields=tar_class_fields,
                    outcome=_outcome,
                )
            _update_status(
                status_file,
                status,
                status="success",
                code="backup.success",
                severity="success",
                diagnosis_id=None,
                abort_reason=None,
                backup_finished_at=_now_iso(),
                suspend_guard_active=False,
                partial_deleted=not Path(partial_path).exists(),
                archive_path=archive_path,
                partial_path=partial_path,
                progress_optional=merged_ok,
                manifest_hash=f"sha256:{payload_hash}",
                subprocess_returncode=0,
                tar_stderr_log=str(stderr_log_path) if stderr_log_path else None,
            )
            _attach_backup_success_notification(
                status_file,
                status,
                job_id=str(status.get("job_id") or ""),
                code="backup.success",
                backup_type=str(status.get("backup_type") or ""),
                backup_profile=str(
                    (status.get("compression_detail") or {}).get("profile_normalized")
                    or status.get("backup_profile")
                    or ""
                ),
                backup_dir=str(status.get("backup_dir") or ""),
                archive_path=archive_path,
                manifest_hash=f"sha256:{payload_hash}",
            )
            try:
                Path(manifest_tmp_path).unlink(missing_ok=True)
            except Exception:
                pass
            _mark_terminal()
            return 0
        if volatile_tar_finalize:
            _outcome = decide_tar_nonzero_job_outcome(
                tar_exit_code=rc,
                stderr_text=stderr_blob,
                partial_exists=True,
                partial_bytes=current_size,
                final_archive_exists=False,
                finalize_attempted=True,
                finalize_ok=False,
                sha256_verified=False,
                verify_deep_ok=False,
            )
            return _publish_tar_nonzero_failure(
                status_file,
                status,
                partial_path=partial_path,
                rc=rc,
                stderr_excerpt=stderr_excerpt_tail,
                stderr_tail=tail_text,
                stderr_log_path=stderr_log_path,
                tar_class_fields=tar_class_fields,
                outcome=_outcome,
            )
        _update_status(
            status_file,
            status,
            status="error",
            code="backup.finalize_failed",
            severity="error",
            diagnosis_id=None,
            abort_reason="finalize_failed",
            backup_finished_at=_now_iso(),
            suspend_guard_active=False,
            partial_deleted=_cleanup_partial(partial_path),
            finalize_error=rename_error[:300],
            subprocess_returncode=0,
            tar_stderr_log=str(stderr_log_path) if stderr_log_path else None,
        )
        _mark_terminal()
        return 1

    _outcome = decide_tar_nonzero_job_outcome(
        tar_exit_code=rc,
        stderr_text=stderr_blob,
        partial_exists=False,
        partial_bytes=0,
        final_archive_exists=False,
        finalize_attempted=False,
        finalize_ok=False,
        sha256_verified=False,
        verify_deep_ok=False,
    )
    return _publish_tar_nonzero_failure(
        status_file,
        status,
        partial_path=partial_path,
        rc=rc,
        stderr_excerpt=stderr_excerpt_tail,
        stderr_tail=tail_text,
        stderr_log_path=stderr_log_path,
        tar_class_fields=tar_class_fields,
        outcome=_outcome,
    )


def _attach_backup_failure_notification(
    status_file: Path,
    state: dict[str, Any],
    *,
    job_id: str,
    code: str,
    stderr_excerpt: str = "",
    tar_return_code: int | None = None,
) -> None:
    """Best-effort failure E-Mail; never changes backup status on SMTP failure."""
    prog = state.get("progress_optional") if isinstance(state.get("progress_optional"), dict) else {}
    bytes_written = prog.get("bytes_current") or state.get("written_bytes")
    runtime_s = prog.get("running_for_s") or prog.get("elapsed_seconds") or state.get("elapsed_seconds")
    try:
        bytes_int = int(bytes_written) if bytes_written is not None else None
    except (TypeError, ValueError):
        bytes_int = None
    try:
        runtime_int = int(runtime_s) if runtime_s is not None else None
    except (TypeError, ValueError):
        runtime_int = None
    cd = state.get("compression_detail") if isinstance(state.get("compression_detail"), dict) else {}
    profile = str(cd.get("profile_normalized") or state.get("backup_profile") or "")
    cfg = load_effective_notification_config()
    result = maybe_send_backup_failure_email(
        job_id=job_id,
        status=str(state.get("status") or "error"),
        status_code=code,
        backup_type=str(state.get("backup_type") or ""),
        backup_profile=profile,
        target_path=str(state.get("backup_dir") or ""),
        diagnosis_id=str(state.get("diagnosis_id") or ""),
        abort_reason=str(state.get("abort_reason") or ""),
        archive_path=str(state.get("archive_path") or ""),
        partial_path=str(state.get("partial_path") or ""),
        partial_deleted=state.get("partial_deleted") if "partial_deleted" in state else None,
        final_archive_exists=bool(state.get("final_archive_exists")),
        runtime_seconds=runtime_int,
        bytes_written=bytes_int,
        tar_return_code=tar_return_code if tar_return_code is not None else state.get("subprocess_returncode"),
        tar_warning_classification=str(state.get("tar_warning_classification") or ""),
        error_excerpt=stderr_excerpt or str(state.get("stderr_excerpt") or "")[:800],
        config=cfg,
    )
    _update_status(status_file, state, **notification_status_fields(cfg, result))


def _attach_backup_success_notification(
    status_file: Path,
    state: dict[str, Any],
    *,
    job_id: str,
    code: str,
    backup_type: str,
    backup_profile: str,
    backup_dir: str,
    archive_path: str,
    manifest_hash: str,
    verify_deep_ok: bool | None = None,
    backup_integrity_status: str | None = None,
    verify_deep_message_key: str | None = None,
    warning_status: str | None = None,
    warnings: Any = None,
) -> None:
    """Best-effort E-Mail after success; never changes backup status on SMTP failure."""
    prog = state.get("progress_optional") if isinstance(state.get("progress_optional"), dict) else {}
    bytes_written = prog.get("bytes_current")
    runtime_s = prog.get("running_for_s") or prog.get("elapsed_seconds")
    try:
        bytes_int = int(bytes_written) if bytes_written is not None else None
    except (TypeError, ValueError):
        bytes_int = None
    try:
        runtime_int = int(runtime_s) if runtime_s is not None else None
    except (TypeError, ValueError):
        runtime_int = None
    cfg = load_effective_notification_config()
    result = maybe_send_backup_success_email(
        job_id=job_id,
        status_code=code,
        backup_type=backup_type,
        backup_profile=backup_profile,
        target_path=backup_dir,
        archive_path=archive_path,
        manifest_hash=manifest_hash,
        verify_deep_ok=verify_deep_ok,
        backup_integrity_status=backup_integrity_status,
        verify_deep_message_key=verify_deep_message_key,
        runtime_seconds=runtime_int,
        bytes_written=bytes_int,
        warning_status=warning_status,
        warnings=warnings,
        config=cfg,
    )
    _update_status(status_file, state, **notification_status_fields(cfg, result))


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Setuphelfer isolated backup runner")
    parser.add_argument("--job-id", required=True)
    parser.add_argument("--backup-type", default="")
    parser.add_argument("--backup-dir", default="")
    parser.add_argument("--source", default="")
    parser.add_argument("--lang", default="")
    parser.add_argument("--status-dir", default="/var/lib/setuphelfer/backup-jobs")
    parser.add_argument("--unit-name", default="")
    parser.add_argument("--unit-scope", default="system")
    return parser.parse_args()


def main() -> int:
    global CHILD_PROC, STATUS_FINAL_WRITTEN, _EVIDENCE_CTX, _EVIDENCE_COLLECTED
    args = _parse_args()
    STATUS_FINAL_WRITTEN = False
    _EVIDENCE_CTX = None
    _EVIDENCE_COLLECTED = False
    signal.signal(signal.SIGTERM, _on_signal)
    signal.signal(signal.SIGINT, _on_signal)

    job_id = args.job_id.strip()
    status_dir = Path(args.status_dir).resolve()
    job_meta = _load_job_json(status_dir, job_id)
    backup_dir_raw = (args.backup_dir or job_meta.get("backup_dir") or "").strip()
    source_raw = (args.source or job_meta.get("source") or "").strip()
    backup_type = (args.backup_type or job_meta.get("backup_type") or "data").strip().lower()
    if backup_type not in ("data", "full"):
        backup_type = "data"

    unit_name = args.unit_name.strip() or os.environ.get("SYSTEMD_UNIT", "").strip() or f"setuphelfer-backup@{job_id}.service"
    unit_scope = (args.unit_scope or "system").strip().lower()

    if backup_type == "full":
        if not backup_dir_raw:
            status_file = _status_path(status_dir, job_id)
            started = _now_iso()
            err_status: dict[str, Any] = {
                "job_id": job_id,
                "unit_name": unit_name,
                "unit_scope": unit_scope,
                "status": "error",
                "code": "backup.runner_config_missing",
                "severity": "error",
                "diagnosis_id": "SYSTEMD-RUNNER-002",
                "backup_started_at": started,
                "backup_finished_at": _now_iso(),
                "backup_type": "full",
                "backup_dir": backup_dir_raw,
                "source": "/",
                "archive_path": None,
                "partial_path": None,
                "abort_reason": "job_config_missing",
                "progress_optional": None,
            }
            _write_status(status_file, err_status)
            _mark_terminal()
            return 1
        if os.geteuid() != 0:
            status_file = _status_path(status_dir, job_id)
            started = _now_iso()
            priv_status: dict[str, Any] = {
                "job_id": job_id,
                "unit_name": unit_name,
                "unit_scope": unit_scope,
                "status": "error",
                "code": "backup.runner_privilege",
                "severity": "error",
                "diagnosis_id": "FULL-RUNNER-ROOT-001",
                "backup_started_at": started,
                "backup_finished_at": _now_iso(),
                "backup_type": "full",
                "backup_dir": backup_dir_raw,
                "source": "/",
                "archive_path": None,
                "partial_path": None,
                "abort_reason": "full_requires_root",
                "progress_optional": None,
            }
            _write_status(status_file, priv_status)
            _mark_terminal()
            return 1
        backup_dir = str(Path(backup_dir_raw).resolve())
        status_file = _status_path(status_dir, job_id)
        archive_path = str(Path(backup_dir) / f"pi-backup-full-{_timestamp()}.tar.gz")
        partial_path = f"{archive_path}.partial"
        manifest_tmp_path = str(Path(partial_path).with_name(f".{job_id}.MANIFEST.json"))
        started = _now_iso()
        completed_at = ""
        manifest_payload_full: dict[str, Any] = {
            "job_id": job_id,
            "backup_type": "full",
            "source": "/",
            "backup_dir": backup_dir,
            "created_at": started,
            "completed_at": completed_at,
            "archive_size": "0",
            "hash": "sha256:",
        }
        Path(manifest_tmp_path).write_text(json.dumps(manifest_payload_full, ensure_ascii=False, indent=2), encoding="utf-8")
        status_full: dict[str, Any] = {
            "job_id": job_id,
            "unit_name": unit_name,
            "unit_scope": unit_scope,
            "status": "running",
            "code": "backup.job.running",
            "severity": "info",
            "diagnosis_id": None,
            "backup_started_at": started,
            "backup_finished_at": None,
            "backup_type": "full",
            "backup_dir": backup_dir,
            "source": "/",
            "archive_path": archive_path,
            "partial_path": partial_path,
            "manifest_tmp_path": manifest_tmp_path,
            "abort_reason": None,
            "progress_optional": {"bytes_current": 0},
        }
        _write_status(status_file, status_full)

        def _finalize_cancel_if_needed_full() -> None:
            global STATUS_FINAL_WRITTEN
            if not STOP_REQUESTED or STATUS_FINAL_WRITTEN:
                return
            try:
                _write_cancel_final(
                    status_file,
                    status_full,
                    partial_path,
                    manifest_tmp_path,
                    abort_reason="user_cancel",
                )
            except Exception:
                pass

        atexit.register(_finalize_cancel_if_needed_full)
        profile_arg = str(job_meta.get("backup_profile") or "").strip()
        inner_full, compression_meta = build_full_root_tar_command(
            partial_path, backup_dir, profile=profile_arg or "recommended"
        )
        status_full["compression_detail"] = compression_meta
        if compression_meta.get("compression_preflight_blocked"):
            msg = str(compression_meta.get("compression_preflight_message") or "Kompression nicht verfügbar")
            _update_status(
                status_file,
                status_full,
                status="error",
                code="backup.compression_unavailable",
                severity="error",
                abort_reason="compression_preflight_blocked",
                backup_finished_at=_now_iso(),
                last_error_code="backup.compression_unavailable",
                last_error_message=msg[:500],
                last_status_message=msg[:200],
                final_archive_exists=False,
            )
            _attach_backup_failure_notification(
                status_file,
                status_full,
                job_id=job_id,
                code="backup.compression_unavailable",
                stderr_excerpt=msg,
            )
            _mark_terminal()
            return 1
        pre = quick_target_preflight(backup_dir)
        progress_ctx: dict[str, Any] = {
            "throughput_state": {"last_bytes": 0, "last_t": time.monotonic()},
            "compression_method": compression_meta.get("compression_engine") or compression_meta["compression_method"],
            "target_free_bytes": pre.get("target_free_bytes"),
            "target_mount": pre.get("target_mount"),
            "bytes_total_estimate": None,
            "profile_warnings": list(compression_meta.get("profile_warnings") or []),
            "preflight_notes": pre.get("preflight_notes") or [],
        }
        return _run_tar_pipeline_from_preflight(
            status_file,
            status_full,
            partial_path,
            manifest_tmp_path,
            archive_path,
            manifest_payload_full,
            inner_full,
            progress_ctx=progress_ctx,
        )

    if not backup_dir_raw or not source_raw:
        status_file = _status_path(status_dir, job_id)
        started = _now_iso()
        status = {
            "job_id": job_id,
            "unit_name": args.unit_name.strip() or os.environ.get("SYSTEMD_UNIT", "").strip() or f"setuphelfer-backup@{job_id}.service",
            "unit_scope": (args.unit_scope or "system").strip().lower(),
            "status": "error",
            "code": "backup.runner_config_missing",
            "severity": "error",
            "diagnosis_id": "SYSTEMD-RUNNER-002",
            "backup_started_at": started,
            "backup_finished_at": _now_iso(),
            "backup_type": backup_type,
            "backup_dir": backup_dir_raw,
            "source": source_raw,
            "archive_path": None,
            "partial_path": None,
            "abort_reason": "job_config_missing",
            "progress_optional": None,
        }
        _write_status(status_file, status)
        _mark_terminal()
        return 1

    backup_dir = str(Path(backup_dir_raw).resolve())
    source = str(Path(source_raw).resolve())
    status_file = _status_path(status_dir, job_id)

    archive_path = str(Path(backup_dir) / f"pi-backup-{backup_type}-{_timestamp()}.tar.gz")
    partial_path = f"{archive_path}.partial"
    manifest_tmp_path = str(Path(partial_path).with_name(f".{job_id}.MANIFEST.json"))
    started = _now_iso()
    completed_at = ""

    manifest_payload: dict[str, Any] = {
        "job_id": job_id,
        "backup_type": backup_type,
        "source": source,
        "backup_dir": backup_dir,
        "created_at": started,
        "completed_at": completed_at,
        "archive_size": "0",
        "hash": "sha256:",
    }
    Path(manifest_tmp_path).write_text(json.dumps(manifest_payload, ensure_ascii=False, indent=2), encoding="utf-8")

    status: dict[str, Any] = {
        "job_id": job_id,
        "unit_name": unit_name,
        "unit_scope": unit_scope,
        "status": "running",
        "code": "backup.job.running",
        "severity": "info",
        "diagnosis_id": None,
        "backup_started_at": started,
        "backup_finished_at": None,
        "backup_type": backup_type,
        "backup_dir": backup_dir,
        "source": source,
        "archive_path": archive_path,
        "partial_path": partial_path,
        "manifest_tmp_path": manifest_tmp_path,
        "abort_reason": None,
        "progress_optional": {"bytes_current": 0},
    }
    _write_status(status_file, status)

    def _finalize_cancel_if_needed() -> None:
        """„finally“-Ersatz: bei Prozessende noch ohne Terminalstate und mit Abbruchwunsch Cancel schreiben."""
        global STATUS_FINAL_WRITTEN
        if not STOP_REQUESTED or STATUS_FINAL_WRITTEN:
            return
        try:
            _write_cancel_final(
                status_file,
                status,
                partial_path,
                manifest_tmp_path,
                abort_reason="user_cancel",
            )
        except Exception:
            pass

    atexit.register(_finalize_cancel_if_needed)

    source_rel = str(Path(source).resolve()).lstrip("/")
    inner_tar_cmd = f"tar -czf {shlex.quote(partial_path)} -C / {shlex.quote(source_rel)}"
    return _run_tar_pipeline_from_preflight(
        status_file,
        status,
        partial_path,
        manifest_tmp_path,
        archive_path,
        manifest_payload,
        inner_tar_cmd,
        progress_ctx=None,
    )

if __name__ == "__main__":
    raise SystemExit(main())
