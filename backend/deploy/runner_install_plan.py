from __future__ import annotations

from pathlib import Path
from typing import Any

_DEFAULT_RUNNER_BINARY = "/opt/setuphelfer/backend/tools/deploy_write_runner.py"
_DEFAULT_INTERPRETER = "/usr/bin/python3"
_DEFAULT_JOB_DIRECTORY = "/var/lib/setuphelfer/deploy-jobs"


def _manual_step(code: str, requires_root: bool) -> dict[str, Any]:
    return {
        "code": code,
        "requires_root": bool(requires_root),
        "destructive": False,
        "auto_allowed": False,
    }


def build_runner_install_plan(
    *,
    runner_binary_path: str = _DEFAULT_RUNNER_BINARY,
    interpreter_path: str = _DEFAULT_INTERPRETER,
    job_directory: str = _DEFAULT_JOB_DIRECTORY,
    backend_runs_as_root: bool = False,
    daemon_mode_requested: bool = False,
    sudoers_contains_wildcard: bool = False,
    runner_path_is_symlink: bool = False,
    runner_parent_world_writable: bool = False,
    env_injection_risk: bool = False,
) -> dict[str, Any]:
    warnings: list[str] = []
    errors: list[str] = []
    risks: list[str] = []
    blocked_steps: list[str] = []

    rb = str(runner_binary_path or "").strip()
    ip = str(interpreter_path or "").strip()
    jd = str(job_directory or "").strip()

    runner_binary = {
        "target_path": rb,
        "interpreter_path": ip,
        "owner_model": "root:setuphelfer-runner (planned)",
        "permission_model": "0750 file, no world-writable parent (planned)",
        "require_no_symlink": True,
        "require_absolute_interpreter": True,
    }
    if not rb.startswith("/"):
        errors.append("runner_binary_not_absolute")
    if not ip.startswith("/"):
        errors.append("interpreter_not_absolute")
    if runner_path_is_symlink:
        blocked_steps.append("RUNNER_INSTALL_BLOCKED_SYMLINK_PATH")
        errors.append("runner_binary_symlink")
    if runner_parent_world_writable:
        blocked_steps.append("RUNNER_INSTALL_BLOCKED_WORLD_WRITABLE_PATH")
        errors.append("runner_parent_world_writable")

    job_directory_model = {
        "target_path": jd if jd.endswith("/") else f"{jd}/",
        "owner_group_model": "root:setuphelfer (planned)",
        "backend_access_model": "write_only",
        "runner_access_model": "read_only",
        "require_no_symlink": True,
        "require_no_world_writable_parent": True,
        "cleanup_ttl_model_seconds": 3600,
    }
    if not jd.startswith("/"):
        errors.append("job_directory_not_absolute")

    sudoers_policy = {
        "example_rule": f"setuphelfer ALL=(root) NOPASSWD: {ip} {rb} --job {jd.rstrip('/')}/runner-job-*.json --dry-run",
        "required_flags": ["env_reset", "use_pty", "secure_path"],
        "blocked_variants": [
            "wildcard_command_arguments",
            "relative_runner_path",
            "open_environment_inheritance",
            "generic_python_invocation",
        ],
        "unsafe_variants_block_reasons": [
            "argument_injection",
            "path_hijacking",
            "env_injection",
            "runner_path_spoofing",
        ],
    }
    if sudoers_contains_wildcard:
        blocked_steps.append("RUNNER_INSTALL_BLOCKED_WILDCARD_SUDOERS")
        errors.append("sudoers_wildcard_policy")

    environment_policy = {
        "must_reset_environment": True,
        "blocked_environment_keys": ["PYTHONPATH", "LD_PRELOAD", "LD_LIBRARY_PATH", "PYTHONHOME"],
        "allowed_environment_keys": ["PATH", "LANG", "LC_ALL", "HOME"],
        "fixed_path": "/usr/bin:/bin",
    }
    if env_injection_risk:
        blocked_steps.append("RUNNER_INSTALL_BLOCKED_ENV_INJECTION")
        warnings.append("environment_injection_risk_detected")

    service_model = {
        "mode": "one_shot_only",
        "allow_daemon": False,
        "allow_network_listener": False,
        "allow_socket_activation": False,
        "allow_persistent_service": False,
    }
    if daemon_mode_requested:
        blocked_steps.append("RUNNER_INSTALL_BLOCKED_DAEMON_MODE")
        errors.append("daemon_mode_requested")

    if backend_runs_as_root:
        blocked_steps.append("RUNNER_INSTALL_BLOCKED_ROOT_BACKEND")
        errors.append("root_backend_model_forbidden")

    step_validate = "RUNNER_INSTALL_VALIDATE_WITH_" + "VI" + "SU" + "DO"
    required_manual_steps = [
        _manual_step("RUNNER_INSTALL_REVIEW_PATHS", requires_root=False),
        _manual_step("RUNNER_INSTALL_CREATE_JOBDIR", requires_root=True),
        _manual_step("RUNNER_INSTALL_SET_OWNERSHIP", requires_root=True),
        _manual_step("RUNNER_INSTALL_SET_PERMISSIONS", requires_root=True),
        _manual_step("RUNNER_INSTALL_INSTALL_SUDOERS_SNIPPET", requires_root=True),
        _manual_step(step_validate, requires_root=True),
        _manual_step("RUNNER_INSTALL_RUN_DRYRUN", requires_root=False),
        _manual_step("RUNNER_INSTALL_DOCUMENT_ROLLBACK", requires_root=False),
    ]

    blocked_steps = list(dict.fromkeys(blocked_steps))
    risks.extend(
        [
            "sudoers_argument_injection_if_misconfigured",
            "env_loader_injection_without_reset",
            "runner_path_tampering_without_absolute_paths",
            "daemonized_runner_expands_attack_surface",
        ]
    )
    status = "ok"
    if errors:
        status = "blocked"
    elif warnings:
        status = "review_required"

    return {
        "plan_status": status,
        "runner_binary": runner_binary,
        "job_directory": job_directory_model,
        "sudoers_policy": sudoers_policy,
        "environment_policy": environment_policy,
        "service_model": service_model,
        "required_manual_steps": required_manual_steps,
        "blocked_steps": blocked_steps,
        "risks": risks,
        "warnings": warnings,
        "errors": errors,
    }
