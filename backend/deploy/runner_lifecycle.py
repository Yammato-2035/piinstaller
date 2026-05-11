from __future__ import annotations

import json
import os
import re
import secrets
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Literal

_BACKEND_ROOT = Path(__file__).resolve().parent.parent
_DEPLOY_CACHE = _BACKEND_ROOT / "cache" / "deploy"
_LOCK_DIR = _DEPLOY_CACHE / "runner-locks"
_AUDIT_DIR = _DEPLOY_CACHE / "runner-audit"

STATE_CREATED = "created"
STATE_VALIDATED = "validated"
STATE_LOCKED = "locked"
STATE_READY = "ready"
STATE_WRITING = "writing"
STATE_VERIFYING = "verifying"
STATE_COMPLETED = "completed"
STATE_ABORTED = "aborted"
STATE_FAILED = "failed"
STATE_EXPIRED = "expired"

TERMINAL_STATES = frozenset(
    {
        STATE_COMPLETED,
        STATE_ABORTED,
        STATE_FAILED,
        STATE_EXPIRED,
    }
)

ALL_STATES = frozenset(
    {
        STATE_CREATED,
        STATE_VALIDATED,
        STATE_LOCKED,
        STATE_READY,
        STATE_WRITING,
        STATE_VERIFYING,
        STATE_COMPLETED,
        STATE_ABORTED,
        STATE_FAILED,
        STATE_EXPIRED,
    }
)

# API-Rückgaben (vgl. Spezifikation)
DEPLOY_RUNNER_STATE_CREATED = "DEPLOY_RUNNER_STATE_CREATED"
DEPLOY_RUNNER_STATE_INVALID = "DEPLOY_RUNNER_STATE_INVALID"
DEPLOY_RUNNER_STATE_TRANSITION_BLOCKED = "DEPLOY_RUNNER_STATE_TRANSITION_BLOCKED"
# Erfolgreiche Transition (explizit, da Spezifikation nur drei Codes nennt — siehe Doku)
DEPLOY_RUNNER_LIFECYCLE_TRANSITION_OK = "DEPLOY_RUNNER_LIFECYCLE_TRANSITION_OK"

Checkpoint = Literal["pre_ready", "pre_writing", "pre_verifying"]

_EDGES: dict[str, frozenset[str]] = {
    STATE_CREATED: frozenset({STATE_VALIDATED, STATE_FAILED, STATE_EXPIRED}),
    STATE_VALIDATED: frozenset({STATE_LOCKED, STATE_FAILED, STATE_EXPIRED, STATE_ABORTED}),
    STATE_LOCKED: frozenset({STATE_READY, STATE_FAILED, STATE_ABORTED, STATE_EXPIRED}),
    STATE_READY: frozenset(
        {STATE_WRITING, STATE_COMPLETED, STATE_FAILED, STATE_ABORTED, STATE_EXPIRED}
    ),
    STATE_WRITING: frozenset({STATE_VERIFYING, STATE_FAILED, STATE_ABORTED}),
    STATE_VERIFYING: frozenset({STATE_COMPLETED, STATE_FAILED, STATE_ABORTED}),
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_job_file_stem(job_id: str) -> str:
    raw = re.sub(r"[^a-zA-Z0-9._-]+", "_", str(job_id or "").strip())[:200]
    return raw or "unknown_job"


def _lock_path(job_id: str) -> Path:
    return _LOCK_DIR / f"{_safe_job_file_stem(job_id)}.lock.json"


def _ensure_dirs() -> None:
    _LOCK_DIR.mkdir(parents=True, exist_ok=True)
    _AUDIT_DIR.mkdir(parents=True, exist_ok=True)


def build_runner_lifecycle(*, job_id: str, job_path: str | None = None) -> tuple[dict[str, Any], str]:
    jid = str(job_id or "").strip()
    if len(jid) < 2:
        return {}, DEPLOY_RUNNER_STATE_INVALID
    lc = {
        "state": STATE_CREATED,
        "job_id": jid,
        "job_path": job_path,
        "created_at": _now_iso(),
        "updated_at": _now_iso(),
    }
    return lc, DEPLOY_RUNNER_STATE_CREATED


def transition_runner_state(lifecycle: dict[str, Any], to_state: str) -> tuple[dict[str, Any], str]:
    if not isinstance(lifecycle, dict):
        return {}, DEPLOY_RUNNER_STATE_INVALID
    cur = str(lifecycle.get("state") or "")
    tgt = str(to_state or "").strip()
    if tgt not in ALL_STATES:
        return lifecycle, DEPLOY_RUNNER_STATE_INVALID
    if cur in TERMINAL_STATES:
        return lifecycle, DEPLOY_RUNNER_STATE_TRANSITION_BLOCKED
    allowed = _EDGES.get(cur, frozenset())
    if tgt not in allowed:
        return lifecycle, DEPLOY_RUNNER_STATE_TRANSITION_BLOCKED
    new_lc = dict(lifecycle)
    new_lc["state"] = tgt
    new_lc["updated_at"] = _now_iso()
    return new_lc, DEPLOY_RUNNER_LIFECYCLE_TRANSITION_OK


def _pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def _parse_iso(s: str) -> datetime | None:
    raw = str(s or "").strip()
    if not raw:
        return None
    try:
        if raw.endswith("Z"):
            raw = raw[:-1] + "+00:00"
        dt = datetime.fromisoformat(raw)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except ValueError:
        return None


def acquire_runner_lock(
    *,
    job_id: str,
    lock_id: str,
    state: str = STATE_LOCKED,
    ttl_seconds: int = 3600,
) -> tuple[bool, str | None]:
    """
    Exklusive Lock-Datei (O_EXCL), kein flock-Subprozess.
    """
    _ensure_dirs()
    path = _lock_path(job_id)
    payload = {
        "lock_id": str(lock_id),
        "job_id": str(job_id),
        "pid": os.getpid(),
        "created_at": _now_iso(),
        "state": str(state),
    }
    raw = json.dumps(payload, sort_keys=True, ensure_ascii=True) + "\n"
    try:
        fd = os.open(str(path), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        try:
            os.write(fd, raw.encode("utf-8"))
        finally:
            os.close(fd)
        return True, None
    except FileExistsError:
        stale, reason = _lock_file_stale(path, ttl_seconds=ttl_seconds)
        if stale:
            try:
                path.unlink(missing_ok=True)
            except TypeError:
                if path.exists():
                    path.unlink()
            try:
                fd = os.open(str(path), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
                try:
                    os.write(fd, raw.encode("utf-8"))
                finally:
                    os.close(fd)
                return True, None
            except OSError:
                return False, "DEPLOY_RUNNER_LOCK_BUSY"
        return False, reason or "DEPLOY_RUNNER_LOCK_BUSY"


def _lock_file_stale(path: Path, *, ttl_seconds: int) -> tuple[bool, str | None]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return True, None
    pid = int(data.get("pid") or 0)
    if not _pid_alive(pid):
        return True, None
    created = _parse_iso(str(data.get("created_at") or ""))
    if created is None:
        return True, None
    if datetime.now(timezone.utc) - created > timedelta(seconds=ttl_seconds):
        return True, None
    return False, "DEPLOY_RUNNER_LOCK_BUSY"


def release_runner_lock(job_id: str, *, pid: int | None = None) -> bool:
    path = _lock_path(job_id)
    me = int(pid if pid is not None else os.getpid())
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        try:
            path.unlink(missing_ok=True)
        except TypeError:
            if path.exists():
                path.unlink()
        return True
    if int(data.get("pid") or 0) != me:
        return False
    try:
        path.unlink()
    except OSError:
        return False
    return True


def cleanup_stale_runner_locks(*, ttl_seconds: int = 3600, now: datetime | None = None) -> int:
    """Entfernt abgelaufene, tote PID- oder defekte Lock-Dateien. Kein Device-Zugriff."""
    _ensure_dirs()
    removed = 0
    now_utc = now or datetime.now(timezone.utc)
    for path in _LOCK_DIR.glob("*.lock.json"):
        stale = False
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            pid = int(data.get("pid") or 0)
            created = _parse_iso(str(data.get("created_at") or ""))
            if not _pid_alive(pid):
                stale = True
            elif created is None:
                stale = True
            elif (now_utc - created) > timedelta(seconds=ttl_seconds):
                stale = True
        except (OSError, json.JSONDecodeError, ValueError):
            stale = True
        if stale:
            try:
                path.unlink()
                removed += 1
            except OSError:
                pass
    return removed


def extract_runner_baseline_from_job(job: dict[str, Any]) -> dict[str, Any]:
    """Read-only Snapshot für TOCTOU-Vergleiche (keine Secrets)."""
    guard = job.get("guard") if isinstance(job.get("guard"), dict) else {}
    return {
        "job_hash": str(job.get("job_hash") or ""),
        "snapshot_fingerprint": str(guard.get("snapshot_fingerprint") or ""),
        "image_sha256": str(job.get("image_sha256") or ""),
        "image_size_bytes": int(job.get("image_size_bytes") or 0),
        "target_device": str(job.get("target_device") or ""),
        "mounted": bool(job.get("_runtime_mounted", False)),
        "removable": bool(job.get("_runtime_removable", True)),
        "readonly": bool(job.get("_runtime_readonly", False)),
        "guard_subset": {
            "snapshot_fingerprint": str(guard.get("snapshot_fingerprint") or ""),
            "hardware_gate_readiness": str(guard.get("hardware_gate_readiness") or ""),
        },
    }


def recheck_runner_consistency(
    *,
    checkpoint: Checkpoint,
    baseline: dict[str, Any],
    current: dict[str, Any],
) -> tuple[bool, list[str]]:
    """
    Read-only drift check. `current` liefert der Aufrufer (z. B. frisch aus Job + Runtime-Metadaten).
    """
    errs: list[str] = []
    pairs = [
        ("job_hash", "job_hash"),
        ("snapshot_fingerprint", "snapshot_fingerprint"),
        ("image_sha256", "image_sha256"),
        ("image_size_bytes", "image_size_bytes"),
        ("target_device", "target_device"),
        ("mounted", "mounted"),
        ("removable", "removable"),
        ("readonly", "readonly"),
    ]
    for bk, ck in pairs:
        if baseline.get(bk) != current.get(ck):
            errs.append(f"DEPLOY_RUNNER_TOCTOU_DRIFT:{checkpoint}:{bk}")
    base_gs = baseline.get("guard_subset")
    cur_gs = current.get("guard_subset")
    if isinstance(base_gs, dict) and isinstance(cur_gs, dict):
        if base_gs != cur_gs:
            errs.append(f"DEPLOY_RUNNER_TOCTOU_DRIFT:{checkpoint}:guard_subset")
    elif base_gs != cur_gs:
        errs.append(f"DEPLOY_RUNNER_TOCTOU_DRIFT:{checkpoint}:guard_subset")
    return (len(errs) == 0, errs)


def append_runner_audit(
    *,
    runner_state: str,
    job_id: str,
    target_device: str,
    event: str,
    code: str,
) -> None:
    """JSON Lines; keine vollständigen Checksummen/Secrets."""
    _ensure_dirs()
    path = _AUDIT_DIR / f"audit-{datetime.now(timezone.utc).strftime('%Y%m%d')}.jsonl"
    entry = {
        "timestamp": _now_iso(),
        "runner_state": str(runner_state)[:64],
        "job_id": str(job_id)[:128],
        "target_device": str(target_device)[:256],
        "event": str(event)[:128],
        "code": str(code)[:128],
    }
    line = json.dumps(entry, sort_keys=True, ensure_ascii=True) + "\n"
    with path.open("a", encoding="utf-8") as f:
        f.write(line)
        try:
            os.fsync(f.fileno())
        except OSError:
            pass


def cleanup_expired_runner_locks(*, ttl_seconds: int = 3600) -> int:
    """Alias mit klarer Semantik für abgelaufene Locks."""
    return cleanup_stale_runner_locks(ttl_seconds=ttl_seconds)


def cleanup_expired_runner_jobs(
    jobs_root: Path | None = None,
    *,
    ttl_seconds: int = 86400,
    now: datetime | None = None,
) -> int:
    """
    Löscht Job-JSON unter jobs_root, wenn `expires_at` in der Vergangenheit liegt.
    Default jobs_root: deploy-cache (nur Entwicklung); Production: /var/lib/...
    """
    root = jobs_root if jobs_root is not None else _DEPLOY_CACHE
    now_utc = now or datetime.now(timezone.utc)
    removed = 0
    if not root.is_dir():
        return 0
    for path in root.glob("*.json"):
        if path.name.endswith(".lock.json"):
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        exp = _parse_iso(str(data.get("expires_at") or ""))
        if exp is None:
            continue
        if exp < now_utc:
            try:
                path.unlink()
                removed += 1
            except OSError:
                pass
    # TTL fallback: sehr alte Dateien ohne expires_at nicht löschen (fail-closed)
    _ = ttl_seconds
    return removed


def prepare_audit_rotation(*, keep_days: int = 7) -> int:
    """Löscht ältere audit-*.jsonl; behält die letzten keep_days Tage nach Dateinamen."""
    _ensure_dirs()
    if keep_days <= 0:
        return 0
    files = sorted(_AUDIT_DIR.glob("audit-*.jsonl"), key=lambda p: p.name, reverse=True)
    removed = 0
    for p in files[keep_days:]:
        try:
            p.unlink()
            removed += 1
        except OSError:
            pass
    return removed


def new_lock_id() -> str:
    return secrets.token_hex(16)
