from __future__ import annotations

from typing import Any

_DEFAULT_RUNNER_PATH = "/opt/setuphelfer/backend/tools/deploy_write_runner.py"
_DEFAULT_JOBDIR_PATH = "/var/lib/setuphelfer/deploy-jobs/"
_DEFAULT_SUDOERS_PATH = "/etc/sudoers.d/setuphelfer-deploy-runner"
_DEFAULT_LOGDIR_PATH = "/var/log/setuphelfer/deploy-runner/"
_REQUIRED_ROLLBACK_CODES = [
    "RUNNER_ROLLBACK_REMOVE_SUDOERS_SNIPPET",
    "RUNNER_ROLLBACK_DISABLE_RUNNER_ACCESS",
    "RUNNER_ROLLBACK_REMOVE_JOBDIR",
    "RUNNER_ROLLBACK_REVOKE_GROUP_ACCESS",
    "RUNNER_ROLLBACK_AUDIT_LOG_REVIEW",
]
_REQUIRED_VALIDATION_CODES = [
    "RUNNER_VALIDATE_INSTALLATION_DRYRUN",
    "RUNNER_VALIDATE_ROOTLESS_E2E_REPEAT",
    "RUNNER_VALIDATE_DRYRUN_UNDER_POLICY",
    "RUNNER_BLOCK_REAL_WRITE_WITHOUT_NEW_RUNTIME_PROOF",
]


def _norm_dir(path: str) -> str:
    p = str(path or "").strip()
    if not p:
        return ""
    return p if p.endswith("/") else f"{p}/"


def _is_relative(path: str) -> bool:
    p = str(path or "").strip()
    return bool(p) and not p.startswith("/")


def validate_runner_install_consistency(
    *,
    install_plan: dict[str, Any] | None = None,
    install_validation: dict[str, Any] | None = None,
    package_blueprint: dict[str, Any] | None = None,
) -> dict[str, Any]:
    plan = dict(install_plan or {})
    validation = dict(install_validation or {})
    blueprint = dict(package_blueprint or {})

    mismatches: list[str] = []
    warnings: list[str] = []
    errors: list[str] = []

    plan_runner = str(((plan.get("runner_binary") or {}).get("target_path")) or _DEFAULT_RUNNER_PATH)
    plan_jobdir = _norm_dir(str(((plan.get("job_directory") or {}).get("target_path")) or _DEFAULT_JOBDIR_PATH))
    val_runner = str((((validation.get("runner_binary_check") or {}).get("target_path")) or plan_runner or _DEFAULT_RUNNER_PATH))
    val_jobdir = _norm_dir(str((((validation.get("job_directory_check") or {}).get("target_path")) or plan_jobdir or _DEFAULT_JOBDIR_PATH)))

    bp_target_paths = list((blueprint.get("package_model") or {}).get("target_paths") or [])
    bp_runner = next((str(x) for x in bp_target_paths if "deploy_write_runner.py" in str(x)), _DEFAULT_RUNNER_PATH)
    bp_jobdir = _norm_dir(next((str(x) for x in bp_target_paths if "/deploy-jobs" in str(x)), _DEFAULT_JOBDIR_PATH))
    bp_sudoers = str(((blueprint.get("sudoers_manifest") or {}).get("path")) or _DEFAULT_SUDOERS_PATH)
    bp_logdir = _norm_dir(next((str(x) for x in bp_target_paths if "/deploy-runner/" in str(x)), _DEFAULT_LOGDIR_PATH))

    path_consistency = {
        "runner_path_plan": plan_runner,
        "runner_path_validation": val_runner,
        "runner_path_blueprint": bp_runner,
        "jobdir_plan": plan_jobdir,
        "jobdir_validation": val_jobdir,
        "jobdir_blueprint": bp_jobdir,
        "sudoers_path_blueprint": bp_sudoers,
        "logdir_blueprint": bp_logdir,
    }
    if not (plan_runner == val_runner == bp_runner):
        mismatches.append("RUNNER_CONSISTENCY_PATH_RUNNER_MISMATCH")
    if not (plan_jobdir == val_jobdir == bp_jobdir):
        mismatches.append("RUNNER_CONSISTENCY_PATH_JOBDIR_MISMATCH")
    if bp_sudoers != _DEFAULT_SUDOERS_PATH:
        mismatches.append("RUNNER_CONSISTENCY_PATH_SUDOERS_MISMATCH")
    if bp_logdir != _DEFAULT_LOGDIR_PATH:
        warnings.append("RUNNER_CONSISTENCY_PATH_LOGDIR_REVIEW")
    path_values = [plan_runner, plan_jobdir, val_runner, val_jobdir, bp_runner, bp_jobdir, bp_sudoers, bp_logdir]
    if any(_is_relative(v) for v in path_values):
        mismatches.append("RUNNER_CONSISTENCY_PATH_UNSAFE_PREFIX")
        errors.append("relative_paths_detected")
    if not bp_jobdir.startswith("/var/lib/setuphelfer/"):
        mismatches.append("RUNNER_CONSISTENCY_PATH_UNSAFE_PREFIX")

    perm_codes = {str(x.get("code") or "") for x in list(blueprint.get("permission_manifest") or []) if isinstance(x, dict)}
    permission_consistency = {
        "sudoers_mode": str((blueprint.get("sudoers_manifest") or {}).get("mode") or ""),
        "runner_mode": next((str(x.get("mode") or "") for x in list(blueprint.get("file_manifest") or []) if str(x.get("path") or "").endswith("deploy_write_runner.py")), ""),
        "jobdir_mode": next((str(x.get("mode") or "") for x in list(blueprint.get("directory_manifest") or []) if "/deploy-jobs/" in str(x.get("path") or "")), ""),
        "backend_access_model": str((plan.get("job_directory") or {}).get("backend_access_model") or ""),
        "runner_access_model": str((plan.get("job_directory") or {}).get("runner_access_model") or ""),
        "permission_codes": sorted(perm_codes),
    }
    if permission_consistency["sudoers_mode"] != "0440":
        errors.append("sudoers_mode_mismatch")
    if permission_consistency["runner_mode"] not in {"0750", "0550"}:
        warnings.append("runner_mode_review")
    if permission_consistency["jobdir_mode"] not in {"0750", "0700"}:
        warnings.append("jobdir_mode_review")
    if permission_consistency["backend_access_model"] != "write_only" or permission_consistency["runner_access_model"] != "read_only":
        errors.append("backend_runner_access_model_mismatch")
    for required_code in ["RUNNER_FILE_NOT_WORLD_WRITABLE", "RUNNER_JOBDIR_NOT_WORLD_WRITABLE", "RUNNER_NO_GENERIC_SHELL_OR_PYTHON"]:
        if required_code not in perm_codes:
            errors.append(f"missing_permission_code:{required_code}")

    sp = dict(plan.get("sudoers_policy") or {})
    sm = dict(blueprint.get("sudoers_manifest") or {})
    snippet_check = dict(validation.get("sudoers_snippet_check") or {})
    blocked_patterns = {str(x) for x in list(sm.get("unsafe_patterns_blocked") or [])}
    required_flags = {str(x) for x in list(sp.get("required_flags") or [])}
    sudoers_consistency = {
        "plan_required_flags": sorted(required_flags),
        "blueprint_unsafe_patterns_blocked": sorted(blocked_patterns),
        "validation_contains_env_reset": bool(snippet_check.get("contains_env_reset")),
        "validation_errors": list(snippet_check.get("errors") or []),
    }
    if "env_reset" not in required_flags or not bool(snippet_check.get("contains_env_reset")):
        errors.append("sudoers_env_reset_missing")
    for pat in ["env_keep_pythonpath", "env_keep_ld_preload", "wildcard_any_job_glob", "generic_python3_invocation", "ALL=(ALL) ALL"]:
        if pat not in blocked_patterns:
            errors.append(f"sudoers_unsafe_pattern_missing:{pat}")
    if any(str(x).startswith("snippet_") for x in list(snippet_check.get("errors") or [])):
        errors.append("sudoers_snippet_inconsistent")

    rb_steps = list((blueprint.get("rollback_manifest") or []))
    rb_codes = {str((x or {}).get("code") or "") for x in rb_steps if isinstance(x, dict)}
    rollback_consistency = {
        "required_codes": list(_REQUIRED_ROLLBACK_CODES),
        "present_codes": sorted(rb_codes),
    }
    missing_rb = [c for c in _REQUIRED_ROLLBACK_CODES if c not in rb_codes]
    if missing_rb:
        errors.append("rollback_codes_missing")
        warnings.extend([f"rollback_missing:{c}" for c in missing_rb])
    for step in rb_steps:
        if isinstance(step, dict) and bool(step.get("auto_allowed")):
            errors.append("rollback_auto_allowed_true")

    vp_steps = list((blueprint.get("validation_plan") or []))
    vp_codes = {str((x or {}).get("code") or "") for x in vp_steps if isinstance(x, dict)}
    validation_consistency = {
        "required_codes": list(_REQUIRED_VALIDATION_CODES),
        "present_codes": sorted(vp_codes),
    }
    missing_vp = [c for c in _REQUIRED_VALIDATION_CODES if c not in vp_codes]
    if missing_vp:
        warnings.append("validation_codes_missing")
        warnings.extend([f"validation_missing:{c}" for c in missing_vp])
    for step in vp_steps:
        if isinstance(step, dict) and bool(step.get("auto_allowed")):
            errors.append("validation_auto_allowed_true")

    status = "ok"
    if errors or mismatches:
        status = "blocked"
    elif warnings:
        status = "review_required"

    return {
        "consistency_status": status,
        "path_consistency": path_consistency,
        "permission_consistency": permission_consistency,
        "sudoers_consistency": sudoers_consistency,
        "rollback_consistency": rollback_consistency,
        "validation_consistency": validation_consistency,
        "mismatches": list(dict.fromkeys(mismatches)),
        "warnings": list(dict.fromkeys(warnings)),
        "errors": list(dict.fromkeys(errors)),
    }
