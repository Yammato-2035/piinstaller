from __future__ import annotations

import stat
from pathlib import Path
from typing import Any

from deploy.runner_permission_boundary import audit_runner_environment
from deploy.runner_sandbox import build_sandbox_environment

_DEFAULT_RUNNER_PATH = "/opt/setuphelfer/backend/tools/deploy_write_runner.py"
_DEFAULT_INTERPRETER_PATH = "/usr/bin/python3"
_DEFAULT_JOB_PATH = "/var/lib/setuphelfer/deploy-jobs"
_DEFAULT_ALLOWED_PREFIXES = ["/var/lib/setuphelfer"]
_DEFAULT_ROLLBACK_CODES = [
    "RUNNER_ROLLBACK_REMOVE_SUDOERS_SNIPPET",
    "RUNNER_ROLLBACK_DISABLE_RUNNER_ACCESS",
    "RUNNER_ROLLBACK_REMOVE_JOBDIR",
    "RUNNER_ROLLBACK_REVOKE_GROUP_ACCESS",
    "RUNNER_ROLLBACK_AUDIT_LOG_REVIEW",
]


def _is_world_writable(path: Path) -> bool:
    try:
        mode = path.stat().st_mode
    except OSError:
        return False
    ww = bool(mode & stat.S_IWOTH)
    sticky = bool(mode & stat.S_ISVTX)
    return ww and not sticky


def _collect_world_writable_ancestors(path: Path) -> list[str]:
    out: list[str] = []
    cur = path
    seen: set[str] = set()
    while True:
        key = str(cur)
        if key in seen:
            break
        seen.add(key)
        if _is_world_writable(cur):
            out.append(str(cur))
        if cur.parent == cur:
            break
        cur = cur.parent
    return out


def _check_runner_binary(path: str, interpreter_path: str) -> dict[str, Any]:
    warns: list[str] = []
    errs: list[str] = []
    out: dict[str, Any] = {
        "target_path": path,
        "interpreter_path": interpreter_path,
        "exists": False,
        "is_file": False,
        "is_symlink": False,
        "parent_world_writable": [],
        "marker_detected": False,
        "warnings": warns,
        "errors": errs,
    }
    p = Path(str(path or "").strip())
    ip = Path(str(interpreter_path or "").strip())
    if not p.is_absolute():
        errs.append("runner_path_not_absolute")
        return out
    if not ip.is_absolute():
        errs.append("interpreter_path_not_absolute")
    out["exists"] = p.exists()
    out["is_file"] = p.is_file()
    out["is_symlink"] = p.is_symlink()
    if not out["exists"]:
        warns.append("runner_path_missing")
    elif not out["is_file"]:
        errs.append("runner_path_not_file")
    if out["is_symlink"]:
        errs.append("runner_path_symlink")
    ww = _collect_world_writable_ancestors(p.parent)
    out["parent_world_writable"] = ww
    if ww:
        errs.append("runner_parent_world_writable")
    if ip.exists():
        out["interpreter_exists"] = True
    else:
        out["interpreter_exists"] = False
        warns.append("interpreter_path_missing")
    if out["exists"] and out["is_file"]:
        name_ok = "deploy_write_runner.py" in p.name
        marker_ok = False
        try:
            txt = p.read_text(encoding="utf-8", errors="ignore")
            marker_ok = ("deploy_write_runner" in txt) or ("runner" in txt and "dry" in txt)
        except OSError:
            warns.append("runner_file_read_failed")
        out["marker_detected"] = bool(name_ok or marker_ok)
        if not out["marker_detected"]:
            warns.append("runner_marker_missing")
    return out


def _check_job_directory(path: str, allowed_prefixes: list[str] | None) -> dict[str, Any]:
    warns: list[str] = []
    errs: list[str] = []
    p = Path(str(path or "").strip())
    out: dict[str, Any] = {
        "target_path": str(path or ""),
        "exists": False,
        "is_dir": False,
        "is_symlink": False,
        "allowed_prefixes": list(allowed_prefixes or _DEFAULT_ALLOWED_PREFIXES),
        "parent_world_writable": [],
        "warnings": warns,
        "errors": errs,
    }
    if not p.is_absolute():
        errs.append("jobdir_not_absolute")
        return out
    out["exists"] = p.exists()
    out["is_symlink"] = p.is_symlink()
    if out["is_symlink"]:
        errs.append("jobdir_symlink")
    if not out["exists"]:
        warns.append("jobdir_missing")
        return out
    out["is_dir"] = p.is_dir()
    if not out["is_dir"]:
        errs.append("jobdir_not_directory")

    resolved = p.resolve(strict=False)
    allowed = [Path(x).resolve(strict=False) for x in (allowed_prefixes or _DEFAULT_ALLOWED_PREFIXES)]
    prefix_ok = False
    for pref in allowed:
        try:
            resolved.relative_to(pref)
            prefix_ok = True
            break
        except ValueError:
            continue
    if not prefix_ok:
        errs.append("jobdir_outside_allowed_prefix")
    ww = _collect_world_writable_ancestors(resolved)
    out["parent_world_writable"] = ww
    if ww:
        errs.append("jobdir_parent_world_writable")
    return out


def _check_snippet(snippet_text: str, runner_path: str, interpreter_path: str) -> dict[str, Any]:
    warns: list[str] = []
    errs: list[str] = []
    txt = str(snippet_text or "")
    low = txt.lower()
    out = {
        "provided": bool(txt.strip()),
        "contains_env_reset": "env_reset" in low,
        "warnings": warns,
        "errors": errs,
    }
    if not out["provided"]:
        warns.append("snippet_missing")
        return out
    if "env_reset" not in low:
        errs.append("snippet_missing_env_reset")
    if "all=(all) all" in low:
        errs.append("snippet_overbroad_all_all")
    if ("pythonpath" in low) or ("ld_preload" in low):
        errs.append("snippet_contains_loader_or_import_injection")
    if "env_keep" in low:
        errs.append("snippet_uses_env_keep")
    if "*" in txt:
        errs.append("snippet_contains_wildcard")
    if ("nopasswd:" in low) and (runner_path not in txt):
        errs.append("snippet_nopasswd_without_runner_binding")
    if "/usr/bin/python3" not in txt and interpreter_path not in txt:
        errs.append("snippet_missing_fixed_interpreter")
    if runner_path not in txt:
        errs.append("snippet_missing_fixed_runner_path")
    if "python3 " in low and runner_path not in txt:
        errs.append("snippet_generic_python_invocation")
    if "../" in txt or " ./ " in f" {txt} ":
        errs.append("snippet_contains_relative_paths")
    return out


def _rollback_entry(code: str) -> dict[str, Any]:
    return {"code": code, "documented": True, "auto_allowed": False}


def _check_rollback(install_plan: dict[str, Any]) -> dict[str, Any]:
    warns: list[str] = []
    errs: list[str] = []
    configured = install_plan.get("rollback_steps")
    steps = configured if isinstance(configured, list) else [_rollback_entry(c) for c in _DEFAULT_ROLLBACK_CODES]
    codes = [str((x or {}).get("code") or "") for x in steps if isinstance(x, dict)]
    missing = [c for c in _DEFAULT_ROLLBACK_CODES if c not in codes]
    if missing:
        errs.append("rollback_steps_missing")
    for step in steps:
        if not isinstance(step, dict):
            errs.append("rollback_entry_invalid")
            continue
        if bool(step.get("auto_allowed")):
            errs.append("rollback_auto_not_allowed")
    return {"required_codes": list(_DEFAULT_ROLLBACK_CODES), "steps": steps, "warnings": warns, "errors": errs}


def validate_runner_installation_dryrun(
    *,
    install_plan: dict[str, Any] | None = None,
    sudoers_snippet_text: str = "",
    environment: dict[str, str] | None = None,
) -> dict[str, Any]:
    plan = dict(install_plan or {})
    runner_path = str(((plan.get("runner_binary") or {}).get("target_path")) or _DEFAULT_RUNNER_PATH)
    interpreter_path = str(((plan.get("runner_binary") or {}).get("interpreter_path")) or _DEFAULT_INTERPRETER_PATH)
    job_path = str(((plan.get("job_directory") or {}).get("target_path")) or _DEFAULT_JOB_PATH).rstrip("/")
    allowed_prefixes = list((plan.get("job_directory") or {}).get("allowed_prefixes") or _DEFAULT_ALLOWED_PREFIXES)

    runner_binary_check = _check_runner_binary(runner_path, interpreter_path)
    job_directory_check = _check_job_directory(job_path, allowed_prefixes)
    sudoers_snippet_check = _check_snippet(sudoers_snippet_text, runner_path, interpreter_path)

    env_src = dict(environment or {})
    env_audit = audit_runner_environment(env_src)
    env_sandbox = build_sandbox_environment(source_environment=env_src)
    environment_check = {
        "boundary_audit": env_audit,
        "sandbox_audit": env_sandbox,
        "warnings": list(env_audit.get("warnings") or []) + list(env_sandbox.get("warnings") or []),
        "errors": list(env_audit.get("errors") or []) + list(env_sandbox.get("errors") or []),
    }
    if "PATH_EMPTY" in environment_check["warnings"]:
        environment_check["errors"].append("path_empty")

    rollback_check = _check_rollback(plan)
    required_manual_actions = [
        {"code": "RUNNER_INSTALL_CREATE_JOBDIR", "auto_allowed": False},
        {"code": "RUNNER_INSTALL_INSTALL_SUDOERS_SNIPPET", "auto_allowed": False},
        {"code": "RUNNER_INSTALL_RUN_DRYRUN", "auto_allowed": False},
    ]

    warnings: list[str] = []
    errors: list[str] = []
    blocked_reasons: list[str] = []

    for section in [runner_binary_check, job_directory_check, sudoers_snippet_check, environment_check, rollback_check]:
        warnings.extend(list(section.get("warnings") or []))
        errors.extend(list(section.get("errors") or []))

    if "runner_path_symlink" in (runner_binary_check.get("errors") or []):
        blocked_reasons.append("runner_binary_symlink")
    if "jobdir_symlink" in (job_directory_check.get("errors") or []):
        blocked_reasons.append("jobdir_symlink")
    if any(x.startswith("snippet_") for x in list(sudoers_snippet_check.get("errors") or [])):
        blocked_reasons.append("snippet_not_secure")
    if "LD_PRELOAD_SET" in list((environment_check.get("boundary_audit") or {}).get("errors") or []):
        blocked_reasons.append("env_ld_preload")

    status = "ok"
    if blocked_reasons or errors:
        status = "blocked"
    elif warnings:
        status = "review_required"

    # Fehlende Pfade sollen review_required statt blocked sein.
    missing_only = set(errors).issubset({"path_empty"}) and (bool(warnings) or not errors)
    if status == "blocked":
        runner_missing = "runner_path_missing" in warnings and "runner_path_not_file" not in errors and "runner_path_symlink" not in errors
        job_missing = "jobdir_missing" in warnings and "jobdir_symlink" not in errors and "jobdir_not_directory" not in errors
        if (runner_missing or job_missing or missing_only) and not blocked_reasons:
            status = "review_required"

    return {
        "validation_status": status,
        "runner_binary_check": runner_binary_check,
        "job_directory_check": job_directory_check,
        "sudoers_snippet_check": sudoers_snippet_check,
        "environment_check": environment_check,
        "rollback_check": rollback_check,
        "required_manual_actions": required_manual_actions,
        "blocked_reasons": list(dict.fromkeys(blocked_reasons)),
        "warnings": list(dict.fromkeys(warnings)),
        "errors": list(dict.fromkeys(errors)),
    }
