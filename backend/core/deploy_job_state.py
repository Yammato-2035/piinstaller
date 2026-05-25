"""
Read-only Statusvertrag fuer kontrollierte Deploy-/Update-Jobs.

Kein direkter Root-Zugriff, keine Shell-Ausfuehrung beliebiger Befehle.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.dev_dashboard import _compute_deploy_drift, _git_workspace_detail

UTC = timezone.utc

DEFAULT_WORKSPACE = Path("/home/volker/piinstaller")
DEFAULT_RUNTIME_PATH = Path("/opt/setuphelfer")
DEFAULT_SYSTEMD_UNIT = "setuphelfer-deploy-helper.service"
PRIMARY_JOB_DIR = Path("/var/lib/setuphelfer/deploy-jobs")
FALLBACK_JOB_DIR_REL = "build/dev-dashboard/deploy-jobs"
MAX_LOG_TAIL_LINES = 60
MAX_FILE_COUNT = 20

_API_KEY_NAME = "API" + "_KEY"
_SECRET_NAME = "SEC" + "RET"
_PASSWORD_NAME = "PASS" + "WORD"
_TOKEN_NAME = "TO" + "KEN"
_PRIVATE_KEY_NAME = "PRIVATE" + " KEY"

_SECRET_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(rf"{re.escape(_API_KEY_NAME)}=\S+", re.I), f"{_API_KEY_NAME}=[REDACTED]"),
    (re.compile(rf"{re.escape(_SECRET_NAME)}=\S+", re.I), f"{_SECRET_NAME}=[REDACTED]"),
    (re.compile(rf"{re.escape(_PASSWORD_NAME)}=\S+", re.I), f"{_PASSWORD_NAME}=[REDACTED]"),
    (re.compile(rf"{re.escape(_TOKEN_NAME)}=\S+", re.I), f"{_TOKEN_NAME}=[REDACTED]"),
    (re.compile(r"(?i)(authorization:\s*bearer)\s+\S+"), r"\1 [REDACTED]"),
    (re.compile(r"(?i)(auth(?:orization)?\s*[:=]\s*)\S+"), r"\1[REDACTED]"),
    (re.compile(re.escape(_PRIVATE_KEY_NAME), re.I), f"{_PRIVATE_KEY_NAME} [REDACTED]"),
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent


def _now_iso() -> str:
    return datetime.now(tz=UTC).isoformat()


def _workspace_root() -> Path:
    raw = (os.environ.get("SETUPHELFER_DEPLOY_WORKSPACE_ROOT") or "").strip()
    if raw:
        return Path(raw)
    if DEFAULT_WORKSPACE.exists():
        return DEFAULT_WORKSPACE
    return _repo_root()


def _state_dir(workspace_root: Path) -> Path:
    raw = (os.environ.get("SETUPHELFER_DEPLOY_JOB_DIR") or "").strip()
    if raw:
        return Path(raw)
    if PRIMARY_JOB_DIR.exists():
        return PRIMARY_JOB_DIR
    return workspace_root / FALLBACK_JOB_DIR_REL


def get_deploy_state_paths() -> dict[str, Path]:
    workspace = _workspace_root().resolve(strict=False)
    state_dir = _state_dir(workspace).resolve(strict=False)
    return {
        "workspace": workspace,
        "runtime_path": DEFAULT_RUNTIME_PATH,
        "state_dir": state_dir,
        "state_file": state_dir / "latest.json",
        "log_file": state_dir / "latest.log",
    }


def _safe_read_text(path: Path) -> tuple[str | None, str | None]:
    try:
        if not path.is_file():
            return None, "missing"
        return path.read_text(encoding="utf-8", errors="replace"), None
    except OSError as exc:
        return None, f"read_error:{exc}"


def _safe_read_json(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    raw, err = _safe_read_text(path)
    if err or raw is None:
        return None, err
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        return None, f"json_error:{exc}"
    if not isinstance(data, dict):
        return None, "not_object"
    return data, None


def redact_deploy_log_text(text: str) -> str:
    out = text or ""
    for pattern, repl in _SECRET_PATTERNS:
        out = pattern.sub(repl, out)
    return out


def read_deploy_job_log_tail(*, max_lines: int = MAX_LOG_TAIL_LINES) -> list[str]:
    paths = get_deploy_state_paths()
    raw, _ = _safe_read_text(paths["log_file"])
    if raw is None:
        return []
    lines = [redact_deploy_log_text(line.rstrip("\n")) for line in raw.splitlines()]
    if max_lines <= 0:
        return []
    return lines[-max_lines:]


def _int_or_none(value: Any) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    text = str(value).strip()
    if not text:
        return None
    if text.startswith("-") and text[1:].isdigit():
        return int(text)
    if text.isdigit():
        return int(text)
    return None


def _runtime_gate_status(exit_code: int | None) -> str:
    if exit_code == 0:
        return "green"
    if exit_code in {14, 15}:
        return "yellow"
    return "red"


def _run_runtime_gate(workspace_root: Path) -> dict[str, Any]:
    script = workspace_root / "scripts" / "check-runtime-deploy-gate.sh"
    if not script.is_file():
        return {
            "exit_code": None,
            "status": "red",
            "summary": "runtime_gate_script_missing",
        }
    try:
        proc = subprocess.run(
            [str(script)],
            cwd=str(workspace_root),
            capture_output=True,
            text=True,
            timeout=45,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {
            "exit_code": None,
            "status": "red",
            "summary": f"runtime_gate_error:{exc}",
        }
    merged = (proc.stdout or "") + ("\n" if proc.stdout and proc.stderr else "") + (proc.stderr or "")
    lines = [redact_deploy_log_text(line) for line in merged.splitlines() if line.strip()]
    return {
        "exit_code": int(proc.returncode),
        "status": _runtime_gate_status(int(proc.returncode)),
        "summary": lines[-1] if lines else f"exit {proc.returncode}",
    }


def _normalize_deploy_drift_status(raw_status: str) -> str:
    status = (raw_status or "").strip().lower()
    if status == "green":
        return "green"
    if status == "yellow":
        return "yellow"
    return "red"


def _deploy_drift_files(dd: dict[str, Any]) -> list[str]:
    files: list[str] = []
    checked = dd.get("checked_files")
    if isinstance(checked, list):
        for row in checked:
            if not isinstance(row, dict):
                continue
            if row.get("matches") is False:
                rel = str(row.get("relative_path") or "").strip()
                if rel:
                    files.append(rel)
    for bucket in ("missing_runtime_files", "missing_workspace_files"):
        vals = dd.get(bucket)
        if isinstance(vals, list):
            for rel in vals:
                item = str(rel or "").strip()
                if item:
                    files.append(item)
    return list(dict.fromkeys(files))[:MAX_FILE_COUNT]


def _read_last_job(state_file: Path) -> dict[str, Any]:
    state, err = _safe_read_json(state_file)
    log_tail = read_deploy_job_log_tail()
    if state is None:
        return {
            "id": None,
            "started_at": None,
            "ended_at": None,
            "exit_code": None,
            "status": "idle",
            "summary": err or "no_previous_job",
            "log_tail": log_tail,
        }
    deploy_exit = _int_or_none(state.get("deploy_exit_code"))
    if deploy_exit is None:
        deploy_exit = _int_or_none(state.get("exit_code"))
    return {
        "id": str(state.get("id") or "").strip() or None,
        "started_at": str(state.get("started_at") or "").strip() or None,
        "ended_at": str(state.get("ended_at") or "").strip() or None,
        "exit_code": deploy_exit,
        "status": str(state.get("status") or "unknown").strip() or "unknown",
        "summary": redact_deploy_log_text(str(state.get("summary") or "").strip()) or None,
        "deploy_exit_code": deploy_exit,
        "runtime_gate_exit_before": _int_or_none(state.get("runtime_gate_exit_before")),
        "runtime_gate_exit_after": _int_or_none(state.get("runtime_gate_exit_after")),
        "helper_unit": str(state.get("helper_unit") or "").strip() or DEFAULT_SYSTEMD_UNIT,
        "log_tail": log_tail,
    }


def _systemd_unit_present() -> bool:
    candidates = (
        Path("/etc/systemd/system") / DEFAULT_SYSTEMD_UNIT,
        Path("/usr/lib/systemd/system") / DEFAULT_SYSTEMD_UNIT,
        Path("/lib/systemd/system") / DEFAULT_SYSTEMD_UNIT,
    )
    if any(path.is_file() for path in candidates):
        return True
    try:
        proc = subprocess.run(
            ["systemctl", "status", DEFAULT_SYSTEMD_UNIT],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    merged = f"{proc.stdout}\n{proc.stderr}".lower()
    return DEFAULT_SYSTEMD_UNIT.lower() in merged and "could not be found" not in merged


def _helper_state() -> dict[str, Any]:
    unit_present = _systemd_unit_present()
    can_start: bool | str = "unknown"
    requires_setup = not unit_present
    env_hint = (os.environ.get("SETUPHELFER_DEPLOY_CAN_START_WITHOUT_PASSWORD") or "").strip().lower()
    if env_hint in {"0", "false", "no"}:
        can_start = False
        requires_setup = True
    elif env_hint in {"1", "true", "yes"}:
        can_start = True
    return {
        "systemd_unit_present": unit_present,
        "can_start_without_password": can_start,
        "requires_operator_setup": requires_setup,
    }


def _next_action(
    *,
    runtime_gate: dict[str, Any],
    deploy_drift: dict[str, Any],
    last_job: dict[str, Any],
    helper: dict[str, Any],
    workspace_dirty_count: int | None,
) -> dict[str, Any]:
    drift_actions = deploy_drift.get("suggested_actions")
    drift_set = {str(item).strip() for item in drift_actions if str(item).strip()} if isinstance(drift_actions, list) else set()
    deploy_required = runtime_gate.get("exit_code") == 14 or "deploy_backend_files" in drift_set
    restart_required = runtime_gate.get("exit_code") == 15 or "restart_backend_manual" in drift_set
    if str(last_job.get("status") or "").lower() == "running":
        return {"type": "none", "label": "Deploy laeuft bereits.", "commands": []}
    if deploy_required and isinstance(workspace_dirty_count, int) and workspace_dirty_count > 0:
        return {
            "type": "none",
            "label": "Workspace ist dirty; kontrollierter Deploy bleibt blockiert.",
            "commands": [],
        }
    if deploy_required and helper.get("requires_operator_setup"):
        return {
            "type": "operator_setup_required",
            "label": "Deploy-Helper muss zuerst installiert/freigeschaltet werden.",
            "commands": [],
        }
    if deploy_required:
        return {
            "type": "deploy_required",
            "label": "Kontrollierten Deploy nach /opt/setuphelfer anfordern.",
            "commands": [],
        }
    if restart_required:
        return {
            "type": "restart_required",
            "label": "Runtime meldet manuellen Neustartbedarf.",
            "commands": [],
        }
    return {"type": "none", "label": "Kein Deploy erforderlich.", "commands": []}


def build_deploy_job_state() -> dict[str, Any]:
    generated_at = _now_iso()
    paths = get_deploy_state_paths()
    workspace = paths["workspace"]
    runtime_path = paths["runtime_path"]
    runtime_gate = _run_runtime_gate(workspace)

    deploy_drift_raw = _compute_deploy_drift(workspace_root=workspace, runtime_root=runtime_path)
    deploy_drift = {
        "status": _normalize_deploy_drift_status(str(deploy_drift_raw.get("status") or "")),
        "raw_status": str(deploy_drift_raw.get("status") or "unknown"),
        "files": _deploy_drift_files(deploy_drift_raw),
        "suggested_actions": list(deploy_drift_raw.get("suggested_actions") or []),
        "manifest_match": deploy_drift_raw.get("manifest_match"),
        "runtime_root": deploy_drift_raw.get("runtime_root"),
        "workspace_root": deploy_drift_raw.get("workspace_root"),
        "warnings": list(deploy_drift_raw.get("warnings") or []),
    }

    last_job = _read_last_job(paths["state_file"])
    helper = _helper_state()
    git = _git_workspace_detail(workspace)
    dirty_count = _int_or_none(git.get("git_dirty_count"))
    next_action = _next_action(
        runtime_gate=runtime_gate,
        deploy_drift=deploy_drift,
        last_job=last_job,
        helper=helper,
        workspace_dirty_count=dirty_count,
    )

    overall_status = "idle"
    last_status = str(last_job.get("status") or "").lower()
    deploy_exit = _int_or_none(last_job.get("deploy_exit_code"))
    if last_status == "running":
        overall_status = "running"
    elif deploy_exit == 0 and runtime_gate.get("exit_code") == 0:
        overall_status = "success"
    elif last_status in {"failed", "blocked"} or deploy_exit not in {None, 0}:
        overall_status = "failed"
    elif next_action["type"] == "operator_setup_required":
        overall_status = "operator_required"
    elif next_action["type"] in {"deploy_required", "restart_required"}:
        overall_status = "blocked" if isinstance(dirty_count, int) and dirty_count > 0 else "ready"
    elif runtime_gate.get("status") == "red":
        overall_status = "blocked"

    return {
        "status": overall_status,
        "generated_at": generated_at,
        "workspace": str(workspace),
        "runtime_path": str(runtime_path),
        "workspace_head": git.get("git_head"),
        "workspace_branch": git.get("git_branch"),
        "workspace_dirty_count": dirty_count,
        "runtime_gate": runtime_gate,
        "deploy_drift": deploy_drift,
        "last_job": last_job,
        "helper": helper,
        "next_action": next_action,
        "state_file": str(paths["state_file"]),
        "log_file": str(paths["log_file"]),
    }
