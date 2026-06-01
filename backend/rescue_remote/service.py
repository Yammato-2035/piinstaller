"""Rescue remote control service — allowlisted jobs, JSONL persistence, redaction."""

from __future__ import annotations

import json
import os
import re
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

UTC = timezone.utc

FORBIDDEN_RUNBOOK_IDS = frozenset(
    {
        "shell",
        "arbitrary_command",
        "run_command",
        "write_usb",
        "restore_execute",
        "mount_rw",
        "partition_write",
        "format",
        "dd",
        "mkfs",
        "apt_install",
        "apt_upgrade",
        "remote_shell",
    }
)

ALLOWLISTED_RUNBOOKS: dict[str, dict[str, Any]] = {
    "collect_boot_logs": {
        "description": "journalctl and dmesg excerpts (read-only)",
        "allowed_mode": "read_only",
        "requires_operator_consent": False,
        "dangerous": False,
        "timeout_seconds": 60,
    },
    "collect_network_status": {
        "description": "ip addr/route, nmcli status",
        "allowed_mode": "read_only",
        "requires_operator_consent": False,
        "dangerous": False,
        "timeout_seconds": 30,
    },
    "collect_storage_inventory_readonly": {
        "description": "lsblk and findmnt (read-only)",
        "allowed_mode": "read_only",
        "requires_operator_consent": False,
        "dangerous": False,
        "timeout_seconds": 30,
    },
    "collect_devserver_agent_logs": {
        "description": "Setuphelfer dev-agent journal excerpt",
        "allowed_mode": "diagnostic",
        "requires_operator_consent": False,
        "dangerous": False,
        "timeout_seconds": 45,
    },
    "collect_qemu_or_rescue_agent_status": {
        "description": "Rescue remote agent unit status",
        "allowed_mode": "diagnostic",
        "requires_operator_consent": False,
        "dangerous": False,
        "timeout_seconds": 30,
    },
    "test_devserver_connectivity": {
        "description": "GET /api/version on configured dev server URL",
        "allowed_mode": "diagnostic",
        "requires_operator_consent": False,
        "dangerous": False,
        "timeout_seconds": 20,
    },
    "upload_rescue_evidence_bundle": {
        "description": "Upload pre-built local evidence bundle metadata (no arbitrary paths)",
        "allowed_mode": "diagnostic",
        "requires_operator_consent": True,
        "dangerous": False,
        "timeout_seconds": 120,
    },
}

SECRET_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"(?i)(api[_-]?key|x-api-key)\s*[:=]\s*['\"]?\S+", re.M),
    re.compile(r"(?i)bearer\s+[a-z0-9._\-]+", re.M),
    re.compile(r"(?i)(token|secret|password|psk)\s*[:=]\s*['\"]?\S{4,}", re.M),
    re.compile(r"-----BEGIN[A-Z ]*PRIVATE KEY-----[\s\S]*?-----END[A-Z ]*PRIVATE KEY-----", re.M),
]


class RescueRemoteError(Exception):
    def __init__(self, code: str, errors: list[str] | None = None, http_status: int = 400) -> None:
        super().__init__(code)
        self.code = code
        self.errors = errors or [code]
        self.http_status = http_status


def rescue_remote_enabled() -> bool:
    env = os.environ.get("SETUPHELFER_RESCUE_REMOTE_ENABLED", "").strip().lower()
    if env in {"1", "true", "yes", "on"}:
        return True
    if env in {"0", "false", "no", "off"}:
        return False
    if os.environ.get("PI_INSTALLER_DEV", "").strip().lower() in {"1", "true", "yes"}:
        return True
    if os.environ.get("SETUPHELFER_DEV_AGENT_MODE", "").strip() == "local_lab":
        return True
    return False


def _repo_root(repo_root: Path | None = None) -> Path:
    if repo_root is not None:
        return repo_root.resolve()
    return Path(__file__).resolve().parents[2]


def _store_dir(repo_root: Path | None = None) -> Path:
    root = _repo_root(repo_root)
    custom = os.environ.get("SETUPHELFER_RESCUE_REMOTE_STORE", "").strip()
    if custom:
        return Path(custom).resolve()
    return root / "build/runtime/rescue-remote"


def _append_jsonl(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False) + "\n")


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    out: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out


def _write_agents_snapshot(agents: list[dict[str, Any]], repo_root: Path | None = None) -> None:
    path = _store_dir(repo_root) / "agents.snapshot.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(agents, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _load_agents(repo_root: Path | None = None) -> dict[str, dict[str, Any]]:
    snap = _store_dir(repo_root) / "agents.snapshot.json"
    if snap.is_file():
        try:
            data = json.loads(snap.read_text(encoding="utf-8"))
            if isinstance(data, list):
                return {a["agent_id"]: a for a in data if isinstance(a, dict) and a.get("agent_id")}
        except json.JSONDecodeError:
            pass
    agents: dict[str, dict[str, Any]] = {}
    for rec in _read_jsonl(_store_dir(repo_root) / "agents.jsonl"):
        aid = rec.get("agent_id")
        if aid:
            agents[aid] = rec
    return agents


def _save_agent(agent: dict[str, Any], repo_root: Path | None = None) -> None:
    agents = _load_agents(repo_root)
    agents[agent["agent_id"]] = agent
    _write_agents_snapshot(list(agents.values()), repo_root)
    _append_jsonl(_store_dir(repo_root) / "agents.jsonl", agent)


def _load_jobs(repo_root: Path | None = None) -> dict[str, dict[str, Any]]:
    jobs: dict[str, dict[str, Any]] = {}
    for rec in _read_jsonl(_store_dir(repo_root) / "jobs.jsonl"):
        jid = rec.get("job_id")
        if jid:
            jobs[jid] = rec
    return jobs


def _save_job(job: dict[str, Any], repo_root: Path | None = None) -> None:
    _append_jsonl(_store_dir(repo_root) / "jobs.jsonl", job)


def mask_token(value: str) -> str:
    if not value:
        return ""
    if len(value) <= 8:
        return "***"
    return value[:4] + "…" + value[-2:]


def redact_text(text: str, max_len: int = 8000) -> tuple[str, list[str]]:
    warnings: list[str] = []
    out = text[:max_len]
    for pat in SECRET_PATTERNS:
        if pat.search(out):
            warnings.append("secret_pattern_redacted")
            out = pat.sub("[REDACTED]", out)
    return out, warnings


def redact_agent_public(agent: dict[str, Any]) -> dict[str, Any]:
    pub = dict(agent)
    if pub.get("pairing_token_hint"):
        pub["pairing_token_hint"] = mask_token(str(pub["pairing_token_hint"]))
    sec = dict(pub.get("security") or {})
    sec["remote_shell"] = False
    sec["controlled_write"] = False
    pub["security"] = sec
    return pub


def assert_runbook_allowed(runbook_id: str, mode: str) -> dict[str, Any]:
    rid = (runbook_id or "").strip()
    if not rid:
        raise RescueRemoteError("RESCUE_REMOTE_JOB_BLOCKED", ["empty_runbook_id"], 400)
    if rid in FORBIDDEN_RUNBOOK_IDS:
        raise RescueRemoteError("RESCUE_REMOTE_JOB_BLOCKED", [f"forbidden_runbook:{rid}"], 403)
    meta = ALLOWLISTED_RUNBOOKS.get(rid)
    if not meta:
        raise RescueRemoteError("RESCUE_REMOTE_JOB_BLOCKED", [f"unknown_runbook:{rid}"], 403)
    allowed_mode = meta.get("allowed_mode", "read_only")
    if mode not in (allowed_mode, "read_only", "diagnostic"):
        if mode == "controlled_write":
            raise RescueRemoteError("RESCUE_REMOTE_JOB_BLOCKED", ["controlled_write_disabled"], 403)
        raise RescueRemoteError("RESCUE_REMOTE_JOB_BLOCKED", [f"mode_not_allowed:{mode}"], 403)
    return meta


def register_agent(payload: dict[str, Any], repo_root: Path | None = None) -> dict[str, Any]:
    if payload.get("security", {}).get("remote_shell"):
        raise RescueRemoteError("RESCUE_REMOTE_JOB_BLOCKED", ["remote_shell_disabled"], 403)
    now = datetime.now(UTC)
    token = (payload.get("pairing_token") or "").strip()
    record = {
        "agent_id": payload["agent_id"],
        "boot_id": payload.get("boot_id", ""),
        "session_id": payload.get("session_id", ""),
        "mode": payload.get("mode", "local_lab"),
        "capabilities": payload.get("capabilities", {}),
        "network": payload.get("network", {}),
        "security": {
            **(payload.get("security") or {}),
            "paired": bool(token) or bool((payload.get("security") or {}).get("paired")),
            "remote_shell": False,
            "controlled_write": False,
        },
        "pairing_token_hint": mask_token(token) if token else "",
        "status": "online",
        "registered_at": now.isoformat(),
        "last_heartbeat_at": now.isoformat(),
    }
    _save_agent(record, repo_root)
    return redact_agent_public(record)


def heartbeat_agent(payload: dict[str, Any], repo_root: Path | None = None) -> dict[str, Any]:
    agents = _load_agents(repo_root)
    aid = payload.get("agent_id", "")
    if aid not in agents:
        raise RescueRemoteError("RESCUE_REMOTE_AGENT_NOT_FOUND", [aid], 404)
    agent = agents[aid]
    agent["last_heartbeat_at"] = datetime.now(UTC).isoformat()
    agent["status"] = payload.get("status", "online")
    if payload.get("network"):
        agent["network"] = payload["network"]
    _save_agent(agent, repo_root)
    return redact_agent_public(agent)


def list_agents(repo_root: Path | None = None) -> list[dict[str, Any]]:
    return [redact_agent_public(a) for a in _load_agents(repo_root).values()]


def get_agent(agent_id: str, repo_root: Path | None = None) -> dict[str, Any]:
    agents = _load_agents(repo_root)
    if agent_id not in agents:
        raise RescueRemoteError("RESCUE_REMOTE_AGENT_NOT_FOUND", [agent_id], 404)
    return redact_agent_public(agents[agent_id])


def create_job(payload: dict[str, Any], repo_root: Path | None = None) -> dict[str, Any]:
    aid = payload.get("agent_id", "")
    agents = _load_agents(repo_root)
    if aid not in agents:
        raise RescueRemoteError("RESCUE_REMOTE_AGENT_NOT_FOUND", [aid], 404)
    runbook_id = payload.get("runbook_id", "")
    mode = payload.get("mode", "read_only")
    meta = assert_runbook_allowed(runbook_id, mode)
    if payload.get("command_plan"):
        raise RescueRemoteError("RESCUE_REMOTE_JOB_BLOCKED", ["command_plan_not_allowed"], 403)
    now = datetime.now(UTC)
    timeout = int(payload.get("timeout_seconds") or meta.get("timeout_seconds") or 30)
    job = {
        "job_id": f"job_{uuid.uuid4().hex[:16]}",
        "created_at": now.isoformat(),
        "expires_at": (now + timedelta(seconds=timeout + 120)).isoformat(),
        "agent_id": aid,
        "runbook_id": runbook_id,
        "mode": mode,
        "requires_operator_consent": bool(meta.get("requires_operator_consent")),
        "command_plan": [],
        "timeout_seconds": timeout,
        "redaction": True,
        "status": "queued",
        "result": {
            "exit_code": None,
            "stdout_excerpt": "",
            "stderr_excerpt": "",
            "artifacts": [],
            "warnings": [],
            "errors": [],
        },
    }
    _save_job(job, repo_root)
    return job


def list_jobs(agent_id: str | None = None, repo_root: Path | None = None) -> list[dict[str, Any]]:
    jobs = list(_load_jobs(repo_root).values())
    if agent_id:
        jobs = [j for j in jobs if j.get("agent_id") == agent_id]
    return sorted(jobs, key=lambda j: j.get("created_at", ""), reverse=True)


def claim_job(job_id: str, agent_id: str, repo_root: Path | None = None) -> dict[str, Any]:
    jobs = _load_jobs(repo_root)
    if job_id not in jobs:
        raise RescueRemoteError("RESCUE_REMOTE_JOB_NOT_FOUND", [job_id], 404)
    job = jobs[job_id]
    if job.get("agent_id") != agent_id:
        raise RescueRemoteError("RESCUE_REMOTE_JOB_BLOCKED", ["agent_mismatch"], 403)
    if job.get("status") not in ("queued",):
        raise RescueRemoteError("RESCUE_REMOTE_JOB_BLOCKED", [f"status:{job.get('status')}"], 409)
    job["status"] = "claimed"
    job["claimed_at"] = datetime.now(UTC).isoformat()
    _save_job(job, repo_root)
    jobs[job_id] = job
    return job


def submit_job_result(
    job_id: str, payload: dict[str, Any], repo_root: Path | None = None
) -> dict[str, Any]:
    jobs = _load_jobs(repo_root)
    if job_id not in jobs:
        raise RescueRemoteError("RESCUE_REMOTE_JOB_NOT_FOUND", [job_id], 404)
    job = jobs[job_id]
    if job.get("agent_id") != payload.get("agent_id"):
        raise RescueRemoteError("RESCUE_REMOTE_JOB_BLOCKED", ["agent_mismatch"], 403)
    result = dict(payload.get("result") or {})
    for field in ("stdout_excerpt", "stderr_excerpt"):
        if field in result and isinstance(result[field], str):
            result[field], w = redact_text(result[field])
            result.setdefault("warnings", []).extend(w)
    job["status"] = payload.get("status", "success")
    job["result"] = result
    job["completed_at"] = datetime.now(UTC).isoformat()
    _save_job(job, repo_root)
    return job


def disconnect_agent(payload: dict[str, Any], repo_root: Path | None = None) -> dict[str, Any]:
    aid = payload.get("agent_id", "")
    agents = _load_agents(repo_root)
    if aid not in agents:
        raise RescueRemoteError("RESCUE_REMOTE_AGENT_NOT_FOUND", [aid], 404)
    agent = agents[aid]
    agent["status"] = "offline"
    agent["disconnected_at"] = datetime.now(UTC).isoformat()
    agent["disconnect_reason"] = payload.get("reason", "disconnect")
    _save_agent(agent, repo_root)
    return redact_agent_public(agent)


def get_agent_logs(agent_id: str, repo_root: Path | None = None) -> dict[str, Any]:
    jobs = [j for j in list_jobs(agent_id, repo_root) if j.get("status") in ("success", "failed", "timeout")]
    return {
        "agent_id": agent_id,
        "job_count": len(jobs),
        "jobs": jobs[:50],
    }


def allowlisted_runbook_ids() -> list[str]:
    return sorted(ALLOWLISTED_RUNBOOKS.keys())
