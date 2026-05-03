#!/usr/bin/env python3
from __future__ import annotations

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
from typing import Any

import psutil

# Volles tar-stderr: /var/log/setuphelfer/backup-<job_id>.log; Kopf/Schwanz nur im RAM.
STDERR_LOG_DIR = Path("/var/log/setuphelfer")
STDERR_HEAD_MAX_BYTES = 8192
STDERR_TAIL_MAX_LINES = 20


STOP_REQUESTED = False
CHILD_PROC: subprocess.Popen[str] | None = None
STATUS_FINAL_WRITTEN = False


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
    _write_status(path, state)


def _detect_active_package_operations() -> list[dict[str, Any]]:
    active: list[dict[str, Any]] = []
    for proc in psutil.process_iter(["pid", "name", "cmdline"]):
        try:
            pid = int(proc.info.get("pid") or 0)
            name = str(proc.info.get("name") or "").strip()
            cmdline = proc.info.get("cmdline") or []
            cmd_joined = " ".join(str(x) for x in cmdline if x)
            hay = f"{name} {cmd_joined}".lower()
            if "/usr/lib/apt/methods/" in hay:
                continue
            if "unattended-upgrade-shutdown" in hay:
                continue
            is_blocking = any(
                token in hay
                for token in (
                    " apt-get ",
                    " apt ",
                    " dpkg ",
                    "unattended-upgrade",
                    "apt.systemd.daily",
                )
            ) or name in {"apt", "apt-get", "dpkg", "apt.systemd.daily"}
            if is_blocking:
                active.append({"pid": pid, "name": name, "cmdline": cmd_joined[:300]})
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
        except Exception:
            continue
    return active


def _cleanup_partial(partial_path: str) -> bool:
    p = Path(partial_path)
    existed = p.exists()
    try:
        if existed:
            p.unlink()
    except Exception:
        pass
    return existed and not p.exists()


def _sha256_file(path: str | Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _sha256_archive_payload(archive_path: str | Path) -> str:
    """
    Deterministischer Integritäts-Hash über Archivinhalt ohne MANIFEST.json,
    damit der Hash stabil bleibt, obwohl das Manifest den Hash selbst trägt.
    """
    h = hashlib.sha256()
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
                        h.update(chunk)
            elif member.issym() or member.islnk():
                h.update((member.linkname or "").encode("utf-8", errors="ignore"))
    return h.hexdigest()


def _rewrite_manifest_in_archive(archive_path: str | Path, manifest_payload: dict[str, Any]) -> tuple[bool, str | None]:
    path = Path(archive_path)
    tmp = path.with_suffix(path.suffix + ".manifest-tmp")
    manifest_tmp = path.parent / f".{path.name}.MANIFEST.json"
    try:
        manifest_tmp.write_text(json.dumps(manifest_payload, ensure_ascii=False, indent=2), encoding="utf-8")
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


def _mark_terminal() -> None:
    global STATUS_FINAL_WRITTEN
    STATUS_FINAL_WRITTEN = True


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
    """Wie app._do_backup_logic (full): Archiv über / mit festen Excludes; Zielverzeichnis ausgeschlossen."""
    bd = str(Path(backup_dir_resolved).resolve())
    return (
        f"tar -czf {shlex.quote(partial_path)} "
        f"--exclude={shlex.quote(bd)} "
        f"--exclude=/proc --exclude=/sys --exclude=/dev --exclude=/tmp --exclude=/run --exclude=/mnt "
        f"--exclude=/media --exclude=/run/media /"
    )


def _run_tar_pipeline_from_preflight(
    status_file: Path,
    status: dict[str, Any],
    partial_path: str,
    manifest_tmp_path: str,
    archive_path: str,
    manifest_payload: dict[str, Any],
    inner_tar_cmd: str,
) -> int:
    """Gemeinsame Pipeline: Preflight (Paket/Inhibit), inhibit-wrap, Monitor, Manifest, finalize — ohne Data-/Full-Tar zu vermischen."""
    global CHILD_PROC

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
        _update_status(status_file, status, progress_optional={"bytes_current": size, "running_for_s": int(time.monotonic() - start_monotonic)})
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
    if rc == 0:
        completed_at = _now_iso()
        for _ in range(3):
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
            payload_hash = _sha256_archive_payload(partial_path)
            manifest_payload.update(
                {
                    "completed_at": completed_at,
                    "archive_size": str(current_size),
                    "hash": f"sha256:{payload_hash}",
                }
            )
            ok_manifest, manifest_err = _rewrite_manifest_in_archive(partial_path, manifest_payload)
            if not ok_manifest:
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
        ok_rename = False
        rename_error = ""
        try:
            os.replace(partial_path, archive_path)
            ok_rename = True
        except Exception as e:
            rename_error = str(e)
        if ok_rename:
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
                progress_optional={"bytes_current": Path(archive_path).stat().st_size if Path(archive_path).exists() else 0},
                manifest_hash=f"sha256:{_sha256_archive_payload(archive_path)}" if Path(archive_path).exists() else "",
                subprocess_returncode=0,
                tar_stderr_log=str(stderr_log_path) if stderr_log_path else None,
            )
            try:
                Path(manifest_tmp_path).unlink(missing_ok=True)
            except Exception:
                pass
            _mark_terminal()
            return 0
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
        )
        _mark_terminal()
        return 1

    _update_status(
        status_file,
        status,
        status="error",
        code="backup.failed",
        severity="error",
        diagnosis_id=None,
        abort_reason="tar_failed",
        backup_finished_at=_now_iso(),
        stderr_excerpt=stderr_excerpt_tail,
        stderr_tail=tail_text,
        subprocess_returncode=rc,
        tar_stderr_log=str(stderr_log_path) if stderr_log_path else None,
        suspend_guard_active=False,
        partial_deleted=_cleanup_partial(partial_path),
    )
    _mark_terminal()
    return 1


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
    global CHILD_PROC, STATUS_FINAL_WRITTEN
    args = _parse_args()
    STATUS_FINAL_WRITTEN = False
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
        inner_full = _full_inner_tar_command(partial_path, backup_dir)
        return _run_tar_pipeline_from_preflight(
            status_file,
            status_full,
            partial_path,
            manifest_tmp_path,
            archive_path,
            manifest_payload_full,
            inner_full,
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
    )

if __name__ == "__main__":
    raise SystemExit(main())
