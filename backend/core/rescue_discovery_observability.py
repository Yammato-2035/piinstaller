"""Discovery boot observability — persistent start/exit/finalizer evidence (001D7C)."""

from __future__ import annotations

import json
import os
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.rescue_physical_e2e_evidence_import import find_setup_logs_mount

START_GATE_SCHEMA = "setuphelfer.rescue.discovery-start-gate.v1"
ORCHESTRATOR_EXIT_SCHEMA = "setuphelfer.rescue.discovery-orchestrator-exit.v1"
SERVICE_RESULT_SCHEMA = "setuphelfer.rescue.discovery-service-result.v1"
BOOT_FINALIZER_SCHEMA = "setuphelfer.rescue.discovery-boot-finalizer.v1"
BOOT_CONTEXT_SCHEMA = "setuphelfer.rescue.discovery-boot-context.v1"


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def boot_id() -> str:
    try:
        return Path("/proc/sys/kernel/random/boot_id").read_text(encoding="utf-8").strip()
    except OSError:
        return str(uuid.uuid4())


def state_dir() -> Path:
    return Path(os.environ.get("SETUPHELFER_RESCUE_STATE_DIR", "/run/setuphelfer-rescue"))


def runtime_discovery_dir(*, create: bool = True) -> Path:
    path = Path(
        os.environ.get("SETUPHELFER_RESCUE_DISCOVERY_DIR", str(state_dir() / "discovery"))
    )
    if create:
        try:
            path.mkdir(parents=True, exist_ok=True)
        except OSError:
            pass
    return path


def discovery_boot_dir(setup_logs_base: Path | None, bid: str | None = None) -> Path:
    bid = bid or boot_id()
    if setup_logs_base and setup_logs_base.is_dir():
        path = setup_logs_base / "setuphelfer" / "evidence" / "discovery-boot" / bid
    else:
        path = state_dir() / "fallback-evidence" / "discovery-boot" / bid
    try:
        path.mkdir(parents=True, exist_ok=True)
    except OSError:
        pass
    return path


def atomic_write_json(path: Path, data: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    with tmp.open("rb") as handle:
        os.fsync(handle.fileno())
    tmp.replace(path)
    try:
        fd = os.open(str(path.parent), os.O_DIRECTORY)
        os.fsync(fd)
        os.close(fd)
    except OSError:
        pass
    return path


def write_dual(name: str, data: dict[str, Any], *, setup_logs_base: Path | None = None) -> dict[str, str]:
    """Write to /run and best-effort SETUP_LOGS discovery-boot/<boot_id>/."""
    bid = str(data.get("boot_id") or boot_id())
    data = {**data, "boot_id": bid, "recorded_at": data.get("recorded_at") or _utc_now()}
    runtime_path = runtime_discovery_dir() / name
    atomic_write_json(runtime_path, data)
    base = setup_logs_base
    if base is None:
        try:
            from core.rescue_setup_logs_resolver import setup_logs_root_from_env

            env_base = setup_logs_root_from_env()
            if env_base is not None:
                base = env_base
        except ImportError:
            base = None
    if base is None:
        base = find_setup_logs_mount()
    persistent = ""
    try:
        persist_path = discovery_boot_dir(base, bid) / name
        atomic_write_json(persist_path, data)
        persistent = str(persist_path)
    except OSError:
        persistent = ""
    return {"runtime": str(runtime_path), "persistent": persistent, "boot_id": bid}


def ensure_boot_context(*, payload_version: str = "") -> dict[str, Any]:
    bid = boot_id()
    try:
        cmdline = Path("/proc/cmdline").read_text(encoding="utf-8").strip()
    except OSError:
        cmdline = ""
    payload = {
        "schema": BOOT_CONTEXT_SCHEMA,
        "boot_id": bid,
        "payload_version": payload_version,
        "cmdline_redacted": redact_text(cmdline),
        "called_at": _utc_now(),
    }
    write_dual("00-boot-context.json", payload)
    return payload


def persist_start_gate_audit(result: dict[str, Any], *, payload_version: str = "") -> dict[str, Any]:
    control_found = bool(result.get("run_control_found"))
    if "run_control_found" not in result:
        # Inferred from reasons used by the gate evaluator.
        control_found = result.get("reason") not in {
            "discovery_run_control_missing",
            "discovery_run_control_unavailable",
            "kernel_trigger_missing",
            "auto_discovery_flag_without_setup_logs_yet",
        }
    audit = {
        "schema": START_GATE_SCHEMA,
        "called": True,
        "called_at": _utc_now(),
        "boot_id": boot_id(),
        "payload_version": payload_version,
        "kernel_auto_discovery": bool(result.get("kernel_auto_discovery")),
        "run_control_found": control_found,
        "run_control_enabled": bool(result.get("run_control_enabled")),
        "run_control_consumed": bool(result.get("run_control_consumed")),
        "run_mode": result.get("run_mode") or "",
        "payload_version_match": bool(result.get("payload_version_match")),
        "start_allowed": bool(result.get("start_allowed")),
        "decision_code": str(result.get("reason") or result.get("decision_code") or ""),
        "exit_code": int(result["exit_code"]) if result.get("exit_code") is not None else 1,
    }
    write_dual("00-start-gate.json", audit)
    # Convenience symlink-style copy for TUI.
    atomic_write_json(runtime_discovery_dir() / "start-gate.json", audit)
    return audit


def persist_service_start(*, payload_version: str = "") -> dict[str, Any]:
    payload = {
        "schema": "setuphelfer.rescue.discovery-service-start.v1",
        "runner_started": True,
        "started_at": _utc_now(),
        "boot_id": boot_id(),
        "payload_version": payload_version,
        "pid": os.getpid(),
    }
    write_dual("01-service-start.json", payload)
    atomic_write_json(runtime_discovery_dir() / "service-start.json", payload)
    return payload


def persist_orchestrator_exit(payload: dict[str, Any]) -> dict[str, Any]:
    data = {
        "schema": ORCHESTRATOR_EXIT_SCHEMA,
        "boot_id": boot_id(),
        "started": bool(payload.get("started", True)),
        "started_at": payload.get("started_at") or _utc_now(),
        "completed_at": payload.get("completed_at") or _utc_now(),
        "exit_code": payload.get("exit_code"),
        "signal": payload.get("signal"),
        "exception_type": payload.get("exception_type"),
        "exception_summary": payload.get("exception_summary"),
        "session_created": bool(payload.get("session_created")),
        "terminal_state_written": bool(payload.get("terminal_state_written")),
        "status": payload.get("status") or "",
    }
    write_dual("02-orchestrator-exit.json", data)
    atomic_write_json(runtime_discovery_dir() / "orchestrator-exit.json", data)
    return data


def persist_service_result(payload: dict[str, Any]) -> dict[str, Any]:
    data = {
        "schema": SERVICE_RESULT_SCHEMA,
        "boot_id": boot_id(),
        "completed_at": _utc_now(),
        "exit_code": payload.get("exit_code"),
        "status": payload.get("status") or "",
        "run_control_consumed": bool(payload.get("run_control_consumed")),
        "session_id": payload.get("session_id") or None,
        "failure_stage": payload.get("failure_stage") or "",
    }
    write_dual("03-service-result.json", data)
    atomic_write_json(runtime_discovery_dir() / "service-result.json", data)
    return data


def persist_boot_finalizer(payload: dict[str, Any]) -> dict[str, Any]:
    terminal = bool(payload.get("terminal", True))
    data = {
        "schema": BOOT_FINALIZER_SCHEMA,
        "boot_id": boot_id(),
        "completed_at": _utc_now(),
        "terminal": terminal,
        "status": payload.get("status") or "",
        "observability_complete": bool(payload.get("observability_complete")),
        "run_control_consumed": bool(payload.get("run_control_consumed")),
        "shutdown_safe": bool(payload.get("shutdown_safe", True)),
        "missing": payload.get("missing") or [],
        "notes": payload.get("notes") or [],
    }
    write_dual("boot-finalizer.json", data)
    atomic_write_json(runtime_discovery_dir() / "boot-finalizer.json", data)
    # Only stamp boot-finalizer.done for terminal outcomes (guard must keep retrying otherwise).
    if terminal:
        try:
            state_dir().mkdir(parents=True, exist_ok=True)
            (state_dir() / "boot-finalizer.done").write_text(data["status"] + "\n", encoding="utf-8")
        except OSError:
            pass
    return data


def read_runtime_json(name: str) -> dict[str, Any] | None:
    path = runtime_discovery_dir(create=False) / name
    if not path.is_file():
        # Also accept short names used by TUI.
        alt = {
            "00-start-gate.json": "start-gate.json",
            "03-service-result.json": "service-result.json",
            "boot-finalizer.json": "boot-finalizer.json",
        }.get(name)
        if alt:
            path = runtime_discovery_dir(create=False) / alt
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


_REDACT_PATTERNS = (
    (re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"), "[REDACTED:ip]"),
    (re.compile(r"\b([0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}\b"), "[REDACTED:mac]"),
    (re.compile(r"(?i)(token|bearer|api[_-]?key|password|secret)\s*[:=]\s*\S+"), r"\1=[REDACTED]"),
    (re.compile(r"/home/[A-Za-z0-9._-]+"), "/home/[REDACTED:user]"),
)


def redact_text(text: str) -> str:
    out = text
    for pattern, repl in _REDACT_PATTERNS:
        out = pattern.sub(repl, out)
    return out


def classify_exception(exc: BaseException) -> str:
    if isinstance(exc, ModuleNotFoundError):
        return "failed_discovery_import"
    if isinstance(exc, ImportError):
        return "failed_discovery_import"
    if isinstance(exc, json.JSONDecodeError):
        return "failed_discovery_configuration"
    if isinstance(exc, FileNotFoundError):
        return "failed_discovery_setup_logs"
    if isinstance(exc, PermissionError):
        return "failed_discovery_setup_logs"
    if isinstance(exc, ValueError) and "schema" in str(exc).lower():
        return "failed_discovery_configuration"
    name = type(exc).__name__
    if "session" in str(exc).lower():
        return "failed_discovery_session_init"
    if name:
        return "failed_discovery_unhandled_exception"
    return "failed_discovery_unhandled_exception"


def exception_summary(exc: BaseException) -> str:
    raw = f"{type(exc).__name__}: {exc}"
    return redact_text(raw)[:400]
