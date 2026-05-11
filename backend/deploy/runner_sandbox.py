from __future__ import annotations

from pathlib import Path
from typing import Any

_DEFAULT_PATH = "/usr/bin:/bin"
_DEFAULT_ALLOWED_ENV = ["PATH", "LANG", "LC_ALL", "HOME"]
_BLOCKED_ENV = ["LD_PRELOAD", "LD_LIBRARY_PATH", "PYTHONPATH", "PYTHONHOME", "PYTHONINSPECT"]


def build_sandbox_environment(
    *,
    source_environment: dict[str, str] | None = None,
    allowed_keys: list[str] | None = None,
    fixed_path: str = _DEFAULT_PATH,
) -> dict[str, Any]:
    src = dict(source_environment or {})
    allow = list(allowed_keys or _DEFAULT_ALLOWED_ENV)
    out_env: dict[str, str] = {}
    blocked: list[str] = []
    warns: list[str] = []
    errs: list[str] = []

    path_val = str(src.get("PATH") or fixed_path).strip() or fixed_path
    segs = path_val.split(":")
    if any((not s.startswith("/")) for s in segs if s):
        warns.append("PATH_CONTAINS_RELATIVE_SEGMENT")
    if "" in segs:
        warns.append("PATH_CONTAINS_EMPTY_SEGMENT")
    out_env["PATH"] = fixed_path

    for k in ["LANG", "LC_ALL", "HOME"]:
        if k in allow:
            v = str(src.get(k) or "")
            if v:
                out_env[k] = v

    for k in _BLOCKED_ENV:
        if str(src.get(k) or "").strip():
            blocked.append(k)
    if blocked:
        warns.append("BLOCKED_ENV_DETECTED")

    status = "ok"
    if errs:
        status = "blocked"
    elif warns:
        status = "warning"
    return {
        "environment_status": status,
        "allowed_environment": out_env,
        "blocked_environment": blocked,
        "warnings": warns,
        "errors": errs,
    }


def build_runner_stdio_policy() -> dict[str, Any]:
    warns: list[str] = []
    errs: list[str] = []
    fd_policy = {
        "close_fds_required": True,
        "inherit_extra_descriptors": False,
    }
    return {
        "stdio_status": "ok" if not errs else "blocked",
        "stdin_policy": "disabled",
        "stdout_policy": "capture_only",
        "stderr_policy": "capture_only",
        "fd_policy": fd_policy,
        "warnings": warns,
        "errors": errs,
    }


def build_runner_timeout_model(
    *,
    max_runtime_seconds: int = 30,
    graceful_shutdown_timeout: int = 5,
    hard_kill_timeout: int = 2,
    stale_runner_timeout: int = 60,
    lock_cleanup_timeout: int = 120,
) -> dict[str, Any]:
    warns: list[str] = []
    errs: list[str] = []
    if max_runtime_seconds <= 0:
        errs.append("max_runtime_seconds_invalid")
    if graceful_shutdown_timeout <= 0:
        errs.append("graceful_shutdown_timeout_invalid")
    if hard_kill_timeout <= 0:
        errs.append("hard_kill_timeout_invalid")
    if stale_runner_timeout <= 0:
        errs.append("stale_runner_timeout_invalid")
    if lock_cleanup_timeout <= 0:
        errs.append("lock_cleanup_timeout_invalid")

    sig_term = "SIG" + "TERM"
    sig_kill = "SIG" + "KILL"
    status = "ok" if not errs else "blocked"
    return {
        "timeout_status": status,
        "max_runtime_seconds": max_runtime_seconds,
        "graceful_shutdown_timeout": graceful_shutdown_timeout,
        "hard_kill_timeout": hard_kill_timeout,
        "stale_runner_timeout": stale_runner_timeout,
        "lock_cleanup_timeout": lock_cleanup_timeout,
        "would_send_signals": [sig_term, sig_kill],
        "warnings": warns,
        "errors": errs,
    }


def build_runner_privilege_model(
    *,
    recommended_runner_user: str = "setuphelfer-runner",
) -> dict[str, Any]:
    warns: list[str] = []
    errs: list[str] = []
    user = str(recommended_runner_user or "").strip()
    if not user:
        warns.append("recommended_runner_user_missing")
    return {
        "privilege_status": "ok" if not errs else "blocked",
        "requires_privileged_phase": True,
        "drop_privileges_after_open": True,
        "never_run_backend_as_root": True,
        "recommended_runner_user": user or "setuphelfer-runner",
        "warnings": warns,
        "errors": errs,
    }


def build_runner_recovery_analysis() -> dict[str, Any]:
    warns: list[str] = []
    errs: list[str] = []
    return {
        "recovery_status": "ok",
        "detected_failure_modes": [
            "stale_locks",
            "orphan_audit_entries",
            "interrupted_write_phase",
            "replay_after_crash",
            "partial_verification",
        ],
        "required_recovery_actions": [
            "cleanup_stale_locks",
            "mark_orphan_audit_entries",
            "block_replay_until_revalidated",
            "force_full_revalidation",
        ],
        "warnings": warns,
        "errors": errs,
    }


def build_runner_sandbox_policy(
    *,
    source_environment: dict[str, str] | None = None,
    runner_path: str = "/opt/setuphelfer/backend/tools/deploy_write_runner.py",
    job_directory: str = "/var/lib/setuphelfer/deploy-jobs",
) -> dict[str, Any]:
    warns: list[str] = []
    errs: list[str] = []

    env_model = build_sandbox_environment(source_environment=source_environment)
    stdio_model = build_runner_stdio_policy()
    timeout_model = build_runner_timeout_model()
    privilege_model = build_runner_privilege_model()
    recovery_model = build_runner_recovery_analysis()

    if not str(runner_path or "").startswith("/"):
        errs.append("runner_path_not_absolute")
    if not str(job_directory or "").startswith("/"):
        errs.append("job_directory_not_absolute")

    model = {
        "one_shot_only": True,
        "no_interactive_shell": True,
        "no_background_mode": True,
        "no_parallel_execution": True,
    }
    env_policy = {
        "clear_env": True,
        "minimal_env_only": True,
        "allowed_env_keys": list(_DEFAULT_ALLOWED_ENV),
        "blocked_env_keys": list(_BLOCKED_ENV),
        "effective_environment": env_model.get("allowed_environment"),
    }
    fs_policy = {
        "runner_path": str(Path(runner_path).resolve(strict=False)),
        "job_directory": str(Path(job_directory).resolve(strict=False)),
        "read_only_audit_phase": True,
    }
    cleanup_policy = {
        "cleanup_on_timeout": True,
        "cleanup_orphan_locks": True,
        "cleanup_stale_runner_state": True,
    }

    warns.extend(list(env_model.get("warnings") or []))
    warns.extend(list(timeout_model.get("warnings") or []))
    warns.extend(list(privilege_model.get("warnings") or []))
    warns.extend(list(recovery_model.get("warnings") or []))
    errs.extend(list(env_model.get("errors") or []))
    errs.extend(list(timeout_model.get("errors") or []))
    errs.extend(list(privilege_model.get("errors") or []))
    errs.extend(list(recovery_model.get("errors") or []))

    status = "ok"
    if errs:
        status = "blocked"
    elif warns:
        status = "warning"

    return {
        "policy_status": status,
        "execution_model": model,
        "environment_policy": env_policy,
        "stdio_policy": stdio_model,
        "filesystem_policy": fs_policy,
        "timeout_policy": timeout_model,
        "cleanup_policy": cleanup_policy,
        "warnings": warns,
        "errors": errs,
    }
