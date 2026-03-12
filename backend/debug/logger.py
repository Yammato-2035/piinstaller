"""
Logger/JSONL: init_debug, get_run_id, get_logger, should_log, write_event.
Nutzt context.py (request_id), levels.py, paths.resolve_debug_log_path, rotate.rotate_if_needed, redaction.
App-Name: pi-installer-backend. Niemals Exceptions nach außen.
"""

import json
import os
import socket
import sys
import threading
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

try:
    from zoneinfo import ZoneInfo
    _TZ = ZoneInfo("Europe/Berlin")
except Exception:
    _TZ = None

from .config import get_effective_config_cached, get_effective_step_config
from .context import get_request_id
from .levels import parse_level, should_log_level, LEVEL_ORDER, DEFAULT_LEVEL
from .paths import resolve_debug_log_path
from .redaction import get_compiled_redact_patterns, redact_value
from . import rotate

# Event-Typen
RUN_START = "RUN_START"
RUN_END = "RUN_END"
STEP_START = "STEP_START"
STEP_END = "STEP_END"
DECISION = "DECISION"
APPLY_ATTEMPT = "APPLY_ATTEMPT"
APPLY_NOOP = "APPLY_NOOP"
APPLY_SUCCESS = "APPLY_SUCCESS"
APPLY_FAILED = "APPLY_FAILED"
ERROR = "ERROR"

_run_id: Optional[str] = None
_log_path: Optional[str] = None
_file_lock = threading.Lock()


def _app_info() -> Dict[str, Any]:
    """app.name = pi-installer-backend, version/build best-effort.

    Quelle für die Version ist konsistent `config/version.json` (falls vorhanden),
    mit Fallback auf die historische VERSION-Datei im Projekt-/Installationsroot.
    """
    version = "0.0.0"
    build = None
    try:
        root = Path(__file__).resolve().parent.parent.parent
        base = root

        # 1. Versuch: config/version.json neben dem Projektroot
        try:
            version_json = base / "config" / "version.json"
            if version_json.exists():
                import json

                data = json.loads(version_json.read_text(encoding="utf-8"))
                v = str(data.get("version") or "").strip()
                if v:
                    version = v
        except Exception:
            # stiller Fallback auf VERSION
            pass

        # 2. Fallback: historische VERSION-Datei
        if version == "0.0.0":
            vf = base / "VERSION"
            if vf.exists():
                version = vf.read_text(encoding="utf-8").strip() or version

        # Git-Build-Hash (optional)
        try:
            import subprocess

            r = subprocess.run(
                ["git", "rev-parse", "--short", "HEAD"],
                cwd=root,
                capture_output=True,
                text=True,
                timeout=2,
            )
            if r.returncode == 0 and r.stdout:
                build = r.stdout.strip()
        except Exception:
            pass
    except Exception:
        pass
    return {"name": "pi-installer-backend", "version": version, "build": build}


def _ts_iso_local() -> str:
    """ISO8601 Europe/Berlin."""
    try:
        now = datetime.now(_TZ) if _TZ else datetime.now().astimezone()
    except Exception:
        now = datetime.now()
    return now.isoformat(timespec="milliseconds")


def _context_meta() -> Dict[str, Any]:
    """host, user, pid."""
    out = {}
    try:
        out["host"] = socket.gethostname() or ""
    except Exception:
        out["host"] = ""
    try:
        out["user"] = os.getlogin() if hasattr(os, "getlogin") else str(os.geteuid())
    except Exception:
        try:
            out["user"] = str(os.geteuid())
        except Exception:
            out["user"] = ""
    try:
        out["pid"] = os.getpid()
    except Exception:
        out["pid"] = 0
    return out


def init_debug(run_id: Optional[str] = None) -> str:
    """Setzt run_id (generiert UUID wenn None). Gibt run_id zurück."""
    global _run_id, _log_path
    _run_id = run_id or str(uuid.uuid4())
    try:
        cfg = get_effective_config_cached()
        sink = (cfg.get("global") or {}).get("sink") or {}
        preferred = (sink.get("file") or {}).get("path") or ""
        _log_path = resolve_debug_log_path(preferred or None)
    except Exception:
        try:
            _log_path = resolve_debug_log_path(None)
        except Exception:
            _log_path = None
    return _run_id


def get_run_id() -> str:
    """Liefert aktuelle run_id (nach init_debug)."""
    return _run_id or ""


def should_log(level: str, module_id: str, step_id: Optional[str] = None) -> bool:
    """
    True wenn für dieses level/module/step geloggt werden soll.
    global.enabled == false -> nur ERROR.
    module/step disabled -> nur ERROR für diesen Scope.
    Sonst: event_level >= effective_level (numerisch).
    """
    try:
        cfg = get_effective_config_cached()
        global_ = cfg.get("global") or {}
        if not global_.get("enabled", True):
            return parse_level(level) == "ERROR"
        step_eff = get_effective_step_config(module_id, step_id or "")
        if not step_eff.get("enabled", True):
            return parse_level(level) == "ERROR"
        effective_level = parse_level(step_eff.get("level") or DEFAULT_LEVEL)
        return should_log_level(level, effective_level)
    except Exception:
        return True


def write_event(event_dict: Dict[str, Any]) -> None:
    """
    Schreibt ein Event als JSONL-Zeile. Redaktion auf context/data/error-Strings.
    Rotation vor Write. Wirft nie – bei Fehler einzeilig nach stderr.
    """
    global _log_path
    try:
        if _log_path is None:
            cfg = get_effective_config_cached()
            sink = (cfg.get("global") or {}).get("sink") or {}
            preferred = (sink.get("file") or {}).get("path") or ""
            _log_path = resolve_debug_log_path(preferred or None)
    except Exception:
        pass

    try:
        payload = dict(event_dict)
        payload.setdefault("ts", _ts_iso_local())
        payload.setdefault("run_id", get_run_id())
        payload.setdefault("request_id", get_request_id())
        payload.setdefault("app", _app_info())
        if "context" not in payload or not isinstance(payload["context"], dict):
            payload["context"] = payload.get("context") or _context_meta()
        else:
            base = _context_meta()
            base.update(payload["context"])
            payload["context"] = base

        patterns = get_compiled_redact_patterns()
        if patterns:
            payload["context"] = redact_value(payload.get("context") or {}, patterns)
            payload["data"] = redact_value(payload.get("data") or {}, patterns)
            if "error" in payload.get("data") and isinstance(payload["data"].get("error"), str):
                payload["data"]["error"] = redact_value(payload["data"]["error"], patterns)
            if "metrics" in payload and isinstance(payload["metrics"], dict):
                payload["metrics"] = redact_value(payload["metrics"], patterns)

        line = json.dumps(payload, ensure_ascii=False) + "\n"

        path = _log_path
        if not path:
            return
        cfg = get_effective_config_cached()
        rotate_cfg = (cfg.get("global") or {}).get("rotate") or {}
        max_size_mb = float(rotate_cfg.get("max_size_mb", 5))
        max_files = int(rotate_cfg.get("max_files", 10))
        max_bytes = int(max_size_mb * 1024 * 1024)

        with _file_lock:
            rotate.rotate_if_needed(path, max_bytes, max_files)
            p = Path(path)
            try:
                p.parent.mkdir(parents=True, exist_ok=True)
            except Exception:
                pass
            try:
                with open(path, "a", encoding="utf-8") as f:
                    f.write(line)
                    f.flush()
                    os.fsync(f.fileno())
            except Exception as e:
                print(f"[debug] write_event failed: {e}", file=sys.stderr)
    except Exception as e:
        print(f"[debug] write_event error: {e}", file=sys.stderr)


def _emit(event_type: str, event_name: str, level: str, module_id: str, step_id: Optional[str],
          context: Optional[Dict] = None, metrics: Optional[Dict] = None, data: Optional[Dict] = None) -> None:
    if not should_log(level, module_id, step_id):
        return
    write_event({
        "level": parse_level(level),
        "scope": {"module_id": module_id or "", "step_id": step_id or ""},
        "event": {"type": event_type, "name": event_name},
        "context": context or {},
        "metrics": metrics or {},
        "data": data or {},
    })


class ModuleLogger:
    """Logger-API für Module: step_start/end, decision, apply_*, error."""

    def __init__(self, module_id: str, step_id: Optional[str] = None):
        self.module_id = module_id
        self.step_id = step_id

    def step_start(self, name: str, data: Optional[Dict] = None) -> None:
        _emit(STEP_START, name, "INFO", self.module_id, self.step_id, data=data)

    def step_end(self, name: str, duration_ms: Optional[float] = None, data: Optional[Dict] = None) -> None:
        metrics = {"duration_ms": duration_ms} if duration_ms is not None else {}
        _emit(STEP_END, name, "INFO", self.module_id, self.step_id, metrics=metrics, data=data)

    def decision(self, name: str, data: Optional[Dict] = None) -> None:
        _emit(DECISION, name, "INFO", self.module_id, self.step_id, data=data)

    def apply_attempt(self, name: str, before_hash: Optional[str] = None, after_hash: Optional[str] = None,
                     diff: Optional[str] = None, data: Optional[Dict] = None) -> None:
        d = dict(data or {})
        if before_hash is not None:
            d["before_hash"] = before_hash
        if after_hash is not None:
            d["after_hash"] = after_hash
        if diff is not None:
            d["diff"] = diff
        _emit(APPLY_ATTEMPT, name, "INFO", self.module_id, self.step_id, data=d)

    def apply_noop(self, name: str, data: Optional[Dict] = None) -> None:
        _emit(APPLY_NOOP, name, "INFO", self.module_id, self.step_id, data=data)

    def apply_success(self, name: str, data: Optional[Dict] = None) -> None:
        _emit(APPLY_SUCCESS, name, "INFO", self.module_id, self.step_id, data=data)

    def apply_failed(self, name: str, error: str, data: Optional[Dict] = None) -> None:
        d = dict(data or {})
        d["error"] = error
        _emit(APPLY_FAILED, name, "ERROR", self.module_id, self.step_id, data=d)

    def error(self, error: str, error_code: Optional[str] = None, data: Optional[Dict] = None) -> None:
        d = dict(data or {})
        d["error"] = error
        if error_code is not None:
            d["error_code"] = error_code
        _emit(ERROR, "error", "ERROR", self.module_id, self.step_id, data=d)


def get_logger(module_id: str, step_id: Optional[str] = None) -> ModuleLogger:
    return ModuleLogger(module_id, step_id)


def run_start(data: Optional[Dict] = None) -> str:
    """Start eines Runs: init_debug falls nötig, RUN_START Event. Rückwärtskompatibel."""
    global _run_id
    if not _run_id:
        init_debug()
    _emit(RUN_START, "run_start", "INFO", "", None, data=data)
    return get_run_id()


def run_end(data: Optional[Dict] = None) -> None:
    """RUN_END Event."""
    _emit(RUN_END, "run_end", "INFO", "", None, data=data)


def set_run_id(rid: Optional[str] = None) -> str:
    """Setzt run_id (z.B. für Tests). Rückwärtskompatibel."""
    global _run_id
    _run_id = rid or str(uuid.uuid4())
    return _run_id


def bind_request_id(rid: Optional[str] = None):
    """Für Middleware: setzt request_id, gibt Token für reset_request_id."""
    from .context import bind_request_id as _bind
    return _bind(rid)


def reset_request_id(token) -> None:
    from .context import reset_request_id as _reset
    _reset(token)


def should_verbose_dump_on_error(module_id: str, step_id: Optional[str] = None) -> bool:
    """True wenn effective level DEBUG für diesen Scope."""
    try:
        step_eff = get_effective_step_config(module_id, step_id or "")
        return parse_level(step_eff.get("level")) == "DEBUG"
    except Exception:
        return False
