"""
PI-Installer Backend - FastAPI mit erweiterten Endpoints
"""

from fastapi import Body, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware
import os
from pathlib import Path
import psutil
import subprocess
import json
import logging
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
import shlex
import re
from typing import Optional
from datetime import datetime, timezone
import asyncio
import uuid
import threading
import time
import signal
import xml.etree.ElementTree as ET

# -------------------- Logging (file + console) --------------------

def _default_log_path() -> Path:
    # Prefer project-local logs (works without sudo)
    repo_root = Path(__file__).resolve().parent.parent
    return repo_root / "logs" / "pi-installer.log"


def _setup_logging() -> Path:
    """
    Writes errors into a persistent log file (rotating by days and size).
    Falls back to console-only if file cannot be created.
    """
    log_path = Path(os.environ.get("PI_INSTALLER_LOG_PATH", "") or _default_log_path()).resolve()
    try:
        log_retention_days = int(os.environ.get("PI_INSTALLER_LOG_RETENTION_DAYS", "30"))
    except Exception:
        log_retention_days = 30
    try:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        fmt = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")

        root = logging.getLogger()
        root.setLevel(logging.INFO)

        # Avoid duplicate handlers on reload
        if not any(isinstance(h, (RotatingFileHandler, TimedRotatingFileHandler)) for h in root.handlers):
            # TimedRotatingFileHandler rotiert nach Tagen (täglich um Mitternacht)
            # backupCount bestimmt, wie viele Tage Logs aufbewahrt werden
            fh = TimedRotatingFileHandler(
                str(log_path),
                when='midnight',
                interval=1,
                backupCount=log_retention_days,
                encoding="utf-8"
            )
            fh.setLevel(logging.INFO)
            fh.setFormatter(fmt)
            root.addHandler(fh)

        # ensure at least one console handler
        if not any(isinstance(h, logging.StreamHandler) for h in root.handlers):
            ch = logging.StreamHandler()
            ch.setLevel(logging.INFO)
            ch.setFormatter(fmt)
            root.addHandler(ch)
    except Exception:
        logging.basicConfig(level=logging.INFO)
    return log_path


LOG_PATH = _setup_logging()
logger = logging.getLogger(__name__)
logger.info("Log-Datei: %s", str(LOG_PATH))

# ==================== Version ====================

def get_pi_installer_version() -> str:
    """Liest die PI-Installer Version aus der Repo-Root `VERSION` Datei."""
    try:
        version_path = Path(__file__).resolve().parent.parent / "VERSION"
        if version_path.exists():
            v = version_path.read_text(encoding="utf-8").strip()
            return v or "0.0.0"
    except Exception:
        pass
    return "0.0.0"

PI_INSTALLER_VERSION = get_pi_installer_version()

# Erstelle FastAPI App
app = FastAPI(
    title="PI-Installer",
    description="Raspberry Pi Konfigurations-Assistent",
    version=PI_INSTALLER_VERSION
)

# Session Storage für sudo-Passwort (in-memory, nur für aktuelle Session)
sudo_password_store = {}

# Globaler Installationsfortschritt
installation_progress = {"progress": 0, "message": "Bereit", "current_step": ""}

# -------------------- Global Config / Initialization --------------------

def _read_text(path: str) -> str:
    try:
        return Path(path).read_text(encoding="utf-8").strip()
    except Exception:
        return ""


def _device_id() -> str:
    # stable id on Linux
    mid = _read_text("/etc/machine-id")
    return mid or "unknown-device"


def _device_model() -> str:
    # Raspberry Pi: /proc/device-tree/model (binary-ish, but usually decodes)
    for p in ("/proc/device-tree/model", "/sys/firmware/devicetree/base/model"):
        try:
            b = Path(p).read_bytes()
            if b:
                return b.decode("utf-8", errors="ignore").strip("\x00").strip()
        except Exception:
            continue
    return ""


def _os_release() -> dict:
    data = {}
    try:
        txt = _read_text("/etc/os-release")
        for line in txt.splitlines():
            if "=" not in line:
                continue
            k, v = line.split("=", 1)
            data[k.strip()] = v.strip().strip('"')
    except Exception:
        pass
    return data


def _config_path() -> Path:
    """
    Prefer /etc/pi-installer/config.json when writable, else fallback to ~/.config/pi-installer/config.json.
    """
    etc = Path("/etc/pi-installer/config.json")
    try:
        etc.parent.mkdir(parents=True, exist_ok=True)
        # check writable (as current process)
        if etc.exists():
            if os.access(str(etc), os.W_OK):
                return etc
        else:
            if os.access(str(etc.parent), os.W_OK):
                return etc
    except Exception:
        pass
    home = Path.home() / ".config" / "pi-installer" / "config.json"
    home.parent.mkdir(parents=True, exist_ok=True)
    return home


def _default_settings() -> dict:
    return {
        "ui": {"language": "de"},
        "backup": {"default_dir": "/mnt/backups"},
        "logging": {"level": "INFO", "retention_days": 30},
        "network": {"remote_access_disabled": False},
    }


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


CONFIG_PATH = _config_path()
CONFIG_STATE = {"loaded": False, "first_run": False, "matched_device": False, "device_id": _device_id()}
APP_SETTINGS = _default_settings()

# -------------------- Backup jobs (async) --------------------

BACKUP_JOBS: dict[str, dict] = {}
BACKUP_JOB_CANCEL: dict[str, threading.Event] = {}


def _new_job_id() -> str:
    return uuid.uuid4().hex[:12]


def _job_snapshot(job: dict) -> dict:
    # non-mutating snapshot with live size
    snap = dict(job)
    bf = snap.get("backup_file")
    try:
        if bf and isinstance(bf, str) and bf.startswith("/") and Path(bf).exists():
            snap["bytes_current"] = int(Path(bf).stat().st_size)
    except Exception:
        pass
    return snap


def _curl_put_with_progress(
    local_file: str,
    remote: str,
    user: str,
    pw: str,
    job_id: str,
    timeout_sec: int,
) -> tuple[bool, Optional[int], Optional[str]]:
    """PUT mit Fortschritts-Updates. Bei Timeout: 1 Min warten, dann PROPFIND; keine Fehlermeldung vorher."""
    cmd = (
        f"curl -o /dev/null -w '%{{http_code}}' "
        f"-u {shlex.quote(user)}:{shlex.quote(pw)} -H 'Overwrite: T' -T {shlex.quote(local_file)} {shlex.quote(remote)}"
    )
    try:
        proc = subprocess.Popen(
            cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    except Exception as e:
        return False, None, str(e)

    def read_stderr():
        buf = ""
        progre = re.compile(r"\s*(\d+)\s+\d+\s+\d+")
        last_pct = -1
        try:
            while True:
                chunk = proc.stderr.read(512)
                if not chunk:
                    break
                buf += chunk
                parts = re.split(r"[\r\n]+", buf)
                buf = parts.pop() if parts else ""
                for part in parts:
                    m = progre.match(part.strip())
                    if m:
                        pct = min(100, int(m.group(1)))
                        if pct != last_pct and job_id and job_id in BACKUP_JOBS:
                            last_pct = pct
                            BACKUP_JOBS[job_id]["upload_progress_pct"] = pct
        except Exception:
            pass

    t = threading.Thread(target=read_stderr, daemon=True)
    t.start()

    try:
        proc.wait(timeout=timeout_sec)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait()
        t.join(timeout=2)
        if job_id and job_id in BACKUP_JOBS:
            BACKUP_JOBS[job_id]["upload_progress_pct"] = None
            BACKUP_JOBS[job_id]["message"] = "Prüfe in 1 Min, ob Datei in Cloud…"
        time.sleep(60)
        rv = run_command(
            f"curl -sS -o /dev/null -w '%{{http_code}}' -u {shlex.quote(user)}:{shlex.quote(pw)} "
            f"-X PROPFIND -H 'Depth: 0' {shlex.quote(remote)}",
            timeout=30,
        )
        try:
            cv = int((rv.get("stdout") or "").strip() or "0")
        except Exception:
            cv = 0
        if rv.get("success") and cv in (200, 201, 204, 207):
            return True, None, None
        return False, None, "Upload-Zeitüberschreitung (Timeout). Datei nach 1 Min nicht in Cloud gefunden."

    t.join(timeout=2)
    out = (proc.stdout.read() or "").strip()
    try:
        put_code = int(out) if out else None
    except Exception:
        put_code = None
    if job_id and job_id in BACKUP_JOBS:
        BACKUP_JOBS[job_id]["upload_progress_pct"] = 100 if proc.returncode == 0 else None
    if proc.returncode != 0:
        return False, put_code, "Upload fehlgeschlagen"
    return True, put_code, None


def _find_last_full_backup(backup_dir: str) -> tuple[Optional[str], Optional[int]]:
    try:
        p = Path(backup_dir)
        files = [f for f in p.glob("pi-backup-full-*.tar.gz") if f.is_file()]
        if not files:
            return None, None
        files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
        f = files[0]
        return str(f), int(f.stat().st_mtime)
    except Exception:
        return None, None


def _do_backup_logic(
    *,
    sudo_password: str,
    backup_type: str,
    backup_dir: str,
    timestamp: str,
    last_backup_hint: str = "",
    cancel_event: Optional[threading.Event] = None,
    job: Optional[dict] = None,
) -> dict:
    """
    Blocking backup implementation (safe to run in a thread).
    Returns a dict shaped like the API response.
    """
    results: list[str] = []

    def _tar_warning_ok(result: dict, backup_file_path: str) -> bool:
        try:
            rc = result.get("returncode")
            if rc != 1:
                return False
            test_cmd = f"test -s {shlex.quote(backup_file_path)}"
            t = run_command(test_cmd)
            if not t["success"] and sudo_password:
                t = run_command(test_cmd, sudo=True, sudo_password=sudo_password)
            return bool(t["success"])
        except Exception:
            return False

    def _tar_partial_ok(result: dict, backup_file_path: str) -> bool:
        try:
            test_cmd = f"test -s {shlex.quote(backup_file_path)}"
            t = run_command(test_cmd)
            if not t["success"] and sudo_password:
                t = run_command(test_cmd, sudo=True, sudo_password=sudo_password)
            return bool(t["success"])
        except Exception:
            return False

    def _tar_no_space(result: dict) -> bool:
        combined = ((result.get("stderr") or "") + "\n" + (result.get("stdout") or "")).lower()
        needles = ["no space left on device", "enospc", "write failed", "broken pipe", "datenübergabe unterbrochen"]
        return any(n in combined for n in needles)

    def _fs_free_hint(dir_path: str) -> str:
        try:
            st = os.statvfs(dir_path)
            free = st.f_frsize * st.f_bavail
            for unit in ["B", "KB", "MB", "GB", "TB"]:
                if free < 1024:
                    return f"{free:.0f} {unit}" if unit == "B" else f"{free:.1f} {unit}"
                free /= 1024
        except Exception:
            pass
        return ""

    def _make_backup_readable(path: str) -> None:
        try:
            uid = os.getuid()
            gid = os.getgid()
            run_command(f"chmod 0755 {shlex.quote(backup_dir)}", sudo=True, sudo_password=sudo_password)
            run_command(f"chmod 0644 {shlex.quote(path)}", sudo=True, sudo_password=sudo_password)
            run_command(f"chown {uid}:{gid} {shlex.quote(path)}", sudo=True, sudo_password=sudo_password)
        except Exception:
            pass

    def _cleanup_backup_file(path: Optional[str]) -> None:
        try:
            if not path:
                return
            # best-effort cleanup (file likely created as root)
            run_command(f"rm -f {shlex.quote(path)}", sudo=True, sudo_password=sudo_password)
        except Exception:
            pass

    warning = None
    backup_file = None
    last_full = None

    if cancel_event and cancel_event.is_set():
        return {"status": "cancelled", "message": "Backup abgebrochen", "results": ["⚠️ Abbruch angefordert"], "backup_file": None, "timestamp": timestamp}

    def _run_tar(cmd: str) -> dict:
        if not cancel_event:
            return run_command(cmd, sudo=True, sudo_password=sudo_password, timeout=7200)
        # cancelable tar
        try:
            # start in separate process group so we can kill everything (tar+gzip)
            proc = subprocess.Popen(
                ["sudo", "-S", "sh", "-c", cmd],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                preexec_fn=os.setsid,
            )
            try:
                if proc.stdin:
                    proc.stdin.write((sudo_password or "") + "\n")
                    proc.stdin.flush()
                    proc.stdin.close()
            except Exception:
                pass

            # expose pgid for cancel endpoint
            try:
                pgid = os.getpgid(proc.pid)
                if job is not None:
                    job["pgid"] = int(pgid)
            except Exception:
                pass

            start = time.monotonic()
            while True:
                if cancel_event.is_set():
                    try:
                        os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
                    except Exception:
                        try:
                            proc.terminate()
                        except Exception:
                            pass
                    try:
                        proc.wait(timeout=5)
                    except Exception:
                        try:
                            os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
                        except Exception:
                            pass
                    return {"success": False, "returncode": -15, "stderr": "Cancelled", "stdout": ""}
                if proc.poll() is not None:
                    break
                if time.monotonic() - start > 7200:
                    try:
                        os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
                    except Exception:
                        pass
                    return {"success": False, "returncode": -9, "stderr": "Timeout", "stdout": ""}
                time.sleep(0.5)

            out, err = proc.communicate(timeout=1)
            return {"success": proc.returncode == 0, "returncode": proc.returncode, "stdout": out or "", "stderr": err or ""}
        except Exception as e:
            return {"success": False, "error": str(e)}

    if backup_type == "full":
        backup_file = f"{backup_dir}/pi-backup-full-{timestamp}.tar.gz"
        backup_cmd = (
            f"tar -czf {shlex.quote(backup_file)} "
            f"--exclude={shlex.quote(backup_dir)} "
            f"--exclude=/proc --exclude=/sys --exclude=/dev --exclude=/tmp --exclude=/run --exclude=/mnt /"
        )
        backup_result = _run_tar(backup_cmd)
        if (cancel_event and cancel_event.is_set()) or backup_result.get("returncode") == -15:
            _cleanup_backup_file(backup_file)
            return {"status": "cancelled", "message": "Backup abgebrochen", "results": ["⚠️ Abbruch angefordert"], "backup_file": None, "timestamp": timestamp}
        if backup_result.get("success"):
            results.append(f"Vollständiges Backup erstellt: {backup_file}")
            _make_backup_readable(backup_file)
            return {"status": "success", "message": "Backup erstellt", "results": results, "backup_file": backup_file, "timestamp": timestamp}
        if _tar_no_space(backup_result):
            free_hint = _fs_free_hint(backup_dir)
            msg = "Nicht genug Speicherplatz im Zielverzeichnis."
            if free_hint:
                msg += f" Freier Speicher: {free_hint}."
            results.append(f"❌ {msg}")
            if backup_result.get("stderr"):
                results.append(f"tar/stderr: {(backup_result.get('stderr') or '')[:200]}")
            _cleanup_backup_file(backup_file)
            return {"status": "error", "message": "Backup fehlgeschlagen", "results": results, "backup_file": backup_file, "timestamp": timestamp}
        if _tar_warning_ok(backup_result, backup_file):
            warning = "Backup erstellt, aber tar meldete Warnungen."
            results.append(f"⚠️ Backup erstellt mit Warnungen: {backup_file}")
            _make_backup_readable(backup_file)
            out = {"status": "success", "message": "Backup erstellt", "results": results, "backup_file": backup_file, "timestamp": timestamp}
            out["warning"] = warning
            return out
        if _tar_partial_ok(backup_result, backup_file):
            warning = f"Backup wurde erstellt, aber tar lieferte Returncode {backup_result.get('returncode')}."
            results.append(f"⚠️ Backup erstellt (möglicherweise unvollständig): {backup_file}")
            _make_backup_readable(backup_file)
            out = {"status": "success", "message": "Backup erstellt", "results": results, "backup_file": backup_file, "timestamp": timestamp}
            out["warning"] = warning
            return out
        stderr = (backup_result.get("stderr") or backup_result.get("stdout") or backup_result.get("error") or "Unbekannter Fehler")
        results.append(f"Backup fehlgeschlagen: {str(stderr)[:200]}")
        _cleanup_backup_file(backup_file)
        return {"status": "error", "message": "Backup fehlgeschlagen", "results": results, "backup_file": backup_file, "timestamp": timestamp}

    if backup_type == "incremental":
        backup_file = f"{backup_dir}/pi-backup-inc-{timestamp}.tar.gz"
        last_backup = (last_backup_hint or "").strip()
        if not last_backup:
            last_full, last_full_mtime = _find_last_full_backup(backup_dir)
            if last_full and last_full_mtime:
                last_backup = f"@{int(last_full_mtime)}"
                results.append(f"Basis (letztes Full Backup): {Path(last_full).name}")
            else:
                results.append("Kein vorheriges Full Backup gefunden, erstelle vollständiges Backup")
                return _do_backup_logic(
                    sudo_password=sudo_password,
                    backup_type="full",
                    backup_dir=backup_dir,
                    timestamp=timestamp,
                    cancel_event=cancel_event,
                    job=job,
                )

        backup_cmd = (
            f"tar -czf {shlex.quote(backup_file)} "
            f"--newer-mtime={shlex.quote(str(last_backup))} "
            f"--exclude={shlex.quote(backup_dir)} "
            f"/home /etc /var/www"
        )
        backup_result = _run_tar(backup_cmd)
        if (cancel_event and cancel_event.is_set()) or backup_result.get("returncode") == -15:
            _cleanup_backup_file(backup_file)
            return {"status": "cancelled", "message": "Backup abgebrochen", "results": ["⚠️ Abbruch angefordert"], "backup_file": None, "timestamp": timestamp}
        if backup_result.get("success"):
            results.append(f"Inkrementelles Backup erstellt: {backup_file}")
            _make_backup_readable(backup_file)
            out = {"status": "success", "message": "Backup erstellt", "results": results, "backup_file": backup_file, "timestamp": timestamp}
            if last_full:
                out["last_full_backup"] = last_full
            return out
        if _tar_no_space(backup_result):
            free_hint = _fs_free_hint(backup_dir)
            msg = "Nicht genug Speicherplatz im Zielverzeichnis."
            if free_hint:
                msg += f" Freier Speicher: {free_hint}."
            results.append(f"❌ {msg}")
            _cleanup_backup_file(backup_file)
            return {"status": "error", "message": "Backup fehlgeschlagen", "results": results, "backup_file": backup_file, "timestamp": timestamp}
        if _tar_warning_ok(backup_result, backup_file) or _tar_partial_ok(backup_result, backup_file):
            warning = "Backup erstellt, aber tar meldete Warnungen."
            results.append(f"⚠️ Inkrementelles Backup erstellt mit Warnungen: {backup_file}")
            _make_backup_readable(backup_file)
            out = {"status": "success", "message": "Backup erstellt", "results": results, "backup_file": backup_file, "timestamp": timestamp}
            out["warning"] = warning
            if last_full:
                out["last_full_backup"] = last_full
            return out
        stderr = (backup_result.get("stderr") or backup_result.get("stdout") or backup_result.get("error") or "Unbekannter Fehler")
        results.append(f"Backup fehlgeschlagen: {str(stderr)[:200]}")
        _cleanup_backup_file(backup_file)
        return {"status": "error", "message": "Backup fehlgeschlagen", "results": results, "backup_file": backup_file, "timestamp": timestamp}

    if backup_type == "data":
        backup_file = f"{backup_dir}/pi-backup-data-{timestamp}.tar.gz"
        backup_cmd = f"tar -czf {shlex.quote(backup_file)} /home /var/www /opt"
        backup_result = _run_tar(backup_cmd)
        if (cancel_event and cancel_event.is_set()) or backup_result.get("returncode") == -15:
            _cleanup_backup_file(backup_file)
            return {"status": "cancelled", "message": "Backup abgebrochen", "results": ["⚠️ Abbruch angefordert"], "backup_file": None, "timestamp": timestamp}
        if backup_result.get("success"):
            results.append(f"Daten-Backup erstellt: {backup_file}")
            _make_backup_readable(backup_file)
            return {"status": "success", "message": "Backup erstellt", "results": results, "backup_file": backup_file, "timestamp": timestamp}
        if _tar_no_space(backup_result):
            free_hint = _fs_free_hint(backup_dir)
            msg = "Nicht genug Speicherplatz im Zielverzeichnis."
            if free_hint:
                msg += f" Freier Speicher: {free_hint}."
            results.append(f"❌ {msg}")
            _cleanup_backup_file(backup_file)
            return {"status": "error", "message": "Backup fehlgeschlagen", "results": results, "backup_file": backup_file, "timestamp": timestamp}
        if _tar_warning_ok(backup_result, backup_file) or _tar_partial_ok(backup_result, backup_file):
            warning = "Backup erstellt, aber tar meldete Warnungen."
            results.append(f"⚠️ Daten-Backup erstellt mit Warnungen: {backup_file}")
            _make_backup_readable(backup_file)
            out = {"status": "success", "message": "Backup erstellt", "results": results, "backup_file": backup_file, "timestamp": timestamp}
            out["warning"] = warning
            return out
        stderr = (backup_result.get("stderr") or backup_result.get("stdout") or backup_result.get("error") or "Unbekannter Fehler")
        results.append(f"Backup fehlgeschlagen: {str(stderr)[:200]}")
        _cleanup_backup_file(backup_file)
        return {"status": "error", "message": "Backup fehlgeschlagen", "results": results, "backup_file": backup_file, "timestamp": timestamp}

    return {"status": "error", "message": f"Unbekannter Backup-Typ: {backup_type}", "results": results, "backup_file": None, "timestamp": timestamp}


@app.get("/api/backup/jobs")
async def backup_jobs_list():
    """Liste aller Backup-Jobs, insbesondere laufende"""
    running = []
    for job_id, job in BACKUP_JOBS.items():
        status = job.get("status", "")
        if status in ("queued", "running", "cancel_requested") or not status:
            running.append(_job_snapshot(job))
    return {"status": "success", "jobs": running}


@app.get("/api/backup/jobs/{job_id}")
async def backup_job_status(job_id: str):
    job_id = (job_id or "").strip()
    job = BACKUP_JOBS.get(job_id)
    if not job:
        return JSONResponse(status_code=200, content={"status": "error", "message": "Job nicht gefunden"})
    return {"status": "success", "job": _job_snapshot(job)}


@app.post("/api/backup/jobs/{job_id}/cancel")
async def backup_job_cancel(job_id: str):
    job_id = (job_id or "").strip()
    job = BACKUP_JOBS.get(job_id)
    if not job:
        return JSONResponse(status_code=200, content={"status": "error", "message": "Job nicht gefunden"})

    if job.get("status") in ("success", "error", "cancelled"):
        return {"status": "success", "message": "Job ist bereits abgeschlossen"}

    ev = BACKUP_JOB_CANCEL.get(job_id)
    if not ev:
        ev = threading.Event()
        BACKUP_JOB_CANCEL[job_id] = ev
    ev.set()
    job["status"] = "cancel_requested"
    job["message"] = "Abbruch angefordert…"

    # best-effort kill running process group if available
    try:
        pgid = job.get("pgid")
        if isinstance(pgid, int) and pgid > 1:
            os.killpg(pgid, signal.SIGTERM)
    except Exception:
        pass

    return {"status": "success", "message": "Abbruch angefordert"}


def _load_or_init_config() -> dict:
    global APP_SETTINGS

    did = _device_id()
    model = _device_model()
    osr = _os_release()
    hostname = _read_text("/etc/hostname") or run_command("hostname").get("stdout", "").strip()
    kernel = run_command("uname -r").get("stdout", "").strip()

    base = {
        "device_id": did,
        "created_at": _now_iso(),
        "last_seen_at": _now_iso(),
        "system": {
            "hostname": hostname,
            "model": model,
            "os_release": osr,
            "kernel": kernel,
        },
        "settings": _default_settings(),
    }

    cfg = None
    if CONFIG_PATH.exists():
        try:
            cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8") or "{}")
        except Exception as e:
            logger.error(f"Config parse failed: {e}")
            cfg = None

    if cfg and isinstance(cfg, dict) and cfg.get("device_id") == did:
        # same device -> reuse settings
        cfg["last_seen_at"] = _now_iso()
        cfg["system"] = base["system"]
        settings = cfg.get("settings") if isinstance(cfg.get("settings"), dict) else {}
        merged = _default_settings()
        # shallow merge + nested
        merged["ui"].update((settings.get("ui") or {}) if isinstance(settings.get("ui"), dict) else {})
        merged["backup"].update((settings.get("backup") or {}) if isinstance(settings.get("backup"), dict) else {})
        merged["logging"].update((settings.get("logging") or {}) if isinstance(settings.get("logging"), dict) else {})
        merged["network"].update((settings.get("network") or {}) if isinstance(settings.get("network"), dict) else {})
        cfg["settings"] = merged
        APP_SETTINGS = merged
        CONFIG_STATE.update({"loaded": True, "first_run": False, "matched_device": True, "device_id": did})
    else:
        # new system or mismatch -> initialize new config (keep old as backup)
        if cfg and isinstance(cfg, dict):
            try:
                bak = CONFIG_PATH.with_suffix(f".bak.{cfg.get('device_id','unknown')}.{int(datetime.now().timestamp())}.json")
                bak.write_text(json.dumps(cfg, indent=2), encoding="utf-8")
            except Exception:
                pass
        cfg = base
        APP_SETTINGS = cfg["settings"]
        CONFIG_STATE.update({"loaded": True, "first_run": True, "matched_device": False, "device_id": did})

    # try to persist (best-effort; no sudo needed if path writable)
    try:
        CONFIG_PATH.write_text(json.dumps(cfg, indent=2), encoding="utf-8")
    except Exception as e:
        logger.error(f"Config write failed: {e}")

    return cfg


@app.on_event("startup")
async def _startup_init():
    try:
        _load_or_init_config()
        logger.info(f"Config ready: path={CONFIG_PATH} device_id={CONFIG_STATE.get('device_id')} first_run={CONFIG_STATE.get('first_run')}")
    except Exception as e:
        logger.error(f"Startup init failed: {e}", exc_info=True)


@app.get("/api/init/status")
async def init_status():
    return {
        "status": "success",
        "config_path": str(CONFIG_PATH),
        "device_id": CONFIG_STATE.get("device_id"),
        "first_run": bool(CONFIG_STATE.get("first_run")),
        "matched_device": bool(CONFIG_STATE.get("matched_device")),
    }


@app.get("/api/settings")
async def get_settings():
    return {"status": "success", "settings": APP_SETTINGS, "config_path": str(CONFIG_PATH), "device_id": CONFIG_STATE.get("device_id")}


@app.post("/api/settings")
async def set_settings(request: Request):
    try:
        data = await request.json()
    except Exception:
        data = {}
    new_settings = data.get("settings") if isinstance(data.get("settings"), dict) else {}

    # merge
    merged = _default_settings()
    if isinstance(new_settings.get("ui"), dict):
        merged["ui"].update(new_settings["ui"])
    if isinstance(new_settings.get("backup"), dict):
        merged["backup"].update(new_settings["backup"])
    if isinstance(new_settings.get("logging"), dict):
        merged["logging"].update(new_settings["logging"])
    if isinstance(new_settings.get("network"), dict):
        merged["network"].update(new_settings["network"])

    # validate backup dir if provided
    try:
        if "default_dir" in merged["backup"]:
            merged["backup"]["default_dir"] = _validate_backup_dir(str(merged["backup"]["default_dir"]))
    except Exception as ve:
        return JSONResponse(status_code=200, content={"status": "error", "message": f"Ungültiger Backup-Pfad: {str(ve)}"})

    # apply logging level (runtime)
    try:
        lvl = str(merged["logging"].get("level", "INFO")).upper()
        if lvl in ("DEBUG", "INFO", "WARNING", "ERROR"):
            logging.getLogger().setLevel(getattr(logging, lvl))
    except Exception:
        pass

    # persist into config
    try:
        cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8") or "{}") if CONFIG_PATH.exists() else {}
    except Exception:
        cfg = {}
    if not isinstance(cfg, dict):
        cfg = {}
    cfg["device_id"] = _device_id()
    cfg["last_seen_at"] = _now_iso()
    cfg["settings"] = merged
    try:
        CONFIG_PATH.write_text(json.dumps(cfg, indent=2), encoding="utf-8")
    except Exception as e:
        logger.error(f"Settings write failed: {e}")
        return JSONResponse(status_code=200, content={"status": "error", "message": f"Konnte Settings nicht speichern: {str(e)}"})

    APP_SETTINGS = merged
    return {"status": "success", "message": "Einstellungen gespeichert", "settings": merged}


@app.get("/api/logs/path")
async def logs_path():
    """Log-Dateipfad (z.B. für tail -f)."""
    return {"status": "success", "path": str(LOG_PATH), "exists": LOG_PATH.exists()}


@app.get("/api/logs/tail")
async def logs_tail(lines: int = 200):
    try:
        lines = max(10, min(int(lines), 2000))
    except Exception:
        lines = 200
    p = Path(LOG_PATH)
    if not p.exists():
        return JSONResponse(status_code=200, content={"status": "error", "message": "Log-Datei nicht gefunden. Backend neu starten (Logging ging zuvor nur auf Konsole).", "path": str(p)})
    try:
        # naive tail (file is small due to rotation)
        txt = p.read_text(encoding="utf-8", errors="ignore")
        out = "\n".join(txt.splitlines()[-lines:])
        return {"status": "success", "path": str(p), "lines": lines, "content": out}
    except Exception as e:
        return JSONResponse(status_code=200, content={"status": "error", "message": str(e), "path": str(p)})

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def _is_demo_mode(request: Request) -> bool:
    """Prüft ob X-Demo-Mode Header gesetzt ist (für Screenshot-Dokumentation ohne echte Daten)."""
    return request.headers.get("X-Demo-Mode") == "1"


def _demo_network():
    """Platzhalter-Netzwerkdaten für Demo/Screenshot-Modus."""
    return {"ips": ["192.168.1.100"], "hostname": "raspberrypi"}


def _demo_users():
    """Platzhalter-Benutzer für Demo/Screenshot-Modus."""
    return {
        "system_users": [{"name": "root", "uid": 0}, {"name": "pi", "uid": 1000}],
        "human_users": [{"name": "admin", "uid": 1001}],
    }


@app.get("/api/system/paths")
async def get_system_paths():
    """Prüft kritische Pfade (NVMe-Boot, Konfiguration). Hilft bei Pfad-Problemen nach Laufwerkswechsel."""
    paths = {
        "config_etc": "/etc/pi-installer/config.json",
        "config_etc_exists": Path("/etc/pi-installer/config.json").exists(),
        "config_home": str(Path.home() / ".config" / "pi-installer" / "config.json"),
        "backup_json": "/etc/pi-installer/backup.json",
        "boot_firmware": "/boot/firmware",
        "boot_firmware_config": "/boot/firmware/config.txt",
        "boot_firmware_cmdline": "/boot/firmware/cmdline.txt",
        "boot_firmware_exists": Path("/boot/firmware").exists(),
        "mnt_backups": "/mnt/backups",
        "mnt_backups_exists": Path("/mnt/backups").exists(),
        "root_mount": _root_mount_device(),
    }
    return {"status": "success", "paths": paths}


def _root_mount_device() -> Optional[str]:
    """Ermittelt das Device für die Root-Partition (z.B. /dev/nvme0n1p1 oder /dev/mmcblk0p2)."""
    for fs in _findmnt_mounts():
        tgt = (fs.get("target") or "").strip()
        src = (fs.get("source") or "").strip()
        if tgt == "/" and src.startswith("/dev/"):
            return src
    return None


def _detect_freenove_case() -> dict:
    """Erkennt Freenove Computer Case Kit Pro (DSI-Display, I2C-Expansion-Board, Audio).
    Expansion-Board: I2C Adresse 0x21 (REG_BRAND 0xfd). DSI: /sys/class/drm oder wlr-randr."""
    result = {
        "detected": False,
        "expansion_board": False,
        "dsi_display": False,
        "audio_available": False,
        "hint": "",
    }
    try:
        # 1. I2C Expansion-Board (Freenove 0x21) – Pi 5: Bus 0,1,6,7 typisch
        for bus in (1, 0, 6, 7, 2, 3, 4, 5):
            r = run_command(f"i2cget -y {bus} 0x21 0xfd 2>/dev/null", timeout=2)
            if r.get("success") and r.get("stdout", "").strip():
                result["expansion_board"] = True
                break
        if not result["expansion_board"]:
            # Sysfs-Fallback: /sys/bus/i2c/devices/*/name oder Adresse 0x21
            try:
                for dev in Path("/sys/bus/i2c/devices").iterdir():
                    if dev.name.endswith("-0021"):
                        result["expansion_board"] = True
                        break
            except Exception:
                pass
        # 2. DSI-Display (4,3" TFT) – zuerst sysfs (funktioniert ohne Wayland)
        try:
            for p in Path("/sys/class/drm").iterdir():
                if "DSI" in p.name:
                    status_file = p / "status"
                    if status_file.exists():
                        try:
                            if status_file.read_text().strip() == "connected":
                                result["dsi_display"] = True
                                break
                        except Exception:
                            pass
        except Exception:
            pass
        if not result["dsi_display"]:
            r = run_command("wlr-randr 2>/dev/null | grep -i dsi || true", timeout=2)
            if r.get("success") and r.get("stdout", "").strip():
                result["dsi_display"] = True
        # 3. Audio (Lautsprecher)
        r = run_command("cat /proc/asound/cards 2>/dev/null | grep -E '^[[:space:]]*[0-9]' || true", timeout=2)
        result["audio_available"] = bool(r.get("success") and r.get("stdout", "").strip())
        # Freenove erkannt wenn DSI ODER Expansion-Board
        result["detected"] = result["dsi_display"] or result["expansion_board"]
        if result["detected"]:
            result["hint"] = "TFT-Modi im App Store nutzbar. Lautsprecher: System-Sound → Ausgabegerät wählen."
    except Exception as e:
        result["hint"] = str(e)
    return result


# ---------- Radio (Internetradio, Stream-Metadaten, Logo-Proxy) ----------
def _parse_icy_metadata_from_stream(url: str) -> dict:
    """Liest ersten ICY-Metadaten-Block aus dem Stream (StreamTitle). Fallback wenn status-json fehlt."""
    try:
        import urllib.request
        req = urllib.request.Request(url, headers={"User-Agent": "PI-Installer/1.0", "Icy-MetaData": "1"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            meta_int = resp.headers.get("icy-metaint")
            if not meta_int:
                return {}
            meta_int = int(meta_int)
            # Ersten Audio-Block lesen
            resp.read(meta_int)
            # Länge des Metadaten-Blocks (1 Byte)
            raw = resp.read(1)
            if not raw:
                return {}
            block_len = ord(raw) * 16
            if block_len <= 0:
                return {}
            meta_raw = resp.read(block_len).decode("utf-8", errors="ignore").strip("\x00")
            # StreamTitle='...';
            for part in meta_raw.split(";"):
                part = part.strip()
                if part.lower().startswith("streamtitle="):
                    val = part.split("=", 1)[1].strip("'\"")
                    if val:
                        artist, song = "", val
                        if " - " in val:
                            parts = val.split(" - ", 1)
                            artist, song = parts[0].strip(), parts[1].strip() if len(parts) > 1 else val
                        return {"title": val, "artist": artist, "song": song}
        return {}
    except Exception as e:
        logger.debug(f"ICY metadata: {e}")
        return {}


def _fetch_icecast_metadata(url: str) -> dict:
    """Holt Metadaten aus Icecast status-json.xsl; Fallback: ICY-Metadaten aus Stream."""
    result = {}
    try:
        import urllib.parse
        import urllib.request
        base = url.rstrip("/").rsplit("/", 1)[0] + "/"
        # Manche Server: status-json.xsl, andere: status-json oder an anderem Pfad
        for path in ("status-json.xsl", "status-json", "status.json"):
            meta_url = urllib.parse.urljoin(base, path)
            try:
                req = urllib.request.Request(meta_url, headers={"User-Agent": "PI-Installer/1.0 (Radio metadata)"})
                with urllib.request.urlopen(req, timeout=6) as resp:
                    data = json.loads(resp.read().decode())
                sources = data.get("icestats", {}).get("source") or []
                if isinstance(sources, dict):
                    sources = [sources]
                for s in sources:
                    title = s.get("title") or s.get("yp_currently_playing")
                    if title:
                        title = str(title).strip()
                        artist, song = "", title
                        if " - " in title:
                            parts = title.split(" - ", 1)
                            artist, song = parts[0].strip(), parts[1].strip() if len(parts) > 1 else ""
                        bitrate = s.get("bitrate") or s.get("audio_bitrate")
                        server = s.get("server_name") or s.get("server_description") or ""
                        result = {
                            "title": title,
                            "artist": artist,
                            "song": song,
                            "bitrate": bitrate,
                            "server_name": server,
                            "show": server,
                        }
                        break
                if result:
                    break
            except Exception:
                continue
    except Exception as e:
        logger.debug("Radio metadata Icecast: %s", e)
    if not result.get("title"):
        icy = _parse_icy_metadata_from_stream(url)
        if icy:
            result.update(icy)
    if not result.get("title"):
        result["title"] = "Live"
        result.setdefault("show", "")
    return result


@app.get("/api/radio/stream-metadata")
async def get_radio_stream_metadata(url: str):
    """Holt Metadaten aus Icecast status-json.xsl: title, Interpret, Qualität, Sendung."""
    try:
        data = await asyncio.to_thread(_fetch_icecast_metadata, url)
        return {"status": "success", **data}
    except Exception as e:
        logger.warning("Radio stream-metadata failed for %s: %s", url[:80], e)
        return {"status": "success", "title": "Live", "show": "", "artist": "", "song": ""}


def _fetch_logo(url: str) -> tuple[bytes, str] | None:
    """Lädt Logo von URL (CORS-Proxy). Sync für to_thread. Folgt Redirects."""
    try:
        import urllib.request
        import urllib.error
        # Wikimedia/Wikipedia verlangen beschreibenden User-Agent (kein generischer Browser-String)
        # vgl. https://meta.wikimedia.org/wiki/User-Agent_policy
        if "wikipedia.org" in url or "wikimedia.org" in url:
            ua = "PI-Installer/1.0 (Radio logo proxy; +https://github.com)"
        else:
            ua = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        headers = {
            "User-Agent": ua,
            "Accept": "image/webp,image/apng,image/*,*/*;q=0.8",
        }
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=12) as resp:
            body = resp.read()
            ct = (resp.headers.get("Content-Type") or "image/png").split(";")[0].strip().lower()
            if not ct or ct == "application/octet-stream":
                if url.rstrip("/").endswith(".ico"):
                    ct = "image/x-icon"
                elif "svg" in url.lower():
                    ct = "image/svg+xml"
                else:
                    ct = "image/png"
            return (body, ct)
    except urllib.error.HTTPError as e:
        logger.debug("Radio logo HTTP %s: %s %s", e.code, url[:80], e.reason)
        return None
    except Exception as e:
        logger.debug("Radio logo %s: %s", url[:80], e)
        return None


@app.get("/api/radio/logo")
async def get_radio_logo(url: str):
    """Proxy für Sender-Logos (umgeht CORS)."""
    from fastapi.responses import Response
    result = await asyncio.to_thread(_fetch_logo, url)
    if result:
        body, ct = result
        return Response(content=body, media_type=ct)
    return Response(status_code=404)


@app.get("/api/radio/stream")
async def get_radio_stream(url: str):
    """Proxy für Radio-Stream (Same-Origin → bessere Autoplay-Unterstützung)."""
    from fastapi.responses import StreamingResponse
    import urllib.request

    def gen():
        req = urllib.request.Request(url, headers={"User-Agent": "PI-Installer/1.0", "Icy-MetaData": "1"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            while True:
                chunk = resp.read(65536)
                if not chunk:
                    break
                yield chunk

    return StreamingResponse(gen(), media_type="audio/mpeg")


RADIO_BROWSER_API = "https://de1.api.radio-browser.info"


@app.get("/api/radio/stations/search")
async def get_radio_stations_search(
    country: str = "Germany",
    name: Optional[str] = None,
    limit: int = 200,
):
    """Sucht Sender über Radio-Browser-API (Deutschland, optional name). Nur MP3, lastcheckok=1."""
    try:
        import urllib.parse
        params = ["country=" + urllib.parse.quote(country)]
        if name and name.strip():
            params.append("name=" + urllib.parse.quote(name.strip()))
        params.append("limit=" + str(min(limit, 500)))
        url = f"{RADIO_BROWSER_API}/json/stations/search?{'&'.join(params)}"
        req = urllib.request.Request(url, headers={"User-Agent": "PI-Installer/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
        # Nur MP3 und als erreichbar markiert
        out = []
        for s in data:
            if s.get("codec") != "MP3" or not s.get("lastcheckok"):
                continue
            url_resolved = (s.get("url_resolved") or s.get("url") or "").strip()
            if not url_resolved or url_resolved.startswith("m3u"):
                continue
            out.append({
                "name": (s.get("name") or "").strip(),
                "url": url_resolved,
                "favicon": (s.get("favicon") or "").strip() or None,
                "homepage": (s.get("homepage") or "").strip() or None,
                "country": s.get("country") or "",
                "state": s.get("state") or "",
                "tags": s.get("tags") or "",
                "bitrate": s.get("bitrate"),
            })
        if out:
            return {"status": "success", "stations": out[:limit]}
        # Fallback: Senderliste nie leer (z. B. API liefert leer)
        fallback = [
            {"name": "1Live", "url": "https://wdr-1live-live.icecastssl.wdr.de/wdr/1live/live/mp3/128/stream.mp3", "favicon": "https://www1.wdr.de/radio/1live/resources/img/favicon/apple-touch-icon.png", "state": "NRW", "tags": "Pop"},
            {"name": "WDR 2", "url": "https://wdr-wdr2-rheinruhr.icecastssl.wdr.de/wdr/wdr2/rheinruhr/mp3/128/stream.mp3", "favicon": None, "state": "NRW", "tags": "Pop"},
            {"name": "NDR 2", "url": "https://icecast.ndr.de/ndr/ndr2/niedersachsen/mp3/128/stream.mp3", "favicon": "https://www.ndr.de/apple-touch-icon-120x120.png", "state": "Nord", "tags": "Pop"},
            {"name": "Deutschlandfunk", "url": "https://st01.sslstream.dlf.de/dlf/01/128/mp3/stream.mp3", "favicon": None, "state": "Bundesweit", "tags": "Info"},
        ]
        return {"status": "success", "stations": fallback[:limit]}
    except Exception as e:
        logger.exception("Radio-Browser-API: %s", e)
        fallback = [
            {"name": "1Live", "url": "https://wdr-1live-live.icecastssl.wdr.de/wdr/1live/live/mp3/128/stream.mp3", "favicon": None, "state": "NRW", "tags": "Pop"},
            {"name": "WDR 2", "url": "https://wdr-wdr2-rheinruhr.icecastssl.wdr.de/wdr/wdr2/rheinruhr/mp3/128/stream.mp3", "favicon": None, "state": "NRW", "tags": "Pop"},
        ]
        return {"status": "success", "stations": fallback}


def _dsi_radio_theme_path() -> str:
    import os
    config_dir = os.path.join(os.path.expanduser("~"), ".config", "pi-installer-dsi-radio")
    return os.path.join(config_dir, "theme.txt")


@app.get("/api/radio/dsi-theme")
async def get_radio_dsi_theme():
    """Design der DSI-Radio-App (Klavierlack, Classic, Hell). Wird von PI-Installer gelesen/gesetzt."""
    try:
        path = _dsi_radio_theme_path()
        if os.path.isfile(path):
            with open(path, "r", encoding="utf-8") as f:
                name = (f.read() or "").strip()
                if name in ("Klavierlack", "Classic", "Hell"):
                    return {"status": "success", "theme": name}
    except Exception as e:
        logger.debug("DSI theme read: %s", e)
    return {"status": "success", "theme": "Klavierlack"}


@app.post("/api/radio/dsi-theme")
async def set_radio_dsi_theme(theme: str = Body(..., embed=True)):
    """Design der DSI-Radio-App setzen (Klavierlack, Classic, Hell)."""
    try:
        if theme not in ("Klavierlack", "Classic", "Hell"):
            theme = "Klavierlack"
        path = _dsi_radio_theme_path()
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(theme)
        return {"status": "success", "theme": theme}
    except Exception as e:
        logger.exception("DSI theme write: %s", e)
        return {"status": "error", "message": str(e)}


@app.get("/api/system/freenove-detection")
async def get_freenove_detection():
    """Erkennt Freenove Computer Case Kit Pro – für TFT-Bereich im App Store."""
    data = _detect_freenove_case()
    return {"status": "success", **data}


def _detect_frontend_port():
    """Erkennt Frontend-Port: 5173 (Tauri/Vite-Dev) bevorzugt, sonst 3001/3002."""
    try:
        r = run_command("ss -tuln 2>/dev/null | grep -E ':5173|:3001|:3002'")
        if r.get("success") and r.get("stdout"):
            out = r["stdout"]
            if ":5173" in out:
                return 5173
            if ":3001" in out:
                return 3001
            if ":3002" in out:
                return 3002
    except Exception:
        pass
    return 3001


@app.get("/api/system/network")
async def get_system_network(request: Request):
    """Netzwerk-Informationen (IP-Adressen, Hostname) für Frontend-Zugriff."""
    try:
        if _is_demo_mode(request):
            d = _demo_network()
            return {"status": "success", "ips": d["ips"], "hostname": d["hostname"], "frontend_port": 3001, "backend_port": 8000}
        net_info = get_network_info()
        frontend_port = _detect_frontend_port()
        return {
            "status": "success",
            "ips": net_info.get("ips", []),
            "hostname": net_info.get("hostname", "unknown"),
            "frontend_port": frontend_port,
            "backend_port": 8000,
        }
    except Exception as e:
        logger.error(f"Fehler beim Abrufen der Netzwerk-Info: {str(e)}", exc_info=True)
        return JSONResponse(status_code=200, content={"status": "error", "message": str(e)})


@app.get("/api/version")
async def get_version():
    """Gibt die PI-Installer Versionsnummer zurück."""
    # nicht cachen, damit VERSION-Änderungen ohne Restart sichtbar werden
    return {"status": "success", "version": get_pi_installer_version()}


# ---------- App Store (Transformationsplan: Katalog mit 7 Apps) ----------
APPS_CATALOG = [
    {"id": "home-assistant", "name": "Home Assistant", "description": "Smart Home zentral steuern – Geräte, Automatisierungen, Dashboards.", "category": "Smart Home", "size": "~500 MB"},
    {"id": "nextcloud", "name": "Nextcloud", "description": "Eigene Cloud für Dateien, Kalender, Kontakte und mehr.", "category": "Cloud", "size": "~400 MB"},
    {"id": "pi-hole", "name": "Pi-hole", "description": "Werbung und Tracker im gesamten Netzwerk blockieren.", "category": "Tools", "size": "~200 MB"},
    {"id": "jellyfin", "name": "Jellyfin", "description": "Medien-Server für Filme, Serien und Musik – streamen auf alle Geräte.", "category": "Media", "size": "~300 MB"},
    {"id": "wordpress", "name": "WordPress", "description": "Website oder Blog erstellen – CMS mit Themes und Plugins.", "category": "Tools", "size": "~200 MB, benötigt MySQL/MariaDB"},
    {"id": "code-server", "name": "VS Code Server", "description": "VS Code im Browser – Code bearbeiten von überall.", "category": "Entwicklung", "size": "~400 MB"},
    {"id": "node-red", "name": "Node-RED", "description": "Automatisierungen und Flows visuell programmieren.", "category": "Entwicklung", "size": "~150 MB"},
]


@app.get("/api/apps")
async def get_apps():
    """Liste der verfügbaren Apps (App Store Katalog)."""
    return {"apps": APPS_CATALOG}


def _apps_data_dir() -> Path:
    """Verzeichnis für Docker-App-Daten (data/apps/<app_id>)."""
    repo_root = Path(__file__).resolve().parent.parent
    return repo_root / "data" / "apps"


def _app_docker_template_path(app_id: str) -> Optional[Path]:
    """Pfad zur docker-compose.yml-Vorlage für die App (apps/<app_id>/docker-compose.yml)."""
    repo_root = Path(__file__).resolve().parent.parent
    p = repo_root / "apps" / app_id / "docker-compose.yml"
    return p if p.is_file() else None


def _app_container_running(app_id: str) -> bool:
    """Prüft ob der Docker-Container der App läuft (Phase 2.2)."""
    container_names = {"pi-hole": "pihole", "nextcloud": "nextcloud", "home-assistant": "homeassistant", "jellyfin": "jellyfin"}
    name = container_names.get(app_id)
    if not name:
        return False
    r = run_command(f"docker ps --format '{{{{.Names}}}}' 2>/dev/null | grep -q '^{name}$'", timeout=5)
    return r.get("success", False)


@app.get("/api/apps/{app_id}/status")
async def get_app_status(app_id: str):
    """Status einer App (installiert / nicht installiert). Phase 2.2: Docker-Container prüfen."""
    if app_id not in {a["id"] for a in APPS_CATALOG}:
        raise HTTPException(status_code=404, detail="App nicht gefunden")
    installed = _app_container_running(app_id)
    return {"installed": installed, "version": "docker" if installed else None}


@app.post("/api/apps/{app_id}/install")
async def install_app(request: Request, app_id: str):
    """App installieren. Phase 2.2: Docker-basierte Installation (nur wenn Vorlage vorhanden)."""
    if app_id not in {a["id"] for a in APPS_CATALOG}:
        raise HTTPException(status_code=404, detail="App nicht gefunden")
    template_path = _app_docker_template_path(app_id)
    if not template_path:
        return JSONResponse(
            status_code=501,
            content={"status": "not_implemented", "message": "Ein-Klick-Installation für diese App kommt in einer späteren Version."},
        )
    try:
        body = await request.json() if (request.headers.get("content-type") or "").startswith("application/json") else {}
    except Exception:
        body = {}
    if not isinstance(body, dict):
        body = {}
    sudo_password = (body.get("sudo_password") or "") if body else ""
    data_dir = _apps_data_dir()
    app_dir = data_dir / app_id
    app_dir.mkdir(parents=True, exist_ok=True)
    compose_dest = app_dir / "docker-compose.yml"
    import shutil
    shutil.copy2(template_path, compose_dest)
    cmd = f"cd {shlex.quote(str(app_dir))} && docker compose up -d"
    r = run_command(cmd, sudo=True, sudo_password=sudo_password or None, timeout=120)
    if r.get("success"):
        return {"status": "success", "installed": True, "message": "App wurde gestartet.", "version": "docker"}
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "message": r.get("stderr") or r.get("stdout") or "Docker Compose fehlgeschlagen.",
            "installed": False,
        },
    )


@app.get("/api/debug/routes")
async def debug_routes():
    """Listet alle registrierten API-Pfade (z. B. zum Prüfen ob /api/peripherals/scan geladen ist)."""
    paths = []
    for r in app.routes:
        path = getattr(r, "path", "")
        if path and "/api/" in path:
            paths.append(path)
    return {"paths": sorted(set(paths)), "version": get_pi_installer_version()}


def _validate_backup_dir(path_str: str) -> str:
    """
    Validiert ein Backup-Zielverzeichnis.
    - muss absolut sein
    - keine gefährlichen Zeichen (Shell-Injection)
    - muss unter erlaubten Mount-Roots liegen (USB-Sticks liegen typischerweise unter /media, /run/media, /mnt)
    """
    if not isinstance(path_str, str):
        raise ValueError("backup_dir muss ein String sein")
    path_str = path_str.strip()
    if not path_str:
        raise ValueError("backup_dir darf nicht leer sein")
    if not path_str.startswith("/"):
        raise ValueError("backup_dir muss ein absoluter Pfad sein (beginnt mit /)")
    # Erlaubte Zeichen:
    # - Wir erlauben bewusst Leerzeichen (USB-Sticks werden oft mit Labels mit Spaces gemountet),
    #   schützen aber gegen Shell-Injection durch:
    #   1) verbotene Metazeichen
    #   2) konsequentes Quoting via shlex.quote bei Shell-Commands
    forbidden = ["\n", "\r", "\t", "\x00", "`", "$", ";", "&", "|", "<", ">", "!", "\"", "'"]
    if any(ch in path_str for ch in forbidden):
        raise ValueError("backup_dir enthält ungültige Zeichen (u.a. Quotes, ;, &, |, Zeilenumbrüche sind nicht erlaubt)")

    resolved = Path(path_str).resolve()
    allowed_roots = [
        Path("/mnt").resolve(),
        Path("/media").resolve(),
        Path("/run/media").resolve(),
        Path("/home").resolve(),
    ]
    if not any(str(resolved).startswith(str(root) + "/") or resolved == root for root in allowed_roots):
        raise ValueError("backup_dir muss unter /mnt, /media, /run/media oder /home liegen")
    # Verhindere versehentliches Backup direkt auf Root-Verzeichnis
    if str(resolved) == "/":
        raise ValueError("backup_dir darf nicht / sein")
    return str(resolved)

# ==================== Hilfsfunktionen ====================

def _ensure_packagekit_stopped(sudo_password: Optional[str] = None) -> None:
    """Stoppt PackageKit temporär, um Konflikte mit apt-get zu vermeiden (PackageKit daemon disappeared).
    Wird nur ausgeführt, wenn ein sudo-Passwort übergeben wird – sonst würde systemctl stop einen
    Polkit-Dialog auslösen und bei wiederholten Aufrufen (z. B. Update-Liste) zu einer Abfrage-Schleife führen."""
    if not (sudo_password or "").strip():
        return  # Ohne Passwort kein Stop – vermeidet Polkit-Schleife
    try:
        check = subprocess.run(
            ["systemctl", "is-active", "packagekit"],
            capture_output=True,
            text=True,
            timeout=2,
        )
        if check.returncode == 0:
            stop_result = subprocess.run(
                ["sudo", "-S", "systemctl", "stop", "packagekit"],
                input=(sudo_password + "\n").encode("utf-8"),
                capture_output=True,
                timeout=5,
            )
            if stop_result.returncode == 0:
                logger.debug("PackageKit gestoppt, um apt-get-Konflikte zu vermeiden")
    except FileNotFoundError:
        pass  # PackageKit nicht installiert
    except Exception:
        pass  # Ignoriere Fehler

def run_command(cmd, sudo=False, sudo_password=None, timeout: int = 10):
    """Befehl ausführen. Stoppt automatisch PackageKit bei apt-get-Operationen."""
    try:
        # Bei apt-get-Operationen PackageKit stoppen, um "PackageKit daemon disappeared" zu vermeiden
        if "apt-get" in cmd or "apt " in cmd:
            _ensure_packagekit_stopped(sudo_password)
        
        if sudo:
            if sudo_password:
                # Mit Passwort via stdin (sicherer)
                cmd_parts = cmd.split()
                
                # Für UFW-Befehle: direkt ohne Shell ausführen
                if len(cmd_parts) > 0 and 'ufw' in cmd_parts[0]:
                    # UFW-Command direkt ausführen (z.B. /usr/sbin/ufw --force enable)
                    process = subprocess.Popen(
                        ['sudo', '-S'] + cmd_parts,
                        stdin=subprocess.PIPE,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True
                    )
                # Für einfache Commands ohne Shell-Syntax direkt ausführen
                elif len(cmd_parts) == 1 and '/' not in cmd and '|' not in cmd and '&&' not in cmd and ';' not in cmd:
                    # Einfacher Command - direkt ausführen
                    process = subprocess.Popen(
                        ['sudo', '-S'] + cmd_parts,
                        stdin=subprocess.PIPE,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True
                    )
                else:
                    # Komplexer Command - mit sh -c
                    process = subprocess.Popen(
                        ['sudo', '-S', 'sh', '-c', cmd],
                        stdin=subprocess.PIPE,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True
                    )
                stdout, stderr = process.communicate(input=sudo_password + '\n', timeout=timeout)
                return {
                    "success": process.returncode == 0,
                    "stdout": stdout,
                    "stderr": stderr,
                    "returncode": process.returncode,
                }
            else:
                cmd = f"sudo {cmd}"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Command timeout"}
    except Exception as e:
        return {"success": False, "error": str(e)}


async def run_command_async(cmd, sudo: bool = False, sudo_password: Optional[str] = None, timeout: int = 10) -> dict:
    """
    Runs blocking system commands in a background thread.
    Important: long-running tasks (tar/rsync/restore) would otherwise block the whole Uvicorn event loop.
    """
    return await asyncio.to_thread(run_command, cmd, sudo=sudo, sudo_password=sudo_password, timeout=timeout)

def check_installed(package):
    """Prüfe ob Paket installiert ist"""
    # Spezielle Prüfung für bestimmte Pakete
    if package == "ufw":
        # UFW spezifisch prüfen
        result = run_command("which ufw")
        if result["success"]:
            return True
        # Alternativ: dpkg prüfen
        result = run_command("dpkg -l | grep '^ii' | grep -E '^ii\\s+ufw\\s'")
        return result["success"] and "ufw" in result.get("stdout", "")
    
    if package == "nginx":
        # Nginx spezifisch prüfen - mehrere Methoden
        # Methode 1: which nginx
        result = run_command("which nginx")
        if result["success"]:
            return True
        # Methode 2: dpkg prüfen
        result = run_command("dpkg -l | grep '^ii' | grep -E '\\snginx\\s'")
        if result["success"] and "nginx" in result.get("stdout", ""):
            return True
        # Methode 3: Prüfe ob nginx-Binary existiert
        result = run_command("test -f /usr/sbin/nginx || test -f /usr/bin/nginx")
        if result["success"]:
            return True
        # Methode 4: Prüfe ob nginx-Config existiert
        result = run_command("test -d /etc/nginx")
        if result["success"]:
            return True
        return False
    
    if package == "apache2" or package == "apache":
        # Apache spezifisch prüfen
        result = run_command("which apache2")
        if result["success"]:
            return True
        result = run_command("dpkg -l | grep '^ii' | grep -E '\\sapache2\\s'")
        if result["success"] and "apache2" in result.get("stdout", ""):
            return True
        result = run_command("test -f /usr/sbin/apache2 || test -d /etc/apache2")
        if result["success"]:
            return True
        return False
    
    # Grafana: which, dpkg, Binary-Pfade, systemd-Unit, Snap
    if package == "grafana":
        if run_command("which grafana-server 2>/dev/null")["success"]:
            return True
        r = run_command("dpkg -l 2>/dev/null | grep -E '^ii\\s+grafana'")
        if r.get("success") and (r.get("stdout") or "").strip():
            return True
        if run_command("test -f /usr/sbin/grafana-server 2>/dev/null")["success"]:
            return True
        if run_command("test -f /usr/bin/grafana-server 2>/dev/null")["success"]:
            return True
        if run_command("test -f /usr/share/grafana/bin/grafana-server 2>/dev/null")["success"]:
            return True
        if run_command("systemctl list-unit-files 2>/dev/null | grep -q 'grafana-server'")["success"]:
            return True
        if run_command("systemctl list-units --all 2>/dev/null | grep -q grafana")["success"]:
            return True
        if run_command("snap list 2>/dev/null | grep -q grafana")["success"]:
            return True
        if run_command("test -f /snap/bin/grafana-server 2>/dev/null")["success"]:
            return True
        return False

    # Standard-Prüfung
    result = run_command(f"which {package} || dpkg -l | grep '^ii' | grep -E '\\s{package}\\s'")
    return result["success"]

def get_package_version(package):
    """Hole Paket-Version"""
    try:
        result = run_command(f"dpkg -l | grep '^ii' | grep {package} | head -1")
        if result["success"] and result["stdout"]:
            parts = result["stdout"].split()
            if len(parts) >= 3:
                return parts[2]
        
        # Versuche which + version
        result = run_command(f"{package} --version 2>/dev/null | head -1")
        if result["success"] and result["stdout"]:
            return result["stdout"].strip()
        
        return None
    except:
        return None

def get_cpu_temp():
    """CPU Temperatur auslesen"""
    try:
        # Versuche verschiedene Pfade
        temp_paths = [
            '/sys/class/thermal/thermal_0/temp',
            '/sys/class/thermal/thermal_zone0/temp',
            '/sys/devices/virtual/thermal/thermal_zone0/temp',
        ]
        
        for path in temp_paths:
            try:
                with open(path, 'r') as f:
                    temp = int(f.read().strip()) / 1000.0
                    return round(temp, 1)
            except:
                continue
        
        # Alternative: vcgencmd (Raspberry Pi)
        result = run_command("vcgencmd measure_temp 2>/dev/null")
        if result["success"] and result["stdout"]:
            temp_str = result["stdout"]
            if "temp=" in temp_str:
                temp = float(temp_str.split("temp=")[1].split("'")[0])
                return round(temp, 1)
        
        # Alternative: sensors (falls installiert)
        result = run_command("sensors 2>/dev/null | grep -i temp | head -1")
        if result["success"] and result["stdout"]:
            # Parse sensors output
            parts = result["stdout"].split()
            for part in parts:
                if "+" in part and "°C" in part:
                    temp = float(part.replace("+", "").replace("°C", ""))
                    return round(temp, 1)
        
        return None
    except:
        return None

def get_all_thermal_sensors():
    """Alle Temperatursensoren (thermal_zone*)"""
    sensors = []
    try:
        base = Path("/sys/class/thermal")
        if not base.exists():
            return sensors
        for zone in sorted(base.glob("thermal_zone*")):
            try:
                temp_path = zone / "temp"
                type_path = zone / "type"
                if temp_path.exists():
                    temp = int(temp_path.read_text().strip()) / 1000.0
                    name = type_path.read_text().strip() if type_path.exists() else zone.name
                    sensors.append({"name": name, "temperature": round(temp, 1), "zone": zone.name})
            except Exception:
                continue
        if not sensors and run_command("which vcgencmd 2>/dev/null")["success"]:
            vc = run_command("vcgencmd measure_temp 2>/dev/null")
            if vc.get("success") and "temp=" in (vc.get("stdout") or ""):
                t = float((vc["stdout"] or "").split("temp=")[1].split("'")[0])
                sensors.append({"name": "cpu", "temperature": round(t, 1), "zone": "vcgencmd"})
        # hwmon Temperatursensoren (Motherboard, GPU, NVMe etc.)
        hwmon_base = Path("/sys/class/hwmon")
        if hwmon_base.exists():
            for hw in sorted(hwmon_base.iterdir()):
                if not hw.is_dir() or not hw.name.startswith("hwmon"):
                    continue
                try:
                    name_path = hw / "name"
                    hw_name = name_path.read_text().strip() if name_path.exists() else hw.name
                    for temp_path in sorted(hw.glob("temp*_input")):
                        try:
                            val = int(temp_path.read_text().strip())
                            temp_c = round(val / 1000.0, 1)
                            label_path = hw / temp_path.name.replace("_input", "_label")
                            label = label_path.read_text().strip() if label_path.exists() else temp_path.stem.replace("_input", "")
                            sensors.append({"name": f"{hw_name} {label}", "temperature": temp_c, "zone": f"{hw.name}/{temp_path.name}"})
                        except Exception:
                            continue
                except Exception:
                    continue
    except Exception:
        pass
    return sensors

def get_all_fans():
    """Alle Lüfter (hwmon fan*_input)"""
    fans = []
    try:
        base = Path("/sys/class/hwmon")
        if not base.exists():
            return fans
        for hw in sorted(base.iterdir()):
            if not hw.is_dir() or not hw.name.startswith("hwmon"):
                continue
            name_path = hw / "name"
            name = name_path.read_text().strip() if name_path.exists() else hw.name
            for fan in sorted(hw.glob("fan*_input")):
                try:
                    rpm = int(fan.read_text().strip())
                    fans.append({"name": f"{name} {fan.stem.replace('_input', '')}", "rpm": rpm})
                except Exception:
                    continue
    except Exception:
        pass
    return fans

def get_all_disks():
    """Alle gemounteten Laufwerke + NVMe/Block-Geräte mit Nutzung bzw. Größe"""
    disks = []
    seen_devices = set()
    try:
        for part in psutil.disk_partitions(all=False):
            try:
                usage = psutil.disk_usage(part.mountpoint)
                disks.append({
                    "device": part.device,
                    "mountpoint": part.mountpoint,
                    "fstype": part.fstype,
                    "total_gb": round(usage.total / (1024**3), 1),
                    "used_gb": round(usage.used / (1024**3), 1),
                    "percent": usage.percent,
                    "label": part.device.rstrip("/").split("/")[-1],
                })
                seen_devices.add(part.device)
            except Exception:
                continue
        # NVMe und weitere Block-Geräte (auch ungemountet)
        block_base = Path("/sys/block")
        if block_base.exists():
            for blk in sorted(block_base.iterdir()):
                if blk.name.startswith("loop") or blk.name.startswith("ram"):
                    continue
                dev = f"/dev/{blk.name}"
                if dev in seen_devices:
                    continue
                try:
                    size_path = blk / "size"
                    if not size_path.exists():
                        continue
                    sectors = int(size_path.read_text().strip())
                    size_gb = round(sectors * 512 / (1024**3), 1)
                    if size_gb <= 0:
                        continue
                    # Mountpoint und Nutzung für dieses Block-Device ermitteln (z. B. nvme0n1p1)
                    mountpoint = ""
                    used_gb = None
                    percent = None
                    for p in psutil.disk_partitions(all=True):
                        if p.device.startswith(dev) or (dev + "1" == p.device or dev + "p1" == p.device):
                            try:
                                u = psutil.disk_usage(p.mountpoint)
                                mountpoint = p.mountpoint
                                used_gb = round(u.used / (1024**3), 1)
                                percent = u.percent
                                break
                            except Exception:
                                pass
                    disks.append({
                        "device": dev,
                        "mountpoint": mountpoint,
                        "fstype": "",
                        "total_gb": size_gb,
                        "used_gb": used_gb,
                        "percent": percent,
                        "label": blk.name,
                    })
                    seen_devices.add(dev)
                except Exception:
                    continue
    except Exception:
        pass
    return disks

def get_all_displays():
    """Alle erkannten Displays (xrandr)"""
    displays = []
    try:
        r = run_command("xrandr --query 2>/dev/null")
        if not r.get("success") or not r.get("stdout"):
            return displays
        current = None
        for line in (r["stdout"] or "").strip().split("\n"):
            if line.startswith(" ") and "x" in line and "+" in line:
                parts = line.strip().split()
                if len(parts) >= 1 and current:
                    mode = parts[0]
                    displays.append({"output": current, "mode": mode, "connected": "connected" in line or "*" in line})
            else:
                parts = line.split()
                if len(parts) >= 2:
                    current = parts[0]
                    if parts[1] == "connected":
                        displays.append({"output": current, "mode": parts[2] if len(parts) > 2 else "", "connected": True})
        if not displays:
            r2 = run_command("DISPLAY=:0 xrandr --query 2>/dev/null")
            if r2.get("success") and r2.get("stdout"):
                for line in (r2["stdout"] or "").strip().split("\n"):
                    if " connected " in line:
                        parts = line.split()
                        if len(parts) >= 1:
                            displays.append({"output": parts[0], "mode": parts[2] if len(parts) > 2 else "", "connected": True})
    except Exception:
        pass
    return displays

def get_fan_speed():
    """Lüfter-Geschwindigkeit (ein Wert für Abwärtskompatibilität)"""
    try:
        fans = get_all_fans()
        return fans[0]["rpm"] if fans else None
    except Exception:
        return None

def get_motherboard_info():
    """Motherboard/Baseboard aus DMI"""
    info = {}
    try:
        for key, path in [("vendor", "board_vendor"), ("name", "board_name"), ("product", "product_name")]:
            p = Path("/sys/class/dmi/id") / path
            if p.exists():
                try:
                    info[key] = p.read_text().strip()
                except Exception:
                    pass
        if not info:
            r = run_command("dmidecode -t baseboard 2>/dev/null")
            if r.get("success") and r.get("stdout"):
                for line in (r["stdout"] or "").split("\n"):
                    if "Manufacturer:" in line:
                        info["vendor"] = line.split(":", 1)[-1].strip()
                    elif "Product Name:" in line:
                        info["name"] = line.split(":", 1)[-1].strip()
    except Exception:
        pass
    return info

def get_ram_info():
    """RAM-Typ, Geschwindigkeit und Hersteller (DMI/dmidecode). Normalisierte Felder: Type, Size, Speed, Manufacturer."""
    rams = []
    try:
        r = run_command("dmidecode -t memory 2>/dev/null")
        if r.get("success") and r.get("stdout"):
            block = {}
            for line in (r["stdout"] or "").split("\n"):
                if line.startswith("Memory Device"):
                    if block.get("Size") and "No Module" not in (block.get("Size") or ""):
                        _normalize_ram_block(block)
                        rams.append(block)
                    block = {}
                elif ":" in line:
                    k, v = line.split(":", 1)
                    block[k.strip()] = v.strip()
            if block.get("Size") and "No Module" not in (block.get("Size") or ""):
                _normalize_ram_block(block)
                rams.append(block)
        if not rams:
            for p in Path("/sys/class/dmi/id").glob("*"):
                if "mem" in p.name.lower():
                    try:
                        rams.append({"source": p.name, "value": p.read_text().strip()})
                    except Exception:
                        pass
    except Exception:
        pass
    return rams


def _normalize_ram_block(block: dict) -> None:
    """Setzt Speed aus dmidecode (Fallback: Configured Clock Speed / Maximum Speed). Type, Size, Manufacturer bleiben unverändert."""
    if not block:
        return
    speed = block.get("Speed") or block.get("Configured Clock Speed") or block.get("Configured Memory Speed") or block.get("Maximum Speed")
    if speed and str(speed).strip() and str(speed) != "Unknown":
        block["Speed"] = speed

def get_cpu_name():
    """CPU-Modellname aus /proc/cpuinfo"""
    try:
        with open("/proc/cpuinfo", "r") as f:
            for line in f:
                if line.strip().startswith("model name"):
                    return line.split(":", 1)[-1].strip()
        return None
    except Exception:
        return None


def get_cpu_summary():
    """Ein CPU-Summary: Name, Kerne, Threads, Cache (L1–L3), Befehlssätze (flags) aus /proc/cpuinfo und lscpu."""
    out = {"name": None, "cores": None, "threads": None, "cache": None, "flags": None}
    try:
        # Aus /proc/cpuinfo (erstes Prozessor-Block)
        with open("/proc/cpuinfo", "r") as f:
            content = f.read()
        blocks = content.strip().split("\n\n")
        first = blocks[0] if blocks else ""
        for line in first.split("\n"):
            line = line.strip()
            if line.startswith("model name"):
                out["name"] = line.split(":", 1)[-1].strip()
            elif line.startswith("cpu cores"):
                try:
                    out["cores"] = int(line.split(":")[-1].strip())
                except ValueError:
                    pass
            elif line.startswith("cache size"):
                out["cache"] = line.split(":", 1)[-1].strip()
            elif line.startswith("flags") or line.startswith("Features"):
                out["flags"] = line.split(":", 1)[-1].strip()
        # Threads = Anzahl Prozessor-Blöcke
        out["threads"] = len([b for b in blocks if "processor" in b or "Processor" in b])
        # lscpu für L1d/L1i/L2/L3 falls vorhanden
        try:
            r = run_command("lscpu 2>/dev/null")
            if r.get("success") and r.get("stdout"):
                for line in (r.get("stdout") or "").splitlines():
                    if "L1d cache:" in line or "L1i cache:" in line or "L2 cache:" in line or "L3 cache:" in line:
                        key, _, val = line.partition(":")
                        val = val.strip()
                        if val:
                            out["cache"] = (out["cache"] or "") + (" · " if out["cache"] else "") + f"{key.strip()}: {val}"
        except Exception:
            pass
        if out["cache"]:
            out["cache"] = out["cache"].strip()
        return out
    except Exception:
        return out


def get_per_core_usage(per_cpu_percent):
    """Aus per-logical-CPU-Auslastung die pro physikalischem Kern (max der Threads) berechnen."""
    if not per_cpu_percent:
        return [], 0
    try:
        proc_to_core = {}
        with open("/proc/cpuinfo", "r") as f:
            proc_id = None
            core_id = None
            for line in f:
                if line.strip().startswith("processor"):
                    proc_id = int(line.split(":")[-1].strip())
                elif line.strip().startswith("core id"):
                    core_id = int(line.split(":")[-1].strip())
                elif line.strip() == "" and proc_id is not None and core_id is not None:
                    proc_to_core[proc_id] = core_id
                    proc_id = core_id = None
            if proc_id is not None and core_id is not None:
                proc_to_core[proc_id] = core_id
        from collections import defaultdict
        core_to_procs = defaultdict(list)
        for p, c in proc_to_core.items():
            core_to_procs[c].append(p)
        if not core_to_procs:
            return list(per_cpu_percent), len(per_cpu_percent)
        per_core = []
        for c in sorted(core_to_procs.keys()):
            procs = core_to_procs[c]
            vals = [per_cpu_percent[i] for i in procs if i < len(per_cpu_percent)]
            per_core.append(max(vals) if vals else 0)
        return per_core, len(per_core)
    except Exception:
        return list(per_cpu_percent), len(per_cpu_percent)

def get_installed_apps():
    """Erkenne installierte Web-Apps"""
    apps = {
        "wordpress": check_installed("wordpress"),
        "nextcloud": check_installed("nextcloud"),
        "drupal": check_installed("drupal"),
        "nginx": check_installed("nginx"),
        "apache": check_installed("apache2"),
        "php": check_installed("php") or check_installed("php-fpm") or check_installed("libapache2-mod-php"),
        "mysql": check_installed("mysql"),
        "postgresql": check_installed("postgresql"),
        "docker": check_installed("docker"),
        "python": check_installed("python3"),
        "nodejs": check_installed("nodejs"),
        "git": check_installed("git"),
        "cursor": False,  # Wird separat geprüft
        "qtqml": check_installed("qt5-default") or check_installed("qtbase5-dev") or run_command("which qmake 2>/dev/null")["success"] or run_command("dpkg -l 2>/dev/null | grep -q 'qt5'")["success"],
        "cockpit": check_installed("cockpit"),
        "webmin": check_installed("webmin"),
        # NAS
        "samba": check_installed("samba") or check_installed("samba-common"),
        "nfs": check_installed("nfs-kernel-server") or check_installed("nfs-common"),
        "ftp": check_installed("vsftpd") or check_installed("proftpd"),
        # Home Automation
        "homeassistant": check_installed("homeassistant") or run_command("docker ps | grep homeassistant")["success"],
        "openhab": check_installed("openhab"),
        "nodered": check_installed("node-red") or run_command("npm list -g node-red 2>/dev/null")["success"],
        # Music Box
        "mopidy": check_installed("mopidy"),
        "volumio": check_installed("volumio") or run_command("test -f /opt/volumio/bin/volumio")["success"],
        "plex": check_installed("plexmediaserver") or run_command("dpkg -l | grep plex")["success"],
    }
    
    # Cursor AI prüfen (kann in verschiedenen Pfaden sein)
    cursor_paths = [
        "/usr/bin/cursor",
        "/usr/local/bin/cursor",
        "/opt/cursor/cursor",
        "~/.local/bin/cursor",
    ]
    for path in cursor_paths:
        result = run_command(f"test -f {path} || which cursor")
        if result["success"]:
            apps["cursor"] = True
            break
    
    # WordPress Plugins prüfen
    wp_plugin_paths = [
        "/var/www/html/wp-content/plugins",
        "/var/www/wordpress/wp-content/plugins",
        "~/wordpress/wp-content/plugins",
    ]
    for path in wp_plugin_paths:
        result = run_command(f"test -d {path} && ls {path} 2>/dev/null | head -5")
        if result["success"] and result["stdout"]:
            plugins = [p.strip() for p in result["stdout"].split("\n") if p.strip()]
            apps["wordpress_plugins"] = plugins
            break
    
    # Websites/Apps erkennen (Webroot prüfen)
    webroots = ["/var/www/html", "/var/www", "/home/*/public_html"]
    websites = []
    for root in webroots:
        result = run_command(f"ls -d {root}/* 2>/dev/null | head -10")
        if result["success"]:
            for site in result["stdout"].split("\n"):
                if site.strip():
                    websites.append(site.strip())
    
    apps["websites"] = websites[:10]  # Erste 10
    
    return apps

def _is_reachable_lan_ip(ip: str) -> bool:
    """Filtert unbrauchbare Adressen. 0.0.0.0 ist keine erreichbare Adresse im Heimnetz."""
    if not ip or not ip.strip():
        return False
    s = ip.strip().lower()
    if s in ("0.0.0.0", "127.0.0.1", "::1", "localhost"):
        return False
    if s.startswith("127.") or s.startswith("fe80:"):
        return False
    return True


def get_network_info():
    """Netzwerk-Informationen. Nur IPs zurückgeben, die von anderen Geräten erreichbar sind (kein 0.0.0.0)."""
    try:
        result = subprocess.run("hostname -I", shell=True, capture_output=True, text=True, timeout=5)
        raw = (result.stdout or "").strip()
        candidates = [x for x in raw.split() if x] if raw else []
        ips = [x for x in candidates if _is_reachable_lan_ip(x)]
        result = subprocess.run("hostname", shell=True, capture_output=True, text=True, timeout=5)
        hostname = (result.stdout or "").strip() or "unknown"
        return {"ips": ips, "hostname": hostname}
    except Exception:
        return {"ips": [], "hostname": "unknown"}

def get_running_services():
    """Laufen Services"""
    services = [
        "nginx", "apache2", "mysql", "mariadb", "postgresql",
        "docker", "fail2ban", "sshd", "postfix", "dovecot",
        "mopidy", "grafana-server", "plexmediaserver",
    ]
    running = {}
    for service in services:
        result = run_command(f"systemctl is-active {service}")
        running[service] = result["success"]
    return running

def _get_installed_packages_list():
    """Detaillierte Liste installierter Pakete"""
    packages = {}
    important_packages = [
        "nginx", "apache2", "mysql-server", "mariadb-server", "postgresql",
        "docker", "docker-compose", "fail2ban", "ufw", "python3", "python3-pip",
        "nodejs", "npm", "git", "php", "php-fpm", "wordpress", "nextcloud",
        "drupal", "postfix", "dovecot", "spamassassin"
    ]
    
    for pkg in important_packages:
        installed = check_installed(pkg)
        version = get_package_version(pkg) if installed else None
        packages[pkg] = {
            "installed": installed,
            "version": version,
        }
    
    return packages

def get_running_processes():
    """Laufende Prozesse"""
    try:
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                p = proc.info
                if p['cpu_percent'] > 0.1 or p['memory_percent'] > 1.0:  # Nur relevante Prozesse
                    processes.append({
                        "pid": p['pid'],
                        "name": p['name'],
                        "cpu": round(p['cpu_percent'], 1),
                        "memory": round(p['memory_percent'], 1),
                    })
            except:
                continue
        
        # Sortiere nach CPU
        processes.sort(key=lambda x: x['cpu'], reverse=True)
        return processes[:20]  # Top 20
    except:
        return []

def get_security_config():
    """Sicherheitseinstellungen prüfen"""
    config = {}
    
    try:
        # SSH Config
        ssh_config = run_command("grep -E '^PasswordAuthentication|^PermitRootLogin|^Port' /etc/ssh/sshd_config 2>/dev/null")
        config["ssh"] = {
            "config": ssh_config.get("stdout", "") if ssh_config["success"] else "Nicht lesbar",
            "installed": check_installed("ssh"),
            "running": get_running_services().get("sshd", False),
        }
    except Exception as e:
        config["ssh"] = {
            "config": "Fehler beim Lesen",
            "installed": False,
            "running": False,
        }
    
    try:
        # UFW Status - verwende direkt sudo, wenn Passwort verfügbar ist
        stored_sudo_password = sudo_password_store.get("password", "")
        
        # Versuche zuerst mit sudo, wenn Passwort verfügbar ist (ufw status benötigt root für Regeln)
        if stored_sudo_password:
            logger.info("🔧 Versuche UFW Status mit sudo (Passwort verfügbar)...")
            ufw_status = run_command("ufw status", sudo=True, sudo_password=stored_sudo_password)
        else:
            # Fallback: Versuche ohne sudo
            logger.info("🔧 Versuche UFW Status ohne sudo...")
            ufw_status = run_command("ufw status")
            # Falls ohne sudo nicht erfolgreich, versuche mit sudo (falls Passwort später gespeichert wird)
            if not ufw_status["success"]:
                stored_sudo_password = sudo_password_store.get("password", "")
                if stored_sudo_password:
                    logger.info("🔧 UFW Status ohne sudo fehlgeschlagen, versuche mit sudo...")
                    ufw_status = run_command("ufw status", sudo=True, sudo_password=stored_sudo_password)
        
        # Falls immer noch nicht erfolgreich, versuche "ufw status verbose" mit sudo
        if not ufw_status["success"] and stored_sudo_password:
            logger.info("🔧 Versuche ufw status verbose mit sudo...")
            ufw_status = run_command("ufw status verbose", sudo=True, sudo_password=stored_sudo_password)
        
        # Falls ufw status nicht funktioniert, versuche alternative Methoden
        ufw_active = False
        status_output = ""
        if ufw_status["success"]:
            status_output = ufw_status.get("stdout", "")
            # Prüfe sowohl englische als auch deutsche Ausgabe
            ufw_active = "Status: active" in status_output or "Status: aktiv" in status_output
        else:
            # Alternative 1: Prüfe UFW-Konfigurationsdatei direkt (funktioniert ohne sudo)
            try:
                ufw_config_check = run_command("grep -E '^ENABLED=' /etc/ufw/ufw.conf 2>/dev/null")
                if ufw_config_check["success"]:
                    config_line = ufw_config_check.get("stdout", "").strip()
                    if "ENABLED=yes" in config_line:
                        ufw_active = True
                        status_output = "Status: active (via /etc/ufw/ufw.conf)"
                        logger.info("🔧 UFW Status via /etc/ufw/ufw.conf ermittelt: active (ENABLED=yes)")
                    else:
                        logger.info(f"🔧 UFW Config zeigt: {config_line}")
            except Exception as e:
                logger.warning(f"⚠️ Konnte UFW-Config nicht lesen: {e}")
            
            # Alternative 2: Prüfe systemd-Status (funktioniert manchmal ohne sudo)
            if not ufw_active:
                systemd_status = run_command("systemctl is-active ufw 2>/dev/null")
                if systemd_status["success"] and "active" in systemd_status.get("stdout", ""):
                    ufw_active = True
                    status_output = "Status: active (via systemctl)"
                    logger.info("🔧 UFW Status via systemctl is-active ermittelt: active")
                else:
                    # Alternative 3: Prüfe systemctl status (zeigt mehr Details)
                    systemd_status_detailed = run_command("systemctl status ufw --no-pager 2>/dev/null | head -3")
                    if systemd_status_detailed["success"]:
                        status_text = systemd_status_detailed.get("stdout", "")
                        if "active (exited)" in status_text or "active (running)" in status_text:
                            ufw_active = True
                            status_output = "Status: active (via systemctl status)"
                            logger.info("🔧 UFW Status via systemctl status ermittelt: active")
                        else:
                            # Alternative 4: Prüfe ob UFW-Service enabled ist
                            ufw_enabled = run_command("systemctl is-enabled ufw 2>/dev/null")
                            if ufw_enabled["success"] and "enabled" in ufw_enabled.get("stdout", ""):
                                # Wenn enabled, ist es wahrscheinlich aktiv
                                ufw_active = True
                                status_output = "Status: active (wahrscheinlich, service enabled)"
                                logger.info("🔧 UFW Status via systemctl is-enabled ermittelt: wahrscheinlich active")
        
        # Wenn UFW installiert ist, aber Status nicht ermittelt werden konnte, versuche nochmal mit einfacheren Methoden
        ufw_installed = check_installed("ufw")
        if ufw_installed and not ufw_active and not status_output:
            # Versuche nochmal mit einem einfacheren Command
            ufw_simple_check = run_command("ufw status 2>&1 | grep -i 'status:' | head -1")
            if ufw_simple_check["success"]:
                simple_output = ufw_simple_check.get("stdout", "")
                if "active" in simple_output.lower() or "aktiv" in simple_output.lower():
                    ufw_active = True
                    status_output = f"Status: active ({simple_output.strip()})"
                    logger.info("🔧 UFW Status via ufw status | grep ermittelt: active")
        
        # Regeln abrufen (auch wenn Status über alternative Methoden ermittelt wurde)
        rules_output = ""
        rules_list = []
        
        # Versuche zuerst, Regeln aus dem Status-Output zu extrahieren
        if ufw_status["success"] and status_output:
            rules_output = status_output
            logger.info(f"✅ UFW-Regeln aus Status-Output extrahiert: {len(rules_output)} Zeichen")
        
        # Wenn Firewall aktiv ist, aber keine Regeln aus Status-Output, versuche separat abzurufen
        if (ufw_active or ufw_installed) and not rules_output:
            stored_sudo_password = sudo_password_store.get("password", "")
            
            # Versuche 1: ufw status numbered (direkt mit sudo, wenn Passwort verfügbar)
            if stored_sudo_password:
                logger.info("🔧 Versuche UFW-Regeln mit sudo abzurufen (numbered)...")
                rules_result = run_command("ufw status numbered", sudo=True, sudo_password=stored_sudo_password)
            else:
                logger.info("🔧 Versuche UFW-Regeln abzurufen (numbered, ohne sudo)...")
                rules_result = run_command("ufw status numbered")
                if not rules_result["success"]:
                    logger.warning(f"⚠️ ufw status numbered ohne sudo fehlgeschlagen: {rules_result.get('stderr', '')[:100]}")
            
            if rules_result["success"]:
                rules_output = rules_result.get("stdout", "")
                logger.info(f"✅ UFW-Regeln erfolgreich abgerufen (numbered): {len(rules_output)} Zeichen")
            else:
                logger.warning(f"⚠️ ufw status numbered fehlgeschlagen: {rules_result.get('stderr', '')[:100]}")
                # Versuche 3: ufw status verbose (ohne sudo)
                logger.info("🔧 Versuche ufw status verbose (ohne sudo)...")
                verbose_result = run_command("ufw status verbose")
                if not verbose_result["success"] and stored_sudo_password:
                    # Versuche 4: ufw status verbose (mit sudo)
                    logger.info("🔧 Versuche UFW-Regeln (verbose) mit sudo abzurufen...")
                    verbose_result = run_command("ufw status verbose", sudo=True, sudo_password=stored_sudo_password)
                
                if verbose_result["success"]:
                    rules_output = verbose_result.get("stdout", "")
                    logger.info(f"✅ UFW-Regeln (verbose) erfolgreich abgerufen: {len(rules_output)} Zeichen")
                else:
                    logger.warning(f"⚠️ ufw status verbose fehlgeschlagen: {verbose_result.get('stderr', '')[:100]}")
                    # Versuche 5: ufw status (direkt mit sudo, wenn Passwort verfügbar)
                    if stored_sudo_password:
                        logger.info("🔧 Versuche ufw status mit sudo...")
                        simple_status = run_command("ufw status", sudo=True, sudo_password=stored_sudo_password)
                    else:
                        logger.info("🔧 Versuche ufw status (einfach, ohne sudo)...")
                        simple_status = run_command("ufw status")
                    
                    if simple_status["success"]:
                        rules_output = simple_status.get("stdout", "")
                        logger.info(f"✅ UFW-Status erfolgreich abgerufen: {len(rules_output)} Zeichen")
                    else:
                        logger.warning(f"⚠️ Konnte UFW-Regeln nicht abrufen. Alle Versuche fehlgeschlagen. Stderr: {simple_status.get('stderr', '')[:100]}")
                        # Als letzter Versuch: Versuche die Regeln aus der Konfigurationsdatei zu lesen
                        logger.info("🔧 Versuche UFW-Regeln aus Konfigurationsdatei zu lesen...")
                        ufw_rules_file = "/etc/ufw/user.rules"
                        rules_file_check = run_command(f"cat {ufw_rules_file} 2>/dev/null | grep -E '^### tuple' | head -20")
                        if rules_file_check["success"]:
                            rules_output = rules_file_check.get("stdout", "")
                            logger.info(f"✅ UFW-Regeln aus Konfigurationsdatei gelesen: {len(rules_output)} Zeichen")
        
        # Regeln aus Output extrahieren und filtern
        if rules_output:
            # Teile in Zeilen und filtere leere/irrelevante Zeilen
            all_lines = rules_output.split("\n")
            # Filtere Header-Zeilen und leere Zeilen
            for line in all_lines:
                line = line.strip()
                if line and not line.startswith("Status:") and not line.startswith("To ") and not line.startswith("--") and line != "":
                    # Nur Zeilen mit tatsächlichen Regeln (enthalten Ports, IPs, etc.)
                    if any(keyword in line.lower() for keyword in ["allow", "deny", "reject", "limit", "/tcp", "/udp", "anywhere", "from", "to"]):
                        rules_list.append(line)
            
            # Wenn keine gefilterten Regeln gefunden wurden, aber Output vorhanden ist,
            # füge alle nicht-leeren Zeilen hinzu (außer Header)
            if not rules_list and all_lines:
                for line in all_lines:
                    line = line.strip()
                    if line and not line.startswith("Status:") and not line.startswith("To ") and not line.startswith("--"):
                        rules_list.append(line)
        
        logger.info(f"📋 UFW Status Check in get_security_config(): success={ufw_status['success']}, active={ufw_active}, installed={ufw_installed}, output_length={len(status_output)}, rules_count={len(rules_list)}, stderr={ufw_status.get('stderr', '')[:100]}")
        
        config["ufw"] = {
            "installed": ufw_installed,
            "active": ufw_active,
            "status": status_output if status_output else ("Nicht aktiv" if ufw_installed else "Nicht installiert"),
            "rules": rules_list,
        }
    except Exception as e:
        config["ufw"] = {
            "installed": check_installed("ufw"),
            "active": False,
            "status": f"Fehler beim Abrufen: {str(e)}",
            "rules": [],
        }
    
    try:
        # Fail2ban - Detaillierter Status
        fail2ban_installed = check_installed("fail2ban")
        fail2ban_running = get_running_services().get("fail2ban", False)
        fail2ban_jails = run_command("fail2ban-client status 2>/dev/null")
        
        config["fail2ban"] = {
            "installed": fail2ban_installed,
            "running": fail2ban_running,
            "active": fail2ban_installed and fail2ban_running,
            "status": fail2ban_jails.get("stdout", "") if fail2ban_jails["success"] else "Nicht aktiv",
            "jails": fail2ban_jails.get("stdout", "").split("\n") if fail2ban_jails["success"] else [],
        }
    except Exception as e:
        config["fail2ban"] = {
            "installed": False,
            "running": False,
            "active": False,
            "status": "Fehler beim Abrufen",
            "jails": [],
        }
    
    try:
        # Auto-Updates
        auto_updates_enabled = run_command("systemctl is-enabled unattended-upgrades 2>/dev/null")
        auto_updates_installed = check_installed("unattended-upgrades")
        config["auto_updates"] = {
            "installed": auto_updates_installed,
            "enabled": auto_updates_enabled["success"],
        }
    except Exception as e:
        config["auto_updates"] = {
            "installed": False,
            "enabled": False,
        }
    
    try:
        # SSH Härtung prüfen
        ssh_hardened = False
        ssh_hardening_checks = []
        
        # Prüfe SSH-Konfiguration auf Härtungsmerkmale
        ssh_config_file = "/etc/ssh/sshd_config"
        
        # Prüfe PermitRootLogin
        root_login_check = run_command(f"grep -E '^PermitRootLogin' {ssh_config_file} 2>/dev/null")
        if root_login_check["success"]:
            root_login_value = root_login_check.get("stdout", "").strip().lower()
            if "permitrootlogin no" in root_login_value:
                ssh_hardening_checks.append("PermitRootLogin: no")
                ssh_hardened = True
        
        # Prüfe PasswordAuthentication
        pass_auth_check = run_command(f"grep -E '^PasswordAuthentication' {ssh_config_file} 2>/dev/null")
        if pass_auth_check["success"]:
            pass_auth_value = pass_auth_check.get("stdout", "").strip().lower()
            if "passwordauthentication no" in pass_auth_value:
                ssh_hardening_checks.append("PasswordAuthentication: no")
                ssh_hardened = True
        
        # Prüfe MaxAuthTries
        max_auth_check = run_command(f"grep -E '^MaxAuthTries' {ssh_config_file} 2>/dev/null")
        if max_auth_check["success"]:
            max_auth_value = max_auth_check.get("stdout", "").strip()
            if "MaxAuthTries" in max_auth_value:
                ssh_hardening_checks.append("MaxAuthTries: gesetzt")
                ssh_hardened = True
        
        # Prüfe ob Backup existiert (Zeichen für durchgeführte Härtung)
        backup_exists = run_command(f"test -f /etc/ssh/sshd_config.backup")
        if backup_exists["success"]:
            ssh_hardening_checks.append("Backup vorhanden")
            ssh_hardened = True
        
        config["ssh_hardening"] = {
            "enabled": ssh_hardened,
            "installed": ssh_hardened,
            "checks": ssh_hardening_checks,
            "status": "Aktiviert" if ssh_hardened else "Nicht aktiviert",
        }
    except Exception as e:
        config["ssh_hardening"] = {
            "enabled": False,
            "installed": False,
            "checks": [],
            "status": f"Fehler: {str(e)}",
        }
    
    try:
        # Audit Logging prüfen
        auditd_installed = check_installed("auditd")
        auditd_running = get_running_services().get("auditd", False)
        
        # Prüfe ob Audit-Regeln existieren
        audit_rules_file = "/etc/audit/rules.d/pi-installer.rules"
        audit_rules_exist = run_command(f"test -f {audit_rules_file}")
        audit_rules_configured = audit_rules_exist["success"]
        
        # Prüfe ob auditd aktiv ist
        auditd_active = False
        if auditd_installed:
            auditd_status = run_command("systemctl is-active auditd 2>/dev/null")
            auditd_active = auditd_status["success"] and "active" in auditd_status.get("stdout", "")
        
        config["audit_logging"] = {
            "installed": auditd_installed,
            "running": auditd_running or auditd_active,
            "enabled": auditd_installed and (auditd_running or auditd_active),
            "rules_configured": audit_rules_configured,
            "status": "Aktiviert" if (auditd_installed and (auditd_running or auditd_active)) else "Nicht aktiviert",
        }
    except Exception as e:
        config["audit_logging"] = {
            "installed": False,
            "running": False,
            "enabled": False,
            "rules_configured": False,
            "status": f"Fehler: {str(e)}",
        }
    
    return config

# ==================== Endpoints ====================

@app.get("/health")
async def health_check():
    """Health Check"""
    return {"status": "ok"}

@app.get("/api/status")
async def get_status(request: Request):
    """System-Status abrufen"""
    try:
        net = _demo_network() if _is_demo_mode(request) else get_network_info()
        return {
            "status": "healthy",
            "hostname": net["hostname"],
            "version": "1.0.0",
            "network": net,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/system-info")
async def get_system_info(request: Request, light: bool = False):
    """Systeminfo auslesen. light=True: minimaler Satz für Polling (weniger CPU auf Pi). X-Demo-Mode: 1 ersetzt sensible Daten durch Platzhalter."""
    try:
        # light-Modus: kurzes interval (0.2s) für aktuelle Werte, ohne 1s zu blockieren. Sonst: 1s.
        cpu_interval = 0.2 if light else 1
        per_cpu_percent = psutil.cpu_percent(interval=cpu_interval, percpu=True)
        cpu_percent = sum(per_cpu_percent) / len(per_cpu_percent) if per_cpu_percent else 0
        per_core_usage, physical_cores = (([], 0) if light else get_per_core_usage(per_cpu_percent))
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        disk_mountpoint = '/'
        disk_partition = ''
        for p in psutil.disk_partitions(all=False):
            if p.mountpoint == '/':
                disk_partition = p.device.rstrip('/').split('/')[-1] or p.device
                break
        
        # Uptime
        with open('/proc/uptime', 'r') as f:
            uptime_seconds = float(f.readline().split()[0])
            hours = int(uptime_seconds // 3600)
            minutes = int((uptime_seconds % 3600) // 60)
            uptime = f"{hours}h {minutes}m"
        
        # CPU Temperatur: light nur schneller sysfs-Lese, sonst voller Weg
        cpu_temp = None
        temp_debug = None
        if light:
            try:
                with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
                    cpu_temp = round(int(f.read().strip()) / 1000.0, 1)
            except Exception:
                pass
        else:
            cpu_temp = get_cpu_temp()
            try:
                import subprocess
                temp_test = subprocess.run("cat /sys/class/thermal/thermal_zone0/temp 2>/dev/null", shell=True, capture_output=True, text=True)
                if temp_test.returncode == 0:
                    temp_debug = int(temp_test.stdout.strip()) / 1000.0
            except Exception:
                pass
        fan_speed = None if light else get_fan_speed()
        
        fan_debug = None
        # Linux-Version (light: minimal)
        os_info = {}
        try:
            # /etc/os-release lesen
            with open('/etc/os-release', 'r') as f:
                for line in f:
                    if '=' in line:
                        key, value = line.strip().split('=', 1)
                        value = value.strip('"')
                        os_info[key.lower()] = value
            
            # Kernel-Version
            kernel_result = run_command("uname -r")
            os_info["kernel"] = kernel_result.get("stdout", "").strip() if kernel_result["success"] else "Unbekannt"
        except:
            os_info = {"name": "Unbekannt", "version": "Unbekannt", "kernel": "Unbekannt"}
        
        resp = {
            "os": {
                "name": os_info.get("pretty_name", os_info.get("name", "Linux")),
                "version": os_info.get("version_id", os_info.get("version", "")),
                "kernel": os_info.get("kernel", "Unbekannt"),
            },
            "cpu": {
                "usage": cpu_percent,
                "per_cpu_usage": per_cpu_percent,
                "per_core_usage": per_core_usage,
                "physical_cores": physical_cores,
                "count": psutil.cpu_count(),
                "thread_count": psutil.cpu_count(),
                "temperature": cpu_temp or temp_debug,
                "fan_speed": fan_speed,
                "temp_debug": temp_debug,
            },
            "memory": {
                "total": memory.total,
                "available": memory.available,
                "percent": memory.percent,
            },
            "disk": {
                "total": disk.total,
                "used": disk.used,
                "free": disk.free,
                "percent": disk.percent,
                "mountpoint": disk_mountpoint,
                "partition": disk_partition,
            },
            "platform": {
                "system": os.uname().sysname,
                "release": os.uname().release,
            },
            "uptime": uptime,
        }
        if light:
            return resp
        resp["is_raspberry_pi"] = False
        resp["device_type"] = None
        try:
            chassis_path = Path("/sys/class/dmi/id/chassis_type")
            if chassis_path.exists():
                try:
                    ct = chassis_path.read_text().strip()
                    if ct == "3":
                        resp["device_type"] = "desktop"
                    elif ct in ("8", "9", "10", "14"):
                        resp["device_type"] = "laptop"
                except Exception:
                    pass
        except Exception:
            pass
        try:
            pi_mod = _get_pi_config_module()
            pi_info = pi_mod.get_system_info()
            if pi_info.get("status") == "success" and pi_info.get("system_info"):
                si = pi_info["system_info"]
                resp["hardware"] = {
                    "cpus": si.get("cpus") or [],
                    "gpus": si.get("gpus") or [],
                }
                cpu_model = (si.get("cpu_model") or "").lower()
                gpus = si.get("gpus") or []
                if "raspberry" in cpu_model or "bcm27" in cpu_model:
                    resp["is_raspberry_pi"] = True
                elif gpus and len(gpus) > 0:
                    if "videocore" in (gpus[0].get("name") or "").lower():
                        resp["is_raspberry_pi"] = True
            else:
                resp["hardware"] = {"cpus": [], "gpus": []}
        except Exception:
            resp["hardware"] = {"cpus": [], "gpus": []}
        # Fallback Pi-Erkennung: Device-Tree-Model prüfen (funktioniert auch wenn Pi-Modul fehlschlägt)
        if not resp.get("is_raspberry_pi"):
            for model_path in ("/proc/device-tree/model", "/sys/firmware/devicetree/base/model"):
                try:
                    if Path(model_path).exists():
                        model = Path(model_path).read_bytes().decode("utf-8", errors="ignore").rstrip("\x00").lower()
                        if "raspberry" in model:
                            resp["is_raspberry_pi"] = True
                            break
                except Exception:
                    pass
        # Auf Nicht-Pi immer lspci/nvidia-smi für alle GPUs (iGPU + NVIDIA/AMD), auf Pi bleibt VideoCore vom Modul
        if not resp.get("is_raspberry_pi"):
            resp["hardware"]["gpus"] = _get_gpus_for_system_info()
        cpu_name = get_cpu_name()
        if cpu_name:
            resp["cpu_name"] = cpu_name
        cpu_summary = get_cpu_summary()
        cpu_summary["name"] = cpu_summary.get("name") or cpu_name
        if resp.get("cpu", {}).get("physical_cores") is not None:
            cpu_summary["cores"] = cpu_summary["cores"] or resp["cpu"]["physical_cores"]
        if resp.get("cpu", {}).get("count") is not None:
            cpu_summary["threads"] = cpu_summary["threads"] or resp["cpu"]["count"]
        resp["cpu_summary"] = cpu_summary
        # Ein CPU-Eintrag für Anzeige (keine Liste aller Threads)
        if not resp.get("hardware", {}).get("cpus") and cpu_name:
            resp["hardware"]["cpus"] = [{"model": cpu_name, "processor_id": 0}]
        elif resp.get("hardware", {}).get("cpus") and len(resp["hardware"]["cpus"]) > 1:
            first_model = (resp["hardware"]["cpus"][0].get("model") or cpu_name or "CPU")
            resp["hardware"]["cpus"] = [{"model": first_model, "processor_id": 0}]
        resp["motherboard"] = get_motherboard_info()
        resp["ram_info"] = get_ram_info()
        # Hersteller-Treiber-TIP: Was bieten NVIDIA/AMD/Intel-Treiber mehr als integrierte?
        gpu_names = " ".join([(g.get("name") or g.get("display_name") or "") for g in resp.get("hardware", {}).get("gpus", [])]).lower()
        cpu_name_lower = (resp.get("cpu_name") or "").lower()
        tips = []
        if "nvidia" in gpu_names:
            tips.append("NVIDIA: Hersteller-Treiber bieten bessere Raytracing-, CUDA- und AI-Unterstützung; bei neueren GPUs oft Open-Source-Kernel + proprietäre Userspace-Komponenten.")
        if "amd" in gpu_names or "radeon" in gpu_names:
            tips.append("AMD: Unter Linux meist Open-Source (Mesa/amdgpu) ausreichend; Hersteller-Seite für Profi-Software und neueste Features.")
        if "intel" in gpu_names or ("intel" in cpu_name_lower and not tips):
            tips.append("Intel: Mesa-Treiber oft ausreichend; Hersteller für neueste Medien-/Encode-Features.")
        resp["manufacturer_driver_tip"] = " ".join(tips) if tips else None
        # Alle Sensoren, Laufwerke, Lüfter, Displays (nach Neustart vollständig sichtbar)
        try:
            resp["sensors"] = get_all_thermal_sensors()
            resp["disks"] = get_all_disks()
            resp["fans"] = get_all_fans()
            resp["displays"] = get_all_displays()
        except Exception:
            resp["sensors"] = []
            resp["disks"] = []
            resp["fans"] = []
            resp["displays"] = []
        try:
            pci_list = _get_pci_with_drivers()
            def _device_display(description: str) -> str:
                if not description:
                    return description or ""
                d = (description or "").lower()
                # Nur bei Grafik-Controller kurze Handelsbezeichnung; NVIDIA-Audio nicht bereinigen
                is_gpu = "vga" in d or "3d" in d or ("display" in d and ("nvidia" in d or "amd" in d or "intel" in d or "radeon" in d))
                if is_gpu and not ("nvidia" in d and "audio" in d):
                    return _clean_gpu_description(description)
                return description
            resp["drivers"] = [{"device": _device_display(p.get("description") or ""), "driver": p.get("driver") or "—"} for p in pci_list]
        except Exception:
            resp["drivers"] = []
        resp["network"] = _demo_network() if _is_demo_mode(request) else get_network_info()
        if _is_demo_mode(request):
            resp["is_raspberry_pi"] = True  # Für Screenshots: Pi-spezifische Seiten anzeigen
        return resp
    except Exception as e:
        return {"error": str(e)}


@app.get("/api/dashboard/services-status")
async def dashboard_services_status():
    """Aggregierter Status für Dashboard: DEV, Webserver, Musikbox (Installation + Grundbetrieb)."""
    try:
        installed = get_installed_apps()
        running = get_running_services()
        # DEV: wie viele Teile installiert, Grundbetrieb (Compiler/IDE lauffähig)
        dev_parts = ["python", "nodejs", "git", "docker", "cursor"]
        dev_installed = sum(1 for p in dev_parts if installed.get(p, False))
        dev_basic_ok = installed.get("python", False) or installed.get("nodejs", False)
        # Webserver: läuft, Webseiten erreichbar (Port 80/443 offen)
        webserver_running = running.get("nginx", False) or running.get("apache2", False)
        ports = run_command("ss -tuln 2>/dev/null | grep -E ':80 |:443 '")
        webserver_reachable = ports.get("success") and bool((ports.get("stdout") or "").strip())
        # Musikbox: Installationsstand + Grundbetrieb (Mopidy läuft oder Plex/Volumio)
        mopidy_ok = installed.get("mopidy", False) and running.get("mopidy", False)
        musicbox_installed = installed.get("mopidy", False) or installed.get("volumio", False) or installed.get("plex", False)
        musicbox_basic_ok = mopidy_ok or running.get("volumio", False) or running.get("plexmediaserver", False)
        return {
            "dev": {
                "installed_count": dev_installed,
                "total_parts": len(dev_parts),
                "basic_ok": dev_basic_ok,
            },
            "webserver": {
                "running": webserver_running,
                "reachable": webserver_reachable or webserver_running,
            },
            "musicbox": {
                "installed": musicbox_installed,
                "basic_ok": musicbox_basic_ok,
            },
        }
    except Exception as e:
        return {"dev": {"installed_count": 0, "total_parts": 5, "basic_ok": False}, "webserver": {"running": False, "reachable": False}, "musicbox": {"installed": False, "basic_ok": False}, "error": str(e)}


@app.get("/api/system/resources")
async def get_system_resources():
    """Ressourcen-Management (Milestone 3): RAM, Swap, Temperatur für Pi-Optimierung und App-Store-Hinweise."""
    try:
        cpu_percent = psutil.cpu_percent(interval=0.2)
        memory = psutil.virtual_memory()
        swap = psutil.swap_memory()
        ram_total_gb = round(memory.total / (1024 ** 3), 1)
        ram_available_gb = round(memory.available / (1024 ** 3), 1)
        swap_total_mb = round(swap.total / (1024 ** 2), 0)
        swap_used_mb = round(swap.used / (1024 ** 2), 0)
        cpu_temp = None
        try:
            with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
                cpu_temp = round(int(f.read().strip()) / 1000.0, 1)
        except Exception:
            cpu_temp = get_cpu_temp()
        temperature_warning = cpu_temp is not None and cpu_temp >= 80
        swap_recommended = ram_total_gb < 2
        return {
            "status": "success",
            "cpu": cpu_percent,
            "ram_total_gb": ram_total_gb,
            "ram_available_gb": ram_available_gb,
            "ram_percent": memory.percent,
            "swap_total_mb": swap_total_mb,
            "swap_used_mb": swap_used_mb,
            "swap_percent": round(swap.percent, 1) if swap.total else 0,
            "temperature_c": cpu_temp,
            "temperature_warning": temperature_warning,
            "swap_recommended": swap_recommended,
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


# ==================== Benutzer Endpoints ====================

def _parse_passwd_lines(lines: list) -> tuple:
    """Parst getent-/etc/passwd-Zeilen; gibt (system_users, human_users) zurück."""
    system_users = []
    human_users = []
    for line in lines:
        line = line.strip().strip("\r")
        if not line or line.startswith("#"):
            continue
        parts = line.split(":")
        if len(parts) < 3:
            continue
        name = parts[0].strip()
        try:
            uid = int(parts[2])
        except (ValueError, IndexError):
            continue
        entry = {"name": name, "uid": uid}
        if uid < 1000:
            system_users.append(entry)
        else:
            human_users.append(entry)
    system_users.sort(key=lambda x: x["name"].lower())
    human_users.sort(key=lambda x: x["name"].lower())
    return system_users, human_users


@app.get("/api/users")
async def list_users(request: Request):
    """Alle Benutzer auflisten, getrennt in Systembenutzer/Dienste (UID < 1000) und Benutzer (Personen, UID >= 1000)."""
    try:
        if _is_demo_mode(request):
            d = _demo_users()
            su, hu = d["system_users"], d["human_users"]
            return {
                "status": "success",
                "system_users": su,
                "human_users": hu,
                "users": [u["name"] for u in su] + [u["name"] for u in hu],
                "count": len(su) + len(hu),
            }
        lines = []
        result = run_command("getent passwd")
        if result.get("success") and result.get("stdout"):
            lines = (result["stdout"] or "").strip().replace("\r\n", "\n").split("\n")
        if not lines:
            try:
                passwd_path = Path("/etc/passwd")
                if passwd_path.exists():
                    lines = passwd_path.read_text(encoding="utf-8", errors="ignore").strip().split("\n")
            except Exception:
                pass
        system_users, human_users = _parse_passwd_lines(lines)
        return {
            "status": "success",
            "system_users": system_users,
            "human_users": human_users,
            "users": [u["name"] for u in system_users] + [u["name"] for u in human_users],
            "count": len(system_users) + len(human_users),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/users/sudo-password/check")
async def check_sudo_password():
    """Prüft ob ein sudo-Passwort gespeichert ist"""
    has_password = bool(sudo_password_store.get("password", ""))
    return {
        "status": "success",
        "has_password": has_password,
        "message": "Sudo-Passwort gespeichert" if has_password else "Kein sudo-Passwort gespeichert"
    }

@app.post("/api/users/sudo-password")
async def save_sudo_password(request: Request):
    """Sudo-Passwort für Session speichern"""
    logger.info("save_sudo_password: Request empfangen")
    try:
        try:
            data = await request.json()
        except Exception:
            logger.warning("save_sudo_password: Ungültiges JSON")
            return JSONResponse(
                status_code=200,
                content={"status": "error", "message": "Ungültige Anfrage (JSON fehlt oder fehlerhaft)."},
            )
        data = data or {}
        sudo_password = (data.get("sudo_password") or "").strip()
        skip_test = bool(data.get("skip_test"))
        
        if not sudo_password:
            return JSONResponse(
                status_code=200,
                content={"status": "error", "message": "Passwort erforderlich"},
            )
        
        if skip_test:
            sudo_password_store["password"] = sudo_password
            logger.info("save_sudo_password: Gespeichert ohne Prüfung (skip_test=True)")
            return {"status": "success", "message": "Sudo-Passwort gespeichert"}
        
        # Test ob Passwort funktioniert (/usr/bin/true, kein PATH nötig)
        test_result = run_command("/usr/bin/true", sudo=True, sudo_password=sudo_password, timeout=15)
        ok = test_result.get("success", False)
        if not ok:
            err = (
                (test_result.get("stderr") or "").strip()
                + " "
                + (test_result.get("stdout") or "").strip()
                + " "
                + (test_result.get("error") or "").strip()
            ).strip() or "(keine Details)"
            err_lower = err.lower()
            if "timeout" in err_lower or "timed out" in err_lower:
                logger.warning("save_sudo_password: Sudo-Test Timeout")
                return JSONResponse(
                    status_code=200,
                    content={"status": "error", "message": "Sudo-Test hat zu lange gedauert. Bitte erneut versuchen oder „Ohne Prüfung speichern“ wählen."},
                )
            if "sorry" in err_lower or "incorrect" in err_lower or "failed" in err_lower or "incorrect password" in err_lower:
                logger.info("save_sudo_password: Sudo-Test fehlgeschlagen (Passwort falsch/ungültig)")
                return JSONResponse(
                    status_code=200,
                    content={"status": "error", "message": "Sudo-Passwort falsch oder ungültig."},
                )
            logger.warning("save_sudo_password: Sudo-Test fehlgeschlagen err=%s", err[:300])
            return JSONResponse(
                status_code=200,
                content={
                    "status": "error",
                    "message": "Sudo-Test fehlgeschlagen. Prüfen Sie Passwort und sudo-Rechte. Alternativ „Ohne Prüfung speichern“ wählen.",
                },
            )
        
        sudo_password_store["password"] = sudo_password
        logger.info("save_sudo_password: Sudo-Passwort gespeichert (Session)")
        return {"status": "success", "message": "Sudo-Passwort gespeichert"}
    except Exception as e:
        logger.exception("save_sudo_password failed")
        return JSONResponse(
            status_code=200,
            content={"status": "error", "message": str(e) or "Fehler beim Speichern des sudo-Passworts."},
        )

@app.post("/api/users/create")
async def create_user(request: Request):
    """Neuen Benutzer erstellen"""
    try:
        try:
            data = await request.json()
        except:
            return JSONResponse(
                status_code=200,
                content={
                    "status": "error",
                    "message": "Ungültige Anfrage"
                }
            )
        
        username = data.get("username", "").strip()
        role = data.get("role", "user")
        password = data.get("password", "")
        sudo_password = data.get("sudo_password", "") or sudo_password_store.get("password", "")
        
        if not username:
            return JSONResponse(
                status_code=200,
                content={
                    "status": "error",
                    "message": "Username erforderlich"
                }
            )
        
        # Benutzer existiert bereits?
        check = run_command(f"id {username}")
        if check["success"]:
            return JSONResponse(
                status_code=200,
                content={
                    "status": "error",
                    "message": f"Benutzer {username} existiert bereits"
                }
            )
        
        # Prüfe ob sudo ohne Passwort funktioniert ODER Passwort vorhanden
        if not sudo_password:
            sudo_test = run_command("sudo -n true", sudo=False)
            if not sudo_test["success"]:
                return JSONResponse(
                    status_code=200,
                    content={
                        "status": "error",
                        "message": "Sudo-Passwort erforderlich. Bitte geben Sie das sudo-Passwort im Frontend ein.",
                        "requires_sudo_password": True
                    }
                )
        
        # Benutzer erstellen mit sudo_password
        result = run_command(f"useradd -m -s /bin/bash {username}", sudo=True, sudo_password=sudo_password)
        if not result["success"]:
            error_msg = result.get("stderr", result.get("error", "Unbekannter Fehler"))
            if "password" in error_msg.lower() or "authentication" in error_msg.lower() or "sudo" in error_msg.lower():
                return JSONResponse(
                    status_code=200,
                    content={
                        "status": "error",
                        "message": "Sudo-Passwort falsch oder erforderlich",
                        "requires_sudo_password": True
                    }
                )
            return JSONResponse(
                status_code=200,
                content={
                    "status": "error",
                    "message": f"Benutzer konnte nicht erstellt werden: {error_msg}"
                }
            )
        
        # Passwort setzen
        if not password:
            password = "ChangeMe123!"
        
        # chpasswd sicherer verwenden - direkt über stdin
        try:
            import subprocess
            chpasswd_cmd = subprocess.Popen(
                ['sudo', '-S', 'chpasswd'],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            chpasswd_input = f"{sudo_password}\n{username}:{password}\n"
            stdout, stderr = chpasswd_cmd.communicate(input=chpasswd_input, timeout=5)
            
            if chpasswd_cmd.returncode != 0:
                return JSONResponse(
                    status_code=200,
                    content={
                        "status": "error",
                        "message": f"Passwort konnte nicht gesetzt werden: {stderr}"
                    }
                )
        except Exception as e:
            return JSONResponse(
                status_code=200,
                content={
                    "status": "error",
                    "message": f"Passwort konnte nicht gesetzt werden: {str(e)}"
                }
            )
        
        # Gruppen hinzufügen
        if role == "admin":
            run_command(f"usermod -aG sudo {username}", sudo=True, sudo_password=sudo_password)
        
        return {
            "status": "success",
            "message": f"Benutzer {username} erstellt",
            "user": {
                "username": username,
                "role": role,
                "password": password,
            }
        }
    except Exception as e:
        return JSONResponse(
            status_code=200,
            content={
                "status": "error",
                "message": str(e)
            }
        )

@app.delete("/api/users/{username}")
async def delete_user(username: str, request: Request):
    """Benutzer löschen"""
    try:
        try:
            data = await request.json()
        except:
            data = {}
        
        sudo_password = data.get("sudo_password", "") or sudo_password_store.get("password", "")
        
        if not username or not username.strip():
            return JSONResponse(
                status_code=200,
                content={
                    "status": "error",
                    "message": "Username erforderlich"
                }
            )
        
        username = username.strip()
        
        # Prüfe ob Benutzer existiert
        check = run_command(f"id {username}")
        if not check["success"]:
            return JSONResponse(
                status_code=200,
                content={
                    "status": "error",
                    "message": f"Benutzer {username} existiert nicht"
                }
            )
        # Systembenutzer (UID < 1000) nicht löschen
        uid_result = run_command(f"id -u {username}")
        if uid_result.get("success"):
            try:
                uid = int((uid_result.get("stdout") or "").strip())
                if uid < 1000:
                    return JSONResponse(
                        status_code=200,
                        content={
                            "status": "error",
                            "message": "Systembenutzer/Dienste (UID < 1000) dürfen nicht gelöscht werden."
                        }
                    )
            except (ValueError, TypeError):
                pass

        # Prüfe ob sudo-Passwort vorhanden ist
        if not sudo_password:
            sudo_test = run_command("sudo -n true", sudo=False)
            if not sudo_test["success"]:
                return JSONResponse(
                    status_code=200,
                    content={
                        "status": "error",
                        "message": "Sudo-Passwort erforderlich",
                        "requires_sudo_password": True
                    }
                )
        
        # Benutzer löschen (mit Home-Verzeichnis)
        result = run_command(f"userdel -r {username}", sudo=True, sudo_password=sudo_password)
        
        if not result["success"]:
            error_msg = result.get("stderr", result.get("error", "Unbekannter Fehler"))
            if "password" in error_msg.lower() or "authentication" in error_msg.lower() or "sudo" in error_msg.lower():
                return JSONResponse(
                    status_code=200,
                    content={
                        "status": "error",
                        "message": "Sudo-Passwort falsch oder erforderlich",
                        "requires_sudo_password": True
                    }
                )
            return JSONResponse(
                status_code=200,
                content={
                    "status": "error",
                    "message": f"Benutzer konnte nicht gelöscht werden: {error_msg}"
                }
            )
        
        return {
            "status": "success",
            "message": f"Benutzer {username} gelöscht"
        }
    except Exception as e:
        return JSONResponse(
            status_code=200,
            content={
                "status": "error",
                "message": str(e)
            }
        )

# ==================== Sicherheit Endpoints ====================

@app.post("/api/security/scan")
async def security_scan():
    """Sicherheits-Scan durchführen"""
    try:
        running_services = get_running_services()
        installed_apps = get_installed_apps()
        
        # Prüfe offene Ports
        ports_result = run_command("ss -tuln | grep LISTEN")
        open_ports = []
        if ports_result["success"]:
            for line in ports_result["stdout"].split("\n"):
                if line.strip():
                    # Parse Port aus Zeile
                    parts = line.split()
                    if len(parts) >= 5:
                        addr = parts[4]
                        if ":" in addr:
                            port = addr.split(":")[-1]
                            open_ports.append(port)
        
        # Prüfe geschlossene Ports (UFW) - verwende die gleiche Logik wie get_security_config()
        ufw_status = run_command("ufw status")
        if not ufw_status["success"] and sudo_password_store.get("password"):
            ufw_status = run_command("ufw status", sudo=True, sudo_password=sudo_password_store.get("password"))
        
        # Falls immer noch nicht erfolgreich, versuche "ufw status verbose" mit sudo
        if not ufw_status["success"] and sudo_password_store.get("password"):
            ufw_status = run_command("ufw status verbose", sudo=True, sudo_password=sudo_password_store.get("password"))
        
        closed_ports = []
        firewall_active = False
        status_output = ""
        
        if ufw_status["success"]:
            status_output = ufw_status.get("stdout", "")
            if "Status: active" in status_output or "Status: aktiv" in status_output:
                firewall_active = True
                # Parse UFW Rules
                for line in status_output.split("\n"):
                    if "DENY" in line or "REJECT" in line:
                        closed_ports.append(line.strip())
        else:
            # Alternative Methoden wie in get_security_config()
            # Prüfe UFW-Konfigurationsdatei
            try:
                ufw_config_check = run_command("grep -E '^ENABLED=' /etc/ufw/ufw.conf 2>/dev/null")
                if ufw_config_check["success"]:
                    config_line = ufw_config_check.get("stdout", "").strip()
                    if "ENABLED=yes" in config_line:
                        firewall_active = True
                        status_output = "Status: active (via /etc/ufw/ufw.conf)"
            except:
                pass
            
            # Prüfe systemd-Status
            if not firewall_active:
                systemd_status = run_command("systemctl is-active ufw 2>/dev/null")
                if systemd_status["success"] and "active" in systemd_status.get("stdout", ""):
                    firewall_active = True
                    status_output = "Status: active (via systemctl)"
                else:
                    ufw_enabled = run_command("systemctl is-enabled ufw 2>/dev/null")
                    if ufw_enabled["success"] and "enabled" in ufw_enabled.get("stdout", ""):
                        firewall_active = True
                        status_output = "Status: active (wahrscheinlich, service enabled)"
        
        # Prüfe fail2ban Status & Installation
        fail2ban_status = run_command("fail2ban-client status")
        fail2ban_installed = check_installed("fail2ban")
        fail2ban_running = running_services.get("fail2ban", False)
        
        # Updates kategorisieren
        updates_info = get_updates_categorized()
        
        return {
            "status": "success",
            "timestamp": __import__("datetime").datetime.now().isoformat(),
            "running_services": running_services,
            "installed_packages": installed_apps,
            "open_ports": list(set(open_ports))[:20],  # Unique Ports
            "closed_ports": closed_ports[:10],
            "firewall": {
                "active": firewall_active,
                "ufw_installed": check_installed("ufw"),
                "ufw_status": ufw_status.get("stdout", "") if ufw_status["success"] else "Nicht aktiv",
            },
            "fail2ban": {
                "installed": fail2ban_installed,
                "running": fail2ban_running,
                "active": fail2ban_installed and fail2ban_running,
                "status": fail2ban_status.get("stdout", "Nicht aktiv") if fail2ban_status["success"] else "Nicht installiert",
            },
            "updates": updates_info,
            "checks": {
                "firewall": {
                    "active": firewall_active,
                    "ufw_installed": check_installed("ufw"),
                },
                "ssh": {
                    "running": running_services.get("sshd", False),
                    "installed": check_installed("ssh"),
                },
                "nginx": {
                    "running": running_services.get("nginx", False),
                    "installed": installed_apps.get("nginx", False),
                },
                "apache": {
                    "running": running_services.get("apache2", False),
                    "installed": installed_apps.get("apache", False),
                },
                "fail2ban": {
                    "installed": fail2ban_installed,
                    "running": fail2ban_running,
                    "active": fail2ban_installed and fail2ban_running,
                },
                "updates_available": updates_info["total"] > 0,
            },
            "message": "Scan abgeschlossen"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/security/status")
async def security_status():
    """Sicherheitsstatus"""
    try:
        return {
            "running_services": get_running_services(),
            "installed_apps": get_installed_apps(),
            "security_config": get_security_config(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/system/installed-packages")
async def get_installed_packages():
    """Installierte Pakete mit Details"""
    try:
        return {
            "status": "success",
            "packages": _get_installed_packages_list(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/system/running-processes")
async def get_running_processes():
    """Laufende Prozesse"""
    try:
        return {
            "status": "success",
            "processes": get_running_processes(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/system/security-config")
async def get_security_config_endpoint(request: Request):
    """Sicherheitseinstellungen"""
    try:
        # Prüfe ob sudo-Passwort als Query-Parameter übergeben wurde
        sudo_password = request.query_params.get("sudo_password", "")
        if sudo_password and not sudo_password_store.get("password"):
            sudo_password_store["password"] = sudo_password
            logger.info("💾 Sudo-Passwort im Store gespeichert (via security-config endpoint)")
        
        return {
            "status": "success",
            "config": get_security_config(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/system/updates")
async def get_system_updates():
    """Verfügbare System-Updates (für Dashboard-Anzeige)"""
    try:
        data = get_updates_categorized()
        return {
            "status": "success",
            "total": data["total"],
            "categories": data["categories"],
            "updates": data["updates"],
        }
    except Exception as e:
        return {
            "status": "error",
            "total": 0,
            "categories": {"security": 0, "critical": 0, "necessary": 0, "optional": 0},
            "updates": [],
            "message": str(e),
        }


def _open_terminal_with_command(shell_cmd: str) -> tuple[bool, str]:
    """Öffnet ein Terminal-Fenster und führt den Befehl aus. Passwort gibt der Benutzer im Terminal ein.
    Gibt (success, message) zurück."""
    import shutil
    wrapped = f"{shell_cmd}; echo ''; read -p 'Drücke Enter zum Schließen' dummy; exit 0"
    env = os.environ.copy()
    # Erweiterte Liste: GNOME, XFCE, KDE, MATE, LXDE, Kitty, Alacritty, QTerminal, Tilix
    for term_cmd, term_args in [
        ("gnome-terminal", ["--", "bash", "-c", wrapped]),
        ("gnome-terminal.wrapper", ["--", "bash", "-c", wrapped]),
        ("xfce4-terminal", ["-e", f"bash -c {shlex.quote(wrapped)}"]),
        ("konsole", ["-e", "bash", "-c", wrapped]),
        ("xterm", ["-e", f"bash -c {shlex.quote(wrapped)}"]),
        ("mate-terminal", ["--", "bash", "-c", wrapped]),
        ("lxterminal", ["-e", f"bash -c {shlex.quote(wrapped)}"]),
        ("kitty", ["bash", "-c", wrapped]),
        ("alacritty", ["-e", "bash", "-c", wrapped]),
        ("qterminal", ["-e", f"bash -c {shlex.quote(wrapped)}"]),
        ("tilix", ["-e", f"bash -c {shlex.quote(wrapped)}"]),
        ("urxvt", ["-e", "bash", "-c", wrapped]),
    ]:
        path = shutil.which(term_cmd)
        if path:
            try:
                subprocess.Popen(
                    [path] + term_args,
                    env=env,
                    start_new_session=True,
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                return True, f"Terminal geöffnet ({term_cmd}). Passwort im Fenster eingeben."
            except Exception as e:
                logger.warning(f"Terminal starten ({term_cmd}) fehlgeschlagen: {e}")
    return False, (
        "Kein Terminal gefunden. Bitte manuell ein Terminal öffnen und ausführen: "
        f"{shell_cmd}"
    )


@app.post("/api/system/run-update-in-terminal")
async def run_update_in_terminal():
    """Öffnet ein Terminal-Fenster mit 'sudo apt update && sudo apt upgrade'.
    Der Benutzer gibt das Passwort im geöffneten Terminal ein. Bei fehlendem Terminal: copyable_command für manuelles Ausführen."""
    try:
        cmd = "sudo apt update && sudo apt upgrade"
        success, msg = _open_terminal_with_command(cmd)
        if success:
            return {"status": "success", "message": msg, "copyable_command": cmd}
        return JSONResponse(
            status_code=200,
            content={"status": "error", "message": msg, "copyable_command": cmd}
        )
    except Exception as e:
        logger.exception("run-update-in-terminal fehlgeschlagen")
        return JSONResponse(status_code=200, content={"status": "error", "message": str(e)})


@app.get("/api/system/terminal-available")
async def check_terminal_available():
    """Prüft, ob ein Terminal zum Öffnen verfügbar ist (für Anzeige des Buttons)."""
    import shutil
    for name in ["gnome-terminal", "gnome-terminal.wrapper", "xfce4-terminal", "konsole", "xterm", "mate-terminal", "lxterminal"]:
        if shutil.which(name):
            return {"available": True, "terminal": name}
    return {"available": False, "terminal": None}


ALLOWED_MIXER_APPS = ("pavucontrol", "qpwgraph")


@app.post("/api/system/run-mixer")
async def run_mixer(request: Request):
    """Startet einen grafischen Mixer (pavucontrol oder qpwgraph) im Hintergrund.
    Läuft auf dem Rechner, auf dem das Backend läuft – bei lokalem Zugriff öffnet sich das Fenster dort."""
    try:
        data = await request.json() if request.headers.get("content-type", "").startswith("application/json") else {}
        app_name = (data.get("app") or "").strip().lower()
        if app_name not in ALLOWED_MIXER_APPS:
            return JSONResponse(
                status_code=200,
                content={"status": "error", "message": f"Ungültige App. Erlaubt: {', '.join(ALLOWED_MIXER_APPS)}"}
            )
        import shutil
        path = shutil.which(app_name)
        if not path:
            return JSONResponse(
                status_code=200,
                content={"status": "error", "message": f"'{app_name}' nicht gefunden. Bitte installieren (z. B. apt install {app_name})."}
            )
        # GUI-Apps brauchen DISPLAY (Backend läuft oft ohne Grafik-Umgebung)
        env = dict(os.environ)
        if not env.get("DISPLAY"):
            env["DISPLAY"] = ":0"
        # GTK-A11y-Warnung unterdrücken (org.a11y.Bus nicht vorhanden)
        if app_name == "pavucontrol":
            env["GTK_A11Y"] = "none"
        subprocess.Popen(
            [path],
            start_new_session=True,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            env=env,
        )
        return {"status": "success", "message": f"{app_name} gestartet"}
    except Exception as e:
        logger.exception("run-mixer fehlgeschlagen")
        return JSONResponse(status_code=200, content={"status": "error", "message": str(e)})


def _run_apt_update(sudo_password: str) -> dict:
    """Führt apt-get update aus. Gibt dict mit success, stderr, stdout zurück."""
    cmd = "DEBIAN_FRONTEND=noninteractive apt-get update -qq"
    return run_command(cmd, sudo=True, sudo_password=sudo_password, timeout=120)


def _run_apt_install_mixer(sudo_password: str) -> dict:
    """Führt apt-get install -y pavucontrol qpwgraph aus. Gibt dict mit success, stderr, stdout zurück."""
    cmd = (
        "DEBIAN_FRONTEND=noninteractive apt-get install -y "
        "-o Dpkg::Options::=--force-confdef -o Dpkg::Options::=--force-confold "
        "pavucontrol qpwgraph"
    )
    return run_command(cmd, sudo=True, sudo_password=sudo_password, timeout=180)


@app.post("/api/system/install-mixer-packages")
async def install_mixer_packages(request: Request):
    """Installiert pavucontrol und qpwgraph (apt-get update, dann apt-get install). Benötigt sudo."""
    copyable = "sudo apt-get update && sudo apt-get install -y pavucontrol qpwgraph"
    try:
        data = await request.json() if request.headers.get("content-type", "").startswith("application/json") else {}
        sudo_password = (data.get("sudo_password", "") or sudo_password_store.get("password", "") or "").strip()
        if not sudo_password:
            return JSONResponse(
                status_code=200,
                content={
                    "status": "error",
                    "message": "Sudo-Passwort erforderlich.",
                    "requires_sudo_password": True,
                    "copyable_command": copyable,
                }
            )
        # Schritt 1: apt-get update
        result_update = _run_apt_update(sudo_password)
        if not result_update.get("success"):
            err = (result_update.get("stderr") or result_update.get("stdout") or result_update.get("error") or "").strip()
            if result_update.get("error") == "Command timeout":
                err = "Zeitüberschreitung beim Paketquellen-Update."
            elif not err:
                err = "apt-get update ist fehlgeschlagen (keine Ausgabe)."
            logger.warning("install-mixer-packages apt-get update fehlgeschlagen: %s", err[:400])
            return JSONResponse(
                status_code=200,
                content={
                    "status": "error",
                    "message": f"Paketquellen-Update fehlgeschlagen: {err[:500]}",
                    "copyable_command": copyable,
                }
            )
        # Schritt 2: apt-get install
        result_install = _run_apt_install_mixer(sudo_password)
        if result_install.get("success"):
            return {"status": "success", "message": "pavucontrol und qpwgraph installiert"}
        err = (result_install.get("stderr") or result_install.get("stdout") or result_install.get("error") or "").strip()
        if result_install.get("error") == "Command timeout":
            err = "Zeitüberschreitung bei der Installation."
        elif not err:
            err = "apt-get install ist fehlgeschlagen (keine Ausgabe)."
        logger.warning("install-mixer-packages apt-get install fehlgeschlagen: %s", err[:400])
        return JSONResponse(
            status_code=200,
            content={
                "status": "error",
                "message": err[:600],
                "copyable_command": copyable,
            }
        )
    except Exception as e:
        logger.exception("install-mixer-packages fehlgeschlagen")
        return JSONResponse(
            status_code=200,
            content={"status": "error", "message": str(e)[:500], "copyable_command": copyable}
        )


@app.post("/api/security/firewall/enable")
async def enable_firewall(request: Request):
    """Firewall aktivieren"""
    try:
        try:
            data = await request.json()
        except:
            data = {}
        
        sudo_password = data.get("sudo_password", "") or sudo_password_store.get("password", "")
        
        # Speichere sudo-Passwort im Store für spätere Verwendung
        if sudo_password and not sudo_password_store.get("password"):
            sudo_password_store["password"] = sudo_password
            logger.info("💾 Sudo-Passwort im Store gespeichert")
        
        logger.info("🔥 Firewall-Aktivierung gestartet")
        
        # Prüfe ob UFW verfügbar ist (mehrere Methoden)
        ufw_installed = check_installed("ufw")
        ufw_which = run_command("which ufw")
        ufw_dpkg = run_command("dpkg -l | grep '^ii' | grep -E '\\bufw\\b'")
        
        # Wenn keine Methode UFW findet, prüfe ob es installiert werden kann
        if not ufw_installed and not ufw_which["success"] and not ufw_dpkg["success"]:
            return JSONResponse(
                status_code=200,
                content={
                    "status": "error",
                    "message": "UFW ist nicht installiert. Bitte installieren Sie es zuerst mit: sudo apt install ufw",
                    "requires_installation": True,
                    "debug": {
                        "check_installed": ufw_installed,
                        "which_result": ufw_which.get("stdout", ""),
                        "dpkg_result": ufw_dpkg.get("stdout", "")
                    }
                }
            )
        
        # Prüfe ob sudo-Passwort vorhanden ist
        if not sudo_password:
            sudo_test = run_command("sudo -n true", sudo=False)
            if not sudo_test["success"]:
                return JSONResponse(
                    status_code=200,
                    content={
                        "status": "error",
                        "message": "Sudo-Passwort erforderlich",
                        "requires_sudo_password": True
                    }
                )
        
        # UFW aktivieren - versuche es direkt, auch wenn check_installed False war
        # Verwende absoluten Pfad falls which ufw funktioniert hat
        ufw_path = "/usr/sbin/ufw"
        if ufw_which["success"]:
            ufw_path = ufw_which["stdout"].strip()
        
        # UFW aktivieren - verwende explizit den absoluten Pfad
        logger.info(f"🔧 Versuche UFW zu aktivieren mit Pfad: {ufw_path}")
        result = run_command(f"{ufw_path} --force enable", sudo=True, sudo_password=sudo_password)
        logger.info(f"📊 Command Result: success={result.get('success')}, returncode={result.get('returncode')}, stdout={result.get('stdout', '')[:100]}, stderr={result.get('stderr', '')[:100]}")
        
        # Warte kurz, damit UFW den Status aktualisieren kann
        import time
        time.sleep(0.5)
        
        # Debug: Prüfe ob Command wirklich erfolgreich war
        # Prüfe den Status mit sudo (falls nötig)
        status_check = run_command(f"{ufw_path} status", sudo=False)
        # Falls ohne sudo nicht funktioniert, versuche mit sudo
        if not status_check["success"]:
            status_check = run_command(f"{ufw_path} status", sudo=True, sudo_password=sudo_password)
        
        status_output = status_check.get("stdout", "")
        is_actually_active = "Status: active" in status_output or "Status: aktiv" in status_output
        logger.info(f"📋 Status Check: success={status_check.get('success')}, is_active={is_actually_active}, output={status_output[:200]}")
        
        if not result["success"]:
            logger.error(f"❌ UFW Command fehlgeschlagen: {result.get('stderr', '')}")
            error_msg = result.get("stderr", result.get("error", "Unbekannter Fehler"))
            stdout_msg = result.get("stdout", "")
            
            return JSONResponse(
                status_code=200,
                content={
                    "status": "error",
                    "message": f"UFW-Befehl fehlgeschlagen: {error_msg}",
                    "debug": {
                        "command_result": result,
                        "status_check": status_check,
                        "ufw_path": ufw_path,
                        "stdout": stdout_msg,
                        "stderr": error_msg,
                    }
                }
            )
        
        # Wenn der Command erfolgreich war, aber Status nicht aktiv ist
        if result["success"] and not is_actually_active:
            logger.warning("⚠️ Command erfolgreich, aber Firewall nicht aktiv. Versuche Retry...")
            # Versuche es nochmal ohne --force
            retry_result = run_command(f"{ufw_path} enable", sudo=True, sudo_password=sudo_password)
            logger.info(f"🔄 Retry Result: success={retry_result.get('success')}, returncode={retry_result.get('returncode')}, stdout={retry_result.get('stdout', '')[:100]}, stderr={retry_result.get('stderr', '')[:100]}")
            time.sleep(0.5)
            
            # Prüfe Status nochmal
            status_check_retry = run_command(f"{ufw_path} status", sudo=False)
            if not status_check_retry["success"]:
                status_check_retry = run_command(f"{ufw_path} status", sudo=True, sudo_password=sudo_password)
            
            status_output_retry = status_check_retry.get("stdout", "")
            is_actually_active_retry = "Status: active" in status_output_retry or "Status: aktiv" in status_output_retry
            logger.info(f"📋 Retry Status Check: success={status_check_retry.get('success')}, is_active={is_actually_active_retry}, output={status_output_retry[:200]}")
            
            if not is_actually_active_retry:
                logger.error(f"❌ Firewall konnte auch nach Retry nicht aktiviert werden. Status: {status_output_retry[:200]}")
                return JSONResponse(
                    status_code=200,
                    content={
                        "status": "error",
                        "message": f"UFW-Befehl wurde ausgeführt, aber Firewall ist nicht aktiv. Status-Output: {status_output_retry[:200]}",
                        "debug": {
                            "command_result": result,
                            "retry_result": retry_result,
                            "status_check": status_check,
                            "status_check_retry": status_check_retry,
                            "ufw_path": ufw_path,
                            "is_active": is_actually_active_retry,
                        }
                    }
                )
            
            # Prüfe ob UFW wirklich nicht gefunden wurde
            if "nicht gefunden" in error_msg.lower() or "not found" in error_msg.lower() or "command not found" in error_msg.lower():
                return JSONResponse(
                    status_code=200,
                    content={
                        "status": "error",
                        "message": "UFW ist nicht installiert. Bitte installieren Sie es zuerst mit: sudo apt install ufw",
                        "requires_installation": True,
                        "debug": {
                            "error": error_msg,
                            "stdout": result.get("stdout", ""),
                            "stderr": result.get("stderr", "")
                        }
                    }
                )
            
            if "password" in error_msg.lower() or "authentication" in error_msg.lower() or "sudo" in error_msg.lower():
                return JSONResponse(
                    status_code=200,
                    content={
                        "status": "error",
                        "message": "Sudo-Passwort falsch oder erforderlich",
                        "requires_sudo_password": True
                    }
                )
            return JSONResponse(
                status_code=200,
                content={
                    "status": "error",
                    "message": f"Firewall konnte nicht aktiviert werden: {error_msg}",
                    "debug": {
                        "stdout": result.get("stdout", ""),
                        "stderr": result.get("stderr", "")
                    }
                }
            )
        
        # Status abrufen (kann fehlschlagen, aber das ist OK)
        # Verwende sudo für status verbose, falls nötig
        status_result = run_command(f"{ufw_path} status verbose", sudo=False)
        if not status_result["success"]:
            status_result = run_command(f"{ufw_path} status verbose", sudo=True, sudo_password=sudo_password)
        
        rules_result = run_command(f"{ufw_path} status numbered", sudo=False)
        if not rules_result["success"]:
            rules_result = run_command(f"{ufw_path} status numbered", sudo=True, sudo_password=sudo_password)
        
        # Erstelle Security-Config direkt aus dem erfolgreichen Status-Check
        # (nicht aus get_security_config(), da das möglicherweise den falschen Status zurückgibt)
        status_output = status_result.get("stdout", "") if status_result["success"] else ""
        is_active = "Status: active" in status_output or "Status: aktiv" in status_output or result["success"]
        
        # Hole die vollständige Security-Config, aber überschreibe UFW-Status mit dem korrekten Wert
        try:
            security_config = get_security_config()
            # Überschreibe UFW-Status mit dem korrekten Wert
            security_config["ufw"] = {
                "installed": True,
                "active": is_active,
                "status": status_output if status_result["success"] else "Aktiviert",
                "rules": status_output.split("\n") if status_result["success"] else [],
            }
        except Exception as config_error:
            logger.warning(f"⚠️ get_security_config() fehlgeschlagen, verwende direkte Config: {config_error}")
            # Wenn get_security_config fehlschlägt, verwende direkte Config
            security_config = {
                "ufw": {
                    "installed": True,
                    "active": is_active,
                    "status": status_output if status_result["success"] else "Aktiviert",
                    "rules": status_output.split("\n") if status_result["success"] else [],
                },
                "ssh": {"installed": False, "running": False, "config": ""},
                "fail2ban": {"installed": False, "running": False, "active": False, "status": "", "jails": []},
                "auto_updates": {"installed": False, "enabled": False},
            }
        
        logger.info(f"✅ Firewall erfolgreich aktiviert! Security-Config UFW active: {security_config['ufw']['active']}")
        return {
            "status": "success",
            "message": "Firewall aktiviert",
            "firewall_status": status_output if status_result["success"] else "Aktiviert",
            "firewall_rules": rules_result.get("stdout", "").split("\n") if rules_result["success"] else [],
            "security_config": security_config,
        }
    except Exception as e:
        logger.error(f"💥 Exception beim Aktivieren der Firewall: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=200,
            content={
                "status": "error",
                "message": f"Fehler beim Aktivieren der Firewall: {str(e)}"
            }
        )

@app.post("/api/security/firewall/install")
async def install_firewall(request: Request):
    """UFW Firewall installieren"""
    try:
        try:
            data = await request.json()
        except:
            data = {}
        
        sudo_password = data.get("sudo_password", "") or sudo_password_store.get("password", "")
        
        # Prüfe ob sudo-Passwort vorhanden ist
        if not sudo_password:
            sudo_test = run_command("sudo -n true", sudo=False)
            if not sudo_test["success"]:
                return JSONResponse(
                    status_code=200,
                    content={
                        "status": "error",
                        "message": "Sudo-Passwort erforderlich",
                        "requires_sudo_password": True
                    }
                )
        
        # UFW installieren
        result = run_command("apt-get install -y ufw", sudo=True, sudo_password=sudo_password)
        
        if not result["success"]:
            error_msg = result.get("stderr", result.get("error", "Unbekannter Fehler"))
            if "password" in error_msg.lower() or "authentication" in error_msg.lower() or "sudo" in error_msg.lower():
                return JSONResponse(
                    status_code=200,
                    content={
                        "status": "error",
                        "message": "Sudo-Passwort falsch oder erforderlich",
                        "requires_sudo_password": True
                    }
                )
            return JSONResponse(
                status_code=200,
                content={
                    "status": "error",
                    "message": f"UFW konnte nicht installiert werden: {error_msg}"
                }
            )
        
        return {
            "status": "success",
            "message": "UFW erfolgreich installiert"
        }
    except Exception as e:
        return JSONResponse(
            status_code=200,
            content={
                "status": "error",
                "message": str(e)
            }
        )

@app.get("/api/security/firewall/rules")
async def get_firewall_rules():
    """Firewall-Regeln abrufen"""
    try:
        sudo_password = sudo_password_store.get("password", "")
        
        # UFW Status mit Regeln abrufen
        ufw_path = "/usr/sbin/ufw"
        ufw_which = run_command("which ufw")
        if ufw_which["success"]:
            ufw_path = ufw_which["stdout"].strip()
        
        status_result = run_command(f"{ufw_path} status numbered")
        if not status_result["success"] and sudo_password:
            status_result = run_command(f"{ufw_path} status numbered", sudo=True, sudo_password=sudo_password)
        
        verbose_result = run_command(f"{ufw_path} status verbose")
        if not verbose_result["success"] and sudo_password:
            verbose_result = run_command(f"{ufw_path} status verbose", sudo=True, sudo_password=sudo_password)
        
        return {
            "status": "success",
            "rules": status_result.get("stdout", "") if status_result["success"] else "",
            "verbose": verbose_result.get("stdout", "") if verbose_result["success"] else "",
        }
    except Exception as e:
        return JSONResponse(
            status_code=200,
            content={
                "status": "error",
                "message": str(e)
            }
        )

@app.post("/api/security/firewall/rules/add")
async def add_firewall_rule(request: Request):
    """Firewall-Regel hinzufügen"""
    try:
        try:
            data = await request.json()
        except:
            data = {}
        
        sudo_password = data.get("sudo_password", "") or sudo_password_store.get("password", "")
        rule = data.get("rule", "").strip()
        
        if not rule:
            return JSONResponse(
                status_code=200,
                content={
                    "status": "error",
                    "message": "Regel erforderlich"
                }
            )
        
        if not sudo_password:
            sudo_test = run_command("sudo -n true", sudo=False)
            if not sudo_test["success"]:
                return JSONResponse(
                    status_code=200,
                    content={
                        "status": "error",
                        "message": "Sudo-Passwort erforderlich",
                        "requires_sudo_password": True
                    }
                )
        
        ufw_path = "/usr/sbin/ufw"
        ufw_which = run_command("which ufw")
        if ufw_which["success"]:
            ufw_path = ufw_which["stdout"].strip()
        
        # Die Regel kommt bereits als vollständiger UFW-Command (z.B. "allow 22/tcp")
        # Füge nur den ufw-Pfad hinzu
        cmd = f"{ufw_path} {rule}"
        result = run_command(cmd, sudo=True, sudo_password=sudo_password)
        
        if not result["success"]:
            error_msg = result.get("stderr", result.get("error", "Unbekannter Fehler"))
            return JSONResponse(
                status_code=200,
                content={
                    "status": "error",
                    "message": f"Regel konnte nicht hinzugefügt werden: {error_msg}"
                }
            )
        
        return {
            "status": "success",
            "message": "Regel hinzugefügt",
            "output": result.get("stdout", "")
        }
    except Exception as e:
        return JSONResponse(
            status_code=200,
            content={
                "status": "error",
                "message": str(e)
            }
        )

@app.delete("/api/security/firewall/rules/{rule_number}")
async def delete_firewall_rule(rule_number: int, request: Request):
    """Firewall-Regel löschen"""
    try:
        try:
            data = await request.json()
        except:
            data = {}
        
        sudo_password = data.get("sudo_password", "") or sudo_password_store.get("password", "")
        
        if not sudo_password:
            sudo_test = run_command("sudo -n true", sudo=False)
            if not sudo_test["success"]:
                return JSONResponse(
                    status_code=200,
                    content={
                        "status": "error",
                        "message": "Sudo-Passwort erforderlich",
                        "requires_sudo_password": True
                    }
                )
        
        ufw_path = "/usr/sbin/ufw"
        ufw_which = run_command("which ufw")
        if ufw_which["success"]:
            ufw_path = ufw_which["stdout"].strip()
        
        # UFW-Regel löschen: ufw delete <number>
        cmd = f"{ufw_path} delete {rule_number}"
        result = run_command(cmd, sudo=True, sudo_password=sudo_password)
        
        if not result["success"]:
            error_msg = result.get("stderr", result.get("error", "Unbekannter Fehler"))
            return JSONResponse(
                status_code=200,
                content={
                    "status": "error",
                    "message": f"Regel konnte nicht gelöscht werden: {error_msg}"
                }
            )
        
        return {
            "status": "success",
            "message": "Regel gelöscht",
            "output": result.get("stdout", "")
        }
    except Exception as e:
        return JSONResponse(
            status_code=200,
            content={
                "status": "error",
                "message": str(e)
            }
        )

@app.post("/api/security/configure")
async def configure_security(request: Request):
    """Sicherheitskonfiguration anwenden"""
    try:
        try:
            data = await request.json()
        except:
            data = {}
        
        sudo_password = data.get("sudo_password", "") or sudo_password_store.get("password", "")
        config = data.get("config", {})
        
        # Speichere sudo-Passwort im Store für spätere Verwendung
        if data.get("sudo_password") and not sudo_password_store.get("password"):
            sudo_password_store["password"] = data.get("sudo_password")
            logger.info("💾 Sudo-Passwort im Store gespeichert (via security/configure)")
        
        # Prüfe ob sudo-Passwort vorhanden ist
        if not sudo_password:
            sudo_test = run_command("sudo -n true", sudo=False)
            if not sudo_test["success"]:
                return JSONResponse(
                    status_code=200,
                    content={
                        "status": "error",
                        "message": "Sudo-Passwort erforderlich",
                        "requires_sudo_password": True
                    }
                )
        
        results = []
        
        # Firewall aktivieren
        if config.get("enable_firewall"):
            # Prüfe ob UFW installiert ist
            ufw_installed = check_installed("ufw")
            if not ufw_installed:
                # Installiere UFW
                install_result = run_command("apt-get install -y ufw", sudo=True, sudo_password=sudo_password)
                if install_result["success"]:
                    results.append("UFW installiert")
                else:
                    return JSONResponse(
                        status_code=200,
                        content={
                            "status": "error",
                            "message": f"UFW konnte nicht installiert werden: {install_result.get('stderr', 'Unbekannter Fehler')}"
                        }
                    )
            else:
                results.append("UFW bereits installiert")
            
            # Prüfe ob UFW bereits aktiv ist
            ufw_status_check = run_command("ufw status", sudo=False)
            if not ufw_status_check["success"]:
                ufw_status_check = run_command("ufw status", sudo=True, sudo_password=sudo_password)
            
            is_already_active = False
            if ufw_status_check["success"]:
                status_output = ufw_status_check.get("stdout", "")
                is_already_active = "Status: active" in status_output or "Status: aktiv" in status_output
            
            # Aktiviere UFW nur wenn nicht bereits aktiv
            if not is_already_active:
                enable_result = run_command("ufw --force enable", sudo=True, sudo_password=sudo_password)
                if enable_result["success"]:
                    results.append("Firewall aktiviert")
                else:
                    results.append(f"Firewall-Aktivierung fehlgeschlagen: {enable_result.get('stderr', 'Unbekannter Fehler')}")
            else:
                results.append("Firewall bereits aktiv")
        
        # Fail2Ban installieren/aktivieren
        if config.get("enable_fail2ban"):
            fail2ban_installed = check_installed("fail2ban")
            if not fail2ban_installed:
                install_result = run_command("apt-get install -y fail2ban", sudo=True, sudo_password=sudo_password)
                if install_result["success"]:
                    results.append("Fail2Ban installiert")
            else:
                results.append("Fail2Ban bereits installiert")
            
            # Prüfe ob Fail2Ban bereits läuft
            fail2ban_running = get_running_services().get("fail2ban", False)
            
            # Fail2Ban starten nur wenn nicht bereits aktiv
            if not fail2ban_running:
                start_result = run_command("systemctl enable --now fail2ban", sudo=True, sudo_password=sudo_password)
                if start_result["success"]:
                    results.append("Fail2Ban aktiviert")
                else:
                    results.append(f"Fail2Ban-Aktivierung fehlgeschlagen: {start_result.get('stderr', 'Unbekannter Fehler')}")
            else:
                results.append("Fail2Ban bereits aktiv")
        
        # Auto-Updates aktivieren
        if config.get("enable_auto_updates"):
            auto_updates_installed = check_installed("unattended-upgrades")
            if not auto_updates_installed:
                install_result = run_command("apt-get install -y unattended-upgrades", sudo=True, sudo_password=sudo_password)
                if install_result["success"]:
                    results.append("Auto-Updates installiert")
            else:
                results.append("Auto-Updates bereits installiert")
            
            # Prüfe ob Auto-Updates bereits aktiviert sind
            auto_updates_enabled = run_command("systemctl is-enabled unattended-upgrades 2>/dev/null")
            if not auto_updates_enabled["success"]:
                enable_result = run_command("systemctl enable unattended-upgrades", sudo=True, sudo_password=sudo_password)
                if enable_result["success"]:
                    results.append("Auto-Updates aktiviert")
                else:
                    results.append(f"Auto-Updates-Aktivierung fehlgeschlagen: {enable_result.get('stderr', 'Unbekannter Fehler')}")
            else:
                results.append("Auto-Updates bereits aktiviert")
        
        # SSH Härtung
        if config.get("enable_ssh_hardening"):
            try:
                ssh_config_file = "/etc/ssh/sshd_config"
                ssh_backup_file = "/etc/ssh/sshd_config.backup"
                
                # Erstelle Backup
                backup_result = run_command(f"cp {ssh_config_file} {ssh_backup_file}", sudo=True, sudo_password=sudo_password)
                if not backup_result["success"]:
                    results.append("⚠️ SSH Backup konnte nicht erstellt werden")
                else:
                    results.append("SSH Backup erstellt")
                
                # SSH-Konfiguration härten
                ssh_hardening_commands = [
                    # Deaktiviere Root-Login
                    f"sed -i 's/^#*PermitRootLogin.*/PermitRootLogin no/' {ssh_config_file}",
                    # Deaktiviere Passwort-Authentifizierung (nur Key-basiert)
                    f"sed -i 's/^#*PasswordAuthentication.*/PasswordAuthentication no/' {ssh_config_file}",
                    # Aktiviere Public Key Authentication
                    f"sed -i 's/^#*PubkeyAuthentication.*/PubkeyAuthentication yes/' {ssh_config_file}",
                    # Deaktiviere leere Passwörter
                    f"sed -i 's/^#*PermitEmptyPasswords.*/PermitEmptyPasswords no/' {ssh_config_file}",
                    # Max Auth Tries begrenzen
                    f"sed -i 's/^#*MaxAuthTries.*/MaxAuthTries 3/' {ssh_config_file}",
                    # Client Alive Interval setzen
                    f"sed -i 's/^#*ClientAliveInterval.*/ClientAliveInterval 300/' {ssh_config_file}",
                    f"sed -i 's/^#*ClientAliveCountMax.*/ClientAliveCountMax 2/' {ssh_config_file}",
                    # Deaktiviere X11 Forwarding (falls nicht benötigt)
                    f"sed -i 's/^#*X11Forwarding.*/X11Forwarding no/' {ssh_config_file}",
                ]
                
                # Führe alle SSH-Härtungsbefehle aus
                ssh_hardening_success = True
                for cmd in ssh_hardening_commands:
                    result = run_command(cmd, sudo=True, sudo_password=sudo_password)
                    if not result["success"]:
                        ssh_hardening_success = False
                        logger.warning(f"SSH Härtung Befehl fehlgeschlagen: {cmd}")
                
                # Füge zusätzliche Sicherheitseinstellungen hinzu, falls sie nicht existieren
                additional_settings = [
                    "Protocol 2",
                    "PermitRootLogin no",
                    "PasswordAuthentication no",
                    "PubkeyAuthentication yes",
                    "PermitEmptyPasswords no",
                    "MaxAuthTries 3",
                    "ClientAliveInterval 300",
                    "ClientAliveCountMax 2",
                    "X11Forwarding no",
                ]
                
                for setting in additional_settings:
                    key = setting.split()[0]
                    # Prüfe ob die Einstellung bereits existiert
                    check_cmd = f"grep -q '^{key}' {ssh_config_file} || echo '{setting}' >> {ssh_config_file}"
                    run_command(check_cmd, sudo=True, sudo_password=sudo_password)
                
                # Teste SSH-Konfiguration
                test_result = run_command("sshd -t", sudo=True, sudo_password=sudo_password)
                if test_result["success"]:
                    # SSH-Service neu laden
                    reload_result = run_command("systemctl reload sshd", sudo=True, sudo_password=sudo_password)
                    if reload_result["success"]:
                        results.append("SSH Härtung erfolgreich angewendet")
                    else:
                        results.append("⚠️ SSH Härtung angewendet, aber Service konnte nicht neu geladen werden")
                else:
                    results.append(f"⚠️ SSH-Konfiguration fehlerhaft: {test_result.get('stderr', 'Unbekannter Fehler')}")
                    # Stelle Backup wieder her
                    restore_result = run_command(f"cp {ssh_backup_file} {ssh_config_file}", sudo=True, sudo_password=sudo_password)
                    if restore_result["success"]:
                        results.append("SSH-Konfiguration aus Backup wiederhergestellt")
            except Exception as e:
                logger.error(f"Fehler bei SSH Härtung: {e}")
                results.append(f"SSH Härtung fehlgeschlagen: {str(e)}")
        
        # Audit Logging
        if config.get("enable_audit_logging"):
            try:
                # Installiere auditd falls nicht vorhanden
                auditd_installed = check_installed("auditd")
                if not auditd_installed:
                    logger.info("🔧 Versuche Auditd zu installieren...")
                    # PackageKit stoppen, um Konflikte zu vermeiden
                    _ensure_packagekit_stopped(sudo_password)
                    # Führe apt-get update separat aus (kann länger dauern)
                    update_result = run_command("apt-get update", sudo=True, sudo_password=sudo_password)
                    if not update_result["success"]:
                        logger.warning(f"⚠️ apt-get update fehlgeschlagen: {update_result.get('stderr', '')[:200]}")
                    
                    # Installiere auditd
                    install_result = run_command("apt-get install -y auditd audispd-plugins", sudo=True, sudo_password=sudo_password)
                    if install_result["success"]:
                        results.append("Auditd installiert")
                        logger.info("✅ Auditd erfolgreich installiert")
                    else:
                        error_msg = install_result.get("stderr", install_result.get("error", "Unbekannter Fehler"))
                        stdout_msg = install_result.get("stdout", "")
                        logger.error(f"❌ Auditd Installation fehlgeschlagen. Stderr: {error_msg[:200]}, Stdout: {stdout_msg[:200]}")
                        results.append(f"⚠️ Auditd konnte nicht installiert werden: {error_msg[:100]}")
                        # Versuche es mit einem einfacheren Befehl
                        logger.info("🔧 Versuche Auditd mit einfacherem Befehl zu installieren...")
                        simple_install = run_command("apt-get install -y auditd", sudo=True, sudo_password=sudo_password)
                        if simple_install["success"]:
                            results.append("Auditd installiert (ohne Plugins)")
                            logger.info("✅ Auditd erfolgreich installiert (ohne Plugins)")
                        else:
                            simple_error = simple_install.get("stderr", simple_install.get("error", "Unbekannter Fehler"))
                            logger.error(f"❌ Auditd Installation auch mit einfachem Befehl fehlgeschlagen: {simple_error[:200]}")
                            return JSONResponse(
                                status_code=200,
                                content={
                                    "status": "error",
                                    "message": f"Auditd konnte nicht installiert werden. Fehler: {simple_error[:200]}. Bitte manuell installieren mit: sudo apt-get install -y auditd",
                                    "results": results,
                                    "debug": {
                                        "stderr": error_msg[:500],
                                        "stdout": stdout_msg[:500],
                                        "simple_stderr": simple_error[:500]
                                    }
                                }
                            )
                else:
                    results.append("Auditd bereits installiert")
                
                # Aktiviere auditd Service
                enable_result = run_command("systemctl enable --now auditd", sudo=True, sudo_password=sudo_password)
                if enable_result["success"]:
                    results.append("Auditd Service aktiviert")
                else:
                    results.append("⚠️ Auditd Service konnte nicht aktiviert werden")
                
                # Konfiguriere Audit-Regeln
                audit_rules_file = "/etc/audit/rules.d/pi-installer.rules"
                audit_rules = [
                    "# PI-Installer Audit Rules",
                    "# Überwache alle Systemaufrufe",
                    "-a always,exit -F arch=b64 -S adjtimex -S settimeofday -k time-change",
                    "-a always,exit -F arch=b32 -S adjtimex -S settimeofday -S stime -k time-change",
                    "-a always,exit -F arch=b64 -S clock_settime -k time-change",
                    "-a always,exit -F arch=b32 -S clock_settime -k time-change",
                    "-w /etc/localtime -p wa -k time-change",
                    "",
                    "# Überwache Benutzer- und Gruppenänderungen",
                    "-w /etc/group -p wa -k identity",
                    "-w /etc/passwd -p wa -k identity",
                    "-w /etc/gshadow -p wa -k identity",
                    "-w /etc/shadow -p wa -k identity",
                    "-w /etc/security/opasswd -p wa -k identity",
                    "",
                    "# Überwache Netzwerkänderungen",
                    "-a always,exit -F arch=b64 -S sethostname -S setdomainname -k system-locale",
                    "-a always,exit -F arch=b32 -S sethostname -S setdomainname -k system-locale",
                    "-w /etc/issue -p wa -k system-locale",
                    "-w /etc/issue.net -p wa -k system-locale",
                    "-w /etc/hosts -p wa -k system-locale",
                    "-w /etc/sysconfig/network -p wa -k system-locale",
                    "",
                    "# Überwache Login/Logout",
                    "-w /var/log/faillog -p wa -k logins",
                    "-w /var/log/lastlog -p wa -k logins",
                    "-w /var/log/tallylog -p wa -k logins",
                    "",
                    "# Überwache Sudo-Befehle",
                    "-w /usr/bin/sudo -p x -k actions",
                    "-w /etc/sudoers -p wa -k actions",
                    "-w /etc/sudoers.d/ -p wa -k actions",
                    "",
                    "# Überwache Dateisystemänderungen",
                    "-w /etc -p wa -k etc",
                    "-w /usr/bin -p wa -k bin",
                    "-w /usr/sbin -p wa -k sbin",
                    "",
                    "# Überwache privilegierte Befehle",
                    "-a always,exit -F arch=b64 -S mount -S umount2 -k mount",
                    "-a always,exit -F arch=b32 -S mount -S umount -k mount",
                ]
                
                # Schreibe Audit-Regeln
                rules_content = "\n".join(audit_rules) + "\n"
                write_cmd = f"cat > {audit_rules_file} << 'EOF'\n{rules_content}EOF"
                write_result = run_command(write_cmd, sudo=True, sudo_password=sudo_password)
                
                if write_result["success"]:
                    results.append("Audit-Regeln konfiguriert")
                    
                    # Lade Audit-Regeln neu
                    reload_result = run_command("augenrules --load", sudo=True, sudo_password=sudo_password)
                    if reload_result["success"]:
                        results.append("Audit-Regeln geladen")
                    else:
                        results.append("⚠️ Audit-Regeln konnten nicht geladen werden")
                    
                    # Starte auditd neu
                    restart_result = run_command("systemctl restart auditd", sudo=True, sudo_password=sudo_password)
                    if restart_result["success"]:
                        results.append("Auditd neu gestartet")
                else:
                    results.append(f"⚠️ Audit-Regeln konnten nicht geschrieben werden: {write_result.get('stderr', 'Unbekannter Fehler')}")
                    
            except Exception as e:
                logger.error(f"Fehler bei Audit Logging: {e}")
                results.append(f"Audit Logging fehlgeschlagen: {str(e)}")
        
        # Wenn keine Ergebnisse, aber Konfiguration wurde angewendet, füge Info hinzu
        if not results:
            # Prüfe welche Features bereits aktiviert sind
            active_features = []
            if config.get("enable_firewall"):
                ufw_installed = check_installed("ufw")
                if ufw_installed:
                    ufw_status_check = run_command("ufw status", sudo=False)
                    if not ufw_status_check["success"] and sudo_password:
                        ufw_status_check = run_command("ufw status", sudo=True, sudo_password=sudo_password)
                    if ufw_status_check["success"]:
                        status_text = ufw_status_check.get("stdout", "")
                        if "Status: active" in status_text or "Status: aktiv" in status_text:
                            active_features.append("Firewall bereits aktiv")
            
            if config.get("enable_fail2ban"):
                fail2ban_installed = check_installed("fail2ban")
                fail2ban_running = get_running_services().get("fail2ban", False)
                if fail2ban_installed and fail2ban_running:
                    active_features.append("Fail2Ban bereits aktiv")
            
            if config.get("enable_auto_updates"):
                auto_updates_installed = check_installed("unattended-upgrades")
                auto_updates_enabled = run_command("systemctl is-enabled unattended-upgrades 2>/dev/null")
                if auto_updates_installed and auto_updates_enabled["success"]:
                    active_features.append("Auto-Updates bereits aktiviert")
            
            if config.get("enable_ssh_hardening"):
                # Prüfe ob SSH bereits gehärtet ist
                ssh_backup_exists = run_command("test -f /etc/ssh/sshd_config.backup")
                if ssh_backup_exists["success"]:
                    active_features.append("SSH Härtung bereits angewendet")
            
            if config.get("enable_audit_logging"):
                auditd_installed = check_installed("auditd")
                auditd_running = get_running_services().get("auditd", False)
                if auditd_installed and auditd_running:
                    active_features.append("Audit Logging bereits aktiv")
            
            if active_features:
                results.extend(active_features)
            else:
                results.append("Alle ausgewählten Features sind bereits konfiguriert")
        
        return {
            "status": "success",
            "message": "Konfiguration angewendet",
            "results": results
        }
    except Exception as e:
        return JSONResponse(
            status_code=200,
            content={
                "status": "error",
                "message": str(e)
            }
        )

def get_updates_categorized():
    """Updates kategorisieren. Kein PackageKit-Stop hier – würde bei Aufruf ohne Passwort (Dashboard/Updates-API) Polkit-Abfrage-Schleife auslösen."""
    try:
        # Zuerst apt update ausführen (ohne zu installieren)
        run_command("apt-get update -qq 2>/dev/null", sudo=False)
        
        # Update-Liste abrufen
        result = run_command("apt list --upgradable 2>/dev/null | tail -n +2")
        updates = []
        
        if result["success"] and result["stdout"].strip():
            for line in result["stdout"].split("\n"):
                line = line.strip()
                if line and "/" in line:
                    # Format: package/version,version,version [upgradable from: version]
                    parts = line.split()
                    if len(parts) >= 1:
                        package_part = parts[0]
                        package = package_part.split("/")[0]
                        version = package_part.split("/")[1] if "/" in package_part else ""
                        
                        # Sicherheits-Updates prüfen (apt-get upgrade --dry-run -s)
                        security_result = run_command(f"apt-get upgrade -s {package} 2>/dev/null | grep -i security")
                        is_security = security_result["success"] and security_result["stdout"].strip() != ""
                        
                        # Kategorisieren
                        category = "optional"
                        if is_security or "security" in package.lower() or "-sec" in package.lower():
                            category = "security"
                        elif "kernel" in package.lower() or "linux-image" in package.lower() or "linux-headers" in package.lower():
                            category = "critical"
                        elif "lib" in package.lower() or "python" in package.lower() or "perl" in package.lower():
                            category = "necessary"
                        
                        updates.append({
                            "package": package,
                            "version": version,
                            "category": category,
                        })
        
        # Kategorien zählen
        categories = {
            "security": len([u for u in updates if u["category"] == "security"]),
            "critical": len([u for u in updates if u["category"] == "critical"]),
            "necessary": len([u for u in updates if u["category"] == "necessary"]),
            "optional": len([u for u in updates if u["category"] == "optional"]),
        }
        
        return {
            "total": len(updates),
            "categories": categories,
            "updates": updates[:50],  # Erste 50
        }
    except Exception as e:
        # Fallback: Einfache Prüfung
        try:
            result = run_command("apt list --upgradable 2>/dev/null | wc -l")
            total = int(result.get("stdout", "0").strip()) - 1 if result["success"] else 0
            return {
                "total": max(0, total),
                "categories": {"security": 0, "critical": 0, "necessary": 0, "optional": 0},
                "updates": [],
            }
        except:
            return {
                "total": 0,
                "categories": {"security": 0, "critical": 0, "necessary": 0, "optional": 0},
                "updates": [],
            }

# ==================== Webserver Endpoints ====================

def get_website_names():
    """Extrahiere Website-Namen aus Webserver-Konfigurationen"""
    websites = []
    
    # Nginx Konfigurationen
    nginx_sites = []
    nginx_result = run_command("find /etc/nginx/sites-enabled /etc/nginx/conf.d -name '*.conf' 2>/dev/null | head -10")
    if nginx_result["success"]:
        for conf_file in nginx_result["stdout"].strip().split("\n"):
            if conf_file.strip():
                server_name_result = run_command(f"grep -E 'server_name|server_name_' {conf_file} 2>/dev/null | head -5")
                if server_name_result["success"]:
                    for line in server_name_result["stdout"].split("\n"):
                        if "server_name" in line:
                            # Extrahiere Domain-Namen
                            parts = line.split()
                            for part in parts[1:]:
                                part = part.strip(';')
                                if part and part not in ['localhost', '_', 'default_server'] and '.' in part:
                                    nginx_sites.append(part)
    
    # Apache Konfigurationen
    apache_sites = []
    apache_result = run_command("find /etc/apache2/sites-enabled /etc/apache2/conf-enabled -name '*.conf' 2>/dev/null | head -10")
    if apache_result["success"]:
        for conf_file in apache_result["stdout"].strip().split("\n"):
            if conf_file.strip():
                server_name_result = run_command(f"grep -E 'ServerName|ServerAlias' {conf_file} 2>/dev/null | head -5")
                if server_name_result["success"]:
                    for line in server_name_result["stdout"].split("\n"):
                        parts = line.split()
                        if len(parts) >= 2:
                            domain = parts[1].strip()
                            if domain and domain not in ['localhost', '*'] and '.' in domain:
                                apache_sites.append(domain)
    
    # Kombiniere und entferne Duplikate
    all_sites = list(set(nginx_sites + apache_sites))
    return all_sites[:20]  # Maximal 20

@app.get("/api/webserver/status")
async def webserver_status():
    """Webserver-Status"""
    try:
        running = get_running_services()
        network = get_network_info()
        installed = get_installed_apps()
        
        # Prüfe Webserver läuft
        nginx_running = running.get("nginx", False)
        apache_running = running.get("apache2", False)
        
        # Webserver Ports prüfen
        webserver_ports = []
        ports_result = run_command("ss -tuln | grep -E ':80|:443|:8000|:8080|:9090|:10000'")
        if ports_result["success"]:
            webserver_ports = ports_result["stdout"].strip().split("\n")
        
        # PI-Installer Adresse (Frontend Port: 5173 Tauri/Vite-Dev, sonst 3001/3002)
        pi_installer_port = _detect_frontend_port()
        
        # Website-Namen extrahieren
        website_names = get_website_names()
        
        # Cockpit & Webmin Status
        cockpit_running = running.get("cockpit", False) or check_installed("cockpit")
        webmin_running = running.get("webmin", False) or check_installed("webmin")
        
        # Prüfe ob Cockpit/Webmin auf Ports laufen
        cockpit_port = run_command("ss -tuln | grep ':9090'")
        webmin_port = run_command("ss -tuln | grep ':10000'")
        
        return {
            "pi_installer": {
                "port": pi_installer_port or 3001,
                "url": f"http://{network.get('ips', ['localhost'])[0]}:{pi_installer_port or 3001}" if network.get('ips') else f"http://localhost:{pi_installer_port or 3001}",
            },
            "website_names": website_names,
            "nginx": {
                "installed": installed.get("nginx", False),
                "running": nginx_running,
            },
            "apache": {
                "installed": installed.get("apache", False),
                "running": apache_running,
            },
            "mysql": {
                "installed": installed.get("mysql", False),
                "running": running.get("mysql", False),
            },
            "mariadb": {
                "installed": installed.get("mariadb", False),
                "running": running.get("mariadb", False),
            },
            "php": {
                "installed": installed.get("php", False),
            },
            "cockpit": {
                "installed": installed.get("cockpit", False),
                "running": cockpit_running or cockpit_port["success"],
                "port": 9090 if cockpit_port["success"] else None,
            },
            "webmin": {
                "installed": installed.get("webmin", False),
                "running": webmin_running or webmin_port["success"],
                "port": 10000 if webmin_port["success"] else None,
            },
            "network": network,
            "webserver_ports": webserver_ports,
            "websites": installed.get("websites", []),
            "installed_cms": {
                "wordpress": {
                    "installed": installed.get("wordpress", False),
                    "plugins": installed.get("wordpress_plugins", []),
                },
                "nextcloud": installed.get("nextcloud", False),
                "drupal": installed.get("drupal", False),
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/webserver/configure")
async def configure_webserver(request: Request):
    """Webserver konfigurieren"""
    try:
        try:
            data = await request.json()
        except:
            data = {}
        
        sudo_password = data.get("sudo_password", "") or sudo_password_store.get("password", "")
        
        # Prüfe ob sudo-Passwort vorhanden ist
        if not sudo_password:
            sudo_test = run_command("sudo -n true", sudo=False)
            if not sudo_test["success"]:
                return JSONResponse(
                    status_code=200,
                    content={
                        "status": "error",
                        "message": "Sudo-Passwort erforderlich",
                        "requires_sudo_password": True
                    }
                )
        
        # Speichere sudo-Passwort im Store
        if sudo_password and not sudo_password_store.get("password"):
            sudo_password_store["password"] = sudo_password
            logger.info("💾 Sudo-Passwort im Store gespeichert (Webserver-Config)")
        
        results = []
        server_type = data.get("server_type", "nginx")
        enable_php = data.get("enable_php", False)
        
        # PHP-Support aktivieren
        if enable_php:
            logger.info("🔧 PHP-Support wird aktiviert...")
            php_installed = check_installed("php")
            logger.info(f"📋 PHP installiert: {php_installed}")
            
            if not php_installed:
                # PHP installieren
                logger.info("📦 Installiere PHP...")
                php_result = run_command("apt-get install -y php php-fpm php-cli php-common php-mysql php-zip php-gd php-mbstring php-curl php-xml php-bcmath", sudo=True, sudo_password=sudo_password)
                logger.info(f"📊 PHP Installation Result: success={php_result.get('success')}, returncode={php_result.get('returncode')}, stderr={php_result.get('stderr', '')[:200]}")
                
                if php_result["success"]:
                    results.append("PHP installiert")
                    # Prüfe nochmal, ob PHP jetzt installiert ist
                    php_installed_after = check_installed("php")
                    logger.info(f"📋 PHP nach Installation: {php_installed_after}")
                else:
                    error_msg = php_result.get('stderr', php_result.get('error', 'Unbekannter Fehler'))
                    logger.error(f"❌ PHP Installation fehlgeschlagen: {error_msg}")
                    return JSONResponse(
                        status_code=200,
                        content={
                            "status": "error",
                            "message": f"PHP konnte nicht installiert werden: {error_msg}",
                            "debug": {
                                "stdout": php_result.get('stdout', ''),
                                "stderr": error_msg,
                                "returncode": php_result.get('returncode'),
                            }
                        }
                    )
            else:
                results.append("PHP bereits installiert")
            
            # PHP für Webserver konfigurieren (auch wenn bereits installiert)
            if server_type == "nginx":
                # Nginx: PHP-FPM sollte bereits installiert sein
                php_fpm_installed = check_installed("php-fpm")
                if not php_fpm_installed:
                    php_fpm_result = run_command("apt-get install -y php-fpm", sudo=True, sudo_password=sudo_password)
                    if php_fpm_result["success"]:
                        results.append("PHP-FPM installiert")
                
                # PHP-FPM aktivieren - finde die richtige PHP-Version
                php_version_result = run_command("php -v 2>/dev/null | head -1 | grep -oE 'PHP [0-9]+\\.[0-9]+' | awk '{print $2}'")
                php_version = "8.2"  # Default
                if php_version_result["success"]:
                    php_version = php_version_result["stdout"].strip() or "8.2"
                
                # Aktiviere PHP-FPM für die gefundene Version
                php_fpm_service = f"php{php_version}-fpm"
                php_fpm_start = run_command(f"systemctl enable --now {php_fpm_service}", sudo=True, sudo_password=sudo_password)
                if php_fpm_start["success"]:
                    results.append(f"PHP-FPM ({php_fpm_service}) aktiviert")
                else:
                    # Versuche alle PHP-FPM Services zu aktivieren
                    php_fpm_all = run_command("systemctl enable --now php*-fpm 2>/dev/null || systemctl enable --now php-fpm", sudo=True, sudo_password=sudo_password)
                    if php_fpm_all["success"]:
                        results.append("PHP-FPM aktiviert")
                
                # Nginx PHP-Konfiguration prüfen
                nginx_php_check = run_command("grep -r 'fastcgi_pass.*php' /etc/nginx/sites-enabled/ 2>/dev/null | head -1")
                if not nginx_php_check["success"]:
                    results.append("⚠️ Nginx PHP-Konfiguration: Bitte manuell konfigurieren (fastcgi_pass)")
            
            elif server_type == "apache":
                # Apache: libapache2-mod-php installieren
                apache_php_installed = check_installed("libapache2-mod-php")
                if not apache_php_installed:
                    apache_php_result = run_command("apt-get install -y libapache2-mod-php", sudo=True, sudo_password=sudo_password)
                    if apache_php_result["success"]:
                        results.append("Apache PHP-Modul installiert")
                
                # PHP-Modul aktivieren
                php_module_enable = run_command("a2enmod php*", sudo=True, sudo_password=sudo_password)
                if php_module_enable["success"]:
                    results.append("Apache PHP-Modul aktiviert")
                
                # Apache neu laden
                apache_reload = run_command("systemctl reload apache2", sudo=True, sudo_password=sudo_password)
                if apache_reload["success"]:
                    results.append("Apache neu geladen")
        
        # Webserver installieren/aktivieren (falls noch nicht installiert)
        if server_type == "nginx":
            nginx_installed = check_installed("nginx")
            if not nginx_installed:
                nginx_result = run_command("apt-get install -y nginx", sudo=True, sudo_password=sudo_password)
                if nginx_result["success"]:
                    results.append("Nginx installiert")
            
            nginx_start = run_command("systemctl enable --now nginx", sudo=True, sudo_password=sudo_password)
            if nginx_start["success"]:
                results.append("Nginx aktiviert")
        
        elif server_type == "apache":
            apache_installed = check_installed("apache2")
            if not apache_installed:
                apache_result = run_command("apt-get install -y apache2", sudo=True, sudo_password=sudo_password)
                if apache_result["success"]:
                    results.append("Apache installiert")
            
            apache_start = run_command("systemctl enable --now apache2", sudo=True, sudo_password=sudo_password)
            if apache_start["success"]:
                results.append("Apache aktiviert")
        
        return {
            "status": "success",
            "message": "Webserver konfiguriert",
            "results": results
        }
    except Exception as e:
        logger.error(f"💥 Fehler bei Webserver-Konfiguration: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=200,
            content={
                "status": "error",
                "message": f"Fehler bei der Webserver-Konfiguration: {str(e)}"
            }
        )

# ==================== NAS Endpoints ====================

@app.get("/api/nas/status")
async def nas_status():
    """NAS-Status abrufen"""
    try:
        installed = get_installed_apps()
        running = get_running_services()
        
        dup_cmd = "fdupes" if run_command("which fdupes 2>/dev/null")["success"] else ("jdupes" if run_command("which jdupes 2>/dev/null")["success"] else None)
        fdupes_installed = bool(dup_cmd)
        # Vorgeschlagener Scan-Pfad: existierendes Verzeichnis (NAS-Pfad oder Heimatverzeichnis)
        home = str(Path.home())
        suggested_path = "/mnt/nas" if Path("/mnt/nas").exists() else home
        return {
            "suggested_scan_path": suggested_path,
            "samba": {
                "installed": check_installed("samba") or check_installed("samba-common"),
                "running": running.get("smbd", False) or running.get("samba", False),
            },
            "nfs": {
                "installed": check_installed("nfs-kernel-server") or check_installed("nfs-common"),
                "running": running.get("nfs", False),
            },
            "ftp": {
                "installed": check_installed("vsftpd") or check_installed("proftpd"),
                "running": running.get("vsftpd", False) or running.get("proftpd", False),
            },
            "fdupes": {"installed": bool(fdupes_installed)},
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/nas/configure")
async def configure_nas(request: Request):
    """NAS konfigurieren"""
    try:
        try:
            data = await request.json()
        except:
            data = {}
        
        sudo_password = data.get("sudo_password", "") or sudo_password_store.get("password", "")
        
        if not sudo_password:
            sudo_test = run_command("sudo -n true", sudo=False)
            if not sudo_test["success"]:
                return JSONResponse(
                    status_code=200,
                    content={
                        "status": "error",
                        "message": "Sudo-Passwort erforderlich",
                        "requires_sudo_password": True
                    }
                )
        
        if sudo_password and not sudo_password_store.get("password"):
            sudo_password_store["password"] = sudo_password
        
        results = []
        nas_type = data.get("nas_type", "samba")
        share_name = data.get("share_name", "pi-share")
        share_path = data.get("share_path", "/mnt/nas")
        
        # Samba konfigurieren
        if nas_type == "samba" or data.get("enable_samba"):
            samba_installed = check_installed("samba")
            if not samba_installed:
                samba_result = run_command("apt-get install -y samba samba-common", sudo=True, sudo_password=sudo_password)
                if samba_result["success"]:
                    results.append("Samba installiert")
                else:
                    return JSONResponse(
                        status_code=200,
                        content={
                            "status": "error",
                            "message": f"Samba konnte nicht installiert werden: {samba_result.get('stderr', 'Unbekannter Fehler')}"
                        }
                    )
            
            # Samba-Freigabe erstellen
            # Erstelle Verzeichnis
            mkdir_result = run_command(f"mkdir -p {share_path}", sudo=True, sudo_password=sudo_password)
            if mkdir_result["success"]:
                results.append(f"Verzeichnis {share_path} erstellt")
            
            # Samba-Konfiguration hinzufügen
            samba_config = f"""
[{share_name}]
   path = {share_path}
   browseable = yes
   read only = no
   guest ok = {'yes' if data.get('enable_guest') else 'no'}
   create mask = 0664
   directory mask = 0775
"""
            # Füge zur smb.conf hinzu
            echo_result = run_command(f'echo "{samba_config}" >> /etc/samba/smb.conf', sudo=True, sudo_password=sudo_password)
            if echo_result["success"]:
                results.append("Samba-Konfiguration hinzugefügt")
            
            # Samba neu starten
            samba_restart = run_command("systemctl restart smbd nmbd", sudo=True, sudo_password=sudo_password)
            if samba_restart["success"]:
                results.append("Samba neu gestartet")
        
        # NFS konfigurieren
        if nas_type == "nfs" or data.get("enable_nfs"):
            nfs_installed = check_installed("nfs-kernel-server")
            if not nfs_installed:
                nfs_result = run_command("apt-get install -y nfs-kernel-server", sudo=True, sudo_password=sudo_password)
                if nfs_result["success"]:
                    results.append("NFS installiert")
            
            # NFS-Export konfigurieren
            mkdir_result = run_command(f"mkdir -p {share_path}", sudo=True, sudo_password=sudo_password)
            nfs_export = f"{share_path} *(rw,sync,no_subtree_check)"
            echo_result = run_command(f'echo "{nfs_export}" >> /etc/exports', sudo=True, sudo_password=sudo_password)
            if echo_result["success"]:
                results.append("NFS-Export konfiguriert")
            
            # NFS neu starten
            nfs_restart = run_command("exportfs -ra && systemctl restart nfs-kernel-server", sudo=True, sudo_password=sudo_password)
            if nfs_restart["success"]:
                results.append("NFS neu gestartet")
        
        # FTP konfigurieren
        if nas_type == "ftp" or data.get("enable_ftp"):
            ftp_installed = check_installed("vsftpd")
            if not ftp_installed:
                ftp_result = run_command("apt-get install -y vsftpd", sudo=True, sudo_password=sudo_password)
                if ftp_result["success"]:
                    results.append("FTP (vsftpd) installiert")
            
            # FTP aktivieren
            ftp_start = run_command("systemctl enable --now vsftpd", sudo=True, sudo_password=sudo_password)
            if ftp_start["success"]:
                results.append("FTP aktiviert")
        
        return {
            "status": "success",
            "message": "NAS konfiguriert",
            "results": results
        }
    except Exception as e:
        logger.error(f"💥 Fehler bei NAS-Konfiguration: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=200,
            content={
                "status": "error",
                "message": f"Fehler bei der NAS-Konfiguration: {str(e)}"
            }
        )


def _require_sudo_for_nas(data: dict) -> tuple:
    """Liefert (sudo_password, error_response). error_response ist None wenn ok."""
    sudo_password = data.get("sudo_password", "") or sudo_password_store.get("password", "")
    if not sudo_password:
        test = run_command("sudo -n true", sudo=False)
        if not test["success"]:
            return "", {
                "status": "error",
                "message": "Sudo-Passwort erforderlich",
                "requires_sudo_password": True,
            }
    if sudo_password and not sudo_password_store.get("password"):
        sudo_password_store["password"] = sudo_password
    return sudo_password, None


@app.post("/api/nas/duplicates/install")
async def nas_duplicates_install(request: Request):
    """fdupes installieren (Duplikat-Finder)."""
    try:
        try:
            data = await request.json()
        except Exception:
            data = {}
        sudo_password, err = _require_sudo_for_nas(data)
        if err:
            return JSONResponse(status_code=200, content=err)
        # Update und Install getrennt, damit Fehlerursache klar erkennbar ist
        r_update = run_command(
            "apt-get update -qq 2>&1",
            sudo=True,
            sudo_password=sudo_password,
            timeout=60,
        )
        if not r_update["success"]:
            out = (r_update.get("stderr") or "") + (r_update.get("stdout") or "")
            msg = (out or r_update.get("error") or "apt-get update fehlgeschlagen")[:600]
            return JSONResponse(status_code=200, content={
                "status": "error",
                "message": f"apt-get update fehlgeschlagen. Ursache: {msg}",
            })
        r = run_command(
            "apt-get install -y fdupes 2>&1",
            sudo=True,
            sudo_password=sudo_password,
            timeout=120,
        )
        if not r["success"]:
            # Fallback: jdupes (oft in Debian/Raspberry Pi OS verfügbar, gleiches Ausgabeformat)
            r2 = run_command(
                "apt-get install -y jdupes 2>&1",
                sudo=True,
                sudo_password=sudo_password,
                timeout=120,
            )
            if r2["success"]:
                return {"status": "success", "message": "jdupes installiert (Alternative zu fdupes)"}
            out = (r.get("stderr") or "") + (r.get("stdout") or "")
            msg = (out or r.get("error") or "Unbekannt")[:600]
            return JSONResponse(status_code=200, content={
                "status": "error",
                "message": f"fdupes/jdupes konnte nicht installiert werden: {msg}",
            })
        return {"status": "success", "message": "fdupes installiert"}
    except Exception as e:
        logger.error(f"Duplikat-Install: {e}", exc_info=True)
        return JSONResponse(status_code=200, content={
            "status": "error",
            "message": str(e),
        })


@app.post("/api/nas/duplicates/scan")
async def nas_duplicates_scan(request: Request):
    """Verzeichnis nach Duplikaten scannen (fdupes -r)."""
    try:
        try:
            data = await request.json()
        except Exception:
            data = {}
        path = (data.get("path") or "/mnt/nas").strip().rstrip("/")
        if not path or ".." in path or path.startswith("-"):
            return JSONResponse(status_code=200, content={
                "status": "error",
                "message": "Ungültiger Pfad",
            })
        if not Path(path).exists():
            home = str(Path.home())
            hint = f" Zum Testen z.B. {home} oder erstelle /mnt/nas mit: sudo mkdir -p /mnt/nas"
            return JSONResponse(status_code=200, content={
                "status": "error",
                "message": f"Pfad existiert nicht: {path}.{hint}",
            })
        dup_cmd = "fdupes" if run_command("which fdupes 2>/dev/null")["success"] else ("jdupes" if run_command("which jdupes 2>/dev/null")["success"] else None)
        if not dup_cmd:
            return JSONResponse(status_code=200, content={
                "status": "error",
                "message": "fdupes/jdupes nicht gefunden. Bitte zuerst installieren.",
                "requires_install": True,
            })
        # System-/Cache-Verzeichnisse ausschließen (Standard: an) – Mesa, __pycache__, node_modules etc.
        exclude_system = data.get("exclude_system_cache", True)
        exclude_patterns = [".cache", "mesa_shader", "__pycache__", "node_modules", ".git/", "Trash/"]
        cmd_extra = ""
        if dup_cmd == "jdupes" and exclude_system:
            cmd_extra = " " + " ".join(f'-X nostr:{p}' for p in exclude_patterns)
        r = run_command(
            f"{dup_cmd} -r{cmd_extra} {shlex.quote(path)} 2>/dev/null",
            sudo=False,
            timeout=600,
        )
        if not r["success"]:
            err = (r.get("stderr") or r.get("stdout") or "Unbekannter Fehler")[:200]
            return JSONResponse(status_code=200, content={
                "status": "error",
                "message": f"Scan fehlgeschlagen: {err}",
            })
        stdout = (r.get("stdout") or "").strip()
        groups = []
        for block in stdout.split("\n\n"):
            files = [ln.strip() for ln in block.splitlines() if ln.strip()]
            if len(files) > 1:
                groups.append({"files": files, "count": len(files)})
        if exclude_system and dup_cmd == "fdupes":
            groups = [
                g for g in groups
                if not any(any(patt in f for patt in exclude_patterns) for f in g["files"])
            ]
        return {
            "status": "success",
            "path": path,
            "groups": groups,
            "total_duplicates": sum(g["count"] - 1 for g in groups),
            "total_groups": len(groups),
        }
    except Exception as e:
        logger.error(f"Duplikat-Scan: {e}", exc_info=True)
        return JSONResponse(status_code=200, content={
            "status": "error",
            "message": str(e),
        })


@app.post("/api/nas/duplicates/move-to-backup")
async def nas_duplicates_move_to_backup(request: Request):
    """Duplikate in Backup-Ordner verschieben (pro Gruppe erste Datei behalten)."""
    try:
        try:
            data = await request.json()
        except Exception:
            data = {}
        sudo_password, err = _require_sudo_for_nas(data)
        if err:
            return JSONResponse(status_code=200, content=err)
        groups = data.get("groups") or []
        backup_path = (data.get("backup_path") or "").strip().rstrip("/")
        if not backup_path or ".." in backup_path:
            return JSONResponse(status_code=200, content={
                "status": "error",
                "message": "Ungültiger Backup-Pfad",
            })
        moved = 0
        errors = []
        run_command(f"mkdir -p {shlex.quote(backup_path)}", sudo=True, sudo_password=sudo_password)
        for group in groups:
            files = group.get("files") or []
            if len(files) < 2:
                continue
            keep = files[0]
            for f in files[1:]:
                if not Path(f).exists():
                    continue
                base = Path(f).name
                dest = Path(backup_path) / base
                idx = 1
                while dest.exists():
                    stem = Path(f).stem
                    suffix = Path(f).suffix
                    dest = Path(backup_path) / f"{stem}_{idx}{suffix}"
                    idx += 1
                cmd = f"mv {shlex.quote(f)} {shlex.quote(str(dest))}"
                res = run_command(cmd, sudo=True, sudo_password=sudo_password)
                if res["success"]:
                    moved += 1
                else:
                    errors.append(f"{f}: {res.get('stderr', 'Fehler')[:80]}")
        return {
            "status": "success",
            "message": f"{moved} Duplikate nach {backup_path} verschoben",
            "moved": moved,
            "errors": errors[:10],
        }
    except Exception as e:
        logger.error(f"Duplikat-Move: {e}", exc_info=True)
        return JSONResponse(status_code=200, content={
            "status": "error",
            "message": str(e),
        })


# ==================== Home Automation Endpoints ====================

@app.get("/api/homeautomation/status")
async def homeautomation_status():
    """Homeautomation-Status abrufen"""
    try:
        installed = get_installed_apps()
        running = get_running_services()
        
        return {
            "homeassistant": {
                "installed": check_installed("homeassistant") or run_command("docker ps | grep homeassistant")["success"],
                "running": running.get("homeassistant", False) or run_command("docker ps | grep homeassistant")["success"],
            },
            "openhab": {
                "installed": check_installed("openhab"),
                "running": running.get("openhab", False),
            },
            "nodered": {
                "installed": check_installed("node-red") or run_command("npm list -g node-red")["success"],
                "running": running.get("node-red", False),
            },
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/homeautomation/search")
async def homeautomation_search():
    """Suche nach Elementen im Haus (Geräte/Integrationen) – Platzhalter für spätere Erkennung."""
    try:
        # Optional: MQTT-Broker, Zigbee-Gateway, bekannte Dienste prüfen
        found = []
        mqtt = run_command("systemctl is-active mosquitto 2>/dev/null")["success"] or run_command("pgrep -x mosquitto")["success"]
        if mqtt:
            found.append({"type": "mqtt", "name": "Mosquitto (MQTT-Broker)", "running": True})
        return {"status": "success", "found": found, "message": "Suche abgeschlossen."}
    except Exception as e:
        return {"status": "success", "found": [], "message": str(e)}


@app.post("/api/homeautomation/uninstall")
async def homeautomation_uninstall(request: Request):
    """Hausautomations-Komponente deinstallieren (Home Assistant, OpenHAB, Node-RED)."""
    try:
        try:
            data = await request.json()
        except Exception:
            data = {}
        component = (data.get("component") or "").strip().lower()
        sudo_password = data.get("sudo_password") or sudo_password_store.get("password") or ""
        if component not in ("homeassistant", "openhab", "nodered"):
            return JSONResponse(status_code=200, content={"status": "error", "message": "Ungültige Komponente."})
        if not sudo_password:
            sudo_test = run_command("sudo -n true", sudo=False)
            if not sudo_test["success"]:
                return JSONResponse(status_code=200, content={"status": "error", "message": "Sudo-Passwort erforderlich", "requires_sudo_password": True})
        results = []
        if component == "homeassistant":
            run_command("docker stop homeassistant 2>/dev/null; docker rm homeassistant 2>/dev/null", sudo=True, sudo_password=sudo_password)
            results.append("Home Assistant Container gestoppt/entfernt.")
        elif component == "openhab":
            run_command("systemctl stop openhab 2>/dev/null; systemctl disable openhab 2>/dev/null", sudo=True, sudo_password=sudo_password)
            run_command("apt-get remove -y openhab 2>/dev/null", sudo=True, sudo_password=sudo_password)
            results.append("OpenHAB deinstalliert.")
        elif component == "nodered":
            run_command("systemctl stop node-red 2>/dev/null; systemctl disable node-red 2>/dev/null", sudo=True, sudo_password=sudo_password)
            run_command("npm uninstall -g node-red 2>/dev/null", sudo=True, sudo_password=sudo_password)
            results.append("Node-RED deinstalliert.")
        return {"status": "success", "message": "Deinstallation durchgeführt.", "results": results}
    except Exception as e:
        return JSONResponse(status_code=200, content={"status": "error", "message": str(e)})


@app.post("/api/homeautomation/configure")
async def configure_homeautomation(request: Request):
    """Homeautomation konfigurieren"""
    try:
        try:
            data = await request.json()
        except:
            data = {}
        
        sudo_password = data.get("sudo_password", "") or sudo_password_store.get("password", "")
        
        if not sudo_password:
            sudo_test = run_command("sudo -n true", sudo=False)
            if not sudo_test["success"]:
                return JSONResponse(
                    status_code=200,
                    content={
                        "status": "error",
                        "message": "Sudo-Passwort erforderlich",
                        "requires_sudo_password": True
                    }
                )
        
        if sudo_password and not sudo_password_store.get("password"):
            sudo_password_store["password"] = sudo_password
        
        results = []
        automation_type = data.get("automation_type", "homeassistant")
        
        # Home Assistant installieren
        if automation_type == "homeassistant":
            # Home Assistant via Docker (empfohlen)
            docker_installed = check_installed("docker")
            if not docker_installed:
                docker_result = run_command("apt-get install -y docker.io docker-compose", sudo=True, sudo_password=sudo_password)
                if docker_result["success"]:
                    results.append("Docker installiert")
            
            # Home Assistant Container starten
            ha_result = run_command("docker run -d --name homeassistant --privileged --restart=unless-stopped -v /home/homeassistant:/config --network=host ghcr.io/home-assistant/home-assistant:stable", sudo=True, sudo_password=sudo_password)
            if ha_result["success"]:
                results.append("Home Assistant gestartet")
            else:
                results.append("⚠️ Home Assistant: Bitte manuell installieren (siehe Dokumentation)")
        
        # OpenHAB installieren
        elif automation_type == "openhab":
            openhab_installed = check_installed("openhab")
            if not openhab_installed:
                openhab_result = run_command("apt-get install -y openhab", sudo=True, sudo_password=sudo_password)
                if openhab_result["success"]:
                    results.append("OpenHAB installiert")
            
            openhab_start = run_command("systemctl enable --now openhab", sudo=True, sudo_password=sudo_password)
            if openhab_start["success"]:
                results.append("OpenHAB aktiviert")
        
        # Node-RED installieren
        elif automation_type == "nodered":
            node_installed = check_installed("nodejs")
            if not node_installed:
                node_result = run_command("apt-get install -y nodejs npm", sudo=True, sudo_password=sudo_password)
                if node_result["success"]:
                    results.append("Node.js installiert")
            
            # Node-RED global installieren
            nodered_result = run_command("npm install -g node-red", sudo=True, sudo_password=sudo_password)
            if nodered_result["success"]:
                results.append("Node-RED installiert")
            
            # Node-RED als Service einrichten
            nodered_service = run_command("systemctl enable --now node-red", sudo=True, sudo_password=sudo_password)
            if nodered_service["success"]:
                results.append("Node-RED aktiviert")
        
        return {
            "status": "success",
            "message": "Homeautomation konfiguriert",
            "results": results
        }
    except Exception as e:
        logger.error(f"💥 Fehler bei Homeautomation-Konfiguration: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=200,
            content={
                "status": "error",
                "message": f"Fehler bei der Homeautomation-Konfiguration: {str(e)}"
            }
        )

# ==================== Music Box Endpoints ====================

@app.get("/api/musicbox/status")
async def musicbox_status():
    """MusicBox-Status abrufen"""
    try:
        installed = get_installed_apps()
        running = get_running_services()
        
        return {
            "mopidy": {
                "installed": check_installed("mopidy"),
                "running": running.get("mopidy", False),
            },
            "volumio": {
                "installed": check_installed("volumio") or run_command("test -f /opt/volumio/bin/volumio")["success"],
                "running": running.get("volumio", False),
            },
            "plex": {
                "installed": check_installed("plexmediaserver") or run_command("dpkg -l | grep plex")["success"],
                "running": running.get("plexmediaserver", False),
            },
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/musicbox/mopidy-diagnose")
async def musicbox_mopidy_diagnose():
    """Mopidy/Iris-Diagnose: warum Iris ggf. nicht lädt (ohne Sudo nur Teilinfos)."""
    try:
        out = {
            "iris_import_current_user": run_command("python3 -c 'import mopidy_iris' 2>/dev/null", sudo=False)["success"],
            "mopidy_running": get_running_services().get("mopidy", False),
            "mopidy_installed": check_installed("mopidy"),
            "iris_visible_to_mopidy": None,
            "iris_config_snippet": None,
            "mopidy_extensions_output": None,
            "mopidy_deps": None,
            "mopidy_log_tail": None,
            "sudo_used": False,
        }
        sudo_password = sudo_password_store.get("password") or ""
        if sudo_password:
            out["sudo_used"] = True
            out["iris_visible_to_mopidy"] = run_command(
                "sudo -n -u mopidy python3 -c 'import mopidy_iris' 2>/dev/null",
                sudo=True, sudo_password=sudo_password
            )["success"]
            r = run_command(
                "grep -A5 '^\\[iris\\]' /etc/mopidy/mopidy.conf 2>/dev/null || true",
                sudo=True, sudo_password=sudo_password
            )
            if r.get("stdout"):
                out["iris_config_snippet"] = r["stdout"].strip()
            r2 = run_command(
                "sudo -n -u mopidy mopidy config 2>&1 | head -120",
                sudo=True, sudo_password=sudo_password
            )
            if r2.get("stdout"):
                out["mopidy_extensions_output"] = r2["stdout"].strip()
            r2d = run_command(
                "sudo -n -u mopidy mopidy deps 2>&1",
                sudo=True, sudo_password=sudo_password
            )
            if r2d.get("stdout"):
                out["mopidy_deps"] = r2d["stdout"].strip()
            r3 = run_command(
                "journalctl -u mopidy -n 50 --no-pager 2>&1",
                sudo=True, sudo_password=sudo_password
            )
            if r3.get("stdout"):
                out["mopidy_log_tail"] = r3["stdout"].strip()
        return out
    except Exception as e:
        logger.exception("Mopidy-Diagnose fehlgeschlagen")
        return {"error": str(e)}


@app.post("/api/musicbox/configure")
async def configure_musicbox(request: Request):
    """MusicBox konfigurieren"""
    try:
        try:
            data = await request.json()
        except:
            data = {}
        
        sudo_password = data.get("sudo_password", "") or sudo_password_store.get("password", "")
        
        if not sudo_password:
            sudo_test = run_command("sudo -n true", sudo=False)
            if not sudo_test["success"]:
                return JSONResponse(
                    status_code=200,
                    content={
                        "status": "error",
                        "message": "Sudo-Passwort erforderlich",
                        "requires_sudo_password": True
                    }
                )
        
        if sudo_password and not sudo_password_store.get("password"):
            sudo_password_store["password"] = sudo_password
        
        results = []
        music_type = data.get("music_type", "mopidy")
        
        # Mopidy installieren
        if music_type == "mopidy":
            mopidy_installed = check_installed("mopidy")
            if not mopidy_installed:
                # Mopidy Repository hinzufügen
                repo_result = run_command("curl -L https://apt.mopidy.com/mopidy.gpg | apt-key add -", sudo=True, sudo_password=sudo_password)
                if repo_result["success"]:
                    echo_result = run_command('echo "deb https://apt.mopidy.com/ stable main contrib non-free" > /etc/apt/sources.list.d/mopidy.list', sudo=True, sudo_password=sudo_password)
                    if echo_result["success"]:
                        update_result = run_command("apt-get update", sudo=True, sudo_password=sudo_password)
                        if update_result["success"]:
                            mopidy_install = run_command("apt-get install -y mopidy mopidy-spotify", sudo=True, sudo_password=sudo_password)
                            if mopidy_install["success"]:
                                results.append("Mopidy installiert")
            
            mopidy_start = run_command("systemctl enable --now mopidy", sudo=True, sudo_password=sudo_password)
            if mopidy_start["success"]:
                results.append("Mopidy aktiviert")
            
            # Mopidy-Webclient: Ohne Erweiterung zeigt localhost:6680 nur Platzhalter. Iris = volle Weboberfläche.
            # Mopidy läuft als User "mopidy" – Iris muss für diesen User sichtbar sein (--user für mopidy oder system-weit).
            webclient_installed_this_run = False
            iris_visible_to_mopidy = run_command("sudo -n -u mopidy python3 -c 'import mopidy_iris' 2>/dev/null", sudo=True, sudo_password=sudo_password)["success"]
            if not iris_visible_to_mopidy:
                pip_ok = run_command("apt-get install -y python3-pip", sudo=True, sudo_password=sudo_password)["success"]
                if pip_ok:
                    # Zuerst system-weit versuchen (für alle Nutzer sichtbar)
                    iris_pip = run_command("PIP_ROOT_USER_ACTION=ignore python3 -m pip install --break-system-packages Mopidy-Iris", sudo=True, sudo_password=sudo_password)
                    if not iris_pip["success"]:
                        iris_pip = run_command("PIP_ROOT_USER_ACTION=ignore python3 -m pip install Mopidy-Iris", sudo=True, sudo_password=sudo_password)
                    # Prüfen, ob User "mopidy" die Erweiterung jetzt sieht (Dienst läuft als mopidy)
                    iris_visible_to_mopidy = run_command("sudo -n -u mopidy python3 -c 'import mopidy_iris' 2>/dev/null", sudo=True, sudo_password=sudo_password)["success"]
                    if not iris_visible_to_mopidy and iris_pip["success"]:
                        # System-Pfad wird von mopidy nicht gelesen → als User mopidy installieren
                        run_command("sudo -n -u mopidy PIP_ROOT_USER_ACTION=ignore python3 -m pip install --user --break-system-packages Mopidy-Iris", sudo=True, sudo_password=sudo_password)
                        iris_visible_to_mopidy = run_command("sudo -n -u mopidy python3 -c 'import mopidy_iris' 2>/dev/null", sudo=True, sudo_password=sudo_password)["success"]
                    if iris_visible_to_mopidy or iris_pip["success"]:
                        results.append("Mopidy-Webclient (Iris) installiert – nach Neustart unter http://localhost:6680/iris")
                        webclient_installed_this_run = True
                    else:
                        mbox = run_command("apt-get install -y mopidy-musicbox-webclient", sudo=True, sudo_password=sudo_password)
                        if mbox["success"]:
                            results.append("Mopidy-Webclient (MusicBox) installiert – unter http://localhost:6680")
                            webclient_installed_this_run = True
                        else:
                            results.append("Hinweis: Mopidy-Webclient manuell als User mopidy: sudo -u mopidy python3 -m pip install --user --break-system-packages Mopidy-Iris, dann systemctl restart mopidy")
                else:
                    results.append("Hinweis: python3-pip installieren, dann: sudo -u mopidy python3 -m pip install --user --break-system-packages Mopidy-Iris, Mopidy neustarten")
            else:
                results.append("Mopidy-Webclient (Iris) bereits installiert – http://localhost:6680/iris")
            
            # [iris] in mopidy.conf ergänzen, falls vorhanden und noch nicht gesetzt
            mopidy_conf = "/etc/mopidy/mopidy.conf"
            conf_check = run_command(f"grep -q '^\\[iris\\]' {mopidy_conf} 2>/dev/null", sudo=True, sudo_password=sudo_password)["success"]
            if not conf_check:
                run_command(
                    f"echo '' >> {mopidy_conf} && echo '[iris]' >> {mopidy_conf} && echo 'enabled = true' >> {mopidy_conf}",
                    sudo=True, sudo_password=sudo_password
                )
            
            if webclient_installed_this_run:
                run_command("systemctl restart mopidy", sudo=True, sudo_password=sudo_password)
            
            # Internetradio (Mopidy-Erweiterung)
            if data.get("enable_internetradio"):
                ir_installed = run_command("dpkg -l mopidy-internetarchive 2>/dev/null | grep -q ^ii", sudo=False)["success"]
                if not ir_installed:
                    ir_result = run_command("apt-get install -y mopidy-internetarchive", sudo=True, sudo_password=sudo_password)
                    if ir_result["success"]:
                        results.append("Mopidy Internetradio (mopidy-internetarchive) installiert")
                else:
                    results.append("Mopidy Internetradio bereits installiert")
        
        # Volumio installieren (komplexer, benötigt spezielle Installation)
        elif music_type == "volumio":
            results.append("⚠️ Volumio: Bitte manuell installieren (siehe https://volumio.org/get-started/)")
        
        # Plex Media Server installieren
        elif music_type == "plex":
            plex_installed = check_installed("plexmediaserver")
            if not plex_installed:
                # Plex Repository hinzufügen
                repo_result = run_command("curl https://downloads.plex.tv/plex-keys/PlexSign.key | apt-key add -", sudo=True, sudo_password=sudo_password)
                if repo_result["success"]:
                    echo_result = run_command('echo "deb https://downloads.plex.tv/repo/deb public main" > /etc/apt/sources.list.d/plexmediaserver.list', sudo=True, sudo_password=sudo_password)
                    if echo_result["success"]:
                        update_result = run_command("apt-get update", sudo=True, sudo_password=sudo_password)
                        if update_result["success"]:
                            plex_install = run_command("apt-get install -y plexmediaserver", sudo=True, sudo_password=sudo_password)
                            if plex_install["success"]:
                                results.append("Plex Media Server installiert")
            
            plex_start = run_command("systemctl enable --now plexmediaserver", sudo=True, sudo_password=sudo_password)
            if plex_start["success"]:
                results.append("Plex aktiviert")
        
        # Streaming (Spotify etc. – bei Mopidy bereits über enable_spotify/mopidy-spotify abgedeckt)
        if data.get("enable_streaming") and music_type == "mopidy" and not check_installed("mopidy-spotify"):
            spotify_install = run_command("apt-get install -y mopidy-spotify", sudo=True, sudo_password=sudo_password)
            if spotify_install["success"]:
                results.append("Mopidy Spotify-Erweiterung installiert (Spotify-Abo erforderlich)")
        if data.get("enable_streaming"):
            results.append("Apple Music: per AirPlay von iPhone/iPad streamen (AirPlay Support aktivieren). Amazon Music: Volumio-Weboberfläche oder Browser (music.amazon.com).")
        
        # AirPlay Support (Shairport-sync)
        if data.get("enable_airplay"):
            shairport_installed = check_installed("shairport-sync")
            if not shairport_installed:
                shairport_result = run_command("apt-get install -y shairport-sync", sudo=True, sudo_password=sudo_password)
                if shairport_result["success"]:
                    results.append("AirPlay (Shairport-sync) installiert")
            
            shairport_start = run_command("systemctl enable --now shairport-sync", sudo=True, sudo_password=sudo_password)
            if shairport_start["success"]:
                results.append("AirPlay aktiviert")
        
        return {
            "status": "success",
            "message": "Musikbox konfiguriert",
            "results": results
        }
    except Exception as e:
        logger.error(f"💥 Fehler bei MusicBox-Konfiguration: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=200,
            content={
                "status": "error",
                "message": f"Fehler bei der MusicBox-Konfiguration: {str(e)}"
            }
        )

# ==================== Dev Environment Endpoints ====================

@app.get("/api/devenv/status")
async def devenv_status():
    """Entwicklungsumgebung Status"""
    try:
        installed = get_installed_apps()
        
        # Hole Versionen
        python_version = get_package_version("python3")
        nodejs_version = get_package_version("nodejs")
        git_version = get_package_version("git")
        docker_version = get_package_version("docker")
        mysql_version = get_package_version("mysql")
        postgresql_version = get_package_version("postgresql")
        
        # Cursor AI prüfen
        cursor_installed = installed.get("cursor", False)
        cursor_version = None
        if cursor_installed:
            cursor_version_result = run_command("cursor --version 2>/dev/null || cursor -v 2>/dev/null")
            if cursor_version_result["success"]:
                cursor_version = cursor_version_result["stdout"].strip()
        
        return {
            "python": {
                "installed": installed.get("python", False),
                "version": python_version,
            },
            "nodejs": {
                "installed": installed.get("nodejs", False),
                "version": nodejs_version,
            },
            "git": {
                "installed": installed.get("git", False),
                "version": git_version,
            },
            "docker": {
                "installed": installed.get("docker", False),
                "version": docker_version,
            },
            "mysql": {
                "installed": installed.get("mysql", False),
                "version": mysql_version,
            },
            "postgresql": {
                "installed": installed.get("postgresql", False),
                "version": postgresql_version,
            },
            "cursor": {
                "installed": cursor_installed,
                "version": cursor_version,
            },
            "qtqml": {
                "installed": installed.get("qtqml", False),
                "version": get_package_version("qt5-default") or get_package_version("qtbase5-dev") or None,
            },
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== Installation Endpoints ====================

@app.post("/api/install/start")
async def start_installation(request: Request):
    """Installation starten"""
    try:
        try:
            data = await request.json()
        except:
            data = {}
        
        sudo_password = data.get("sudo_password", "") or sudo_password_store.get("password", "")
        
        # Prüfe ob sudo-Passwort vorhanden ist
        if not sudo_password:
            sudo_test = run_command("sudo -n true", sudo=False)
            if not sudo_test["success"]:
                return JSONResponse(
                    status_code=200,
                    content={
                        "status": "error",
                        "message": "Sudo-Passwort erforderlich",
                        "requires_sudo_password": True
                    }
                )
        
        if sudo_password and not sudo_password_store.get("password"):
            sudo_password_store["password"] = sudo_password
        
        security_config = data.get("security", {})
        users_config = data.get("users", [])
        devenv_config = data.get("devenv", {})
        webserver_config = data.get("webserver", {})
        mail_config = data.get("mail", {})
        
        results = []
        total_steps = 0
        completed_steps = 0
        
        # Sicherheit konfigurieren
        if security_config:
            total_steps += 1
            try:
                # Führe Sicherheitskonfiguration direkt aus
                security_results = []
                
                # Firewall aktivieren
                if security_config.get("enable_firewall"):
                    ufw_installed = check_installed("ufw")
                    if not ufw_installed:
                        install_result = run_command("apt-get install -y ufw", sudo=True, sudo_password=sudo_password)
                        if install_result["success"]:
                            security_results.append("UFW installiert")
                    
                    enable_result = run_command("ufw --force enable", sudo=True, sudo_password=sudo_password)
                    if enable_result["success"]:
                        security_results.append("Firewall aktiviert")
                
                # Fail2Ban
                if security_config.get("enable_fail2ban"):
                    fail2ban_installed = check_installed("fail2ban")
                    if not fail2ban_installed:
                        install_result = run_command("apt-get install -y fail2ban", sudo=True, sudo_password=sudo_password)
                        if install_result["success"]:
                            security_results.append("Fail2Ban installiert")
                    
                    start_result = run_command("systemctl enable --now fail2ban", sudo=True, sudo_password=sudo_password)
                    if start_result["success"]:
                        security_results.append("Fail2Ban aktiviert")
                
                # Auto-Updates
                if security_config.get("enable_auto_updates"):
                    install_result = run_command("apt-get install -y unattended-upgrades", sudo=True, sudo_password=sudo_password)
                    if install_result["success"]:
                        enable_result = run_command("systemctl enable unattended-upgrades", sudo=True, sudo_password=sudo_password)
                        if enable_result["success"]:
                            security_results.append("Auto-Updates aktiviert")
                
                if security_results:
                    completed_steps += 1
                    results.extend(security_results)
                else:
                    results.append("Sicherheit: Keine Änderungen")
            except Exception as e:
                logger.error(f"Fehler bei Sicherheitskonfiguration: {e}")
                results.append(f"Sicherheit: Fehler - {str(e)}")
        
        # Benutzer erstellen
        if users_config and len(users_config) > 0:
            total_steps += len(users_config)
            for user in users_config:
                try:
                    # Erstelle Benutzer direkt
                    username = user.get("username", "")
                    password = user.get("password", "")
                    role = user.get("role", "user")
                    
                    if username and password:
                        # Führe useradd direkt aus
                        useradd_cmd = f"useradd -m -s /bin/bash {username}"
                        useradd_result = run_command(useradd_cmd, sudo=True, sudo_password=sudo_password)
                        
                        if useradd_result["success"]:
                            # Setze Passwort
                            chpasswd_cmd = f"echo '{username}:{password}' | chpasswd"
                            chpasswd_result = run_command(chpasswd_cmd, sudo=True, sudo_password=sudo_password)
                            
                            if chpasswd_result["success"]:
                                completed_steps += 1
                                results.append(f"Benutzer {username} erstellt")
                            else:
                                results.append(f"Benutzer {username}: Passwort konnte nicht gesetzt werden")
                        else:
                            results.append(f"Benutzer {username}: Konnte nicht erstellt werden")
                except Exception as e:
                    logger.error(f"Fehler bei Benutzererstellung: {e}")
                    results.append(f"Benutzer {user.get('username', '')}: Fehler - {str(e)}")
        
        # Entwicklungsumgebung
        if devenv_config:
            total_steps += 1
            results.append("Entwicklungsumgebung: Konfiguration wird vorbereitet")
            # TODO: Implementiere devenv configure endpoint
        
        # Webserver
        if webserver_config:
            total_steps += 1
            try:
                server_type = webserver_config.get("server_type", "nginx")
                enable_php = webserver_config.get("enable_php", False)
                webserver_results = []
                
                # Webserver installieren
                if server_type == "nginx":
                    nginx_installed = check_installed("nginx")
                    if not nginx_installed:
                        nginx_result = run_command("apt-get install -y nginx", sudo=True, sudo_password=sudo_password)
                        if nginx_result["success"]:
                            webserver_results.append("Nginx installiert")
                    
                    nginx_start = run_command("systemctl enable --now nginx", sudo=True, sudo_password=sudo_password)
                    if nginx_start["success"]:
                        webserver_results.append("Nginx aktiviert")
                
                elif server_type == "apache":
                    apache_installed = check_installed("apache2")
                    if not apache_installed:
                        apache_result = run_command("apt-get install -y apache2", sudo=True, sudo_password=sudo_password)
                        if apache_result["success"]:
                            webserver_results.append("Apache installiert")
                    
                    apache_start = run_command("systemctl enable --now apache2", sudo=True, sudo_password=sudo_password)
                    if apache_start["success"]:
                        webserver_results.append("Apache aktiviert")
                
                # PHP installieren
                if enable_php:
                    php_installed = check_installed("php")
                    if not php_installed:
                        php_result = run_command("apt-get install -y php php-fpm php-cli php-common", sudo=True, sudo_password=sudo_password)
                        if php_result["success"]:
                            webserver_results.append("PHP installiert")
                    
                    if server_type == "nginx":
                        php_fpm_start = run_command("systemctl enable --now php*-fpm", sudo=True, sudo_password=sudo_password)
                        if php_fpm_start["success"]:
                            webserver_results.append("PHP-FPM aktiviert")
                    elif server_type == "apache":
                        apache_php = run_command("apt-get install -y libapache2-mod-php", sudo=True, sudo_password=sudo_password)
                        if apache_php["success"]:
                            webserver_results.append("Apache PHP-Modul installiert")
                
                if webserver_results:
                    completed_steps += 1
                    results.extend(webserver_results)
                else:
                    results.append("Webserver: Keine Änderungen")
            except Exception as e:
                logger.error(f"Fehler bei Webserver-Konfiguration: {e}")
                results.append(f"Webserver: Fehler - {str(e)}")
        
        # Mailserver
        if mail_config:
            total_steps += 1
            results.append("Mailserver: Konfiguration wird vorbereitet")
            # TODO: Implementiere mailserver configure endpoint
        
        # Aktualisiere globalen Fortschritt
        progress_percent = (completed_steps / total_steps * 100) if total_steps > 0 else 0
        installation_progress["progress"] = progress_percent
        installation_progress["message"] = f"{completed_steps}/{total_steps} Schritte abgeschlossen"
        installation_progress["current_step"] = "Installation läuft"
        
        return {
            "status": "success",
            "message": "Installation gestartet",
            "total_steps": total_steps,
            "completed_steps": completed_steps,
            "results": results,
            "progress": progress_percent
        }
    except Exception as e:
        logger.error(f"💥 Fehler bei Installation: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=200,
            content={
                "status": "error",
                "message": f"Fehler beim Starten der Installation: {str(e)}"
            }
        )

@app.get("/api/install/progress")
async def get_progress():
    """Installationsfortschritt"""
    return installation_progress

# ==================== Learning Computer Endpoints ====================

@app.get("/api/learning/status")
async def learning_status():
    """Lerncomputer-Status abrufen"""
    try:
        installed = get_installed_apps()
        
        return {
            "scratch": {
                "installed": check_installed("scratch") or run_command("which scratch")["success"],
            },
            "python_learning": {
                "installed": check_installed("python3"),
                "version": get_package_version("python3"),
            },
            "robotics": {
                "installed": check_installed("python3-gpiozero") or check_installed("python3-rpi.gpio"),
            },
            "electronics": {
                "installed": check_installed("fritzing") or check_installed("kicad"),
            },
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/learning/configure")
async def configure_learning(request: Request):
    """Lerncomputer konfigurieren"""
    try:
        try:
            data = await request.json()
        except:
            data = {}
        
        sudo_password = data.get("sudo_password", "") or sudo_password_store.get("password", "")
        
        if not sudo_password:
            sudo_test = run_command("sudo -n true", sudo=False)
            if not sudo_test["success"]:
                return JSONResponse(
                    status_code=200,
                    content={
                        "status": "error",
                        "message": "Sudo-Passwort erforderlich",
                        "requires_sudo_password": True
                    }
                )
        
        results = []
        
        # Scratch Programmierung
        if data.get("enable_scratch"):
            scratch_installed = check_installed("scratch")
            if not scratch_installed:
                # Scratch3 installieren (Node.js-basiert)
                scratch_result = run_command("npm install -g scratch-vm scratch-gui", sudo=True, sudo_password=sudo_password)
                if scratch_result["success"]:
                    results.append("Scratch installiert")
                else:
                    # Alternativ: Scratch Desktop
                    scratch_desktop = run_command("apt-get install -y scratch", sudo=True, sudo_password=sudo_password)
                    if scratch_desktop["success"]:
                        results.append("Scratch Desktop installiert")
            else:
                results.append("Scratch bereits installiert")
        
        # Python Lernumgebung
        if data.get("enable_python_learning"):
            python_installed = check_installed("python3")
            if not python_installed:
                python_result = run_command("apt-get install -y python3 python3-pip python3-venv", sudo=True, sudo_password=sudo_password)
                if python_result["success"]:
                    results.append("Python Lernumgebung installiert")
            else:
                results.append("Python bereits installiert")
            
            # Jupyter Notebook für interaktives Lernen
            jupyter_result = run_command("pip3 install --user jupyter notebook", sudo=False)
            if jupyter_result["success"]:
                results.append("Jupyter Notebook installiert")
        
        # Robotik (GPIO)
        if data.get("enable_robotics"):
            gpio_installed = check_installed("python3-gpiozero")
            if not gpio_installed:
                gpio_result = run_command("apt-get install -y python3-gpiozero python3-rpi.gpio python3-picamera2", sudo=True, sudo_password=sudo_password)
                if gpio_result["success"]:
                    results.append("Robotik-Bibliotheken installiert")
            else:
                results.append("Robotik-Bibliotheken bereits installiert")
            
            # Beispiel-Projekte erstellen
            examples_dir = "/home/pi/robotik-beispiele"
            mkdir_result = run_command(f"mkdir -p {examples_dir}", sudo=False)
            if mkdir_result["success"]:
                results.append("Robotik-Beispiele-Verzeichnis erstellt")
        
        # Elektronik Grundlagen
        if data.get("enable_electronics"):
            fritzing_installed = check_installed("fritzing")
            if not fritzing_installed:
                fritzing_result = run_command("apt-get install -y fritzing", sudo=True, sudo_password=sudo_password)
                if fritzing_result["success"]:
                    results.append("Fritzing (Elektronik-Design) installiert")
            else:
                results.append("Fritzing bereits installiert")
        
        # Mathematik-Tools
        if data.get("enable_math_tools"):
            # Geogebra oder ähnliche Tools
            geogebra_result = run_command("apt-get install -y geogebra", sudo=True, sudo_password=sudo_password)
            if geogebra_result["success"]:
                results.append("Geogebra (Mathematik) installiert")
            else:
                # Alternativ: Python-Mathematik-Bibliotheken
                math_libs = run_command("pip3 install --user numpy matplotlib scipy sympy", sudo=False)
                if math_libs["success"]:
                    results.append("Mathematik-Bibliotheken installiert")
        
        return {
            "status": "success",
            "message": "Lerncomputer konfiguriert",
            "results": results
        }
    except Exception as e:
        logger.error(f"💥 Fehler bei Lerncomputer-Konfiguration: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=200,
            content={
                "status": "error",
                "message": f"Fehler bei der Lerncomputer-Konfiguration: {str(e)}"
            }
        )

# ==================== Monitoring Endpoints ====================

@app.get("/api/monitoring/status")
async def monitoring_status():
    """Monitoring-Status abrufen"""
    try:
        # Laufend: systemd-Dienstnamen (grafana-server, nicht grafana)
        prometheus_running = run_command("systemctl is-active prometheus 2>/dev/null")["success"]
        grafana_running = run_command("systemctl is-active grafana-server 2>/dev/null")["success"]
        node_exporter_running = run_command("systemctl is-active node_exporter 2>/dev/null")["success"]

        return {
            "prometheus": {
                "installed": check_installed("prometheus") or run_command("which prometheus 2>/dev/null")["success"] or run_command("test -f /usr/bin/prometheus 2>/dev/null")["success"],
                "running": prometheus_running,
            },
            "grafana": {
                "installed": check_installed("grafana"),
                "running": grafana_running,
            },
            "node_exporter": {
                "installed": check_installed("node_exporter") or run_command("which node_exporter 2>/dev/null")["success"] or run_command("test -f /usr/local/bin/node_exporter 2>/dev/null")["success"],
                "running": node_exporter_running,
            },
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/monitoring/configure")
async def configure_monitoring(request: Request):
    """Monitoring konfigurieren"""
    try:
        try:
            data = await request.json()
        except:
            data = {}
        
        sudo_password = data.get("sudo_password", "") or sudo_password_store.get("password", "")
        
        if not sudo_password:
            sudo_test = run_command("sudo -n true", sudo=False)
            if not sudo_test["success"]:
                return JSONResponse(
                    status_code=200,
                    content={
                        "status": "error",
                        "message": "Sudo-Passwort erforderlich",
                        "requires_sudo_password": True
                    }
                )
        
        results = []
        
        # Node Exporter (System-Metriken)
        if data.get("enable_node_exporter"):
            node_exporter_installed = check_installed("node_exporter")
            if not node_exporter_installed:
                # Node Exporter herunterladen und installieren
                node_exporter_result = run_command(
                    "wget https://github.com/prometheus/node_exporter/releases/download/v1.6.1/node_exporter-1.6.1.linux-arm64.tar.gz -O /tmp/node_exporter.tar.gz && "
                    "tar xzf /tmp/node_exporter.tar.gz -C /tmp && "
                    "sudo mv /tmp/node_exporter-1.6.1.linux-arm64/node_exporter /usr/local/bin/ && "
                    "sudo chmod +x /usr/local/bin/node_exporter",
                    sudo=True, sudo_password=sudo_password
                )
                if node_exporter_result["success"]:
                    # Systemd Service erstellen
                    service_content = """[Unit]
Description=Node Exporter
After=network.target

[Service]
Type=simple
User=prometheus
ExecStart=/usr/local/bin/node_exporter

[Install]
WantedBy=multi-user.target"""
                    
                    service_file = "/tmp/node_exporter.service"
                    with open(service_file, 'w') as f:
                        f.write(service_content)
                    
                    install_service = run_command(
                        f"sudo mv {service_file} /etc/systemd/system/node_exporter.service && "
                        "sudo systemctl daemon-reload && "
                        "sudo systemctl enable node_exporter && "
                        "sudo systemctl start node_exporter",
                        sudo=True, sudo_password=sudo_password
                    )
                    if install_service["success"]:
                        results.append("Node Exporter installiert und aktiviert")
            else:
                results.append("Node Exporter bereits installiert")
        
        # Prometheus
        if data.get("enable_prometheus"):
            prometheus_installed = check_installed("prometheus")
            if not prometheus_installed:
                prometheus_result = run_command(
                    "apt-get install -y prometheus",
                    sudo=True, sudo_password=sudo_password
                )
                if prometheus_result["success"]:
                    # Prometheus konfigurieren
                    prometheus_config = """global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'node'
    static_configs:
      - targets: ['localhost:9100']
"""
                    config_file = "/tmp/prometheus.yml"
                    with open(config_file, 'w') as f:
                        f.write(prometheus_config)
                    
                    move_config = run_command(
                        f"sudo mv {config_file} /etc/prometheus/prometheus.yml && "
                        "sudo systemctl restart prometheus",
                        sudo=True, sudo_password=sudo_password
                    )
                    if move_config["success"]:
                        results.append("Prometheus installiert und konfiguriert")
            else:
                results.append("Prometheus bereits installiert")
        
        # Grafana
        if data.get("enable_grafana"):
            grafana_installed = check_installed("grafana")
            if not grafana_installed:
                # Grafana Repository hinzufügen
                add_repo = run_command(
                    "sudo apt-get install -y apt-transport-https software-properties-common && "
                    "wget -q -O - https://packages.grafana.com/gpg.key | sudo apt-key add - && "
                    "echo 'deb https://packages.grafana.com/oss/deb stable main' | sudo tee /etc/apt/sources.list.d/grafana.list && "
                    "sudo apt-get update",
                    sudo=True, sudo_password=sudo_password
                )
                
                if add_repo["success"]:
                    grafana_install = run_command(
                        "apt-get install -y grafana",
                        sudo=True, sudo_password=sudo_password
                    )
                    if grafana_install["success"]:
                        grafana_start = run_command(
                            "systemctl enable --now grafana-server",
                            sudo=True, sudo_password=sudo_password
                        )
                        if grafana_start["success"]:
                            results.append("Grafana installiert und aktiviert (Port 3000)")
            else:
                results.append("Grafana bereits installiert")
        
        return {
            "status": "success",
            "message": "Monitoring konfiguriert",
            "results": results
        }
    except Exception as e:
        logger.error(f"💥 Fehler bei Monitoring-Konfiguration: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=200,
            content={
                "status": "error",
                "message": f"Fehler bei der Monitoring-Konfiguration: {str(e)}"
            }
        )

@app.post("/api/monitoring/uninstall")
async def monitoring_uninstall(request: Request):
    """Eine Monitoring-Komponente entfernen (Prometheus, Grafana, Node Exporter)."""
    try:
        try:
            data = await request.json()
        except Exception:
            data = {}
        component = (data.get("component") or "").strip().lower()
        sudo_password = data.get("sudo_password") or sudo_password_store.get("password") or ""
        if component not in ("prometheus", "grafana", "node_exporter"):
            return JSONResponse(
                status_code=200,
                content={"status": "error", "message": "Ungültige Komponente. Erlaubt: prometheus, grafana, node_exporter"}
            )
        if not sudo_password:
            sudo_test = run_command("sudo -n true", sudo=False)
            if not sudo_test["success"]:
                return JSONResponse(
                    status_code=200,
                    content={"status": "error", "message": "Sudo-Passwort erforderlich", "requires_sudo_password": True}
                )
        results = []
        if component == "node_exporter":
            run_command("sudo systemctl stop node_exporter 2>/dev/null; sudo systemctl disable node_exporter 2>/dev/null", sudo=True, sudo_password=sudo_password)
            run_command("sudo rm -f /etc/systemd/system/node_exporter.service 2>/dev/null; sudo systemctl daemon-reload", sudo=True, sudo_password=sudo_password)
            run_command("sudo rm -f /usr/local/bin/node_exporter 2>/dev/null", sudo=True, sudo_password=sudo_password)
            results.append("Node Exporter entfernt.")
        elif component == "prometheus":
            run_command("sudo systemctl stop prometheus 2>/dev/null; sudo systemctl disable prometheus 2>/dev/null", sudo=True, sudo_password=sudo_password)
            run_command("sudo apt-get remove -y prometheus 2>/dev/null; sudo apt-get purge -y prometheus 2>/dev/null", sudo=True, sudo_password=sudo_password)
            results.append("Prometheus entfernt.")
        elif component == "grafana":
            run_command("sudo systemctl stop grafana-server 2>/dev/null; sudo systemctl disable grafana-server 2>/dev/null", sudo=True, sudo_password=sudo_password)
            run_command("sudo apt-get remove -y grafana 2>/dev/null; sudo apt-get purge -y grafana 2>/dev/null", sudo=True, sudo_password=sudo_password)
            results.append("Grafana entfernt.")
        return {"status": "success", "message": f"{component} entfernt", "results": results}
    except Exception as e:
        logger.error(f"Monitoring uninstall error: {e}", exc_info=True)
        return JSONResponse(status_code=200, content={"status": "error", "message": str(e)})

# ==================== GPU/System-Info (ohne Pi) ====================

# AMD iGPU Codenamen -> Handelsbezeichnung (Ryzen 7000 etc.)
_AMD_IGPU_CODENAMES = {
    "raphael": "AMD Radeon 610M (integriert)",   # Ryzen 7045/7945
    "phoenix": "AMD Radeon 760M (integriert)",   # Ryzen 7040
    "phoenix2": "AMD Radeon 760M (integriert)",
    "renoir": "AMD Radeon Graphics (integriert)",  # Ryzen 4000
    "cezanne": "AMD Radeon Graphics (integriert)",  # Ryzen 5000
    "vangogh": "AMD Radeon Graphics (integriert)",
    "rembrandt": "AMD Radeon 680M (integriert)",
    "stoney": "AMD Radeon R5/R7 (integriert)",
}


def _clean_gpu_description(desc: str) -> str:
    """Entfernt technische Bezeichnungen (VGA compatible controller, Audio device, rev xx) und liefert kurze Handelsbezeichnung."""
    if not (desc or "").strip():
        return desc or ""
    s = desc.strip()
    low = s.lower()
    # Audio-Geräte sind keine Grafik – leeren String zurück (wird vom Aufrufer gefiltert)
    if "audio device" in low or (low.startswith("audio ") and "nvidia" in low):
        return ""
    # Führende Controller-Typen entfernen (VGA compatible controller, 3D, Display controller – Benutzer braucht sie nicht)
    if low.startswith("vga ") or low.startswith("vga compatible") or "vga compatible controller:" in low:
        colon = s.find(":")
        if colon >= 0:
            s = s[colon + 1 :].strip()
            low = s.lower()
        else:
            for prefix in ("VGA compatible controller ", "VGA compatible controller: ", "vga compatible controller "):
                if low.startswith(prefix) or prefix.lower() in low:
                    start = low.find("vga compatible controller")
                    end = start + len("vga compatible controller")
                    if end < len(s) and s[end : end + 1] in (":", " "):
                        s = s[end + 1 :].lstrip(": ").strip()
                    low = s.lower()
                    break
    else:
        for prefix in ["3d ", "display controller: ", "display controller:"]:
            if low.startswith(prefix):
                s = s[len(prefix):].strip()
                low = s.lower()
                break
    # "(rev xx)" am Ende entfernen
    if " (rev " in s and ")" in s:
        idx = s.find(" (rev ")
        if idx > 0:
            s = s[:idx].strip()
    # NVIDIA: Nur Inhalt der eckigen Klammer als Handelsname (z. B. [GeForce RTX 4070 Max-Q / Mobile])
    if "nvidia" in s.lower() and "[" in s and "]" in s:
        start = s.find("[")
        end = s.find("]", start)
        if start >= 0 and end > start:
            name = s[start + 1 : end].strip()
            if name.lower().startswith("geforce") or name.lower().startswith("quadro") or "rtx" in name.lower():
                return "NVIDIA " + name
            return "NVIDIA " + name
    # AMD/ATI: Codenamen (Raphael, Phoenix) -> lesbare Bezeichnung aus Herstellerdaten
    if "amd" in s.lower() or "ati" in s.lower():
        s_lower = s.lower()
        for codename, label in _AMD_IGPU_CODENAMES.items():
            if codename in s_lower:
                return label
        for prefix in ["Advanced Micro Devices, Inc. [AMD/ATI] ", "AMD/ATI ", "AMD "]:
            if s.startswith(prefix):
                s = s[len(prefix):].strip()
                break
        # Letzte eckige Klammer oft Codename (z. B. [AMD/ATI] Raphael)
        if "[" in s and "]" in s:
            bracket = s[s.rfind("[") + 1 : s.rfind("]")].strip()
            codename = bracket.split()[-1].lower() if bracket else ""
            if codename in _AMD_IGPU_CODENAMES:
                return _AMD_IGPU_CODENAMES[codename]
            if bracket and bracket.lower() not in ("amd/ati", "amd"):
                return "AMD " + bracket
        if s and not s.lower().startswith("vga"):
            return s
    # Sicherheit: verbliebene technische Präfixe am Anfang entfernen
    low = s.strip().lower()
    for strip_prefix in ("vga compatible controller:", "vga compatible controller", "audio device:"):
        if low.startswith(strip_prefix):
            s = s[len(strip_prefix):].lstrip(" ").strip()
            low = s.lower()
            break
    # Intel: Nur Grafik-Bezeichnung (UHD Graphics 770, Iris Xe etc.), ohne Chip-Code
    if "intel" in s.lower():
        low = s.lower()
        for marker in ["uhd graphics", "iris xe", "iris graphics", "hd graphics", "iris plus"]:
            i = low.find(marker)
            if i >= 0:
                part = s[i:].strip()
                return "Intel " + part
        for prefix in ["Intel Corporation ", "Intel "]:
            if s.startswith(prefix):
                s = s[len(prefix):].strip()
                break
        return "Intel " + s if s else s
    return s.strip()


def _shorten_gpu_display_name(name: str, gpu_type: str, memory_mb: Optional[int] = None) -> tuple:
    """Liefert (display_name, memory_display). Handelsbezeichnung kurz, Speicher in GB (ggf. GDDR)."""
    name = (name or "").strip()
    n = name.lower()
    mem_display = ""
    if memory_mb is not None and memory_mb > 0:
        gb = memory_mb / 1024
        if gb >= 1:
            mem_display = f"{int(round(gb))} GB"
            if "nvidia" in n and ("rtx 40" in n or "rtx 30" in n or "geforce rtx" in n):
                mem_display += " GDDR6"
            elif "nvidia" in n:
                mem_display += " GDDR5/GDDR6"
        else:
            mem_display = f"{memory_mb} MB"
    # NVIDIA: Bereits bereinigt (z. B. "NVIDIA GeForce RTX 4070 Max-Q / Mobile") oder aus nvidia-smi – nur Prefix prüfen
    if "nvidia" in n and ("geforce" in n or "quadro" in n or "rtx" in n):
        if "corporation" not in n and "vga compatible" not in n and " (rev " not in n and "[" not in name:
            return (name if name.strip().lower().startswith("nvidia") else "NVIDIA " + name.strip(), mem_display)
        s = name.replace("NVIDIA Corporation", "").strip()
        for skip in ["GPU", "Graphics", "NVIDIA "]:
            if s.startswith(skip):
                s = s[len(skip):].strip()
        if "Laptop" in name:
            s = s.replace(" Laptop GPU", "").replace(" Laptop", "").strip() + " Laptop"
        elif "Mobile" in name or "Max-Q" in name:
            s = s.replace(" Mobile", "").replace(" Max-Q", "").strip()
            if "Max-Q" in name:
                s += " Max-Q"
            elif "Mobile" in name:
                s += " Mobile"
        if not s.startswith("NVIDIA"):
            s = "NVIDIA " + s
        return (s.strip() or name, mem_display)
    # Intel: z. B. "Intel UHD Graphics 770" / "Intel Iris Xe Graphics"
    if "intel" in n:
        for marker in ["uhd graphics", "iris xe", "iris graphics", "hd graphics", "iris plus", "graphics"]:
            if marker in n:
                i = n.find(marker)
                part = name[i:].strip() if i >= 0 else name
                return ("Intel " + part, mem_display)
        return (name.split("]")[-1].strip() if "]" in name else name, mem_display)
    # AMD: integriert (Radeon 610M, 760M, Radeon Graphics) vs. diskret (RX 6800)
    if "amd" in n or "radeon" in n or "ati" in n:
        if "radeon graphics" in n or "vega" in n or "610m" in n or "760m" in n or ("radeon" in n and "rx " not in n and "graphics" in n):
            short = name
            for prefix in ["Advanced Micro Devices, Inc. [AMD/ATI]", "AMD/ATI", "AMD"]:
                if short.startswith(prefix):
                    short = short[len(prefix):].strip()
            if gpu_type == "integrated" and "integriert" not in short.lower():
                short = short + " (integriert)" if short else "AMD Radeon (integriert)"
            return (short or name, mem_display)
        short = name.split("[")[-1].split("]")[0].strip() if "[" in name else name
        for prefix in ["Advanced Micro Devices, Inc. [AMD/ATI]", "AMD/ATI", "AMD"]:
            if short.startswith(prefix):
                short = short[len(prefix):].strip()
        return (short or name, mem_display)
    return (name, mem_display)


def _get_gpus_for_system_info():
    """GPU-Liste für System-Info (Nicht-Pi): Handelsbezeichnung kurz, Speicher in GB. iGPU getrennt, Audio-Geräte nie als Grafik."""
    gpus = []
    try:
        pci_list = _get_pci_with_drivers()
        seen = set()
        for item in pci_list:
            desc = (item.get("description") or "").strip()
            desc_lower = desc.lower()
            # Audio-Geräte sind keine Grafikkarten – immer ausblenden (NVIDIA HDMI-Audio, Audio device, etc.)
            if "audio device" in desc_lower or "high definition audio" in desc_lower or "hdmi audio" in desc_lower or ("audio" in desc_lower and "nvidia" in desc_lower):
                continue
            # Nur echte Grafik-Controller: VGA, 3D, Display – kein reines "NVIDIA" (könnte Audio sein)
            is_vga_3d_display = "vga" in desc_lower or "3d" in desc_lower or "display" in desc_lower
            is_intel_graphics = "intel" in desc_lower and ("graphics" in desc_lower or "uhd" in desc_lower or "iris" in desc_lower or "vga" in desc_lower)
            is_amd_radeon = ("radeon" in desc_lower or "amd" in desc_lower or "ati" in desc_lower) and ("graphics" in desc_lower or "vga" in desc_lower or "display" in desc_lower or "raphael" in desc_lower or "phoenix" in desc_lower)
            is_nvidia_graphics = "nvidia" in desc_lower and (is_vga_3d_display or "geforce" in desc_lower or "quadro" in desc_lower or "rtx" in desc_lower or "gtx" in desc_lower)
            if not (is_vga_3d_display or is_intel_graphics or is_amd_radeon or is_nvidia_graphics):
                continue
            # Typ: integriert (Intel iGPU, AMD Codenamen Raphael/Phoenix, Radeon Graphics) vs. diskret
            gpu_type = "discrete"
            if is_intel_graphics:
                gpu_type = "integrated"
            elif is_amd_radeon and (
                "radeon graphics" in desc_lower or "vega" in desc_lower or "610m" in desc_lower or "760m" in desc_lower
                or ("radeon" in desc_lower and "rx " not in desc_lower)
                or any(c in desc_lower for c in ("raphael", "phoenix", "renoir", "cezanne", "rembrandt", "vangogh", "stoney"))
            ):
                gpu_type = "integrated"
            # Kurze Handelsbezeichnung (ohne "VGA compatible controller", ohne "rev xx", NVIDIA = Inhalt [...], AMD = Codenamen-Map)
            clean_name = _clean_gpu_description(desc)
            if not clean_name or clean_name in seen:
                continue
            seen.add(clean_name)
            gpus.append({"name": clean_name, "memory_mb": None, "driver": item.get("driver"), "gpu_type": gpu_type})
        if not gpus:
            r = run_command("lspci 2>/dev/null | grep -iE 'vga|3d|display'")
            if r.get("success") and r.get("stdout"):
                for line in (r["stdout"] or "").strip().split("\n"):
                    line_lower = line.lower()
                    if line.strip() and "audio" not in line_lower and "audio device" not in line_lower:
                        raw = line.split(" ", 1)[1] if " " in line else line.strip()
                        clean_name = _clean_gpu_description(raw)
                        if clean_name and clean_name not in seen:
                            seen.add(clean_name)
                            gpus.append({"name": clean_name.strip(), "memory_mb": None, "gpu_type": "discrete"})
        # NVIDIA: Name + Speicher aus nvidia-smi (Handelsbezeichnung, Speicher in GB)
        nv = run_command("nvidia-smi --query-gpu=name,memory.total --format=csv,noheader,nounits 2>/dev/null")
        if nv.get("success") and nv.get("stdout"):
            nvidia_in_gpus = [g for g in gpus if "nvidia" in (g.get("name") or "").lower()]
            for idx, line in enumerate((nv["stdout"] or "").strip().split("\n")):
                if not line.strip():
                    continue
                parts = [p.strip() for p in line.split(",")]
                if len(parts) >= 2 and idx < len(nvidia_in_gpus):
                    try:
                        mem_mb = int(parts[1].strip().split()[0])
                        nvidia_in_gpus[idx]["memory_mb"] = mem_mb
                        nvidia_in_gpus[idx]["name"] = parts[0].strip()  # nvidia-smi Name (kürzer als lspci)
                    except (ValueError, IndexError):
                        pass
        # display_name + memory_display für jede GPU
        for g in gpus:
            display_name, memory_display = _shorten_gpu_display_name(
                g.get("name"), g.get("gpu_type", "discrete"), g.get("memory_mb")
            )
            g["display_name"] = display_name
            g["memory_display"] = memory_display
    except Exception:
        pass
    return gpus


# ==================== Peripherie-Scan (Assimilation) ====================

def _get_pci_with_drivers():
    """lspci -k: PCI-Geräte mit Kernel-Treiber; gibt Liste (address, line, driver) zurück."""
    result = run_command("/usr/bin/lspci -k 2>/dev/null")
    if not result.get("success") or not result.get("stdout"):
        result = run_command("lspci -k 2>/dev/null")
    if not result.get("success") or not result.get("stdout"):
        return []
    lines = (result["stdout"] or "").strip().split("\n")
    out = []
    current_addr = ""
    current_line = ""
    current_driver = ""
    for line in lines:
        if line and not line.startswith("\t"):
            if current_addr and current_line:
                out.append({"address": current_addr, "description": current_line, "driver": current_driver or None})
            parts = line.split(None, 1)
            current_addr = parts[0] if parts else ""
            current_line = parts[1] if len(parts) > 1 else ""
            current_driver = ""
        elif line.strip().startswith("Kernel driver in use:"):
            current_driver = line.split(":", 1)[-1].strip()
    if current_addr and current_line:
        out.append({"address": current_addr, "description": current_line, "driver": current_driver or None})
    return out

@app.get("/api/peripherals/scan")
async def peripherals_scan():
    """Scan nach verwendeter Peripherie (Grafikkarten, Tastaturen, Mäuse, Headsets, Webcams) inkl. Treiber."""
    try:
        pci_with_driver = _get_pci_with_drivers()
        gpus = []
        seen_descriptions = set()
        for item in pci_with_driver:
            desc = (item.get("description") or "").strip()
            desc_lower = desc.lower()
            # Nur echte Grafik-Controller: VGA, Display-Controller, 3D; nicht jede "graphics"-Subfunktion doppelt
            is_vga = "vga compatible" in desc_lower or "vga compatible controller" in desc_lower
            is_display = "display controller" in desc_lower and ("intel" in desc_lower or "nvidia" in desc_lower or "amd" in desc_lower or "radeon" in desc_lower)
            is_3d = "3d" in desc_lower and ("nvidia" in desc_lower or "amd" in desc_lower or "radeon" in desc_lower or "intel" in desc_lower)
            is_graphics = ("nvidia" in desc_lower or "radeon" in desc_lower or "amd radeon" in desc_lower) and ("graphics" in desc_lower or "vga" in desc_lower or "display" in desc_lower)
            is_intel_graphics = "intel" in desc_lower and "graphics" in desc_lower
            if is_vga or is_display or is_3d or is_graphics or is_intel_graphics:
                # Deduplizieren: gleiche Beschreibung nur einmal (z. B. mehrere PCI-Funktionen einer GPU)
                if desc not in seen_descriptions:
                    seen_descriptions.add(desc)
                    gpus.append({
                        "type": "gpu",
                        "description": desc,
                        "driver": item.get("driver"),
                        "driver_hint": item.get("driver") or "Kein Treiber geladen – prüfen: lspci -k, Hersteller-Linux-Treiber",
                    })
        if not gpus:
            r = run_command("/usr/bin/lspci 2>/dev/null | grep -iE 'vga|3d|display|nvidia|amd|radeon|graphics'")
            if not r.get("success") or not r.get("stdout"):
                r = run_command("lspci 2>/dev/null | grep -iE 'vga|3d|display|nvidia|amd|radeon|graphics'")
            if r.get("success") and r.get("stdout"):
                for line in (r["stdout"] or "").strip().split("\n"):
                    if line.strip():
                        gpus.append({"type": "gpu", "description": line.strip(), "driver": None, "driver_hint": "lspci -k für Treiber"})
        usb = []
        r = run_command("/usr/bin/lsusb 2>/dev/null")
        if not r.get("success") or not r.get("stdout"):
            r = run_command("lsusb 2>/dev/null")
        if r.get("success") and r.get("stdout"):
            for line in (r["stdout"] or "").strip().split("\n"):
                if line.strip():
                    desc = line.strip()
                    kind = "usb"
                    if any(x in desc.lower() for x in ["keyboard", "tastatur"]):
                        kind = "keyboard"
                    elif any(x in desc.lower() for x in ["mouse", "maus", "pointer"]):
                        kind = "mouse"
                    elif any(x in desc.lower() for x in ["webcam", "camera", "kamera", "video", "uvc", "integrated camera"]):
                        kind = "webcam"
                    elif any(x in desc.lower() for x in ["audio", "headset", "microphone", "sound"]):
                        kind = "headset"
                    usb.append({"type": kind, "description": desc})
        input_devices = []
        try:
            with open("/proc/bus/input/devices", "r") as f:
                content = f.read()
            for block in content.split("\n\n"):
                if not block.strip():
                    continue
                name = ""
                handlers = ""
                for line in block.split("\n"):
                    if line.startswith("N: Name="):
                        name = line.replace("N: Name=", "").strip().strip('"')
                    elif line.startswith("H: Handlers="):
                        handlers = line.replace("H: Handlers=", "").strip()
                if name and ("kbd" in handlers or "mouse" in handlers or "event" in handlers):
                    input_devices.append({"name": name, "handlers": handlers})
        except Exception:
            pass
        drivers_list = [{"device": p["description"], "driver": p.get("driver") or "—"} for p in pci_with_driver]
        return {
            "status": "success",
            "gpus": gpus,
            "usb": usb,
            "input_devices": input_devices,
            "drivers": drivers_list,
        }
    except Exception as e:
        err_msg = str(e).strip() if str(e) else "Unbekannter Fehler beim Peripherie-Scan"
        logger.error(f"Peripherie-Scan Fehler: {e}", exc_info=True)
        return JSONResponse(
            status_code=200,
            content={"status": "error", "message": err_msg, "gpus": [], "usb": [], "input_devices": [], "drivers": []}
        )

# ==================== Backup & Restore Endpoints ====================

@app.get("/api/backup/status")
async def backup_status():
    """Backup-Status abrufen"""
    try:
        # Prüfe installierte Backup-Tools
        return {
            "rsync": {
                "installed": check_installed("rsync"),
            },
            "tar": {
                "installed": check_installed("tar"),
            },
            "backup_scripts": {
                "installed": run_command("test -f /usr/local/bin/pi-backup")["success"],
            },
            "backups": [],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# -------------------- Backup Settings + Scheduling --------------------

def _backup_settings_path() -> Path:
    return Path("/etc/pi-installer/backup.json")


def _default_backup_settings() -> dict:
    return {
        "enabled": True,
        "backup_dir": "/mnt/backups",
        "retention": {"keep_last": 5},
        # legacy (pre multi-schedule). kept for migration/backward compat.
        "incremental_only": False,
        "schedule": {"enabled": False, "on_calendar": "daily", "time": "02:00"},
        # new multi-rule schedules
        "schedules": [],
        "datasets": {
            "personal_default": {
                "type": "personal",
                "folders": ["Downloads", "Documents", "Pictures", "Images", "Videos", "Desktop"],
                "incremental": False,
            }
        },
        "state": {},
        "cloud": {
            "enabled": False,
            "provider": "seafile_webdav",
            "webdav_url": "",
            "username": "",
            "password": "",
            "remote_path": "",
        },
    }


def _ensure_schedule_migration(settings: dict) -> dict:
    """
    Migrate legacy single schedule fields into schedules[].
    Keeps legacy keys for backward compatibility but ensures schedules[] exists.
    """
    if not isinstance(settings, dict):
        settings = {}
    base = _default_backup_settings()
    base.update(settings)
    # nested merges
    base["retention"] = {**_default_backup_settings()["retention"], **(settings.get("retention") or {})}
    base["cloud"] = {**_default_backup_settings()["cloud"], **(settings.get("cloud") or {})}
    base["datasets"] = {**_default_backup_settings()["datasets"], **(settings.get("datasets") or {})}
    base["state"] = settings.get("state") if isinstance(settings.get("state"), dict) else {}

    # If schedules already present, keep it
    if isinstance(settings.get("schedules"), list) and settings.get("schedules") is not None:
        base["schedules"] = settings.get("schedules") or []
        return base

    # Create a single rule from legacy schedule
    legacy_sch = settings.get("schedule") if isinstance(settings.get("schedule"), dict) else _default_backup_settings()["schedule"]
    enabled = bool(legacy_sch.get("enabled"))
    on_cal = (legacy_sch.get("on_calendar") or "daily").strip()
    t = (legacy_sch.get("time") or "02:00").strip()
    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    if on_cal == "hourly":
        # represent hourly rule
        days = []
    btype = "incremental" if bool(settings.get("incremental_only")) else "full"

    rule = {
        "id": "default",
        "enabled": enabled,
        "name": "Zeitplan (migriert)",
        "type": btype,
        "target": "local",
        "keep_last": int((base.get("retention") or {}).get("keep_last", 5) or 5),
        "days": days,
        "time": t,
        "on_calendar": on_cal,  # legacy-like value, will be rendered for systemd
        "dataset": None,
        "incremental": False,
    }
    base["schedules"] = [rule] if enabled or settings.get("schedule") else []
    return base


def _read_backup_settings() -> dict:
    try:
        p = _backup_settings_path()
        if p.exists():
            raw = json.loads(p.read_text(encoding="utf-8") or "{}")
            return _ensure_schedule_migration(raw)
    except Exception:
        pass
    return _default_backup_settings()


def _write_backup_settings(settings: dict, sudo_password: str) -> None:
    # write via local tmp, then sudo-move (robust, avoids shell quoting issues)
    import tempfile

    content = json.dumps(settings, indent=2)
    run_command("mkdir -p /etc/pi-installer", sudo=True, sudo_password=sudo_password)

    with tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8", prefix="pi-installer-backup-", suffix=".json") as f:
        f.write(content)
        tmp_path = f.name

    # move atomically into place with correct permissions
    run_command(f"mv {shlex.quote(tmp_path)} /etc/pi-installer/backup.json", sudo=True, sudo_password=sudo_password)
    run_command("chmod 600 /etc/pi-installer/backup.json", sudo=True, sudo_password=sudo_password)


def _systemd_timer_name(rule_id: Optional[str] = None) -> str:
    base = "pi-installer-backup"
    if rule_id:
        rid = "".join(ch for ch in str(rule_id) if ch.isalnum() or ch in ("-", "_")).strip("-_")
        rid = rid[:32] if rid else "default"
        return f"{base}-{rid}"
    return base


def _render_systemd_service(rule_id: str) -> str:
    return """[Unit]
Description=PI-Installer scheduled backup

[Service]
Type=oneshot
ExecStart=/usr/local/bin/pi-installer-backup-run --rule {rule_id}
""".format(rule_id=rule_id)


def _render_systemd_timer(on_calendar: str, rule_name: str = "") -> str:
    return f"""[Unit]
Description=PI-Installer scheduled backup timer{(' - ' + rule_name) if rule_name else ''}

[Timer]
OnCalendar={on_calendar}
Persistent=true

[Install]
WantedBy=timers.target
"""


def _render_backup_runner_script() -> str:
    # Minimaler Runner: liest /etc/pi-installer/backup.json und erstellt Backup + Retention + optional WebDAV Upload.
    # läuft als root via systemd service.
    return r"""#!/usr/bin/env python3
import argparse
import json
import os
import shlex
import shutil
import subprocess
import time
import glob
from pathlib import Path

CFG = Path("/etc/pi-installer/backup.json")

def run_cmd(cmd, shell=True):
    return subprocess.run(cmd, shell=shell, capture_output=True, text=True)

def human(n):
    for u in ["B","KB","MB","GB","TB","PB"]:
        if n < 1024:
            return f"{n:.0f} {u}" if u=="B" else f"{n:.1f} {u}"
        n /= 1024
    return f"{n:.1f} PB"

def retry_upload(local_path, remote_url, user, pw, attempts=4):
    if not shutil.which("curl"):
        raise RuntimeError("curl not installed")
    last_err = ""
    for i in range(attempts):
        up = subprocess.run(
            ["curl", "-sS", "-u", f"{user}:{pw}", "-T", str(local_path), remote_url],
            capture_output=True,
            text=True,
        )
        if up.returncode == 0:
            return True
        last_err = (up.stderr or up.stdout or "").strip()[:500]
        # backoff
        time.sleep(min(60, 3 * (2 ** i)))
    raise RuntimeError(f"upload failed: {last_err}")

def remote_verify(remote_url, user, pw):
    # PROPFIND Depth:0 should return 207 when present (or 200/204 in some DAV)
    cmd = (
        "curl -sS -o /dev/null -w '%{http_code}' "
        f"-u {shlex.quote(user)}:{shlex.quote(pw)} "
        "-X PROPFIND -H 'Depth: 0' "
        f"{shlex.quote(remote_url)}"
    )
    r = run_cmd(cmd)
    code = (r.stdout or "").strip()
    try:
        code_i = int(code)
    except Exception:
        code_i = None
    return (r.returncode == 0) and (code_i in (200, 201, 204, 207))

def remote_list(base_url, user, pw):
    # PROPFIND Depth:1, parse very loosely by href lines
    cmd = (
        "curl -sS "
        f"-u {shlex.quote(user)}:{shlex.quote(pw)} "
        "-X PROPFIND -H 'Depth: 1' "
        f"{shlex.quote(base_url)}"
    )
    r = run_cmd(cmd)
    if r.returncode != 0:
        return []
    out = (r.stdout or "")
    hrefs = []
    for line in out.splitlines():
        line = line.strip()
        if "<D:href>" in line:
            try:
                href = line.split("<D:href>", 1)[1].split("</D:href>", 1)[0]
                hrefs.append(href)
            except Exception:
                pass
    return hrefs

def remote_delete(remote_url, user, pw):
    cmd = (
        "curl -sS -o /dev/null -w '%{http_code}' "
        f"-u {shlex.quote(user)}:{shlex.quote(pw)} "
        "-X DELETE "
        f"{shlex.quote(remote_url)}"
    )
    r = run_cmd(cmd)
    try:
        code = int((r.stdout or "").strip())
    except Exception:
        code = None
    return (r.returncode == 0) and (code in (200, 202, 204))

def find_last_full(backup_dir, pattern):
    files = sorted(glob.glob(os.path.join(backup_dir, pattern)), key=lambda p: os.path.getmtime(p), reverse=True)
    if not files:
        return None, None
    f = files[0]
    try:
        return f, int(os.path.getmtime(f))
    except Exception:
        return f, None

def local_list(backup_dir, pattern):
    return sorted(glob.glob(os.path.join(backup_dir, pattern)), key=lambda p: os.path.getmtime(p), reverse=True)

def build_personal_paths(folders):
    roots = []
    try:
        for u in sorted(Path("/home").iterdir()):
            if not u.is_dir():
                continue
            # skip system-ish homes
            if u.name in ("lost+found",):
                continue
            for folder in folders:
                p = u / folder
                if p.exists():
                    roots.append(str(p))
    except Exception:
        pass
    return roots

def tar_create(out_path, includes, exclude_dir=None, newer_epoch=None, full_system=False):
    inc = " ".join(shlex.quote(p) for p in includes)
    if full_system:
        cmd = (
            f"tar -czf {shlex.quote(out_path)} "
            + (f"--newer-mtime=@{int(newer_epoch)} " if newer_epoch else "")
            + (f"--exclude={shlex.quote(exclude_dir)} " if exclude_dir else "")
            + "--exclude=/proc --exclude=/sys --exclude=/dev --exclude=/tmp --exclude=/run --exclude=/mnt /"
        )
    else:
        cmd = (
            f"tar -czf {shlex.quote(out_path)} "
            + (f"--newer-mtime=@{int(newer_epoch)} " if newer_epoch else "")
            + (f"--exclude={shlex.quote(exclude_dir)} " if exclude_dir else "")
            + inc
        )
    return run_cmd(cmd)

def local_verify_gzip(path):
    # quick verify: list archive
    r = run_cmd(f"tar -tzf {shlex.quote(str(path))} >/dev/null 2>&1")
    return r.returncode == 0

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rule", required=False, default="", help="rule id")
    args = ap.parse_args()

    if not CFG.exists():
        raise SystemExit("missing /etc/pi-installer/backup.json")
    cfg = json.loads(CFG.read_text() or "{}")
    if not cfg.get("enabled", True):
        print("disabled")
        return

    schedules = cfg.get("schedules") if isinstance(cfg.get("schedules"), list) else []
    rule = None
    rid = (args.rule or "").strip()
    if rid:
        for r in schedules:
            if isinstance(r, dict) and str(r.get("id") or "") == rid:
                rule = r
                break
        if not rule:
            raise SystemExit(f"rule not found: {rid}")
    else:
        # legacy fallback
        rule = {"id": "legacy", "type": "full", "target": "local", "keep_last": int((cfg.get("retention") or {}).get("keep_last", 5) or 5)}
        rid = "legacy"

    backup_dir = cfg.get("backup_dir") or "/mnt/backups"
    Path(backup_dir).mkdir(parents=True, exist_ok=True)
    ts = time.strftime("%Y%m%d_%H%M%S")

    rtype = (rule.get("type") or "full").strip()
    target = (rule.get("target") or "local").strip()
    keep_last = int(rule.get("keep_last") or int((cfg.get("retention") or {}).get("keep_last", 5) or 5))

    # create archive
    out = None
    if rtype == "full":
        out = f"{backup_dir}/pi-backup-full-{rid}-{ts}.tar.gz"
        r = tar_create(out, [], exclude_dir=backup_dir, full_system=True)
    elif rtype == "incremental":
        last_full, last_m = find_last_full(backup_dir, f"pi-backup-full-{rid}-*.tar.gz")
        if not last_full or not last_m:
            out = f"{backup_dir}/pi-backup-full-{rid}-{ts}.tar.gz"
            r = tar_create(out, [], exclude_dir=backup_dir, full_system=True)
        else:
            out = f"{backup_dir}/pi-backup-inc-{rid}-{ts}.tar.gz"
            r = tar_create(out, ["/home", "/etc", "/var/www", "/opt"], exclude_dir=backup_dir, newer_epoch=int(last_m), full_system=False)
    elif rtype == "data":
        out = f"{backup_dir}/pi-backup-data-{rid}-{ts}.tar.gz"
        r = tar_create(out, ["/home", "/var/www", "/opt"], exclude_dir=backup_dir, full_system=False)
    elif rtype == "personal":
        ds_id = rule.get("dataset") or "personal_default"
        ds = (cfg.get("datasets") or {}).get(ds_id) if isinstance(cfg.get("datasets"), dict) else None
        folders = (ds or {}).get("folders") if isinstance((ds or {}).get("folders"), list) else ["Downloads","Documents","Pictures","Videos","Desktop"]
        do_inc = bool(rule.get("incremental") or (ds or {}).get("incremental"))
        includes = build_personal_paths(folders)
        if not includes:
            raise SystemExit("personal dataset empty: no folders found under /home/*")
        if not do_inc:
            out = f"{backup_dir}/pi-backup-personal-full-{rid}-{ts}.tar.gz"
            r = tar_create(out, includes, exclude_dir=backup_dir, full_system=False)
        else:
            last_full, last_m = find_last_full(backup_dir, f"pi-backup-personal-full-{rid}-*.tar.gz")
            if not last_full or not last_m:
                out = f"{backup_dir}/pi-backup-personal-full-{rid}-{ts}.tar.gz"
                r = tar_create(out, includes, exclude_dir=backup_dir, full_system=False)
            else:
                out = f"{backup_dir}/pi-backup-personal-inc-{rid}-{ts}.tar.gz"
                r = tar_create(out, includes, exclude_dir=backup_dir, newer_epoch=int(last_m), full_system=False)
    else:
        raise SystemExit(f"unknown rule type: {rtype}")

    # tar can return 1 for warnings; accept if file exists
    outp = Path(out)
    if r.returncode not in (0,1) or not outp.exists() or outp.stat().st_size == 0:
        print("backup failed")
        print((r.stderr or r.stdout or "").strip()[:500])
        raise SystemExit(1)
    if not local_verify_gzip(outp):
        print("verify failed (local)")
        raise SystemExit(1)

    print(f"backup created: {out} ({human(outp.stat().st_size)}) rc={r.returncode}")

    # cloud upload (optional)
    cloud = cfg.get("cloud") or {}
    cloud_enabled = bool(cloud.get("enabled"))
    provider = cloud.get("provider") or "seafile_webdav"
    # Unterstütze WebDAV-basierte Provider
    webdav_providers = ("seafile_webdav", "webdav", "nextcloud_webdav")
    if target in ("cloud_only","local_and_cloud") and cloud_enabled and provider in webdav_providers:
        url = (cloud.get("webdav_url") or "").rstrip("/")
        user = cloud.get("username") or ""
        pw = cloud.get("password") or ""
        remote_path = (cloud.get("remote_path") or "").strip("/")
        if not (url and user and pw):
            raise SystemExit("cloud target selected but webdav settings missing")
        base = f"{url}/{remote_path}" if remote_path else url
        if not base.endswith("/"):
            base = base + "/"
        remote = f"{base}{os.path.basename(out)}"

        retry_upload(outp, remote, user, pw)
        if not remote_verify(remote, user, pw):
            raise SystemExit("remote verify failed after upload")
        print(f"uploaded+verified: {remote}")

        # remote retention
        hrefs = remote_list(base, user, pw)
        want_prefixes = [
            f"pi-backup-full-{rid}-",
            f"pi-backup-inc-{rid}-",
            f"pi-backup-data-{rid}-",
            f"pi-backup-personal-full-{rid}-",
            f"pi-backup-personal-inc-{rid}-",
        ]
        files = []
        for h in hrefs:
            bn = os.path.basename(h.rstrip("/"))
            if not bn.endswith(".tar.gz"):
                continue
            if not any(bn.startswith(p) for p in want_prefixes):
                continue
            files.append(h)
        # keep_last newest based on filename timestamp suffix; if unsorted, this is still safe enough
        for old in files[keep_last:]:
            remote_delete(old, user, pw)

        if target == "cloud_only":
            try:
                outp.unlink(missing_ok=True)
                print("local deleted (cloud-only)")
            except Exception as e:
                print(f"local delete failed: {e}")

    # local retention
    if target in ("local","local_and_cloud"):
        patterns = [
            f"pi-backup-full-{rid}-*.tar.gz",
            f"pi-backup-inc-{rid}-*.tar.gz",
            f"pi-backup-data-{rid}-*.tar.gz",
            f"pi-backup-personal-full-{rid}-*.tar.gz",
            f"pi-backup-personal-inc-{rid}-*.tar.gz",
        ]
        files = []
        for pat in patterns:
            files.extend(local_list(backup_dir, pat))
        # remove duplicates while preserving order
        seen = set()
        ordered = []
        for f in files:
            if f in seen:
                continue
            seen.add(f)
            ordered.append(f)
        for old in ordered[keep_last:]:
            try:
                os.remove(old)
            except Exception:
                pass

    # store minimal state
    cfg.setdefault("state", {})
    cfg["state"][rid] = {"last_run_epoch": int(time.time()), "last_file": os.path.basename(out)}
    CFG.write_text(json.dumps(cfg, indent=2))
    os.chmod(CFG, 0o600)

if __name__ == "__main__":
    main()
"""


def _apply_backup_schedule(settings: dict, sudo_password: str) -> None:
    # ensure runner
    runner = "/usr/local/bin/pi-installer-backup-run"
    script = _render_backup_runner_script()
    import tempfile
    with tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8", prefix="pi-installer-runner-", suffix=".py") as f:
        f.write(script)
        tmp_runner = f.name
    run_command(f"mv {shlex.quote(tmp_runner)} {shlex.quote(runner)}", sudo=True, sudo_password=sudo_password)
    run_command(f"chmod 755 {shlex.quote(runner)}", sudo=True, sudo_password=sudo_password)

    def render_on_calendar(rule: dict) -> str:
        # supports legacy values and explicit systemd strings
        oc = (rule.get("on_calendar") or "daily").strip()
        t = (rule.get("time") or "02:00").strip()
        days = rule.get("days") if isinstance(rule.get("days"), list) else []
        if oc == "hourly":
            return "hourly"
        if oc.startswith("*-*-*") or oc.startswith("Mon") or oc.startswith("Tue") or oc.startswith("Wed") or oc.startswith("Thu") or oc.startswith("Fri") or oc.startswith("Sat") or oc.startswith("Sun"):
            return oc
        if days:
            # systemd: "Mon..Sun *-*-* HH:MM:00"
            d = ",".join(days)
            return f"{d} *-*-* {t}:00"
        # default daily
        return f"*-*-* {t}:00"

    schedules = settings.get("schedules") if isinstance(settings.get("schedules"), list) else []

    # cleanup legacy single timer (best-effort)
    legacy = _systemd_timer_name()
    run_command(f"systemctl disable --now {legacy}.timer 2>/dev/null || true", sudo=True, sudo_password=sudo_password)

    # cleanup removed per-rule units
    try:
        keep_ids = set()
        for r in schedules:
            if isinstance(r, dict) and r.get("id"):
                keep_ids.add(_systemd_timer_name(str(r["id"])))
        sysdir = Path("/etc/systemd/system")
        for p in sysdir.glob("pi-installer-backup-*.timer"):
            name = p.name.replace(".timer", "")
            if name not in keep_ids:
                run_command(f"systemctl disable --now {shlex.quote(name)}.timer 2>/dev/null || true", sudo=True, sudo_password=sudo_password)
                run_command(f"rm -f {shlex.quote(str(sysdir / (name + '.timer')))} {shlex.quote(str(sysdir / (name + '.service')))}", sudo=True, sudo_password=sudo_password)
    except Exception:
        pass

    import tempfile
    for rule in schedules:
        if not isinstance(rule, dict):
            continue
        rid = str(rule.get("id") or "").strip()
        if not rid:
            continue
        svc_name = _systemd_timer_name(rid)
        svc_path = f"/etc/systemd/system/{svc_name}.service"
        timer_path = f"/etc/systemd/system/{svc_name}.timer"
        on_cal = render_on_calendar(rule)
        svc_txt = _render_systemd_service(rid)
        timer_txt = _render_systemd_timer(on_cal, rule_name=str(rule.get("name") or "").strip())

        with tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8", prefix="pi-installer-svc-", suffix=".service") as f:
            f.write(svc_txt)
            tmp_svc = f.name
        with tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8", prefix="pi-installer-timer-", suffix=".timer") as f:
            f.write(timer_txt)
            tmp_timer = f.name

        run_command(f"mv {shlex.quote(tmp_svc)} {shlex.quote(svc_path)}", sudo=True, sudo_password=sudo_password)
        run_command(f"mv {shlex.quote(tmp_timer)} {shlex.quote(timer_path)}", sudo=True, sudo_password=sudo_password)

        if rule.get("enabled") is True:
            run_command(f"systemctl enable --now {svc_name}.timer", sudo=True, sudo_password=sudo_password)
        else:
            run_command(f"systemctl disable --now {svc_name}.timer", sudo=True, sudo_password=sudo_password)

    run_command("systemctl daemon-reload", sudo=True, sudo_password=sudo_password)


@app.get("/api/backup/settings")
async def backup_get_settings():
    s = _read_backup_settings()
    # Timer status (per rule)
    statuses = {}
    for r in (s.get("schedules") or []):
        if not isinstance(r, dict) or not r.get("id"):
            continue
        svc = _systemd_timer_name(str(r["id"]))
        enabled = run_command(f"systemctl is-enabled {svc}.timer 2>/dev/null").get("stdout", "").strip()
        active = run_command(f"systemctl is-active {svc}.timer 2>/dev/null").get("stdout", "").strip()
        statuses[str(r["id"])] = {"enabled": enabled, "active": active}
    s["_timer_status"] = statuses
    return {"status": "success", "settings": s}


@app.post("/api/backup/settings")
async def backup_set_settings(request: Request):
    try:
        data = await request.json()
    except Exception:
        data = {}

    sudo_password = data.get("sudo_password", "") or sudo_password_store.get("password", "")
    if not sudo_password:
        return JSONResponse(status_code=200, content={"status": "error", "message": "Sudo-Passwort erforderlich", "requires_sudo_password": True})

    settings = data.get("settings") or {}
    # merge + migrate legacy -> schedules[]
    base = _ensure_schedule_migration(settings)
    # ensure we keep explicit schedules if provided
    if isinstance(settings.get("schedules"), list):
        base["schedules"] = settings.get("schedules") or []
    if isinstance(settings.get("datasets"), dict):
        base["datasets"] = {**_default_backup_settings()["datasets"], **settings.get("datasets")}
    if isinstance(settings.get("state"), dict):
        base["state"] = settings.get("state") or {}

    # validate some fields
    try:
        base["backup_dir"] = _validate_backup_dir(base.get("backup_dir", "/mnt/backups"))
    except Exception as ve:
        return JSONResponse(status_code=200, content={"status": "error", "message": f"Ungültiges Backup-Ziel: {str(ve)}"})
    try:
        keep = int((base.get("retention") or {}).get("keep_last", 5))
        if keep < 1 or keep > 100:
            raise ValueError()
        base["retention"]["keep_last"] = keep
    except Exception:
        return JSONResponse(status_code=200, content={"status": "error", "message": "retention.keep_last muss zwischen 1 und 100 liegen"})

    # validate schedules basic shape
    try:
        cleaned = []
        for r in (base.get("schedules") or []):
            if not isinstance(r, dict):
                continue
            rid = str(r.get("id") or "").strip()
            if not rid:
                continue
            rr = dict(r)
            rr["id"] = rid
            rr["enabled"] = bool(rr.get("enabled"))
            rr["name"] = str(rr.get("name") or "").strip() or rid
            rr["type"] = str(rr.get("type") or "incremental").strip()
            rr["target"] = str(rr.get("target") or "local").strip()
            rr["keep_last"] = int(rr.get("keep_last") or base["retention"]["keep_last"])
            rr["time"] = str(rr.get("time") or "02:00").strip()
            rr["days"] = rr.get("days") if isinstance(rr.get("days"), list) else ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
            cleaned.append(rr)
        base["schedules"] = cleaned
    except Exception:
        return JSONResponse(status_code=200, content={"status": "error", "message": "schedules ist ungültig"})

    # store config (root-protected) + apply timer
    _write_backup_settings(base, sudo_password=sudo_password)
    _apply_backup_schedule(base, sudo_password=sudo_password)

    return {"status": "success", "message": "Backup-Einstellungen gespeichert", "settings": base}


@app.post("/api/backup/schedule/run-now")
async def backup_run_now(request: Request):
    """Scheduled Backup sofort ausführen (nutzt Runner Script)."""
    try:
        data = await request.json()
    except Exception:
        data = {}

    sudo_password = data.get("sudo_password", "") or sudo_password_store.get("password", "")
    if not sudo_password:
        return JSONResponse(status_code=200, content={"status": "error", "message": "Sudo-Passwort erforderlich", "requires_sudo_password": True})

    runner = "/usr/local/bin/pi-installer-backup-run"
    rule_id = (data.get("rule_id") or "").strip()
    # ensure it exists via applying schedule with current settings
    settings = _read_backup_settings()
    _apply_backup_schedule(settings, sudo_password=sudo_password)
    cmd = runner if not rule_id else f"{runner} --rule {shlex.quote(rule_id)}"
    res = await run_command_async(cmd, sudo=True, sudo_password=sudo_password, timeout=7200)
    return {
        "status": "success" if res["success"] else "error",
        "stdout": (res.get("stdout") or "").strip()[:4000],
        "stderr": (res.get("stderr") or "").strip()[:4000],
        "returncode": res.get("returncode"),
    }


@app.post("/api/backup/cloud/test")
async def backup_cloud_test(request: Request):
    """Testet WebDAV/Seafile Erreichbarkeit (ohne Speichern)."""
    try:
        data = await request.json()
    except Exception:
        data = {}

    url = (data.get("webdav_url") or "").strip()
    username = (data.get("username") or "").strip()
    password = (data.get("password") or "").strip()

    if not url:
        return JSONResponse(status_code=200, content={"status": "error", "message": "webdav_url erforderlich"})
    if not username or not password:
        return JSONResponse(status_code=200, content={"status": "error", "message": "username + password erforderlich"})

    # PROPFIND Depth:0 ist typisch für WebDAV (Status 207 = Multi-Status)
    cmd = (
        "curl -sS -o /dev/null "
        "-w '%{http_code}' "
        f"-u {shlex.quote(username)}:{shlex.quote(password)} "
        "-X PROPFIND -H 'Depth: 0' "
        f"{shlex.quote(url)}"
    )
    res = run_command(cmd)
    code_str = (res.get("stdout") or "").strip()
    try:
        code = int(code_str) if code_str else None
    except Exception:
        code = None

    ok = res.get("success") and (code in (200, 201, 204, 207))
    msg = None
    if not ok:
        if code == 401:
            msg = "401 Unauthorized (Login/Token prüfen)"
        elif code:
            msg = f"HTTP {code} (Server erreichbar, aber Antwort unerwartet)"
        else:
            msg = (res.get("stderr") or "Verbindung fehlgeschlagen").strip()[:300]

    return {"status": "success" if ok else "error", "ok": bool(ok), "http_code": code, "message": msg}


@app.get("/api/backup/cloud/list")
async def backup_cloud_list(rule_id: str = ""):
    """
    Listet externe Backups im konfigurierten WebDAV-Ziel (Seafile).
    Nutzt gespeicherte Settings (/etc/pi-installer/backup.json).
    """
    settings = _read_backup_settings()
    cloud = settings.get("cloud") or {}
    if not cloud.get("enabled"):
        return {"status": "success", "backups": [], "message": "Cloud-Upload ist deaktiviert"}
    provider = cloud.get("provider") or "seafile_webdav"
    
    # Versuche Backup-Modul zu verwenden für alle Provider
    try:
        backup_mod = _get_backup_module()
        backup_mod.run_command = run_command
        
        # Für WebDAV: Verwende bestehende Logik
        if provider in ("seafile_webdav", "webdav", "nextcloud_webdav"):
            pass  # Weiter mit WebDAV-Logik unten
        # Für S3: Versuche S3-Liste
        elif provider in ("s3", "s3_compatible"):
            bucket = cloud.get("bucket") or ""
            if not bucket:
                return {"status": "success", "backups": [], "message": "S3-Bucket nicht konfiguriert"}
            # TODO: S3-Liste implementieren
            return {"status": "success", "backups": [], "message": "S3-Liste wird noch nicht unterstützt"}
        # Für andere Provider: Noch nicht unterstützt
        else:
            return {"status": "success", "backups": [], "message": f"Provider '{provider}' wird für Cloud-Liste noch nicht unterstützt"}
    except Exception as e:
        logger.error(f"Fehler beim Abrufen der Cloud-Backups: {str(e)}", exc_info=True)
        # Fallback auf WebDAV
    
    # Unterstütze WebDAV-basierte Provider (Fallback)
    if provider not in ("seafile_webdav", "webdav", "nextcloud_webdav"):
        return {"status": "success", "backups": [], "message": f"Provider '{provider}' wird für Cloud-Liste nicht unterstützt"}

    url = (cloud.get("webdav_url") or "").strip().rstrip("/")
    user = (cloud.get("username") or "").strip()
    pw = (cloud.get("password") or "").strip()
    remote_path = (cloud.get("remote_path") or "").strip().strip("/")

    if not url or not user or not pw:
        return JSONResponse(status_code=200, content={"status": "error", "message": "WebDAV URL + Username + Passwort fehlen"})

    base = f"{url}/{remote_path}" if remote_path else url
    # Ensure trailing slash for collection listing
    if not base.endswith("/"):
        base = base + "/"

    # PROPFIND Depth:1 to list directory contents
    cmd = (
        "curl -sS "
        f"-u {shlex.quote(user)}:{shlex.quote(pw)} "
        "-X PROPFIND -H 'Depth: 1' "
        f"{shlex.quote(base)}"
    )
    res = run_command(cmd)
    if not res.get("success"):
        return JSONResponse(status_code=200, content={"status": "error", "message": (res.get("stderr") or res.get("error") or "Request fehlgeschlagen")[:300]})

    xml_text = (res.get("stdout") or "").strip()
    if not xml_text:
        return {"status": "success", "backups": []}

    rid = (rule_id or "").strip()
    backups = []
    try:
        # Parse DAV XML. Be tolerant with namespaces.
        root = ET.fromstring(xml_text)
        ns_dav = "{DAV:}"

        def _text(el, path):
            try:
                n = el.find(path)
                return (n.text or "").strip() if n is not None else ""
            except Exception:
                return ""

        for resp in root.findall(f".//{ns_dav}response"):
            href = _text(resp, f"{ns_dav}href")
            if not href:
                continue
            # skip directory itself
            if href.rstrip("/") == base.rstrip("/"):
                continue
            # We only care about backup files (inkl. verschlüsselte)
            name = href.split("/")[-1]
            if not (name.endswith(".tar.gz") or name.endswith(".tar.gz.gpg") or name.endswith(".tar.gz.enc")):
                continue
            if rid and f"-{rid}-" not in name:
                # only filter those that encode rule id in filename
                continue

            size = None
            last_modified = None
            for propstat in resp.findall(f"{ns_dav}propstat"):
                prop = propstat.find(f"{ns_dav}prop")
                if prop is None:
                    continue
                cl = prop.find(f"{ns_dav}getcontentlength")
                lm = prop.find(f"{ns_dav}getlastmodified")
                if cl is not None and cl.text:
                    try:
                        size = int(cl.text.strip())
                    except Exception:
                        size = None
                if lm is not None and lm.text:
                    last_modified = lm.text.strip()
            backup_info = {"name": name, "href": href, "size_bytes": size, "last_modified": last_modified}
            # Markiere verschlüsselte Backups
            if name.endswith(".gpg") or name.endswith(".enc"):
                backup_info["encrypted"] = True
            backup_info["location"] = "Cloud"
            backups.append(backup_info)

        # sort newest first if possible
        backups.sort(key=lambda b: (b.get("last_modified") or "", b.get("name") or ""), reverse=True)
    except Exception:
        # fallback: if parsing fails, return empty but not error (avoid breaking UI)
        backups = []

    return {"status": "success", "backups": backups, "base_url": base}


@app.get("/api/backup/cloud/quota")
async def backup_cloud_quota():
    """Gibt verfügbaren Speicherplatz für Cloud-Backups zurück"""
    try:
        settings = _read_backup_settings()
        cloud = settings.get("cloud") or {}
        if not cloud.get("enabled"):
            return {"status": "success", "quota": None, "message": "Cloud-Upload ist deaktiviert"}
        
        provider = cloud.get("provider") or "seafile_webdav"
        url = (cloud.get("webdav_url") or "").strip().rstrip("/")
        user = (cloud.get("username") or "").strip()
        pw = (cloud.get("password") or "").strip()
        
        if not url or not user or not pw:
            return {"status": "success", "quota": None, "message": "Cloud-Settings unvollständig"}
        
        # Versuche Quota-Informationen zu erhalten (WebDAV QUOTA Property)
        # Für Seafile/Nextcloud: PROPFIND mit Quota-Property
        base = url.rstrip("/")
        cmd = (
            "curl -sS "
            f"-u {shlex.quote(user)}:{shlex.quote(pw)} "
            "-X PROPFIND -H 'Depth: 0' "
            f"{shlex.quote(base)}"
        )
        res = run_command(cmd)
        
        if not res.get("success"):
            return {"status": "success", "quota": None, "message": "Quota-Informationen nicht verfügbar"}
        
        xml_text = (res.get("stdout") or "").strip()
        if not xml_text:
            return {"status": "success", "quota": None, "message": "Keine Quota-Informationen"}
        
        # Parse XML für Quota-Informationen
        try:
            root = ET.fromstring(xml_text)
            ns_dav = "{DAV:}"
            
            # Suche nach quota-used und quota-available
            quota_used = None
            quota_available = None
            
            for propstat in root.findall(f".//{ns_dav}propstat"):
                prop = propstat.find(f"{ns_dav}prop")
                if prop is None:
                    continue
                
                # Seafile/Nextcloud verwenden verschiedene Namespaces
                for ns in ["{DAV:}", "{http://owncloud.org/ns}", "{http://nextcloud.org/ns}"]:
                    used_el = prop.find(f"{ns}quota-used-bytes")
                    avail_el = prop.find(f"{ns}quota-available-bytes")
                    
                    if used_el is not None and used_el.text:
                        try:
                            quota_used = int(used_el.text.strip())
                        except Exception:
                            pass
                    if avail_el is not None and avail_el.text:
                        try:
                            quota_available = int(avail_el.text.strip())
                        except Exception:
                            pass
            
            if quota_used is not None or quota_available is not None:
                def human(n: int) -> str:
                    for unit in ["B", "KB", "MB", "GB", "TB"]:
                        if n < 1024:
                            return f"{n:.0f} {unit}" if unit == "B" else f"{n:.1f} {unit}"
                        n /= 1024
                    return f"{n:.1f} TB"
                
                total = (quota_used or 0) + (quota_available or 0) if quota_available is not None else None
                
                return {
                    "status": "success",
                    "quota": {
                        "used_bytes": quota_used,
                        "available_bytes": quota_available,
                        "total_bytes": total,
                        "used_human": human(quota_used) if quota_used is not None else None,
                        "available_human": human(quota_available) if quota_available is not None else None,
                        "total_human": human(total) if total else None,
                        "used_percent": round((quota_used / total * 100), 1) if (quota_used and total and total > 0) else None,
                    }
                }
        except Exception as e:
            logger.debug(f"Quota-Parsing fehlgeschlagen: {str(e)}")
        
        return {"status": "success", "quota": None, "message": "Quota-Informationen nicht verfügbar für diesen Provider"}
    except Exception as e:
        logger.error(f"Fehler beim Abrufen der Cloud-Quota: {str(e)}", exc_info=True)
        return {"status": "error", "message": str(e)}


@app.post("/api/backup/cloud/delete")
async def backup_cloud_delete(request: Request):
    """Löscht ein Cloud-Backup über WebDAV DELETE"""
    try:
        data = await request.json()
    except Exception:
        data = {}
    
    backup_file = (data.get("backup_file") or data.get("href") or "").strip()
    if not backup_file:
        return JSONResponse(status_code=200, content={"status": "error", "message": "backup_file oder href erforderlich"})
    
    settings = _read_backup_settings()
    cloud = settings.get("cloud") or {}
    if not cloud.get("enabled"):
        return JSONResponse(status_code=200, content={"status": "error", "message": "Cloud-Upload ist deaktiviert"})
    
    provider = cloud.get("provider") or "seafile_webdav"
    if provider not in ("seafile_webdav", "webdav", "nextcloud_webdav"):
        return JSONResponse(status_code=200, content={"status": "error", "message": f"Provider '{provider}' wird für Cloud-Löschung nicht unterstützt"})
    
    url = (cloud.get("webdav_url") or "").strip().rstrip("/")
    user = (cloud.get("username") or "").strip()
    pw = (cloud.get("password") or "").strip()
    
    if not url or not user or not pw:
        return JSONResponse(status_code=200, content={"status": "error", "message": "WebDAV URL + Username + Passwort fehlen"})
    
    # Verwende base_url aus Request, falls vorhanden (wird vom Frontend gesendet)
    # Sonst konstruiere base aus webdav_url und remote_path
    base_url_from_request = (data.get("base_url") or "").strip()
    remote_path = (cloud.get("remote_path") or "").strip().strip("/")
    
    if base_url_from_request:
        base = base_url_from_request
        if not base.endswith("/"):
            base = base + "/"
    else:
        base = f"{url}/{remote_path}" if remote_path else url
        if not base.endswith("/"):
            base = base + "/"
    
    # backup_file (href) kann sein:
    # 1. Vollständige URL (https://example.com/dav/backups/file.tar.gz)
    # 2. Relativer Pfad zur WebDAV-Root (/dav/backups/file.tar.gz) 
    # 3. Relativer Pfad zur base (file.tar.gz)
    #
    # PROPFIND gibt href relativ zur angeforderten URL zurück.
    # Wenn PROPFIND auf base (z.B. https://example.com/dav/backups/) ausgeführt wird,
    # dann ist href entweder:
    # - Absolut relativ zur Root: /dav/backups/file.tar.gz
    # - Relativ zur base: file.tar.gz
    # - Vollständige URL: https://example.com/dav/backups/file.tar.gz
    
    from urllib.parse import urlparse, urljoin
    
    if backup_file.startswith("http://") or backup_file.startswith("https://"):
        # Vollständige URL - verwende direkt
        remote_url = backup_file
    elif backup_file.startswith("/"):
        # href ist absolut relativ zur WebDAV-Root
        # Kombiniere mit der Domain der base_url
        parsed_base = urlparse(base.rstrip("/"))
        base_domain = f"{parsed_base.scheme}://{parsed_base.netloc}"
        remote_url = base_domain + backup_file
    else:
        # href ist relativ zur base - füge zur base hinzu
        # urljoin behandelt relative Pfade korrekt
        remote_url = urljoin(base, backup_file)
    
    # Debug-Informationen für Response (MUSS vor der Verwendung definiert werden)
    debug_info = {
        "webdav_url": url,
        "remote_path": remote_path,
        "base_from_request": base_url_from_request,
        "base": base,
        "backup_file": backup_file,
        "remote_url": remote_url
    }
    
    # WICHTIG: Wenn remote_url mit base beginnt, aber base bereits in href enthalten ist,
    # könnte es zu einer doppelten Pfadstruktur kommen. Prüfe das.
    # Beispiel: base = "https://example.com/dav/backups/", href = "/dav/backups/file.tar.gz"
    # Dann wäre remote_url = "https://example.com/dav/backups/file.tar.gz" (korrekt)
    # Aber wenn base = "https://example.com/dav/backups/", href = "backups/file.tar.gz"
    # Dann wäre remote_url = "https://example.com/dav/backups/backups/file.tar.gz" (falsch!)
    
    # Prüfe, ob der Pfad bereits in base enthalten ist
    parsed_remote = urlparse(remote_url)
    parsed_base_check = urlparse(base.rstrip("/"))
    
    # Wenn der Pfad der remote_url bereits mit dem Pfad der base beginnt, ist es korrekt
    # Sonst könnte es ein Problem geben
    if parsed_remote.path.startswith(parsed_base_check.path):
        # Pfad ist korrekt
        pass
    else:
        # Möglicherweise falsche Konstruktion - versuche es mit base + Dateiname
        filename = backup_file.split("/")[-1]
        alt_remote_url = base.rstrip("/") + "/" + filename
        # Verwende diese nur, wenn sie anders ist
        if alt_remote_url != remote_url:
            debug_info["alternative_construction"] = alt_remote_url
    
    # DELETE Request mit zusätzlichem Debug-Output
    # Zuerst versuchen wir mit der konstruierten URL
    cmd = (
        "curl -sS -o /dev/null -w '%{http_code}' "
        f"-u {shlex.quote(user)}:{shlex.quote(pw)} "
        "-X DELETE "
        f"{shlex.quote(remote_url)}"
    )
    res = run_command(cmd)
    
    if res.get("success"):
        http_code = (res.get("stdout") or "").strip()
        try:
            code = int(http_code)
            if code in (200, 202, 204):
                return {"status": "success", "message": "Cloud-Backup gelöscht", "debug": debug_info}
            elif code == 404:
                # Debug-Info für 404-Fehler
                debug_info["http_code"] = 404
                # Datei nicht gefunden - versuche mehrere alternative URL-Konstruktionen
                alternatives_tried = [remote_url]
                
                if not backup_file.startswith("http://") and not backup_file.startswith("https://"):
                    # Versuch 1: Nur Dateiname zur base hinzufügen
                    filename = backup_file.split("/")[-1]
                    alt_url1 = base + filename
                    alternatives_tried.append(alt_url1)
                    logger.info(f"[Cloud-Delete] Versuche alternative URL 1: {alt_url1}")
                    
                    cmd_alt1 = (
                        "curl -sS -o /dev/null -w '%{http_code}' "
                        f"-u {shlex.quote(user)}:{shlex.quote(pw)} "
                        "-X DELETE "
                        f"{shlex.quote(alt_url1)}"
                    )
                    res_alt1 = run_command(cmd_alt1)
                    if res_alt1.get("success"):
                        http_code_alt1 = (res_alt1.get("stdout") or "").strip()
                        try:
                            code_alt1 = int(http_code_alt1)
                            if code_alt1 in (200, 202, 204):
                                debug_info["successful_alternative"] = alt_url1
                                return {"status": "success", "message": "Cloud-Backup gelöscht", "debug": debug_info}
                        except ValueError:
                            pass
                    
                    # Versuch 2: Wenn href mit / beginnt, entferne führenden / und kombiniere mit base
                    if backup_file.startswith("/"):
                        # Entferne führenden Slash und kombiniere mit base
                        path_without_leading_slash = backup_file.lstrip("/")
                        # Entferne remote_path aus dem Pfad, falls vorhanden
                        if remote_path:
                            path_parts = path_without_leading_slash.split("/")
                            remote_path_parts = remote_path.strip("/").split("/")
                            # Prüfe, ob der Pfad mit remote_path beginnt
                            if len(path_parts) >= len(remote_path_parts):
                                if path_parts[:len(remote_path_parts)] == remote_path_parts:
                                    # Entferne remote_path-Teil
                                    path_without_leading_slash = "/".join(path_parts[len(remote_path_parts):])
                        alt_url2 = base.rstrip("/") + "/" + path_without_leading_slash
                        alternatives_tried.append(alt_url2)
                        logger.info(f"[Cloud-Delete] Versuche alternative URL 2: {alt_url2}")
                        
                        cmd_alt2 = (
                            "curl -sS -o /dev/null -w '%{http_code}' "
                            f"-u {shlex.quote(user)}:{shlex.quote(pw)} "
                            "-X DELETE "
                            f"{shlex.quote(alt_url2)}"
                        )
                        res_alt2 = run_command(cmd_alt2)
                        if res_alt2.get("success"):
                            http_code_alt2 = (res_alt2.get("stdout") or "").strip()
                            try:
                                code_alt2 = int(http_code_alt2)
                                if code_alt2 in (200, 202, 204):
                                    debug_info["successful_alternative"] = alt_url2
                                    return {"status": "success", "message": "Cloud-Backup gelöscht", "debug": debug_info}
                            except ValueError:
                                pass
                
                # Datei nicht gefunden - könnte bereits gelöscht sein oder falscher Pfad
                debug_info["alternatives_tried"] = alternatives_tried[:5]
                debug_info["http_code"] = code
                debug_info["final_remote_url"] = remote_url[:200]
                return JSONResponse(
                    status_code=200, 
                    content={
                        "status": "error", 
                        "message": f"Datei nicht gefunden (HTTP 404). Versuchte URLs: {', '.join(alternatives_tried[:3])}",
                        "http_code": code,
                        "remote_url": remote_url[:200],
                        "backup_file": backup_file[:200],
                        "alternatives_tried": alternatives_tried[:5],
                        "debug": debug_info
                    }
                )
            else:
                debug_info["http_code"] = code
                return JSONResponse(
                    status_code=200, 
                    content={
                        "status": "error", 
                        "message": f"Löschung fehlgeschlagen (HTTP {code})",
                        "http_code": code,
                        "remote_url": remote_url[:200],
                        "debug": debug_info
                    }
                )
        except ValueError:
            debug_info["http_code_error"] = http_code
            return JSONResponse(status_code=200, content={"status": "error", "message": f"Ungültige HTTP-Antwort: {http_code}", "debug": debug_info})
    else:
        error_msg = res.get("stderr") or res.get("error") or "Unbekannter Fehler"
        debug_info["curl_error"] = error_msg[:200]
        return JSONResponse(status_code=200, content={"status": "error", "message": f"Löschung fehlgeschlagen: {error_msg[:200]}", "debug": debug_info})


@app.post("/api/backup/cloud/verify")
async def backup_cloud_verify(request: Request):
    """Verifiziert ein einzelnes Remote-Backup via WebDAV PROPFIND Depth:0."""
    try:
        data = await request.json()
    except Exception:
        data = {}

    name = (data.get("name") or "").strip()
    settings = _read_backup_settings()
    cloud = settings.get("cloud") or {}
    url = (cloud.get("webdav_url") or "").strip().rstrip("/")
    user = (cloud.get("username") or "").strip()
    pw = (cloud.get("password") or "").strip()
    remote_path = (cloud.get("remote_path") or "").strip().strip("/")

    if not name or not name.endswith(".tar.gz"):
        return JSONResponse(status_code=200, content={"status": "error", "message": "name (.tar.gz) erforderlich"})
    if not url or not user or not pw:
        return JSONResponse(status_code=200, content={"status": "error", "message": "WebDAV Settings fehlen"})

    base = f"{url}/{remote_path}" if remote_path else url
    if not base.endswith("/"):
        base += "/"
    remote = f"{base}{name}"
    cmd = (
        "curl -sS -o /dev/null "
        "-w '%{http_code}' "
        f"-u {shlex.quote(user)}:{shlex.quote(pw)} "
        "-X PROPFIND -H 'Depth: 0' "
        f"{shlex.quote(remote)}"
    )
    res = run_command(cmd)
    code_str = (res.get("stdout") or "").strip()
    try:
        code = int(code_str) if code_str else None
    except Exception:
        code = None
    ok = res.get("success") and (code in (200, 201, 204, 207))
    return {"status": "success" if ok else "error", "ok": bool(ok), "http_code": code, "remote": remote}

@app.get("/api/backup/targets")
async def backup_targets():
    """Liste sinnvoller Backup-Ziele (z.B. USB-Sticks / gemountete Datenträger)."""
    try:
        # lsblk liefert Mountpoints sehr zuverlässig.
        # Wichtig: Auf manchen Systemen gibt es "MOUNTPOINTS" (Plural) → Liste von Mountpoints.
        # NOTE: Wir brauchen TYPE/PKNAME, um ungemountete USB-Partitionen zuverlässig zu erkennen.
        res = run_command("lsblk -J -o NAME,TYPE,PKNAME,LABEL,SIZE,FSTYPE,MOUNTPOINTS,RM,RO,MODEL,TRAN 2>/dev/null")
        targets = []
        raw = res.get("stdout", "") if res["success"] else ""
        if not raw:
            # Fallback: ältere util-linux Versionen kennen evtl. MOUNTPOINTS nicht
            res2 = run_command("lsblk -J -o NAME,TYPE,PKNAME,LABEL,SIZE,FSTYPE,MOUNTPOINT,RM,RO,MODEL,TRAN 2>/dev/null")
            raw = res2.get("stdout", "") if res2["success"] else ""

        if raw:
            try:
                data = json.loads(raw or "{}")
                devices = data.get("blockdevices", []) or []

                system_mounts = {"/", "/boot", "/boot/firmware", "[SWAP]"}

                def add_target(d, mp, extra=None):
                    payload = {
                        "name": d.get("name"),
                        "label": d.get("label"),
                        "size": d.get("size"),
                        "fstype": d.get("fstype"),
                        "mountpoint": mp,
                        "rm": d.get("rm"),
                        "model": d.get("model"),
                        "tran": d.get("tran"),
                        "device": f"/dev/{d.get('name')}" if d.get("name") else None,
                        "mounted": bool(mp),
                    }
                    if extra:
                        payload.update(extra)
                    targets.append(payload)

                def walk(items, disk_ctx=None):
                    for d in items:
                        dtype = d.get("type")
                        if dtype == "disk":
                            disk_ctx = d

                        name = d.get("name")
                        mps = d.get("mountpoints")
                        mp = d.get("mountpoint")

                        # mounted items
                        if isinstance(mps, list) and mps:
                            for one in mps:
                                if one and one not in system_mounts:
                                    add_target(d, one, {"mounted": True})
                        elif mp and mp not in system_mounts:
                            add_target(d, mp, {"mounted": True})

                        # unmounted USB/Removable partitions → anzeigen, damit der Stick "erkannt" wird
                        if dtype == "part" and disk_ctx and name:
                            dtran = disk_ctx.get("tran") or d.get("tran")
                            drm = disk_ctx.get("rm") if disk_ctx.get("rm") is not None else d.get("rm")
                            is_usb = dtran == "usb"
                            is_rm = bool(drm)
                            has_mount = bool(mp) or (isinstance(mps, list) and len(mps) > 0)
                            if (is_usb or is_rm) and not has_mount:
                                add_target(d, None, {"mounted": False, "tran": dtran, "rm": drm, "model": disk_ctx.get("model")})

                        if d.get("children"):
                            walk(d["children"], disk_ctx)

                walk(devices, None)
            except Exception:
                # Ignorieren - targets bleibt leer
                pass

        # Ergänzung: Mounts unter /mnt/pi-installer-usb sicher aufnehmen (auch wenn lsblk nichts liefert)
        try:
            for fs in _findmnt_mounts():
                tgt = (fs.get("target") or "").strip()
                if tgt.startswith("/mnt/pi-installer-usb/"):
                    # Doppelte vermeiden
                    if not any(t.get("mountpoint") == tgt for t in targets):
                        targets.append({
                            "name": None,
                            "label": None,
                            "size": None,
                            "fstype": fs.get("fstype"),
                            "mountpoint": tgt,
                            "rm": None,
                            "model": None,
                            "tran": None,
                        })
        except Exception:
            pass

        # Fallback: typische Pfade (ohne Garantie)
        common = ["/mnt", "/mnt/pi-installer-usb", "/media", "/run/media"]
        return {"status": "success", "targets": targets, "common_roots": common}
    except Exception as e:
        return JSONResponse(status_code=200, content={"status": "error", "message": str(e), "targets": [], "common_roots": ["/mnt", "/mnt/pi-installer-usb", "/media", "/run/media"]})

@app.get("/api/backup/target-check")
async def backup_target_check(backup_dir: str, create: int = 0):
    """
    Prüft ein Backup-Ziel:
    - Existenz / optional anlegen (create=1)
    - Freier Speicher (statvfs)
    - Schreibtest (normaler User, fallback: sudo wenn Passwort gespeichert)
    """
    try:
        try:
            backup_dir = _validate_backup_dir(backup_dir)
        except Exception as ve:
            return JSONResponse(status_code=200, content={"status": "error", "message": f"Ungültiges Backup-Ziel: {str(ve)}"})

        p = Path(backup_dir)
        sudo_password = sudo_password_store.get("password", "")
        created = False

        if create and not p.exists():
            mkdir_cmd = f"mkdir -p {shlex.quote(backup_dir)}"
            mkdir_res = run_command(mkdir_cmd)
            if not mkdir_res["success"] and sudo_password:
                mkdir_res = run_command(mkdir_cmd, sudo=True, sudo_password=sudo_password)
            if mkdir_res["success"]:
                created = True
            else:
                return JSONResponse(
                    status_code=200,
                    content={
                        "status": "error",
                        "message": f"Zielverzeichnis konnte nicht erstellt werden: {backup_dir}",
                        "created": False,
                    },
                )

        exists = p.exists()
        is_dir = p.is_dir() if exists else False

        # Filesystem Stats
        fs = {}
        try:
            st = os.statvfs(backup_dir if exists else str(p.parent))
            total = st.f_frsize * st.f_blocks
            free = st.f_frsize * st.f_bavail
            used = total - free
            used_percent = round((used / total) * 100, 1) if total else 0.0

            def human(n: int) -> str:
                for unit in ["B", "KB", "MB", "GB", "TB", "PB"]:
                    if n < 1024:
                        return f"{n:.0f} {unit}" if unit == "B" else f"{n:.1f} {unit}"
                    n /= 1024
                return f"{n:.1f} PB"

            fs = {
                "total_bytes": int(total),
                "free_bytes": int(free),
                "used_percent": used_percent,
                "total_human": human(total),
                "free_human": human(free),
            }
        except Exception:
            fs = {}

        def _best_mount_for_path(path_str: str) -> Optional[dict]:
            """Findet den passendsten (längsten) findmnt Mount für einen Pfad."""
            path_str = (path_str or "").strip()
            if not path_str:
                return None
            best = None
            best_len = -1
            for fs in _findmnt_mounts():
                tgt = (fs.get("target") or "").strip()
                if not tgt:
                    continue
                if path_str == tgt or path_str.startswith(tgt.rstrip("/") + "/"):
                    if len(tgt) > best_len:
                        best = fs
                        best_len = len(tgt)
            return best

        # Diagnostics: mount/device readonly, fstype, options, usb/removable
        mount_info = None
        try:
            mi = _best_mount_for_path(backup_dir if exists else str(p.parent))
            if mi:
                src = (mi.get("source") or "").strip()
                fstype = (mi.get("fstype") or "").strip()
                opts = (mi.get("options") or "").strip()
                is_ro_mount = ("ro" in [o.strip() for o in opts.split(",") if o.strip()]) if opts else False

                node = _find_lsblk_by_name(src) if src.startswith("/dev/") else None
                disk = _find_disk_by_name(node.get("pkname") or node.get("name")) if node and node.get("name") else None
                is_usb = bool((disk or node or {}).get("tran") == "usb") if (disk or node) else False
                is_rm = bool((disk or node or {}).get("rm")) if (disk or node) else False
                is_ro_dev = bool((disk or node or {}).get("ro")) if (disk or node) else False

                mount_info = {
                    "target": (mi.get("target") or "").strip(),
                    "source": src,
                    "fstype": fstype,
                    "options": opts,
                    "mount_readonly": is_ro_mount,
                    "device_readonly": is_ro_dev,
                    "is_usb": is_usb,
                    "is_removable": is_rm,
                }
        except Exception:
            mount_info = None

        # Write test
        write_test = {"success": False, "mode": "user", "message": "", "reason_code": None, "hints": [], "suggest_usb_prepare": False}
        if exists and is_dir:
            test_name = f".pi-installer-write-test-{os.getpid()}.tmp"
            test_path = p / test_name
            try:
                test_path.write_text("ok", encoding="utf-8")
                test_path.unlink(missing_ok=True)
                write_test = {"success": True, "mode": "user", "message": "Schreibtest ok (User)", "reason_code": None, "hints": [], "suggest_usb_prepare": False}
            except Exception as e:
                err_user = str(e)
                write_test = {"success": False, "mode": "user", "message": f"Schreibtest fehlgeschlagen (User): {err_user}", "reason_code": None, "hints": [], "suggest_usb_prepare": False}
                # Fallback: sudo write test, wenn Passwort gespeichert
                if sudo_password:
                    cmd = (
                        f"sh -c "
                        f"{shlex.quote('tmp=$(mktemp -p ' + backup_dir + ' .pi-installer-write-test.XXXXXX) && echo ok > \"$tmp\" && rm -f \"$tmp\"')}"
                    )
                    sudo_res = run_command(cmd, sudo=True, sudo_password=sudo_password)
                    if sudo_res["success"]:
                        write_test = {"success": True, "mode": "sudo", "message": "Schreibtest ok (sudo)", "reason_code": "permissions", "hints": [], "suggest_usb_prepare": False}
                    else:
                        err_sudo = (sudo_res.get("stderr") or sudo_res.get("error") or "Schreibtest fehlgeschlagen (sudo)").strip()
                        write_test = {
                            "success": False,
                            "mode": "sudo",
                            "message": err_sudo[:200],
                            "reason_code": None,
                            "hints": [],
                            "suggest_usb_prepare": False,
                        }

        # Post-process diagnostics if write failed
        if exists and is_dir and not write_test.get("success"):
            combined = (write_test.get("message") or "")
            hints: list[str] = []
            reason = None

            fstype = (mount_info or {}).get("fstype") or ""
            is_ro_mount = bool((mount_info or {}).get("mount_readonly"))
            is_ro_dev = bool((mount_info or {}).get("device_readonly"))
            is_usb = bool((mount_info or {}).get("is_usb") or (mount_info or {}).get("is_removable"))

            if fstype in ("iso9660", "udf", "squashfs"):
                reason = "readonly_filesystem"
                hints.append(f"Dateisystem ist read-only ({fstype}).")
            if is_ro_mount:
                reason = reason or "mount_readonly"
                hints.append("Datenträger ist read-only gemountet (mount option ro).")
            if is_ro_dev:
                reason = reason or "device_readonly"
                hints.append("Datenträger ist hardwareseitig/Kernel-seitig schreibgeschützt (RO=1).")

            if "Read-only file system" in combined or "EROFS" in combined:
                reason = reason or "read_only"
                hints.append("Schreibfehler: Read-only file system (EROFS).")
            if "Permission denied" in combined:
                reason = reason or "permission_denied"
                hints.append("Schreibrechte fehlen (Permission denied).")
                if write_test.get("mode") == "user" and not sudo_password:
                    hints.append("Mit sudo könnte es funktionieren (Sudo-Passwort fehlt / Backend neu gestartet).")
            if "No space left on device" in combined:
                reason = reason or "no_space"
                hints.append("Kein freier Speicher (ENOSPC).")

            # generic USB hint: wrong FS / ISO / readonly
            suggest_usb_prepare = bool(is_usb and (reason in ("readonly_filesystem", "mount_readonly", "device_readonly", "read_only")))
            if suggest_usb_prepare:
                hints.append("Hinweis: Schreibtest ist fehlgeschlagen. Der Stick ist evtl. schreibgeschützt oder im falschen Dateisystem (z.B. ISO). „USB vorbereiten…“ kann das beheben (Datenverlust).")

            write_test["reason_code"] = reason
            write_test["hints"] = hints
            write_test["suggest_usb_prepare"] = suggest_usb_prepare

        return {
            "status": "success",
            "backup_dir": backup_dir,
            "exists": exists,
            "is_dir": is_dir,
            "created": created,
            "fs": fs,
            "write_test": write_test,
            "mount": mount_info,
        }
    except Exception as e:
        return JSONResponse(status_code=200, content={"status": "error", "message": str(e)})


def _lsblk_tree() -> dict:
    """
    Liefert lsblk JSON (mit MOUNTPOINTS), fallback auf MOUNTPOINT.
    """
    res = run_command("lsblk -J -o NAME,TYPE,PKNAME,LABEL,SIZE,FSTYPE,MOUNTPOINTS,RM,RO,MODEL,TRAN 2>/dev/null")
    raw = res.get("stdout", "") if res["success"] else ""
    if not raw:
        res2 = run_command("lsblk -J -o NAME,TYPE,PKNAME,LABEL,SIZE,FSTYPE,MOUNTPOINT,RM,RO,MODEL,TRAN 2>/dev/null")
        raw = res2.get("stdout", "") if res2["success"] else ""
    try:
        return json.loads(raw or "{}")
    except Exception:
        return {}

def _findmnt_mounts() -> list[dict]:
    """
    Liefert Mounts aus findmnt (JSON), inkl. TARGET mit Leerzeichen.
    """
    try:
        res = run_command("findmnt -J -o SOURCE,TARGET,FSTYPE,OPTIONS 2>/dev/null")
        if not res["success"]:
            return []
        data = json.loads(res.get("stdout", "") or "{}")
        return data.get("filesystems", []) or []
    except Exception:
        return []

def _mountpoints_for_disk(disk_dev: str) -> list[str]:
    """
    Liefert alle Mountpoints für eine Disk (/dev/sdb) inkl. Partitionen (/dev/sdb1),
    robust gegen Leerzeichen, via findmnt JSON.
    """
    mps: list[str] = []
    for fs in _findmnt_mounts():
        src = (fs.get("source") or "").strip()
        tgt = (fs.get("target") or "").strip()
        if not src or not tgt:
            continue
        if src.startswith(disk_dev):
            mps.append(tgt)
    # nested first
    return sorted(set(mps), key=len, reverse=True)


def _find_lsblk_by_mountpoint(mountpoint: str) -> Optional[dict]:
    """
    Findet die Partition/Device in lsblk-JSON anhand eines Mountpoints.
    """
    mountpoint = (mountpoint or "").strip()
    if not mountpoint:
        return None

    data = _lsblk_tree()
    devices = data.get("blockdevices", []) or []

    def matches(d: dict) -> bool:
        mp = d.get("mountpoint")
        mps = d.get("mountpoints")
        if mp and mp == mountpoint:
            return True
        if isinstance(mps, list) and mountpoint in mps:
            return True
        return False

    def walk(items):
        for d in items:
            if matches(d):
                return d
            if d.get("children"):
                found = walk(d["children"])
                if found:
                    return found
        return None

    return walk(devices)


def _find_lsblk_by_name(dev_name: str) -> Optional[dict]:
    """Findet einen lsblk node anhand NAME (z.B. 'sda1'). dev_name darf auch '/dev/sda1' sein."""
    dev_name = (dev_name or "").strip()
    if dev_name.startswith("/dev/"):
        dev_name = dev_name[5:]
    if not dev_name:
        return None

    data = _lsblk_tree()
    devices = data.get("blockdevices", []) or []

    def walk(items):
        for d in items:
            if d.get("name") == dev_name:
                return d
            if d.get("children"):
                found = walk(d["children"])
                if found:
                    return found
        return None

    return walk(devices)


def _disk_is_system(disk: dict) -> bool:
    """
    True wenn Disk/Children Root/Boot gemountet haben.
    """
    bad = {"/", "/boot", "/boot/firmware"}

    def has_bad_mount(d: dict) -> bool:
        mp = d.get("mountpoint")
        mps = d.get("mountpoints")
        if mp in bad:
            return True
        if isinstance(mps, list) and any(x in bad for x in mps):
            return True
        for c in d.get("children", []) or []:
            if has_bad_mount(c):
                return True
        return False

    return has_bad_mount(disk)


def _find_disk_by_name(name: str) -> Optional[dict]:
    data = _lsblk_tree()
    devices = data.get("blockdevices", []) or []
    for d in devices:
        if d.get("name") == name and d.get("type") == "disk":
            return d
    return None


def _sanitize_label(label: str, max_len: int = 16) -> str:
    """
    Filesystem-Label safe (ext4/vfat).
    - erlaubt Buchstaben/Zahlen/Space/_/-
    - begrenzt Länge (vfat typ. 11/labeltools; wir nehmen 16 als praktikabel)
    """
    label = (label or "").strip()
    if not label:
        raise ValueError("Label darf nicht leer sein")
    allowed = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 _-")
    if any(ch not in allowed for ch in label):
        raise ValueError("Label enthält ungültige Zeichen (erlaubt: a-zA-Z0-9, Leerzeichen, _ , -)")
    if len(label) > max_len:
        label = label[:max_len].rstrip()
    return label


# -------------------- Clone (SD -> Ziellaufwerk) --------------------

CLONE_MOUNT = "/mnt/pi-installer-clone"


# Cache für disk-info (reduziert Last bei wiederholten Aufrufen)
_clone_disk_info_cache: dict = {}
_clone_disk_info_cache_ts: float = 0
CLONE_DISK_INFO_CACHE_SEC = 15


def _clone_disk_info(sudo_password: Optional[str] = None) -> dict:
    """Ermittelt Quell- (Root) und Ziel-Laufwerke für Clone. Gecacht für 15s."""
    global _clone_disk_info_cache_ts
    import time as _time
    now = _time.time()
    cache_key = "with_sudo" if (sudo_password or "").strip() else "no_sudo"
    if _clone_disk_info_cache.get(cache_key) and (now - _clone_disk_info_cache_ts) < CLONE_DISK_INFO_CACHE_SEC:
        return _clone_disk_info_cache[cache_key]

    source = {}
    boot_info = {}
    targets = []
    system_mounts = {"/", "/boot", "/boot/firmware"}
    _sudo = (sudo_password or "").strip()

    # Nur je 1x findmnt und lsblk (Performance)
    mounts = _findmnt_mounts()
    data = _lsblk_tree()
    devices = data.get("blockdevices", []) or []

    def find_node_by_name(name: str, items=None) -> Optional[dict]:
        for d in (items or devices):
            if d.get("name") == name:
                return d
            if d.get("children"):
                n = find_node_by_name(name, d["children"])
                if n:
                    return n
        return None

    def find_disk_for_part(part: dict) -> Optional[dict]:
        pk = part.get("pkname") or (part.get("name", "").rstrip("0123456789") if part.get("name") else None)
        if pk:
            return find_node_by_name(pk)
        return None

    # Root-Mount
    for fs in mounts:
        tgt = (fs.get("target") or "").strip()
        src = (fs.get("source") or "").strip()
        if tgt == "/" and src.startswith("/dev/"):
            name = src.replace("/dev/", "")
            node = find_node_by_name(name)
            disk = find_disk_for_part(node) if node else None
            if node:
                source = {
                    "device": src,
                    "mountpoint": "/",
                    "size": node.get("size"),
                    "fstype": node.get("fstype") or fs.get("fstype"),
                    "name": node.get("name"),
                    "model": disk.get("model") if disk else None,
                }
            break

    # Boot-Partition
    for fs in mounts:
        tgt = (fs.get("target") or "").strip()
        src = (fs.get("source") or "").strip()
        if tgt in ("/boot", "/boot/firmware") and src.startswith("/dev/"):
            boot_info = {"mountpoint": tgt, "device": src}
            break
    if not boot_info and Path("/boot/firmware").exists():
        boot_info = {"mountpoint": "/boot/firmware", "device": None}

    def _get_fstype(dev_path: str) -> str:
        if not dev_path or not dev_path.startswith("/dev/"):
            return ""
        r = run_command(f"blkid -o value -s TYPE {shlex.quote(dev_path)} 2>/dev/null", timeout=2)
        if r.get("success") and r.get("stdout"):
            return (r.get("stdout") or "").strip().lower()
        if _sudo:
            r = run_command(f"blkid -o value -s TYPE {shlex.quote(dev_path)} 2>/dev/null", sudo=True, sudo_password=_sudo, timeout=2)
            if r.get("success") and r.get("stdout"):
                return (r.get("stdout") or "").strip().lower()
        return ""

    def walk_for_targets(items, disk_ctx=None):
        for d in items:
            if d.get("type") == "disk":
                disk_ctx = d
            dtype = d.get("type")
            name = d.get("name")
            fstype_raw = (d.get("fstype") or "").strip()
            fstype = fstype_raw.lower() if fstype_raw else ""
            mp = d.get("mountpoint")
            mps = d.get("mountpoints")
            mps_list = mps if isinstance(mps, list) else ([mp] if mp else [])
            is_system = any(m in system_mounts for m in mps_list if m)

            if dtype == "part" and name and not is_system:
                dev_path = f"/dev/{name}"
                if dev_path == source.get("device"):
                    continue
                if not fstype:
                    fstype = _get_fstype(dev_path)
                if fstype != "ext4":
                    continue
                disk = disk_ctx or find_disk_for_part(d)
                targets.append({
                    "device": dev_path,
                    "name": name,
                    "size": d.get("size"),
                    "fstype": fstype,
                    "mounted": bool(mp or (mps_list and mps_list[0])),
                    "mountpoint": mp or (mps_list[0] if mps_list else None),
                    "model": disk.get("model") if disk else None,
                    "tran": disk.get("tran") if disk else d.get("tran"),
                })
            if d.get("children"):
                walk_for_targets(d["children"], disk_ctx)

    walk_for_targets(devices)
    result = {"source": source, "boot": boot_info, "targets": targets}
    _clone_disk_info_cache[cache_key] = result
    _clone_disk_info_cache_ts = now
    return result


@app.api_route("/api/backup/clone/disk-info", methods=["GET", "POST"])
async def clone_disk_info(request: Request, refresh: int = 0):
    """Quell- und Ziel-Laufwerke für System-Clone auflisten. POST mit sudo_password nutzt dieses für blkid. refresh=1 umgeht Cache."""
    try:
        global _clone_disk_info_cache_ts
        if refresh:
            _clone_disk_info_cache_ts = 0  # Cache invalidieren
        sudo_password = sudo_password_store.get("password", "") or ""
        if request.method == "POST":
            try:
                body = await request.json()
                pw = (body.get("sudo_password") or "").strip()
                if pw:
                    sudo_password = pw
                    if not sudo_password_store.get("password"):
                        sudo_password_store["password"] = pw
            except Exception:
                pass
        info = _clone_disk_info(sudo_password=sudo_password)
        return {"status": "success", **info}
    except Exception as e:
        logger.exception("clone disk-info failed")
        return JSONResponse(status_code=200, content={"status": "error", "message": str(e), "source": {}, "boot": {}, "targets": []})


def _do_clone_logic(
    target_device: str,
    sudo_password: str,
    job: dict,
    cancel_event: Optional[threading.Event] = None,
) -> dict:
    """Führt den Klon-Vorgang aus (rsync + fstab/cmdline.txt)."""
    results = []
    mountpoint = CLONE_MOUNT

    def _add(msg: str):
        results.append(msg)
        if job:
            job["results"] = list(results)
            job["message"] = msg

    try:
        info = _clone_disk_info()
        source = info.get("source") or {}
        boot_info = info.get("boot") or {}
        boot_mount = (boot_info.get("mountpoint") or "/boot/firmware").strip()
        boot_device = boot_info.get("device")

        if not source.get("device"):
            return {"status": "error", "message": "Quell-Laufwerk (/) nicht gefunden", "results": results}

        target_device = (target_device or "").strip()
        if not target_device or not target_device.startswith("/dev/"):
            return {"status": "error", "message": "Ungültiges Ziellaufwerk", "results": results}

        # Prüfen ob Ziel in targets
        targets = info.get("targets") or []
        tgt_match = next((t for t in targets if t.get("device") == target_device), None)
        if not tgt_match:
            return {"status": "error", "message": f"Ziellaufwerk {target_device} ist kein gültiger ext4-Zielkandidat", "results": results}

        _add("Klon wird gestartet: " + target_device)

        # Ziel unmounten falls woanders gemountet
        mp = tgt_match.get("mountpoint")
        if mp:
            r = run_command(f"umount {shlex.quote(mp)} 2>/dev/null", sudo=True, sudo_password=sudo_password, timeout=30)
            if r.get("success"):
                _add(f"Ziel von {mp} ausgehängt")
            else:
                return {"status": "error", "message": f"Ziel ist unter {mp} gemountet und konnte nicht ausgehängt werden. Bitte manuell unmounten.", "results": results}

        # Mount-Punkt anlegen (sudo – /mnt/ benötigt Root-Rechte)
        r = run_command(f"mkdir -p {shlex.quote(mountpoint)}", sudo=True, sudo_password=sudo_password, timeout=10)
        if not r.get("success"):
            return {"status": "error", "message": f"Mount-Punkt {mountpoint} konnte nicht erstellt werden: {(r.get('stderr') or r.get('stdout') or '')[:150]}", "results": results}

        # Mount Ziel
        r = run_command(f"mount {shlex.quote(target_device)} {shlex.quote(mountpoint)}", sudo=True, sudo_password=sudo_password, timeout=30)
        if not r.get("success"):
            return {"status": "error", "message": f"Ziel konnte nicht gemountet werden: {(r.get('stderr') or r.get('stdout') or '')[:200]}", "results": results}
        _add("Ziel gemountet")

        # rsync
        excludes = [
            "/boot", "/boot/firmware",
            "/proc", "/sys", "/dev", "/tmp", "/run", "/mnt", "/lost+found",
            mountpoint.rstrip("/"),
        ]
        excl_args = " ".join(f"--exclude={shlex.quote(x)}" for x in excludes)
        rsync_cmd = (
            f"rsync -axHAWXS --numeric-ids --info=progress2 {excl_args} / {shlex.quote(mountpoint)}/"
        )
        _add("Rsync läuft (kann einige Minuten dauern)…")
        r = run_command(rsync_cmd, sudo=True, sudo_password=sudo_password, timeout=7200)
        if cancel_event and cancel_event.is_set():
            run_command(f"umount {shlex.quote(mountpoint)} 2>/dev/null", sudo=True, sudo_password=sudo_password, timeout=30)
            return {"status": "cancelled", "message": "Abgebrochen", "results": results}
        if not r.get("success"):
            run_command(f"umount {shlex.quote(mountpoint)} 2>/dev/null", sudo=True, sudo_password=sudo_password, timeout=30)
            return {"status": "error", "message": f"Rsync fehlgeschlagen: {(r.get('stderr') or r.get('stdout') or '')[:300]}", "results": results}
        _add("Rsync abgeschlossen")

        # fstab auf Ziel anpassen
        fstab_path = Path(mountpoint) / "etc" / "fstab"
        if fstab_path.exists():
            try:
                content = fstab_path.read_text(encoding="utf-8")
                lines = content.splitlines()
                new_lines = []
                for line in lines:
                    s = line.strip()
                    if not s or s.startswith("#"):
                        new_lines.append(line)
                        continue
                    parts = s.split()
                    if len(parts) >= 2 and parts[1] == "/":
                        # Root-Zeile ersetzen
                        new_lines.append(f"{target_device}  /  ext4  defaults,noatime  0  1")
                    else:
                        new_lines.append(line)
                fstab_path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
                _add("fstab angepasst")
            except Exception as e:
                _add(f"Warnung: fstab konnte nicht angepasst werden: {e}")

        # cmdline.txt anpassen
        cmdline_path = Path(boot_mount) / "cmdline.txt"
        if cmdline_path.exists():
            try:
                content = cmdline_path.read_text(encoding="utf-8")
                new_content = re.sub(r"root=[^\s]+", f"root={target_device}", content)
                if new_content != content:
                    cmdline_path.write_text(new_content, encoding="utf-8")
                    _add("cmdline.txt angepasst (root=" + target_device + ")")
                else:
                    _add("cmdline.txt bereits korrekt oder unverändert")
            except Exception as e:
                _add(f"Warnung: cmdline.txt konnte nicht angepasst werden: {e}")
        else:
            _add("cmdline.txt nicht gefunden unter " + boot_mount)

        # Unmount
        run_command(f"umount {shlex.quote(mountpoint)} 2>/dev/null", sudo=True, sudo_password=sudo_password, timeout=30)
        _add("Ziel ausgehängt – Klon fertig. Bitte neu starten (sudo reboot), damit von " + target_device + " gebootet wird.")

        return {"status": "success", "message": "Klon erfolgreich", "results": results}
    except Exception as e:
        logger.exception("clone failed")
        try:
            run_command(f"umount {shlex.quote(mountpoint)} 2>/dev/null", sudo=True, sudo_password=sudo_password, timeout=30)
        except Exception:
            pass
        return {"status": "error", "message": str(e), "results": results}


@app.post("/api/backup/clone")
async def clone_disk(request: Request):
    """System von SD-Karte auf Ziellaufwerk klonen (async Job)."""
    try:
        try:
            data = await request.json()
        except Exception:
            data = {}

        sudo_password = (data.get("sudo_password") or "").strip() or sudo_password_store.get("password", "")
        target_device = (data.get("target_device") or "").strip()

        if not target_device or not target_device.startswith("/dev/"):
            return JSONResponse(status_code=200, content={"status": "error", "message": "target_device (/dev/...) erforderlich"})
        if not sudo_password:
            sudo_test = run_command("sudo -n true", sudo=False)
            if not sudo_test.get("success"):
                return JSONResponse(status_code=200, content={"status": "error", "message": "Sudo-Passwort erforderlich", "requires_sudo_password": True})

        job_id = _new_job_id()
        BACKUP_JOBS[job_id] = {
            "job_id": job_id,
            "status": "queued",
            "type": "clone",
            "target_device": target_device,
            "started_at": _now_iso(),
            "finished_at": None,
            "message": "Wartet…",
            "results": [],
        }

        def _runner():
            try:
                ev = BACKUP_JOB_CANCEL.get(job_id)
                if not ev:
                    ev = threading.Event()
                    BACKUP_JOB_CANCEL[job_id] = ev
                BACKUP_JOBS[job_id]["status"] = "running"
                BACKUP_JOBS[job_id]["message"] = "Klon läuft…"
                result = _do_clone_logic(target_device, sudo_password, BACKUP_JOBS[job_id], cancel_event=ev)
                BACKUP_JOBS[job_id]["results"] = result.get("results") or []
                BACKUP_JOBS[job_id]["finished_at"] = _now_iso()
                BACKUP_JOBS[job_id]["status"] = result.get("status", "error")
                BACKUP_JOBS[job_id]["message"] = result.get("message", "Fertig")
            except Exception as e:
                logger.exception("clone job failed")
                BACKUP_JOBS[job_id]["status"] = "error"
                BACKUP_JOBS[job_id]["message"] = str(e)
                BACKUP_JOBS[job_id]["finished_at"] = _now_iso()
            finally:
                BACKUP_JOB_CANCEL.pop(job_id, None)

        t = threading.Thread(target=_runner, daemon=True)
        t.start()

        return JSONResponse(status_code=200, content={
            "status": "accepted",
            "job_id": job_id,
            "message": "Klon-Job gestartet",
        })
    except Exception as e:
        logger.exception("clone endpoint failed")
        return JSONResponse(status_code=200, content={"status": "error", "message": str(e)})


@app.get("/api/backup/usb/info")
async def backup_usb_info(mountpoint: str = "", device: str = ""):
    """Gibt Infos zum ausgewählten USB-Mountpoint zurück (Device, FS, Label, Safety Flags)."""
    try:
        node = _find_lsblk_by_mountpoint(mountpoint) if mountpoint else None
        # Fallback: manchmal ist lsblk nicht synchron / mountpoint kommt nicht zurück -> findmnt SOURCE nutzen
        if not node and mountpoint:
            for fs in _findmnt_mounts():
                tgt = (fs.get("target") or "").strip()
                src = (fs.get("source") or "").strip()
                if tgt and src and tgt == mountpoint and src.startswith("/dev/"):
                    node = _find_lsblk_by_name(src)
                    break
        if not node and device:
            node = _find_lsblk_by_name(device)
        if not node:
            return JSONResponse(status_code=200, content={"status": "error", "message": "USB-Gerät nicht gefunden (Mountpoint/Device)"})

        name = node.get("name")
        pk = node.get("pkname")  # parent disk
        disk_name = pk or (name if node.get("type") == "disk" else None)
        if not disk_name:
            return JSONResponse(status_code=200, content={"status": "error", "message": "Konnte Disk nicht bestimmen"})

        disk = _find_disk_by_name(disk_name)
        if not disk:
            return JSONResponse(status_code=200, content={"status": "error", "message": "Disk nicht gefunden"})

        info = {
            "status": "success",
            "mountpoint": mountpoint or None,
            "partition": f"/dev/{name}" if name else None,
            "disk": f"/dev/{disk_name}",
            "fstype": node.get("fstype"),
            "label": node.get("label"),
            "size": node.get("size"),
            "rm": disk.get("rm"),
            "ro": node.get("ro") or disk.get("ro"),
            "tran": disk.get("tran"),
            "model": disk.get("model"),
            "is_usb": (disk.get("tran") == "usb"),
            "is_removable": bool(disk.get("rm")),
            "is_system_disk": _disk_is_system(disk),
        }
        return info
    except Exception as e:
        return JSONResponse(status_code=200, content={"status": "error", "message": str(e)})


@app.post("/api/backup/usb/mount")
async def backup_usb_mount(request: Request):
    """
    Mountet ein (noch) ungemountetes USB-Device (Partition) nach /mnt/pi-installer-usb/<name>.
    Nicht-destruktiv: kein Formatieren, kein Label ändern.
    """
    try:
        try:
            data = await request.json()
        except Exception:
            data = {}

        device = (data.get("device") or "").strip()
        sudo_password = data.get("sudo_password", "") or sudo_password_store.get("password", "")

        if not device or not device.startswith("/dev/"):
            return JSONResponse(status_code=200, content={"status": "error", "message": "device (/dev/...) erforderlich"})
        if not sudo_password:
            return JSONResponse(status_code=200, content={"status": "error", "message": "Sudo-Passwort erforderlich", "requires_sudo_password": True})

        node = _find_lsblk_by_name(device)
        if not node:
            return JSONResponse(status_code=200, content={"status": "error", "message": "USB-Gerät nicht gefunden"})

        # bereits gemountet? -> bestehenden Mountpoint zurückgeben
        system_mounts = {"/", "/boot", "/boot/firmware", "[SWAP]"}
        mps = node.get("mountpoints")
        mp = node.get("mountpoint")
        existing = None
        if isinstance(mps, list):
            for one in mps:
                if one and one not in system_mounts:
                    existing = one
                    break
        elif mp and mp not in system_mounts:
            existing = mp
        if existing:
            return {"status": "success", "message": "Bereits gemountet", "mounted_to": existing, "device": device}

        part_name = node.get("name")
        pk = node.get("pkname")
        disk_name = pk or (part_name if node.get("type") == "disk" else None)
        if not disk_name:
            return JSONResponse(status_code=200, content={"status": "error", "message": "Konnte Disk nicht bestimmen"})

        disk = _find_disk_by_name(disk_name)
        if not disk:
            return JSONResponse(status_code=200, content={"status": "error", "message": "Disk nicht gefunden"})

        # Safety: nur USB/removable, nie Systemdisk
        is_usb = (disk.get("tran") == "usb")
        is_rm = bool(disk.get("rm"))
        if not (is_usb or is_rm):
            return JSONResponse(status_code=200, content={"status": "error", "message": "Nur USB/Removable Datenträger sind erlaubt"})
        if _disk_is_system(disk):
            return JSONResponse(status_code=200, content={"status": "error", "message": "Refused: System-Datenträger erkannt"})

        # Mount directory name
        def safe_seg(s: str) -> str:
            s = (s or "").strip()
            if not s:
                return ""
            allowed = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-")
            out = []
            for ch in s.replace(" ", "_"):
                if ch in allowed:
                    out.append(ch)
            return "".join(out)[:32].strip("_") or ""

        label = str(node.get("label") or "")
        seg = safe_seg(label) or safe_seg(str(part_name or "")) or safe_seg(str(disk_name or "")) or "USB"
        mount_dir = f"/mnt/pi-installer-usb/{seg}"

        # mount
        run_command(f"mkdir -p {shlex.quote(mount_dir)}", sudo=True, sudo_password=sudo_password, timeout=30)
        uid = os.getuid()
        gid = os.getgid()
        fstype = (node.get("fstype") or "").strip().lower()
        mount_opts = "rw"
        # Non-POSIX FS (vfat/exfat/ntfs) need uid/gid so UI user can write
        if fstype in ("vfat", "fat", "msdos", "exfat", "ntfs", "ntfs3"):
            mount_opts = f"rw,uid={uid},gid={gid},umask=0022"
        mnt_cmd = f"mount -o {shlex.quote(mount_opts)} {shlex.quote(device)} {shlex.quote(mount_dir)}"
        mnt = run_command(mnt_cmd, sudo=True, sudo_password=sudo_password, timeout=60)
        if not mnt.get("success"):
            msg = (mnt.get("stderr") or mnt.get("stdout") or mnt.get("error") or "Mount fehlgeschlagen").strip()[:300]
            return JSONResponse(status_code=200, content={"status": "error", "message": msg})

        # ensure backup folder exists and is writable for current user
        backups_dir = f"{mount_dir}/pi-installer-backups"
        run_command(f"mkdir -p {shlex.quote(backups_dir)}", sudo=True, sudo_password=sudo_password, timeout=30)
        run_command(f"chmod 0775 {shlex.quote(mount_dir)} {shlex.quote(backups_dir)}", sudo=True, sudo_password=sudo_password, timeout=30)
        run_command(f"chown {uid}:{gid} {shlex.quote(mount_dir)} {shlex.quote(backups_dir)}", sudo=True, sudo_password=sudo_password, timeout=30)

        return {"status": "success", "message": "Gemountet", "mounted_to": mount_dir, "device": device, "label": label or None}
    except Exception as e:
        return JSONResponse(status_code=200, content={"status": "error", "message": str(e)})


@app.post("/api/backup/usb/prepare")
async def backup_usb_prepare(request: Request):
    """
    USB vorbereiten:
    - optional formatieren (Datenverlust!)
    - optional umbenennen (Label)
    - mounten auf /mnt/pi-installer-usb/<label>
    """
    try:
        data = await request.json()
        mountpoint = (data.get("mountpoint") or "").strip()
        device = (data.get("device") or "").strip()
        do_format = bool(data.get("format", False))
        new_label_raw = data.get("label", "")
        sudo_password = data.get("sudo_password", "") or sudo_password_store.get("password", "")

        if not sudo_password:
            return JSONResponse(status_code=200, content={"status": "error", "message": "Sudo-Passwort erforderlich", "requires_sudo_password": True})

        node = _find_lsblk_by_mountpoint(mountpoint) if mountpoint else None
        if not node and mountpoint:
            for fs in _findmnt_mounts():
                tgt = (fs.get("target") or "").strip()
                src = (fs.get("source") or "").strip()
                if tgt and src and tgt == mountpoint and src.startswith("/dev/"):
                    node = _find_lsblk_by_name(src)
                    break
        if not node and device:
            node = _find_lsblk_by_name(device)
        if not node:
            return JSONResponse(status_code=200, content={"status": "error", "message": "Mountpoint nicht gefunden"})

        part_name = node.get("name")
        pk = node.get("pkname")
        disk_name = pk or (part_name if node.get("type") == "disk" else None)
        if not disk_name:
            return JSONResponse(status_code=200, content={"status": "error", "message": "Konnte Disk nicht bestimmen"})

        disk = _find_disk_by_name(disk_name)
        if not disk:
            return JSONResponse(status_code=200, content={"status": "error", "message": "Disk nicht gefunden"})

        # Safety: nur USB/removable, nie Systemdisk
        is_usb = (disk.get("tran") == "usb")
        is_rm = bool(disk.get("rm"))
        if not (is_usb or is_rm):
            return JSONResponse(status_code=200, content={"status": "error", "message": "Nur USB/Removable Datenträger sind erlaubt"})
        if _disk_is_system(disk):
            return JSONResponse(status_code=200, content={"status": "error", "message": "Refused: System-Datenträger erkannt"})

        new_label = None
        if new_label_raw:
            new_label = _sanitize_label(new_label_raw, max_len=16)

        results = []

        disk_dev = f"/dev/{disk_name}"
        part_dev = f"/dev/{part_name}" if part_name else None

        def step(cmd: str, label: str, allow_fail: bool = False) -> dict:
            res = run_command(cmd, sudo=True, sudo_password=sudo_password, timeout=120)
            ok = bool(res.get("success"))
            if ok:
                results.append(f"✅ {label}")
                return res
            msg = (res.get("stderr") or res.get("stdout") or res.get("error") or "").strip()
            msg = msg[:300] if msg else "Unbekannter Fehler"
            results.append(f"❌ {label}: {msg}")
            if allow_fail:
                return res
            return {"_failed": True, "label": label, "message": msg, "raw": res}

        # quick tool checks (helps on minimal images)
        for tool in ("wipefs", "parted", "mkfs.ext4", "partprobe", "mount", "umount"):
            w = run_command(f"which {shlex.quote(tool)} 2>/dev/null")
            if not w.get("success"):
                return JSONResponse(
                    status_code=200,
                    content={"status": "error", "message": f"Formatierung nicht möglich: Tool fehlt ({tool})", "results": results},
                )

        # refuse hardware RO
        if bool(disk.get("ro")) or bool(node.get("ro")):
            return JSONResponse(
                status_code=200,
                content={
                    "status": "error",
                    "message": "Formatierung nicht möglich: Datenträger ist schreibgeschützt (RO=1).",
                    "results": results,
                },
            )

        # Unmount (erforderlich für wipefs/parted/mkfs)
        # 1) explizit den ausgewählten Mountpoint unmounten (auch mit Spaces)
        if mountpoint:
            step(f"umount {shlex.quote(mountpoint)}", f"Unmount {mountpoint}", allow_fail=True)
            step(f"umount -l {shlex.quote(mountpoint)}", f"Lazy-Unmount {mountpoint}", allow_fail=True)

        # 2) alles von dieser Disk unmounten (sicher)
        for mp in _mountpoints_for_disk(disk_dev):
            step(f"umount {shlex.quote(mp)}", f"Unmount {mp}", allow_fail=True)
            step(f"umount -l {shlex.quote(mp)}", f"Lazy-Unmount {mp}", allow_fail=True)

        # 3) prüfen ob noch etwas gemountet ist -> dann abbrechen
        remaining = _mountpoints_for_disk(disk_dev)
        if remaining:
            return JSONResponse(
                status_code=200,
                content={
                    "status": "error",
                    "message": (
                        "Der USB-Stick ist noch gemountet oder wird von einem Prozess verwendet. "
                        "Bitte schließen Sie alle Fenster/Programme, die auf den Stick zugreifen, und versuchen Sie es erneut."
                    ),
                    "still_mounted": remaining,
                },
            )

        mounted_to = None

        if do_format:
            if not new_label:
                new_label = "PI-INSTALLER"

            # Partition table + single partition
            # Achtung: extrem destruktiv -> nur nach explizitem User-Confirm im Frontend aufrufen!
            results.append(f"Formatierung gestartet: {disk_dev}")
            r = step(f"wipefs -a {shlex.quote(disk_dev)}", f"wipefs auf {disk_dev}")
            if r.get("_failed"):
                return JSONResponse(status_code=200, content={"status": "error", "message": f"Formatierung fehlgeschlagen bei wipefs: {r['message']}", "results": results})

            r = step(f"parted -s {shlex.quote(disk_dev)} mklabel gpt", f"Partitionstabelle GPT erstellen ({disk_dev})")
            if r.get("_failed"):
                return JSONResponse(status_code=200, content={"status": "error", "message": f"Formatierung fehlgeschlagen bei parted mklabel: {r['message']}", "results": results})

            r = step(f"parted -s {shlex.quote(disk_dev)} mkpart primary 1MiB 100%", f"Partition erstellen ({disk_dev})")
            if r.get("_failed"):
                return JSONResponse(status_code=200, content={"status": "error", "message": f"Formatierung fehlgeschlagen bei parted mkpart: {r['message']}", "results": results})

            # Let kernel settle
            step("partprobe", "partprobe", allow_fail=True)
            step("udevadm settle 2>/dev/null", "udevadm settle", allow_fail=True)

            # Bestimme neue Partition (meist ...1)
            part_guess = f"{disk_dev}1"
            # mkfs ext4
            r = step(f"mkfs.ext4 -F -L {shlex.quote(new_label)} {shlex.quote(part_guess)}", f"mkfs.ext4 ({part_guess})")
            if r.get("_failed"):
                return JSONResponse(status_code=200, content={"status": "error", "message": f"Formatierung fehlgeschlagen bei mkfs.ext4: {r['message']}", "results": results})
            results.append("Dateisystem ext4 erstellt")
            part_dev = part_guess
        else:
            # Rename only (best effort)
            if new_label and part_dev:
                fstype = node.get("fstype") or ""
                if fstype == "ext4":
                    rn = run_command(f"e2label {shlex.quote(part_dev)} {shlex.quote(new_label)}", sudo=True, sudo_password=sudo_password)
                    if rn["success"]:
                        results.append(f"Label gesetzt: {new_label}")
                    else:
                        results.append(f"Label setzen fehlgeschlagen: {rn.get('stderr','')[:120]}")
                elif fstype in ("vfat", "fat", "msdos"):
                    rn = run_command(f"fatlabel {shlex.quote(part_dev)} {shlex.quote(new_label)}", sudo=True, sudo_password=sudo_password)
                    if rn["success"]:
                        results.append(f"Label gesetzt: {new_label}")
                    else:
                        results.append(f"Label setzen fehlgeschlagen: {rn.get('stderr','')[:120]}")
                else:
                    results.append(f"Umbenennen nicht unterstützt für fstype={fstype} (bitte formatieren)")

        # Mount after format/rename (optional, to stable path)
        if part_dev and (do_format or new_label):
            label_for_mount = (new_label or "PI-INSTALLER").replace(" ", "_")
            mount_dir = f"/mnt/pi-installer-usb/{label_for_mount}"
            step(f"mkdir -p {shlex.quote(mount_dir)}", f"Mount-Verzeichnis anlegen ({mount_dir})")
            mnt = step(f"mount {shlex.quote(part_dev)} {shlex.quote(mount_dir)}", f"Mount {part_dev} -> {mount_dir}", allow_fail=True)
            if mnt.get("success"):
                mounted_to = mount_dir
                results.append(f"Gemountet: {mount_dir}")
            else:
                # give actionable hint
                err = (mnt.get("stderr") or mnt.get("stdout") or mnt.get("error") or "").strip()[:200]
                results.append(f"Mount fehlgeschlagen: {err}")

        return {
            "status": "success",
            "message": "USB vorbereitet",
            "results": results,
            "mounted_to": mounted_to,
            "disk": disk_dev,
            "partition": part_dev,
            "label": new_label,
        }
    except Exception as e:
        return JSONResponse(status_code=200, content={"status": "error", "message": str(e)})


@app.post("/api/backup/usb/eject")
async def backup_usb_eject(request: Request):
    """
    USB sicher auswerfen:
    - sync
    - unmount (alle Mountpoints der Disk)
    - optional power-off (udisksctl), wenn verfügbar
    """
    try:
        data = await request.json()
        mountpoint = (data.get("mountpoint") or "").strip()
        device = (data.get("device") or "").strip()
        sudo_password = data.get("sudo_password", "") or sudo_password_store.get("password", "")

        if not sudo_password:
            return JSONResponse(status_code=200, content={"status": "error", "message": "Sudo-Passwort erforderlich", "requires_sudo_password": True})

        node = _find_lsblk_by_mountpoint(mountpoint) if mountpoint else None
        if not node and device:
            node = _find_lsblk_by_name(device)
        if not node:
            return JSONResponse(status_code=200, content={"status": "error", "message": "USB-Gerät nicht gefunden (Mountpoint/Device)"})

        part_name = node.get("name")
        pk = node.get("pkname")
        disk_name = pk or (part_name if node.get("type") == "disk" else None)
        if not disk_name:
            return JSONResponse(status_code=200, content={"status": "error", "message": "Konnte Disk nicht bestimmen"})

        disk = _find_disk_by_name(disk_name)
        if not disk:
            return JSONResponse(status_code=200, content={"status": "error", "message": "Disk nicht gefunden"})

        # Safety
        is_usb = (disk.get("tran") == "usb")
        is_rm = bool(disk.get("rm"))
        if not (is_usb or is_rm):
            return JSONResponse(status_code=200, content={"status": "error", "message": "Nur USB/Removable Datenträger sind erlaubt"})
        if _disk_is_system(disk):
            return JSONResponse(status_code=200, content={"status": "error", "message": "Refused: System-Datenträger erkannt"})

        disk_dev = f"/dev/{disk_name}"

        results = []
        run_command("sync", sudo=True, sudo_password=sudo_password)
        results.append("sync ausgeführt")

        # Unmount all mountpoints for disk
        for mp in _mountpoints_for_disk(disk_dev):
            run_command(f"umount {shlex.quote(mp)}", sudo=True, sudo_password=sudo_password)
            run_command(f"umount -l {shlex.quote(mp)}", sudo=True, sudo_password=sudo_password)

        remaining = _mountpoints_for_disk(disk_dev)
        if remaining:
            return JSONResponse(
                status_code=200,
                content={
                    "status": "error",
                    "message": "Auswerfen fehlgeschlagen: Datenträger ist noch gemountet/busy",
                    "still_mounted": remaining,
                    "results": results,
                },
            )
        results.append("Unmount erfolgreich")

        # Optional: power off
        power_off = None
        which = run_command("which udisksctl 2>/dev/null")
        if which["success"] and which.get("stdout", "").strip():
            po = run_command(f"udisksctl power-off -b {shlex.quote(disk_dev)}", sudo=True, sudo_password=sudo_password)
            if po["success"]:
                power_off = True
                results.append("udisksctl power-off erfolgreich")
            else:
                power_off = False
                results.append(f"udisksctl power-off fehlgeschlagen: {(po.get('stderr') or '')[:120]}")

        return {
            "status": "success",
            "message": "USB sicher ausgeworfen",
            "disk": disk_dev,
            "results": results,
            "power_off": power_off,
        }
    except Exception as e:
        return JSONResponse(status_code=200, content={"status": "error", "message": str(e)})

@app.post("/api/backup/create")
async def create_backup(request: Request):
    """Backup erstellen (optional async job)."""
    try:
        try:
            data = await request.json()
        except Exception:
            data = {}

        sudo_password = data.get("sudo_password", "") or sudo_password_store.get("password", "")
        backup_type = (data.get("type", "full") or "full").strip()
        run_async = bool(data.get("async", False))
        target = (data.get("target") or "local").strip()  # local | cloud_only | local_and_cloud

        if not sudo_password:
            sudo_test = run_command("sudo -n true", sudo=False)
            if not sudo_test.get("success"):
                return JSONResponse(status_code=200, content={"status": "error", "message": "Sudo-Passwort erforderlich", "requires_sudo_password": True})

        backup_dir = data.get("backup_dir", "/mnt/backups")
        try:
            backup_dir = _validate_backup_dir(backup_dir)
        except Exception as ve:
            return JSONResponse(status_code=200, content={"status": "error", "message": f"Ungültiges Backup-Ziel: {str(ve)}"})

        timestamp = run_command("date +%Y%m%d_%H%M%S").get("stdout", "").strip()

        mkdir_result = run_command(f"mkdir -p {shlex.quote(backup_dir)}", sudo=True, sudo_password=sudo_password, timeout=60)
        if not mkdir_result.get("success"):
            return JSONResponse(status_code=200, content={"status": "error", "message": f"Backup-Verzeichnis konnte nicht erstellt werden: {backup_dir}"})

        # precompute backup file name for UI
        bf = None
        if backup_type == "full":
            bf = f"{backup_dir}/pi-backup-full-{timestamp}.tar.gz"
        elif backup_type == "incremental":
            bf = f"{backup_dir}/pi-backup-inc-{timestamp}.tar.gz"
        elif backup_type == "data":
            bf = f"{backup_dir}/pi-backup-data-{timestamp}.tar.gz"

        last_hint = str(data.get("last_backup", "") or "")
        # cloud settings from persisted backup settings
        backup_settings = _read_backup_settings()
        cloud = backup_settings.get("cloud") or {}

        def _cloud_remote_url(local_file: str, cloud_settings: dict = None) -> Optional[str]:
            # Verwende übergebene Cloud-Einstellungen oder die aus dem äußeren Scope
            cloud_to_use = cloud_settings if cloud_settings is not None else cloud
            # Prüfe ob Cloud aktiviert ist
            if not cloud_to_use.get("enabled"):
                return None
            provider = cloud_to_use.get("provider") or "seafile_webdav"
            # Für WebDAV-basierte Provider: URL konstruieren
            if provider in ("seafile_webdav", "webdav", "nextcloud_webdav"):
                url = (cloud_to_use.get("webdav_url") or "").strip().rstrip("/")
                user = (cloud_to_use.get("username") or "").strip()
                pw = (cloud_to_use.get("password") or "").strip()
                if not url or not user or not pw:
                    return None
                remote_path = (cloud_to_use.get("remote_path") or "").strip().strip("/")
                base = f"{url}/{remote_path}" if remote_path else url
                if not base.endswith("/"):
                    base += "/"
                return f"{base}{Path(local_file).name}"
            # Für andere Provider wird die URL vom Backup-Modul generiert
            return None

        def _cloud_upload_and_verify(local_file: str, cloud_settings: dict = None, job_id: str = "") -> tuple[bool, str]:
            """Cloud-Upload mit Verifizierung. job_id für Fortschritt und 1‑Min‑Prüfung bei Timeout."""
            # Verwende übergebene Cloud-Einstellungen oder die aus dem äußeren Scope
            cloud_to_use = cloud_settings if cloud_settings is not None else cloud
            logger.info(f"[Cloud-Upload] _cloud_upload_and_verify: local_file={local_file}, cloud.enabled={cloud_to_use.get('enabled')}, target={target}")
            if not cloud_to_use.get("enabled"):
                logger.warning("[Cloud-Upload] Cloud-Upload ist deaktiviert (cloud.enabled=False)")
                return False, "Cloud-Upload ist deaktiviert"
            provider = cloud_to_use.get("provider") or "seafile_webdav"
            url_ok = bool((cloud_to_use.get("webdav_url") or "").strip())
            user_ok = bool((cloud_to_use.get("username") or "").strip())
            pw_ok = bool((cloud_to_use.get("password") or "").strip())
            logger.info(f"[Cloud-Upload] Provider={provider}, url={url_ok}, user={user_ok}, pw={pw_ok}, file_exists={Path(local_file).exists()}")
            
            webdav_providers = ("seafile_webdav", "webdav", "nextcloud_webdav")
            if provider not in webdav_providers:
                try:
                    backup_mod = _get_backup_module()
                    backup_mod.run_command = run_command
                    ok, info = backup_mod.upload_to_cloud(local_file, provider, cloud_to_use, sudo_password)
                    if ok:
                        return True, info
                except Exception as e:
                    logger.error(f"Backup-Modul Upload (non-WebDAV): {e}", exc_info=True)
                return False, f"Provider '{provider}' wird für Cloud-Upload nicht unterstützt (nur WebDAV)"
            # WebDAV: eigene Logik mit Fortschritt und 1‑Min‑Prüfung bei Timeout
            url = (cloud_to_use.get("webdav_url") or "").strip().rstrip("/")
            user = (cloud_to_use.get("username") or "").strip()
            pw = (cloud_to_use.get("password") or "").strip()
            if not url or not user or not pw:
                logger.error("[Cloud-Upload] Cloud-Settings fehlen: url=%s, user=%s, pw=%s", bool(url), bool(user), bool(pw))
                return False, "Cloud-Settings fehlen (URL/User/Passwort)"
            remote = _cloud_remote_url(local_file, cloud_to_use)
            if not remote:
                logger.error("[Cloud-Upload] Cloud-Ziel konnte nicht bestimmt werden; provider=%s, url_len=%s", provider, len(url))
                return False, f"Cloud-Ziel konnte nicht bestimmt werden (Provider: {provider}, URL: {url[:50]}...)"
            upload_timeout = 7200  # 2 h für große Backups / langsame Verbindungen
            # Parent-Collection (Verzeichnis) für MKCOL: null -> 409 vermeiden
            remote_path = (cloud_to_use.get("remote_path") or "").strip().strip("/")
            if remote_path:
                base = f"{url}/{remote_path}".rstrip("/") + "/"
                parts = [p for p in base.rstrip("/").replace(url.rstrip("/"), "", 1).strip("/").split("/") if p]
                mkcol_base = url.rstrip("/") + "/"
                for seg in parts:
                    mkcol_base = mkcol_base.rstrip("/") + "/" + seg + "/"
                    mc = run_command(
                        f"curl -sS -o /dev/null -w '%{{http_code}}' -u {shlex.quote(user)}:{shlex.quote(pw)} -X MKCOL {shlex.quote(mkcol_base)}",
                        timeout=60,
                    )
                    code_mk = (mc.get("stdout") or "").strip()
                    try:
                        c = int(code_mk) if code_mk else None
                    except Exception:
                        c = None
                    if c in (201, 204):
                        logger.info("[Cloud-Upload] MKCOL %s -> %s", mkcol_base, code_mk)
                    elif c == 405:
                        pass  # existiert bereits
                    elif c not in (200, 201, 204, 405):
                        logger.warning("[Cloud-Upload] MKCOL %s -> HTTP %s (weiter mit PUT)", mkcol_base, c)
            logger.info("[Cloud-Upload] WebDAV PUT → %s (timeout=%ds)", remote, upload_timeout)
            ok, put_code, err = _curl_put_with_progress(
                local_file, remote, user, pw, job_id, upload_timeout
            )
            if not ok:
                logger.error("[Cloud-Upload] PUT fehlgeschlagen: %s", err)
                return False, err or "Upload fehlgeschlagen"
            if put_code is not None and put_code not in (200, 201, 204):
                hint = " (Datei existiert evtl. oder übergeordnetes Verzeichnis fehlt – MKCOL/Overwrite prüfen)" if put_code == 409 else ""
                logger.error("[Cloud-Upload] PUT HTTP %s (erwartet 200/201/204)%s", put_code, hint)
                return False, f"Upload fehlgeschlagen (HTTP {put_code or '—'}){hint}"
            if put_code is None:
                return True, remote  # Timeout, 1‑Min‑Prüfung war erfolgreich
            # verify via PROPFIND (optional; manche Server liefern 404 für PROPFIND auf Datei)
            cmd_v = (
                "curl -sS -o /dev/null -w '%{http_code}' "
                f"-u {shlex.quote(user)}:{shlex.quote(pw)} "
                "-X PROPFIND -H 'Depth: 0' "
                f"{shlex.quote(remote)}"
            )
            vr = run_command(cmd_v, timeout=120)
            code_str = (vr.get("stdout") or "").strip()
            try:
                code = int(code_str) if code_str else None
            except Exception:
                code = None
            if vr.get("success") and code in (200, 201, 204, 207):
                logger.info("[Cloud-Upload] Erfolgreich (PUT %s, PROPFIND %s): %s", put_code, code, remote)
                return True, remote
            # PROPFIND 404 ist bei einigen WebDAV-Servern normal; PUT war erfolgreich
            if put_code in (200, 201, 204):
                logger.info("[Cloud-Upload] PUT ok, PROPFIND %s (ignoriert): %s", code, remote)
                return True, remote
            logger.error("[Cloud-Upload] PROPFIND HTTP %s; PUT war %s", code, put_code)
            return False, f"Remote Verifizierung fehlgeschlagen (HTTP {code or '—'})"

        if run_async:
            job_id = _new_job_id()
            BACKUP_JOBS[job_id] = {
                "job_id": job_id,
                "status": "queued",
                "type": backup_type,
                "backup_dir": backup_dir,
                "backup_file": bf,
                "target": target,
                "started_at": _now_iso(),
                "finished_at": None,
                "message": "Wartet…",
                "results": [],
            }

            def _runner_thread():
                try:
                    cancel_ev = BACKUP_JOB_CANCEL.get(job_id)
                    if not cancel_ev:
                        cancel_ev = threading.Event()
                        BACKUP_JOB_CANCEL[job_id] = cancel_ev
                    BACKUP_JOBS[job_id]["status"] = "running"
                    BACKUP_JOBS[job_id]["message"] = "Backup läuft…"
                    result = _do_backup_logic(
                        sudo_password=sudo_password,
                        backup_type=backup_type,
                        backup_dir=backup_dir,
                        timestamp=timestamp,
                        last_backup_hint=last_hint,
                        cancel_event=cancel_ev,
                        job=BACKUP_JOBS[job_id],
                    )
                    BACKUP_JOBS[job_id]["results"] = result.get("results") or []
                    backup_file_path = result.get("backup_file") or bf
                    
                    # Optional: Verschlüsselung
                    encryption_method = data.get("encryption_method")
                    encryption_key = data.get("encryption_key")
                    if encryption_method and backup_file_path and result.get("status") == "success":
                        try:
                            backup_mod = _get_backup_module()
                            backup_mod.run_command = run_command
                            BACKUP_JOBS[job_id]["message"] = "Verschlüsselung läuft…"
                            enc_success, enc_file, enc_error = backup_mod.encrypt_backup(
                                backup_file_path,
                                encryption_key,
                                encryption_method,
                                sudo_password
                            )
                            if enc_success:
                                backup_file_path = enc_file
                                BACKUP_JOBS[job_id]["backup_file"] = enc_file
                                BACKUP_JOBS[job_id]["encrypted"] = True
                                BACKUP_JOBS[job_id]["results"].append(f"verschlüsselt: {enc_file}")
                                logger.info(f"Backup verschlüsselt: {enc_file}")
                            else:
                                BACKUP_JOBS[job_id]["results"].append(f"Verschlüsselung fehlgeschlagen: {enc_error}")
                                BACKUP_JOBS[job_id]["warning"] = f"Verschlüsselung fehlgeschlagen: {enc_error}"
                        except Exception as e:
                            BACKUP_JOBS[job_id]["results"].append(f"Verschlüsselung Fehler: {str(e)}")
                            BACKUP_JOBS[job_id]["warning"] = f"Verschlüsselung Fehler: {str(e)}"
                    else:
                        BACKUP_JOBS[job_id]["backup_file"] = backup_file_path
                    
                    # optional cloud upload nur wenn explizit gewünscht (cloud_only oder local_and_cloud)
                    # Bei target="local" (z.B. USB-Stick) NIEMALS in die Cloud hochladen
                    backup_settings_thread = _read_backup_settings()
                    cloud_thread = backup_settings_thread.get("cloud") or {}
                    cloud_should_upload = target in ("cloud_only", "local_and_cloud")
                    logger.info(f"Cloud-Upload-Prüfung: target={target}, cloud.enabled={cloud_thread.get('enabled')}, cloud_should_upload={cloud_should_upload}, backup_file={BACKUP_JOBS[job_id].get('backup_file')}")
                    if result.get("status") == "success" and cloud_should_upload:
                        # Verwende Cloud-Einstellungen aus Thread
                        cloud = cloud_thread
                        backup_file_to_upload = BACKUP_JOBS[job_id]["backup_file"]
                        logger.info(f"Cloud-Upload gestartet für {backup_file_to_upload}, Provider: {cloud.get('provider')}, Enabled: {cloud.get('enabled')}, Target: {target}")
                        
                        # Prüfe Cloud-Credentials VOR dem Upload
                        provider = cloud.get("provider") or "seafile_webdav"
                        webdav_providers = ("seafile_webdav", "webdav", "nextcloud_webdav")
                        credentials_ok = False
                        if provider in webdav_providers:
                            url_ok = bool((cloud.get("webdav_url") or "").strip())
                            user_ok = bool((cloud.get("username") or "").strip())
                            pw_ok = bool((cloud.get("password") or "").strip())
                            credentials_ok = url_ok and user_ok and pw_ok
                        else:
                            # Für andere Provider: Prüfe Provider-spezifische Settings
                            if provider in ("s3", "s3_compatible"):
                                credentials_ok = bool(cloud.get("bucket") and cloud.get("access_key_id") and cloud.get("secret_access_key"))
                            elif provider == "google_cloud":
                                credentials_ok = bool(cloud.get("bucket"))
                            elif provider == "azure":
                                credentials_ok = bool(cloud.get("account_name") and cloud.get("container") and cloud.get("account_key"))
                            else:
                                credentials_ok = False
                        
                        if not credentials_ok:
                            error_msg = f"Cloud-Credentials fehlen für Provider '{provider}'. Backup wurde nur lokal gespeichert."
                            BACKUP_JOBS[job_id]["results"].append(f"⚠️ Cloud-Upload übersprungen: {error_msg}")
                            BACKUP_JOBS[job_id]["warning"] = error_msg
                            logger.warning(f"[Cloud-Upload] {error_msg}")
                            # Bei cloud_only ist das ein Fehler, bei local_and_cloud nur eine Warnung
                            if target == "cloud_only":
                                BACKUP_JOBS[job_id]["status"] = "error"
                                BACKUP_JOBS[job_id]["message"] = "Cloud-Upload fehlgeschlagen: Credentials fehlen"
                            else:
                                # Backup lokal erfolgreich, Cloud-Upload fehlgeschlagen
                                BACKUP_JOBS[job_id]["status"] = "success"
                                BACKUP_JOBS[job_id]["message"] = "Backup lokal erfolgreich (Cloud-Upload übersprungen)"
                        # Prüfe ob Datei existiert
                        elif not Path(backup_file_to_upload).exists():
                            error_msg = f"Backup-Datei nicht gefunden: {backup_file_to_upload}"
                            BACKUP_JOBS[job_id]["results"].append(f"upload failed: {error_msg}")
                            BACKUP_JOBS[job_id]["warning"] = f"Cloud-Upload fehlgeschlagen: {error_msg}"
                            if target == "cloud_only":
                                BACKUP_JOBS[job_id]["status"] = "error"
                            else:
                                BACKUP_JOBS[job_id]["status"] = "success"
                                BACKUP_JOBS[job_id]["message"] = "Backup lokal erfolgreich (Cloud-Upload fehlgeschlagen)"
                            logger.error(error_msg)
                        else:
                            BACKUP_JOBS[job_id]["message"] = "Upload läuft…"
                            try:
                                ok, info = _cloud_upload_and_verify(backup_file_to_upload, cloud, job_id)
                                logger.info(f"Cloud-Upload Ergebnis: ok={ok}, info={info}")
                                if ok:
                                    BACKUP_JOBS[job_id].pop("upload_progress_pct", None)
                                    BACKUP_JOBS[job_id]["remote_file"] = info
                                    BACKUP_JOBS[job_id]["results"].append(f"✅ uploaded: {info}")
                                    BACKUP_JOBS[job_id]["location"] = "Cloud"
                                    BACKUP_JOBS[job_id]["message"] = "Backup erfolgreich hochgeladen"
                                    if target == "cloud_only":
                                        try:
                                            run_command(f"rm -f {shlex.quote(backup_file_to_upload)}", sudo=True, sudo_password=sudo_password)
                                            BACKUP_JOBS[job_id]["results"].append("Lokale Datei gelöscht (cloud_only)")
                                        except Exception as e:
                                            logger.warning(f"Lokale Datei konnte nicht gelöscht werden: {e}")
                                else:
                                    BACKUP_JOBS[job_id].pop("upload_progress_pct", None)
                                    BACKUP_JOBS[job_id]["results"].append(f"❌ upload failed: {info}")
                                    BACKUP_JOBS[job_id]["warning"] = f"Cloud-Upload fehlgeschlagen: {info}"
                                    if target == "cloud_only":
                                        BACKUP_JOBS[job_id]["status"] = "error"
                                        BACKUP_JOBS[job_id]["message"] = "Cloud-Upload fehlgeschlagen"
                                    else:
                                        BACKUP_JOBS[job_id]["status"] = "success"
                                        BACKUP_JOBS[job_id]["message"] = "Backup lokal erfolgreich (Cloud-Upload fehlgeschlagen)"
                                    logger.error(f"Cloud-Upload fehlgeschlagen: {info}")
                            except Exception as e:
                                error_msg = f"Cloud-Upload Fehler: {str(e)}"
                                logger.error(f"[Cloud-Upload] Unerwarteter Fehler: {e}", exc_info=True)
                                BACKUP_JOBS[job_id]["results"].append(f"❌ upload exception: {error_msg}")
                                BACKUP_JOBS[job_id]["warning"] = error_msg
                                if target == "cloud_only":
                                    BACKUP_JOBS[job_id]["status"] = "error"
                                    BACKUP_JOBS[job_id]["message"] = "Cloud-Upload fehlgeschlagen"
                                else:
                                    BACKUP_JOBS[job_id]["status"] = "success"
                                    BACKUP_JOBS[job_id]["message"] = "Backup lokal erfolgreich (Cloud-Upload fehlgeschlagen)"
                    BACKUP_JOBS[job_id]["finished_at"] = _now_iso()
                    # Status wird bereits oben gesetzt, nur noch finalisieren
                    if BACKUP_JOBS[job_id]["status"] not in ("error", "cancelled"):
                        if result.get("status") == "cancelled":
                            BACKUP_JOBS[job_id]["status"] = "cancelled"
                            BACKUP_JOBS[job_id]["message"] = "Abgebrochen"
                        elif result.get("status") == "success":
                            # Status bleibt success (auch wenn Upload fehlgeschlagen ist, außer bei cloud_only)
                            if BACKUP_JOBS[job_id]["status"] != "error":
                                BACKUP_JOBS[job_id]["status"] = "success"
                                BACKUP_JOBS[job_id]["message"] = "Fertig"
                            if result.get("warning"):
                                BACKUP_JOBS[job_id]["warning"] = result.get("warning")
                        else:
                            BACKUP_JOBS[job_id]["status"] = "error"
                            BACKUP_JOBS[job_id]["message"] = result.get("message") or "Fehler"
                except Exception as e:
                    BACKUP_JOBS[job_id]["status"] = "error"
                    BACKUP_JOBS[job_id]["message"] = str(e)
                    BACKUP_JOBS[job_id]["finished_at"] = _now_iso()
                finally:
                    # cleanup cancel event
                    try:
                        BACKUP_JOB_CANCEL.pop(job_id, None)
                    except Exception:
                        pass

            threading.Thread(target=_runner_thread, daemon=True).start()
            return {"status": "accepted", "job_id": job_id, "backup_file": bf, "message": "Backup gestartet"}

        # sync mode
        result = await asyncio.to_thread(
            _do_backup_logic,
            sudo_password=sudo_password,
            backup_type=backup_type,
            backup_dir=backup_dir,
            timestamp=timestamp,
            last_backup_hint=last_hint,
        )
        
        # Optional: Verschlüsselung
        encryption_method = data.get("encryption_method")
        encryption_key = data.get("encryption_key")
        backup_file_path = result.get("backup_file") or bf
        if encryption_method and backup_file_path and result.get("status") == "success":
            try:
                backup_mod = _get_backup_module()
                backup_mod.run_command = run_command
                enc_success, enc_file, enc_error = backup_mod.encrypt_backup(
                    backup_file_path,
                    encryption_key,
                    encryption_method,
                    sudo_password
                )
                if enc_success:
                    backup_file_path = enc_file
                    result["backup_file"] = enc_file
                    result["results"] = (result.get("results") or []) + [f"verschlüsselt: {enc_file}"]
                else:
                    result["warning"] = (result.get("warning") or "") + f" Verschlüsselung fehlgeschlagen: {enc_error}"
            except Exception as e:
                result["warning"] = (result.get("warning") or "") + f" Verschlüsselung Fehler: {str(e)}"
        
        # Cloud-Upload nur bei explizitem Cloud-Ziel; bei target="local" (z.B. USB) nie hochladen
        cloud_should_upload = target in ("cloud_only", "local_and_cloud")
        if result.get("status") == "success" and cloud_should_upload:
            ok, info = _cloud_upload_and_verify(result.get("backup_file") or bf)
            if ok:
                result["remote_file"] = info
                if target == "cloud_only":
                    try:
                        run_command(f"rm -f {shlex.quote(str(result.get('backup_file') or bf))}", sudo=True, sudo_password=sudo_password)
                    except Exception:
                        pass
            else:
                result["warning"] = f"Upload fehlgeschlagen: {info}"
        return result
    except Exception as e:
        logger.error(f"💥 Fehler bei Backup-Erstellung: {str(e)}", exc_info=True)
        return JSONResponse(status_code=200, content={"status": "error", "message": f"Fehler bei der Backup-Erstellung: {str(e)}"})

@app.get("/api/backup/list")
async def list_backups(backup_dir: str = "/mnt/backups"):
    """Liste aller Backups"""
    try:
        try:
            backup_dir = _validate_backup_dir(backup_dir)
        except Exception as ve:
            return JSONResponse(status_code=200, content={"status": "error", "message": f"Ungültiges Backup-Ziel: {str(ve)}", "backups": []})

        p = Path(backup_dir)
        # Wenn das Verzeichnis nicht existiert, einfach leer zurückgeben
        if not p.exists():
            return {"status": "success", "backups": []}

        backups = []
        # Robust: Python glob statt Shell-Glob (funktioniert auch mit Spaces)
        # Suche auch nach verschlüsselten Backups (.tar.gz.gpg, .tar.gz.enc)
        all_backup_files = list(p.glob("*.tar.gz")) + list(p.glob("*.tar.gz.gpg")) + list(p.glob("*.tar.gz.enc"))
        for f in sorted(all_backup_files):
            try:
                st = f.stat()
                size = st.st_size
                mtime = st.st_mtime

                def human(n: int) -> str:
                    for unit in ["B", "KB", "MB", "GB", "TB", "PB"]:
                        if n < 1024:
                            return f"{n:.0f} {unit}" if unit == "B" else f"{n:.1f} {unit}"
                        n /= 1024
                    return f"{n:.1f} PB"

                # einfache Datumsdarstellung (lokal)
                date_str = run_command(f"date -d @{int(mtime)} '+%Y-%m-%d %H:%M:%S'").get("stdout", "").strip()
                if not date_str:
                    date_str = ""

                backup_info = {
                    "file": str(f),
                    "size": human(size),
                    "date": date_str,
                    "encrypted": False,
                }
                # Prüfe auf Verschlüsselung (auch verschachtelte Endungen wie .tar.gz.gpg)
                filename = str(f)
                if filename.endswith('.gpg') or filename.endswith('.enc') or '.tar.gz.gpg' in filename or '.tar.gz.enc' in filename:
                    backup_info["encrypted"] = True
                # Prüfe auf Cloud-Backup (Dateiname enthält möglicherweise Hinweise)
                if 'cloud' in str(f).lower() or 'remote' in str(f).lower():
                    backup_info["location"] = "Cloud"
                else:
                    backup_info["location"] = "Lokal"
                backups.append(backup_info)
            except Exception:
                continue

        return {"status": "success", "backups": backups}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/backup/verify")
async def verify_backup(request: Request):
    """Verifiziert ein Backup-Archiv (prüft Integrität und zeigt Inhalt)"""
    try:
        data = await request.json()
    except Exception:
        data = {}
    
    backup_file = (data.get("backup_file") or "").strip()
    if not backup_file:
        return JSONResponse(status_code=200, content={"status": "error", "message": "backup_file erforderlich"})
    
    # Sicherheitsprüfung: Pfad-Validierung
    try:
        bf = Path(backup_file).resolve()
        allowed_roots = [Path("/mnt").resolve(), Path("/media").resolve(), Path("/run/media").resolve(), Path("/home").resolve()]
        if not any(str(bf).startswith(str(r) + "/") or bf == r for r in allowed_roots):
            return JSONResponse(status_code=200, content={"status": "error", "message": "Backup-Datei liegt außerhalb erlaubter Pfade"})
    except Exception as e:
        return JSONResponse(status_code=200, content={"status": "error", "message": f"Ungültiger Pfad: {str(e)}"})
    
    if not Path(backup_file).exists():
        return JSONResponse(status_code=200, content={"status": "error", "message": "Backup-Datei existiert nicht"})
    
    # Prüfe, ob verschlüsselt
    is_encrypted = backup_file.endswith('.gpg') or backup_file.endswith('.enc') or '.tar.gz.gpg' in backup_file or '.tar.gz.enc' in backup_file
    
    results = {
        "file": backup_file,
        "exists": True,
        "encrypted": is_encrypted,
        "valid": False,
        "size_bytes": 0,
        "size_human": "",
        "file_count": 0,
        "sample_files": [],
        "error": None
    }
    
    try:
        st = Path(backup_file).stat()
        results["size_bytes"] = st.st_size
        
        def human(n: int) -> str:
            for unit in ["B", "KB", "MB", "GB", "TB"]:
                if n < 1024:
                    return f"{n:.0f} {unit}" if unit == "B" else f"{n:.1f} {unit}"
                n /= 1024
            return f"{n:.1f} TB"
        results["size_human"] = human(st.st_size)
    except Exception as e:
        results["error"] = f"Fehler beim Lesen der Dateigröße: {str(e)}"
        return {"status": "success", "results": results}
    
    # Wenn verschlüsselt, können wir nur die Dateigröße prüfen
    if is_encrypted:
        results["valid"] = results["size_bytes"] > 0
        if results["valid"]:
            results["error"] = None  # Kein Fehler, nur Info
        else:
            results["error"] = "Verschlüsselte Backup-Datei ist leer oder nicht gefunden"
        return {"status": "success", "results": results}
    
    # Verifizierung: tar -tzf listet den Inhalt (prüft Integrität)
    cmd = f"tar -tzf {shlex.quote(backup_file)} 2>&1 | head -100"
    res = await run_command_async(cmd, timeout=60)
    
    if res.get("success") and res.get("stdout"):
        results["valid"] = True
        files = [line.strip() for line in res.get("stdout", "").split("\n") if line.strip()]
        results["file_count"] = len(files)
        results["sample_files"] = files[:20]  # Erste 20 Dateien als Beispiel
        
        # Zähle alle Dateien (kann bei großen Archiven langsam sein)
        if results["file_count"] < 100:
            # Kleines Archiv, zähle alle
            cmd_count = f"tar -tzf {shlex.quote(backup_file)} 2>/dev/null | wc -l"
            res_count = await run_command_async(cmd_count, timeout=30)
            if res_count.get("success"):
                try:
                    results["file_count"] = int(res_count.get("stdout", "0").strip())
                except Exception:
                    pass
    else:
        results["valid"] = False
        error_msg = res.get("stderr") or res.get("error") or "Unbekannter Fehler"
        results["error"] = f"Backup-Archiv ist beschädigt oder ungültig: {error_msg[:200]}"
    
    return {"status": "success", "results": results}


@app.post("/api/backup/delete")
async def delete_backup(request: Request):
    """Löscht ein Backup (.tar.gz, auch verschlüsselte .tar.gz.gpg/.tar.gz.enc) sicher (mit sudo fallback)."""
    try:
        data = await request.json()
    except Exception:
        data = {}

    backup_file = (data.get("backup_file") or "").strip()
    sudo_password = data.get("sudo_password", "") or sudo_password_store.get("password", "")

    # Erlaube auch verschlüsselte Backups (.tar.gz.gpg, .tar.gz.enc)
    if not backup_file or not (backup_file.endswith(".tar.gz") or backup_file.endswith(".tar.gz.gpg") or backup_file.endswith(".tar.gz.enc")):
        return JSONResponse(status_code=200, content={"status": "error", "message": "backup_file (.tar.gz, .tar.gz.gpg oder .tar.gz.enc) erforderlich"})

    # Allowlist path roots
    try:
        bf = Path(backup_file).resolve()
        allowed_roots = [Path("/mnt").resolve(), Path("/media").resolve(), Path("/run/media").resolve(), Path("/home").resolve()]
        if not any(str(bf).startswith(str(r) + "/") or bf == r for r in allowed_roots):
            return JSONResponse(status_code=200, content={"status": "error", "message": "Backup-Datei liegt außerhalb erlaubter Pfade"})
    except Exception:
        pass

    # Prüfe ob Datei existiert
    if not Path(backup_file).exists():
        return JSONResponse(status_code=200, content={"status": "error", "message": "Backup-Datei existiert nicht"})

    # Versuche zuerst ohne sudo zu löschen
    cmd = f"rm -f {shlex.quote(backup_file)}"
    res = await run_command_async(cmd, sudo=False, timeout=30)
    
    # Wenn fehlgeschlagen und sudo verfügbar, versuche mit sudo
    if not res.get("success"):
        if sudo_password:
            res = await run_command_async(cmd, sudo=True, sudo_password=sudo_password, timeout=30)
        else:
            # Versuche es nochmal mit sudo -n (falls NOPASSWD konfiguriert)
            res_sudo_n = await run_command_async(cmd, sudo=True, sudo_password="", timeout=30)
            if res_sudo_n.get("success"):
                res = res_sudo_n

    # verify gone
    test = await run_command_async(f"test -e {shlex.quote(backup_file)}", timeout=10)
    if test.get("success"):
        # Datei existiert noch - sammle Fehlerdetails
        error_parts = []
        if res.get("stderr"):
            stderr_text = (res.get("stderr") or "").strip()
            if stderr_text:
                error_parts.append(f"Fehler: {stderr_text[:300]}")
        if res.get("error"):
            error_text = (res.get("error") or "").strip()
            if error_text:
                error_parts.append(f"Details: {error_text[:300]}")
        
        # Prüfe Dateiberechtigungen
        perm_check = await run_command_async(f"ls -la {shlex.quote(backup_file)} 2>&1", timeout=10)
        if perm_check.get("success") and perm_check.get("stdout"):
            error_parts.append(f"Berechtigungen: {perm_check.get('stdout')[:200]}")
        
        error_message = "Backup konnte nicht gelöscht werden."
        if error_parts:
            error_message += " " + " ".join(error_parts)
        else:
            error_message += " Möglicherweise fehlen Berechtigungen oder die Datei ist gesperrt."
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "error",
                "message": error_message,
                "stderr": (res.get("stderr") or res.get("error") or "").strip()[:500],
            },
        )
    
    # Erfolgreich gelöscht
    return {"status": "success", "message": "Backup gelöscht"}

    return {"status": "success", "message": "Backup gelöscht"}

@app.post("/api/backup/restore")
async def restore_backup(request: Request):
    """Backup wiederherstellen"""
    try:
        try:
            data = await request.json()
        except:
            data = {}
        
        sudo_password = data.get("sudo_password", "") or sudo_password_store.get("password", "")
        backup_file = data.get("backup_file", "")
        
        if not backup_file:
            return JSONResponse(
                status_code=200,
                content={
                    "status": "error",
                    "message": "Backup-Datei erforderlich"
                }
            )
        
        if not sudo_password:
            sudo_test = run_command("sudo -n true", sudo=False)
            if not sudo_test["success"]:
                return JSONResponse(
                    status_code=200,
                    content={
                        "status": "error",
                        "message": "Sudo-Passwort erforderlich",
                        "requires_sudo_password": True
                    }
                )
        
        # Warnung: Restore ist gefährlich!
        # Extrahiere Backup
        restore_cmd = f"tar -xzf {backup_file} -C /"
        restore_result = await run_command_async(restore_cmd, sudo=True, sudo_password=sudo_password, timeout=7200)
        
        if restore_result["success"]:
            return {
                "status": "success",
                "message": f"Backup {backup_file} wiederhergestellt",
                "warning": "System-Neustart empfohlen"
            }
        else:
            return JSONResponse(
                status_code=200,
                content={
                    "status": "error",
                    "message": f"Restore fehlgeschlagen: {restore_result.get('stderr', 'Unbekannter Fehler')}"
                }
            )
    except Exception as e:
        logger.error(f"💥 Fehler bei Backup-Restore: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=200,
            content={
                "status": "error",
                "message": f"Fehler beim Restore: {str(e)}"
            }
        )


@app.post("/api/backup/verify")
async def verify_backup(request: Request):
    """Backup verifizieren (tar-Test, optional sha256)."""
    try:
        data = await request.json()
        backup_file = (data.get("backup_file") or "").strip()
        mode = (data.get("mode") or "tar").strip()  # tar | sha256 | gzip
        sudo_password = data.get("sudo_password", "") or sudo_password_store.get("password", "")

        if not backup_file:
            return JSONResponse(status_code=200, content={"status": "error", "message": "backup_file erforderlich"})

        # Allowlist: nur unter erlaubten roots
        try:
            bf = Path(backup_file).resolve()
            allowed_roots = [Path("/mnt").resolve(), Path("/media").resolve(), Path("/run/media").resolve(), Path("/home").resolve()]
            if not any(str(bf).startswith(str(r) + "/") or bf == r for r in allowed_roots):
                return JSONResponse(status_code=200, content={"status": "error", "message": "Backup-Datei liegt außerhalb erlaubter Pfade"})
        except Exception:
            pass

        # Existence check (mit sudo fallback)
        test_cmd = f"test -s {shlex.quote(backup_file)}"
        t = run_command(test_cmd)
        if not t["success"] and sudo_password:
            t = run_command(test_cmd, sudo=True, sudo_password=sudo_password)
        if not t["success"]:
            return JSONResponse(status_code=200, content={"status": "error", "message": "Backup-Datei nicht gefunden oder leer"})

        import time
        start = time.time()

        if mode == "sha256":
            cmd = f"sha256sum {shlex.quote(backup_file)}"
            res = await run_command_async(cmd, timeout=600)
            if not res["success"] and sudo_password:
                res = await run_command_async(cmd, sudo=True, sudo_password=sudo_password, timeout=600)
            ok = bool(res["success"])
            sha = (res.get("stdout") or "").strip().split()[0] if ok and (res.get("stdout") or "").strip() else None
            return {
                "status": "success" if ok else "error",
                "mode": "sha256",
                "ok": ok,
                "sha256": sha,
                "stderr": (res.get("stderr") or "").strip()[:200],
                "duration_ms": int((time.time() - start) * 1000),
            }

        if mode == "gzip":
            # gzip stream integrity test (no output on success)
            cmd = f"gzip -t {shlex.quote(backup_file)}"
            res = await run_command_async(cmd, timeout=600)
            if not res["success"] and sudo_password:
                res = await run_command_async(cmd, sudo=True, sudo_password=sudo_password, timeout=600)
            ok = bool(res["success"])
            msg = (res.get("stderr") or res.get("stdout") or res.get("error") or "").strip()
            if not msg and not ok:
                msg = f"gzip test failed (rc={res.get('returncode')})"
            return {
                "status": "success" if ok else "error",
                "mode": "gzip",
                "ok": ok,
                "message": msg[:400] if msg else None,
                "duration_ms": int((time.time() - start) * 1000),
            }

        # Default: tar.gz structural test via python (avoids huge stdout lists)
        try:
            import tarfile
            with tarfile.open(backup_file, mode="r:gz") as tf:
                # iterate headers; raises on corruption/truncation
                for _ in tf:
                    pass
            ok = True
            msg = None
        except Exception as te:
            ok = False
            msg = str(te) or "tar verify failed"

        return {
            "status": "success" if ok else "error",
            "mode": "tar",
            "ok": ok,
            "message": msg[:400] if msg else None,
            "duration_ms": int((time.time() - start) * 1000),
        }
    except Exception as e:
        return JSONResponse(status_code=200, content={"status": "error", "message": str(e)})


# ==================== Raspberry Pi Konfiguration ====================

pi_config_module = None
backup_module = None

def _get_pi_config_module():
    global pi_config_module
    if pi_config_module is None:
        from modules.raspberry_pi_config import RaspberryPiConfigModule
        pi_config_module = RaspberryPiConfigModule()
    return pi_config_module

def _get_backup_module():
    global backup_module
    if backup_module is None:
        from modules.backup import BackupModule
        backup_module = BackupModule()
    return backup_module


@app.get("/api/raspberry-pi/config")
async def get_raspberry_pi_config():
    """Liest die aktuelle Raspberry Pi Konfiguration"""
    try:
        module = _get_pi_config_module()
        # Versuche mit gespeichertem sudo_password
        sudo_password = sudo_password_store.get("password", "")
        result = module.read_config(sudo_password=sudo_password)
        # Wenn Fehler und requires_sudo_password, dann Flag setzen
        if result.get("status") == "error":
            error_msg = result.get("message", "").lower()
            if ("berechtigung" in error_msg or "sudo" in error_msg or "permission" in error_msg or "keine berechtigung" in error_msg):
                result["requires_sudo_password"] = True
            # Stelle sicher, dass das Flag gesetzt ist, wenn es fehlt
            if "requires_sudo_password" not in result:
                result["requires_sudo_password"] = True
        return result
    except Exception as e:
        logger.error(f"Fehler beim Lesen der Raspberry Pi Konfiguration: {str(e)}", exc_info=True)
        return JSONResponse(status_code=200, content={"status": "error", "message": str(e), "requires_sudo_password": True})


@app.post("/api/raspberry-pi/config")
async def set_raspberry_pi_config(request: Request):
    """Speichert die Raspberry Pi Konfiguration"""
    try:
        data = await request.json()
        config = data.get("config", {})
        sudo_password = data.get("sudo_password", "") or sudo_password_store.get("password", "")
        
        if not sudo_password:
            sudo_test = run_command("sudo -n true", sudo=False)
            if not sudo_test.get("success"):
                return JSONResponse(status_code=200, content={"status": "error", "message": "Sudo-Passwort erforderlich", "requires_sudo_password": True})
        
        module = _get_pi_config_module()
        result = module.write_config(config, sudo_password)
        
        if result.get("status") == "success":
            result["message"] = "Konfiguration gespeichert. Neustart erforderlich, damit Änderungen wirksam werden."
        
        return result
    except Exception as e:
        logger.error(f"Fehler beim Schreiben der Raspberry Pi Konfiguration: {str(e)}", exc_info=True)
        return JSONResponse(status_code=200, content={"status": "error", "message": str(e)})


@app.get("/api/raspberry-pi/system-info")
async def get_raspberry_pi_system_info():
    """CPU-, Grafik- und Systeminfos (vcgencmd, /proc/cpuinfo)"""
    try:
        module = _get_pi_config_module()
        return module.get_system_info()
    except Exception as e:
        logger.error(f"Fehler beim Abrufen der Systeminfos: {str(e)}", exc_info=True)
        return JSONResponse(status_code=200, content={"status": "error", "message": str(e)})


@app.get("/api/raspberry-pi/config/options")
async def get_raspberry_pi_config_options():
    """Gibt alle verfügbaren Konfigurationsoptionen zurück, gefiltert nach Pi-Modell"""
    try:
        module = _get_pi_config_module()
        return module.get_all_config_options(filter_by_model=True)
    except Exception as e:
        logger.error(f"Fehler beim Abrufen der Konfigurationsoptionen: {str(e)}", exc_info=True)
        return JSONResponse(status_code=200, content={"status": "error", "message": str(e)})


@app.get("/api/raspberry-pi/config/option/{key}")
async def get_raspberry_pi_config_option_info(key: str):
    """Gibt Informationen zu einer spezifischen Konfigurationsoption zurück"""
    try:
        module = _get_pi_config_module()
        return module.get_config_option_info(key)
    except Exception as e:
        logger.error(f"Fehler beim Abrufen der Option-Info: {str(e)}", exc_info=True)
        return JSONResponse(status_code=200, content={"status": "error", "message": str(e)})


@app.post("/api/raspberry-pi/config/validate")
async def validate_raspberry_pi_config_value(request: Request):
    """Validiert einen Konfigurationswert"""
    try:
        data = await request.json()
        key = data.get("key", "")
        value = data.get("value")
        
        if not key:
            return JSONResponse(status_code=200, content={"status": "error", "message": "key erforderlich"})
        
        module = _get_pi_config_module()
        return module.validate_config_value(key, value)
    except Exception as e:
        logger.error(f"Fehler bei der Validierung: {str(e)}", exc_info=True)
        return JSONResponse(status_code=200, content={"status": "error", "message": str(e)})


# -------------------- Control Center --------------------

def _get_control_center_module():
    """Singleton für Control Center Modul"""
    global control_center_module
    if control_center_module is None:
        from modules.control_center import ControlCenterModule
        control_center_module = ControlCenterModule()
    return control_center_module

control_center_module = None


@app.get("/api/control-center/wifi/networks")
async def get_wifi_networks():
    """Listet verfügbare WiFi-Netzwerke auf (verwendet sudo_password_store)."""
    try:
        sudo_password = sudo_password_store.get("password", "")
        module = _get_control_center_module()
        return module.get_wifi_networks(sudo_password)
    except Exception as e:
        logger.error(f"Fehler beim Abrufen der WiFi-Netzwerke: {str(e)}", exc_info=True)
        return JSONResponse(status_code=200, content={"status": "error", "message": str(e)})


@app.post("/api/control-center/wifi/scan")
async def wifi_scan_post(request: Request):
    """WiFi-Scan mit explizitem sudo-Passwort (um Session/Worker-Probleme zu umgehen)."""
    try:
        data = {}
        if "application/json" in (request.headers.get("content-type") or ""):
            try:
                data = await request.json() or {}
            except Exception:
                pass
        sudo_password = (data.get("sudo_password") or "").strip()
        if not sudo_password:
            sudo_password = sudo_password_store.get("password", "")
        if not sudo_password:
            return JSONResponse(
                status_code=200,
                content={"status": "error", "message": "Sudo-Passwort erforderlich", "requires_sudo_password": True},
            )
        if sudo_password and not sudo_password_store.get("password"):
            sudo_password_store["password"] = sudo_password
        module = _get_control_center_module()
        return module.get_wifi_networks(sudo_password)
    except Exception as e:
        logger.error(f"Fehler beim WiFi-Scan: {str(e)}", exc_info=True)
        return JSONResponse(status_code=200, content={"status": "error", "message": str(e)})


@app.get("/api/control-center/wifi/config")
async def get_wifi_config():
    """Liest aktuelle WiFi-Konfiguration"""
    try:
        sudo_password = sudo_password_store.get("password", "")
        module = _get_control_center_module()
        return module.get_wifi_config(sudo_password)
    except Exception as e:
        logger.error(f"Fehler beim Lesen der WiFi-Konfiguration: {str(e)}", exc_info=True)
        return JSONResponse(status_code=200, content={"status": "error", "message": str(e)})


@app.get("/api/control-center/wifi/status")
async def get_wifi_status():
    """Aktuell verbundenes WLAN, Interface, Signal, WLAN aktiviert (rfkill)."""
    try:
        sudo_password = sudo_password_store.get("password", "")
        module = _get_control_center_module()
        return module.get_wifi_status(sudo_password)
    except Exception as e:
        logger.error(f"Fehler beim WiFi-Status: {str(e)}", exc_info=True)
        return JSONResponse(status_code=200, content={"status": "error", "message": str(e)})


@app.post("/api/control-center/wifi/disconnect")
async def wifi_disconnect(request: Request):
    """WLAN-Verbindung trennen."""
    try:
        data = await request.json() if request.headers.get("content-type", "").startswith("application/json") else {}
        sudo_password = data.get("sudo_password", "") or sudo_password_store.get("password", "")
        module = _get_control_center_module()
        return module.wifi_disconnect(sudo_password)
    except Exception as e:
        logger.error(f"Fehler beim WLAN-Trennen: {str(e)}", exc_info=True)
        return JSONResponse(status_code=200, content={"status": "error", "message": str(e)})


@app.post("/api/control-center/wifi/enabled")
async def wifi_set_enabled(request: Request):
    """WLAN aktivieren/deaktivieren (rfkill)."""
    try:
        data = await request.json()
        enabled = data.get("enabled", True)
        sudo_password = data.get("sudo_password", "") or sudo_password_store.get("password", "")
        module = _get_control_center_module()
        return module.wifi_set_enabled(bool(enabled), sudo_password)
    except Exception as e:
        logger.error(f"Fehler beim WLAN aktivieren/deaktivieren: {str(e)}", exc_info=True)
        return JSONResponse(status_code=200, content={"status": "error", "message": str(e)})


@app.post("/api/control-center/wifi/add")
async def add_wifi_network(request: Request):
    """Fügt ein WiFi-Netzwerk hinzu"""
    try:
        data = await request.json()
        ssid = data.get("ssid", "")
        password = data.get("password", "")
        security = data.get("security", "WPA2")
        
        if not ssid:
            return JSONResponse(status_code=200, content={"status": "error", "message": "SSID erforderlich"})
        
        sudo_password = data.get("sudo_password", "") or sudo_password_store.get("password", "")
        module = _get_control_center_module()
        return module.add_wifi_network(ssid, password, security, sudo_password)
    except Exception as e:
        logger.error(f"Fehler beim Hinzufügen des WiFi-Netzwerks: {str(e)}", exc_info=True)
        return JSONResponse(status_code=200, content={"status": "error", "message": str(e)})


@app.post("/api/control-center/wifi/connect")
async def wifi_connect(request: Request):
    """Verbindung zu einem konfigurierten WLAN-Netzwerk herstellen"""
    try:
        data = await request.json() if request.headers.get("content-type", "").startswith("application/json") else {}
        ssid = (data.get("ssid") or "").strip()
        if not ssid:
            return JSONResponse(status_code=200, content={"status": "error", "message": "SSID erforderlich"})
        sudo_password = data.get("sudo_password", "") or sudo_password_store.get("password", "")
        module = _get_control_center_module()
        return module.wifi_connect(ssid, sudo_password)
    except Exception as e:
        logger.error(f"Fehler beim WLAN-Verbinden: {str(e)}", exc_info=True)
        return JSONResponse(status_code=200, content={"status": "error", "message": str(e)})


@app.get("/api/control-center/ssh/status")
async def get_ssh_status():
    """Prüft SSH-Status"""
    try:
        module = _get_control_center_module()
        return module.get_ssh_status()
    except Exception as e:
        logger.error(f"Fehler beim Abrufen des SSH-Status: {str(e)}", exc_info=True)
        return JSONResponse(status_code=200, content={"status": "error", "message": str(e)})


@app.post("/api/control-center/ssh/set")
async def set_ssh_enabled(request: Request):
    """Aktiviert/deaktiviert SSH"""
    try:
        data = await request.json()
        enabled = data.get("enabled", False)
        
        sudo_password = data.get("sudo_password", "") or sudo_password_store.get("password", "")
        module = _get_control_center_module()
        return module.set_ssh_enabled(enabled, sudo_password)
    except Exception as e:
        logger.error(f"Fehler beim Setzen des SSH-Status: {str(e)}", exc_info=True)
        return JSONResponse(status_code=200, content={"status": "error", "message": str(e)})


@app.post("/api/control-center/ssh/start")
async def start_ssh(request: Request):
    """SSH-Dienst starten"""
    try:
        data = await request.json() if request.headers.get("content-type", "").startswith("application/json") else {}
        sudo_password = data.get("sudo_password", "") or sudo_password_store.get("password", "")
        module = _get_control_center_module()
        return module.start_ssh_service(sudo_password)
    except Exception as e:
        logger.error(f"Fehler beim SSH-Start: {str(e)}", exc_info=True)
        return JSONResponse(status_code=200, content={"status": "error", "message": str(e)})


@app.get("/api/control-center/vnc/status")
async def get_vnc_status():
    """Prüft VNC-Status"""
    try:
        module = _get_control_center_module()
        return module.get_vnc_status()
    except Exception as e:
        logger.error(f"Fehler beim Abrufen des VNC-Status: {str(e)}", exc_info=True)
        return JSONResponse(status_code=200, content={"status": "error", "message": str(e)})


@app.post("/api/control-center/vnc/set")
async def set_vnc_enabled(request: Request):
    """Aktiviert/deaktiviert VNC"""
    try:
        data = await request.json()
        enabled = data.get("enabled", False)
        password = data.get("password", "")
        
        sudo_password = data.get("sudo_password", "") or sudo_password_store.get("password", "")
        module = _get_control_center_module()
        return module.set_vnc_enabled(enabled, password, sudo_password)
    except Exception as e:
        logger.error(f"Fehler beim Setzen des VNC-Status: {str(e)}", exc_info=True)
        return JSONResponse(status_code=200, content={"status": "error", "message": str(e)})


@app.post("/api/control-center/vnc/start")
async def start_vnc(request: Request):
    """VNC-Dienst starten"""
    try:
        data = await request.json() if request.headers.get("content-type", "").startswith("application/json") else {}
        sudo_password = data.get("sudo_password", "") or sudo_password_store.get("password", "")
        module = _get_control_center_module()
        return module.start_vnc_service(sudo_password)
    except Exception as e:
        logger.error(f"Fehler beim VNC-Start: {str(e)}", exc_info=True)
        return JSONResponse(status_code=200, content={"status": "error", "message": str(e)})


@app.get("/api/control-center/keyboard")
async def get_keyboard_layout():
    """Liest Tastatur-Layout"""
    try:
        module = _get_control_center_module()
        return module.get_keyboard_layout()
    except Exception as e:
        logger.error(f"Fehler beim Lesen des Tastatur-Layouts: {str(e)}", exc_info=True)
        return JSONResponse(status_code=200, content={"status": "error", "message": str(e)})


@app.post("/api/control-center/keyboard/set")
async def set_keyboard_layout(request: Request):
    """Setzt Tastatur-Layout"""
    try:
        data = await request.json()
        layout = data.get("layout", "de")
        variant = data.get("variant", "")
        options = data.get("options", "")
        
        sudo_password = data.get("sudo_password", "") or sudo_password_store.get("password", "")
        module = _get_control_center_module()
        return module.set_keyboard_layout(layout, variant, options, sudo_password)
    except Exception as e:
        logger.error(f"Fehler beim Setzen des Tastatur-Layouts: {str(e)}", exc_info=True)
        return JSONResponse(status_code=200, content={"status": "error", "message": str(e)})


@app.get("/api/control-center/locale")
async def get_locale():
    """Liest Locale-Einstellungen"""
    try:
        module = _get_control_center_module()
        return module.get_locale()
    except Exception as e:
        logger.error(f"Fehler beim Lesen der Locale: {str(e)}", exc_info=True)
        return JSONResponse(status_code=200, content={"status": "error", "message": str(e)})


@app.post("/api/control-center/locale/set")
async def set_locale(request: Request):
    """Setzt Locale und Timezone"""
    try:
        data = await request.json()
        locale = data.get("locale", "de_DE.UTF-8")
        timezone = data.get("timezone", "")
        
        sudo_password = data.get("sudo_password", "") or sudo_password_store.get("password", "")
        module = _get_control_center_module()
        return module.set_locale(locale, timezone, sudo_password)
    except Exception as e:
        logger.error(f"Fehler beim Setzen der Locale: {str(e)}", exc_info=True)
        return JSONResponse(status_code=200, content={"status": "error", "message": str(e)})


@app.get("/api/control-center/desktop")
async def get_desktop_settings():
    """Liest Desktop-Einstellungen"""
    try:
        module = _get_control_center_module()
        return module.get_desktop_settings()
    except Exception as e:
        logger.error(f"Fehler beim Lesen der Desktop-Einstellungen: {str(e)}", exc_info=True)
        return JSONResponse(status_code=200, content={"status": "error", "message": str(e)})


@app.get("/api/control-center/desktop/boot-target")
async def get_desktop_boot_target():
    """Liest das Boot-Ziel (Desktop vs. Kommandozeile)."""
    try:
        module = _get_control_center_module()
        return module.get_boot_target()
    except Exception as e:
        logger.error(f"Fehler beim Lesen des Boot-Ziels: {str(e)}", exc_info=True)
        return JSONResponse(status_code=200, content={"status": "error", "message": str(e)})


@app.post("/api/control-center/desktop/boot-target")
async def set_desktop_boot_target(request: Request):
    """Setzt das Boot-Ziel: graphical (Desktop) oder multi-user (Kommandozeile)."""
    try:
        try:
            data = await request.json()
        except Exception:
            data = {}
        data = data or {}
        target = data.get("target", "").strip()
        sudo_password = data.get("sudo_password", "") or sudo_password_store.get("password", "")
        if not sudo_password:
            return JSONResponse(
                status_code=200,
                content={"status": "error", "message": "Sudo-Passwort erforderlich", "requires_sudo_password": True},
            )
        module = _get_control_center_module()
        return module.set_boot_target(target, sudo_password)
    except Exception as e:
        logger.error(f"Fehler beim Setzen des Boot-Ziels: {str(e)}", exc_info=True)
        return JSONResponse(status_code=200, content={"status": "error", "message": str(e)})


@app.get("/api/control-center/display")
async def get_display_settings():
    """Liest Display-Einstellungen (xrandr: Outputs, Modi, Rotation)."""
    try:
        module = _get_control_center_module()
        return module.get_display_settings()
    except Exception as e:
        logger.error(f"Fehler beim Lesen der Display-Einstellungen: {str(e)}", exc_info=True)
        return JSONResponse(status_code=200, content={"status": "error", "message": str(e)})


@app.post("/api/control-center/display")
async def set_display_settings(request: Request):
    """Setzt Display (xrandr: Output, Modus, Wiederholrate, Rotation). Kein sudo."""
    try:
        try:
            data = await request.json()
        except Exception:
            data = {}
        data = data or {}
        output = (data.get("output") or "").strip()
        mode = (data.get("mode") or "").strip()
        rate = data.get("rate")
        if rate is not None:
            try:
                rate = float(rate)
            except (TypeError, ValueError):
                rate = None
        rotation = (data.get("rotation") or "").strip() or "normal"
        module = _get_control_center_module()
        return module.set_display_settings(
            output=output or "HDMI-1",
            mode=mode or "1920x1080",
            rate=rate,
            rotation=rotation,
            sudo_password="",
        )
    except Exception as e:
        logger.error(f"Fehler beim Setzen der Display-Einstellungen: {str(e)}", exc_info=True)
        return JSONResponse(status_code=200, content={"status": "error", "message": str(e)})


@app.get("/api/control-center/printers")
async def get_printers():
    """Listet Drucker auf"""
    try:
        sudo_password = sudo_password_store.get("password", "")
        module = _get_control_center_module()
        return module.get_printers(sudo_password)
    except Exception as e:
        logger.error(f"Fehler beim Abrufen der Drucker: {str(e)}", exc_info=True)
        return JSONResponse(status_code=200, content={"status": "error", "message": str(e)})


@app.get("/api/control-center/scanners")
async def get_scanners():
    """Listet SANE-Scanner auf"""
    try:
        sudo_password = sudo_password_store.get("password", "")
        module = _get_control_center_module()
        return module.get_scanners(sudo_password)
    except Exception as e:
        logger.error(f"Fehler beim Abrufen der Scanner: {str(e)}", exc_info=True)
        return JSONResponse(status_code=200, content={"status": "error", "message": str(e)})


@app.get("/api/control-center/performance")
async def get_performance():
    """Performance: CPU-Governor, GPU/Overclocking (config.txt), Swap."""
    try:
        sudo_password = sudo_password_store.get("password", "")
        module = _get_control_center_module()
        return module.get_performance(sudo_password)
    except Exception as e:
        logger.error(f"Fehler beim Abrufen der Performance-Daten: {str(e)}", exc_info=True)
        return JSONResponse(status_code=200, content={"status": "error", "message": str(e)})


@app.post("/api/control-center/performance")
async def set_performance(request: Request):
    """Performance setzen: Governor, GPU-Mem, Overclocking, Swap-Größe."""
    try:
        try:
            data = await request.json() if request.headers.get("content-type", "").startswith("application/json") else {}
        except Exception:
            data = {}
        data = data or {}
        sudo_password = data.get("sudo_password", "") or sudo_password_store.get("password", "")
        if not sudo_password:
            sudo_ok = run_command("sudo -n true", sudo=False)
            if not sudo_ok.get("success"):
                return JSONResponse(status_code=200, content={"status": "error", "message": "Sudo-Passwort erforderlich", "requires_sudo_password": True})
        module = _get_control_center_module()
        swap_mb = data.get("swap_size_mb")
        if swap_mb is not None:
            try:
                swap_mb = int(swap_mb)
            except (TypeError, ValueError):
                swap_mb = None
        result = module.set_performance(
            sudo_password=sudo_password,
            governor=data.get("governor"),
            gpu_mem=data.get("gpu_mem"),
            arm_freq=data.get("arm_freq"),
            over_voltage=data.get("over_voltage"),
            force_turbo=data.get("force_turbo"),
            swap_size_mb=swap_mb,
        )
        return result
    except Exception as e:
        logger.error(f"Fehler beim Setzen der Performance: {str(e)}", exc_info=True)
        return JSONResponse(status_code=200, content={"status": "error", "message": str(e)})


@app.post("/api/system/reboot")
async def reboot_system(request: Request):
    """Startet das System neu"""
    try:
        try:
            data = await request.json()
        except:
            data = {}
        sudo_password = data.get("sudo_password", "") or sudo_password_store.get("password", "")
        if not sudo_password:
            return JSONResponse(status_code=200, content={"status": "error", "message": "Sudo-Passwort erforderlich", "requires_sudo_password": True})
        
        result = run_command("sudo -S reboot", sudo=True, sudo_password=sudo_password, timeout=5)
        if result.get("success"):
            return {"status": "success", "message": "Neustart gestartet"}
        else:
            return JSONResponse(status_code=200, content={"status": "error", "message": result.get("stderr") or "Neustart fehlgeschlagen"})
    except Exception as e:
        logger.error(f"Fehler beim Neustart: {str(e)}", exc_info=True)
        return JSONResponse(status_code=200, content={"status": "error", "message": str(e)})


@app.post("/api/raspberry-pi/config/reset")
async def reset_raspberry_pi_config(request: Request):
    """Setzt die Raspberry Pi Konfiguration auf Werkseinstellungen zurück"""
    try:
        try:
            data = await request.json()
        except:
            data = {}
        sudo_password = data.get("sudo_password", "") or sudo_password_store.get("password", "")
        if not sudo_password:
            return JSONResponse(status_code=200, content={"status": "error", "message": "Sudo-Passwort erforderlich", "requires_sudo_password": True})
        
        module = _get_pi_config_module()
        config_file = module.get_config_file()
        
        # Erstelle Backup
        backup_file = Path(str(config_file) + ".backup." + run_command("date +%Y%m%d_%H%M%S").get("stdout", "").strip())
        if config_file.exists():
            result = run_command(f"sudo -S cp {shlex.quote(str(config_file))} {shlex.quote(str(backup_file))}", sudo=True, sudo_password=sudo_password, timeout=5)
            if not result.get("success"):
                return JSONResponse(status_code=200, content={"status": "error", "message": "Backup konnte nicht erstellt werden"})
        
        # Erstelle Standard-Konfiguration
        default_config = "# Raspberry Pi Konfiguration - Werkseinstellungen\n# Generiert von PI-Installer\n\n"
        
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as tmp:
            tmp.write(default_config)
            tmp_path = tmp.name
        
        result = run_command(f"sudo -S mv {shlex.quote(tmp_path)} {shlex.quote(str(config_file))}", sudo=True, sudo_password=sudo_password, timeout=5)
        if result.get("success"):
            return {"status": "success", "message": "Konfiguration zurückgesetzt", "backup": str(backup_file)}
        else:
            return JSONResponse(status_code=200, content={"status": "error", "message": result.get("stderr") or "Zurücksetzen fehlgeschlagen"})
    except Exception as e:
        logger.error(f"Fehler beim Zurücksetzen: {str(e)}", exc_info=True)
        return JSONResponse(status_code=200, content={"status": "error", "message": str(e)})


@app.post("/api/system/packagekit/stop")
async def stop_packagekit(request: Request):
    """Stoppt PackageKit manuell, um apt-get-Konflikte zu vermeiden."""
    try:
        data = await request.json() if request.headers.get("content-type", "").startswith("application/json") else {}
        sudo_password = data.get("sudo_password", "") or sudo_password_store.get("password", "")
        _ensure_packagekit_stopped(sudo_password)
        return {"status": "success", "message": "PackageKit gestoppt (falls aktiv)"}
    except Exception as e:
        logger.error(f"Fehler beim Stoppen von PackageKit: {str(e)}", exc_info=True)
        return JSONResponse(status_code=200, content={"status": "error", "message": str(e)})


@app.get("/api/control-center/bluetooth/status")
async def get_bluetooth_status():
    """Bluetooth-Status: aktiviert/deaktiviert, verbundene Geräte."""
    try:
        sudo_password = sudo_password_store.get("password", "")
        module = _get_control_center_module()
        return module.get_bluetooth_status(sudo_password)
    except Exception as e:
        logger.error(f"Fehler beim Bluetooth-Status: {str(e)}", exc_info=True)
        return JSONResponse(status_code=200, content={"status": "error", "message": str(e)})


@app.post("/api/control-center/bluetooth/scan")
async def bluetooth_scan(request: Request):
    """Bluetooth-Geräte scannen."""
    try:
        data = await request.json() if request.headers.get("content-type", "").startswith("application/json") else {}
        sudo_password = data.get("sudo_password", "") or sudo_password_store.get("password", "")
        module = _get_control_center_module()
        return module.bluetooth_scan(sudo_password)
    except Exception as e:
        logger.error(f"Fehler beim Bluetooth-Scan: {str(e)}", exc_info=True)
        return JSONResponse(status_code=200, content={"status": "error", "message": str(e)})


@app.post("/api/control-center/bluetooth/enabled")
async def bluetooth_set_enabled(request: Request):
    """Bluetooth aktivieren/deaktivieren."""
    try:
        data = await request.json()
        enabled = data.get("enabled", True)
        sudo_password = data.get("sudo_password", "") or sudo_password_store.get("password", "")
        module = _get_control_center_module()
        return module.bluetooth_set_enabled(bool(enabled), sudo_password)
    except Exception as e:
        logger.error(f"Fehler beim Bluetooth aktivieren/deaktivieren: {str(e)}", exc_info=True)
        return JSONResponse(status_code=200, content={"status": "error", "message": str(e)})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
