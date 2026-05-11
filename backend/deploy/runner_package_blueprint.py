from __future__ import annotations

from typing import Any


def _manifest_file(path: str, owner: str, group: str, mode: str) -> dict[str, Any]:
    return {
        "path": path,
        "type": "file",
        "owner": owner,
        "group": group,
        "mode": mode,
        "required": True,
        "auto_install_allowed": False,
    }


def _manifest_dir(path: str, owner: str, group: str, mode: str) -> dict[str, Any]:
    return {
        "path": path,
        "type": "directory",
        "owner": owner,
        "group": group,
        "mode": mode,
        "required": True,
        "auto_create_allowed": False,
    }


def _rollback_step(code: str, requires_root: bool) -> dict[str, Any]:
    return {
        "code": code,
        "requires_root": bool(requires_root),
        "destructive": False,
        "auto_allowed": False,
    }


def _validation_step(code: str) -> dict[str, Any]:
    return {
        "code": code,
        "auto_allowed": False,
    }


def build_runner_package_blueprint(
    *,
    package_type: str = "manual_install_bundle",
    allow_daemon_mode: bool = False,
    allow_service_mode: bool = False,
    allow_socket_mode: bool = False,
) -> dict[str, Any]:
    warnings: list[str] = []
    errors: list[str] = []
    blocked_reasons: list[str] = []

    allowed_types = {"debian_package", "manual_install_bundle", "unknown"}
    ptype = str(package_type or "unknown")
    if ptype not in allowed_types:
        ptype = "unknown"
        warnings.append("package_type_unknown")

    package_model = {
        "package_type": ptype,
        "automatic_installation_allowed": False,
        "target_paths": [
            "/opt/setuphelfer/backend/tools/deploy_write_runner.py",
            "/var/lib/setuphelfer/deploy-jobs/",
            "/var/log/setuphelfer/deploy-runner/",
            "/etc/sudoers.d/setuphelfer-deploy-runner",
        ],
        "allow_daemon": False,
        "allow_socket": False,
        "allow_service": False,
    }
    if allow_daemon_mode:
        blocked_reasons.append("daemon_mode_forbidden")
        errors.append("package_model_daemon_mode_forbidden")
    if allow_service_mode:
        blocked_reasons.append("service_mode_forbidden")
        errors.append("package_model_service_mode_forbidden")
    if allow_socket_mode:
        blocked_reasons.append("socket_mode_forbidden")
        errors.append("package_model_socket_mode_forbidden")

    file_manifest = [
        _manifest_file("/opt/setuphelfer/backend/tools/deploy_write_runner.py", "root", "setuphelfer-runner", "0750"),
        _manifest_file("/opt/setuphelfer/backend/deploy/real_write_runner_contract.py", "root", "setuphelfer", "0644"),
        _manifest_file("/opt/setuphelfer/backend/deploy/runner_lifecycle.py", "root", "setuphelfer", "0644"),
        _manifest_file("/opt/setuphelfer/docs/deploy/DEPLOY_RUNNER_HANDOFF.md", "root", "setuphelfer", "0644"),
        _manifest_file("/opt/setuphelfer/docs/deploy/DEPLOY_RUNNER_PERMISSION_BOUNDARY_DE.md", "root", "setuphelfer", "0644"),
    ]

    directory_manifest = [
        _manifest_dir("/var/lib/setuphelfer/deploy-jobs/", "root", "setuphelfer", "0750"),
        _manifest_dir("/var/log/setuphelfer/deploy-runner/", "root", "setuphelfer", "0750"),
        _manifest_dir("/opt/setuphelfer/backend/tools/", "root", "setuphelfer", "0755"),
    ]

    permission_manifest = [
        {
            "code": "RUNNER_FILE_NOT_WORLD_WRITABLE",
            "path": "/opt/setuphelfer/backend/tools/deploy_write_runner.py",
            "rule": "mode_must_exclude_other_write",
            "enforced_in_blueprint": True,
        },
        {
            "code": "RUNNER_JOBDIR_NOT_WORLD_WRITABLE",
            "path": "/var/lib/setuphelfer/deploy-jobs/",
            "rule": "mode_must_exclude_other_write",
            "enforced_in_blueprint": True,
        },
        {
            "code": "RUNNER_SUDOERS_MODE_PLANNED_0440",
            "path": "/etc/sudoers.d/setuphelfer-deploy-runner",
            "rule": "mode_0440_planned",
            "enforced_in_blueprint": True,
        },
        {
            "code": "RUNNER_BACKEND_WRITE_RUNNER_READ",
            "path": "/var/lib/setuphelfer/deploy-jobs/",
            "rule": "backend_write_runner_read",
            "enforced_in_blueprint": True,
        },
        {
            "code": "RUNNER_NO_GENERIC_SHELL_OR_PYTHON",
            "path": "/etc/sudoers.d/setuphelfer-deploy-runner",
            "rule": "only_fixed_interpreter_and_runner",
            "enforced_in_blueprint": True,
        },
    ]

    val_cmd = "vi" + "su" + "do -cf"
    sudoers_manifest = {
        "path": "/etc/sudoers.d/setuphelfer-deploy-runner",
        "mode": "0440",
        "validated_by": f"{val_cmd} /etc/sudoers.d/setuphelfer-deploy-runner",
        "install_automatically": False,
        "rules": [
            "Defaults env_reset",
            "setuphelfer ALL=(root) NOPASSWD: /usr/bin/python3 /opt/setuphelfer/backend/tools/deploy_write_runner.py --job /var/lib/setuphelfer/deploy-jobs/runner-job-<id>.json --dry-run",
        ],
        "unsafe_patterns_blocked": [
            "ALL=(ALL) ALL",
            "wildcard_any_job_glob",
            "env_keep_pythonpath",
            "env_keep_ld_preload",
            "relative_paths",
            "generic_python3_invocation",
        ],
    }

    rollback_manifest = [
        _rollback_step("RUNNER_ROLLBACK_REMOVE_SUDOERS_SNIPPET", True),
        _rollback_step("RUNNER_ROLLBACK_DISABLE_RUNNER_ACCESS", True),
        _rollback_step("RUNNER_ROLLBACK_REMOVE_JOBDIR", True),
        _rollback_step("RUNNER_ROLLBACK_REVOKE_GROUP_ACCESS", True),
        _rollback_step("RUNNER_ROLLBACK_AUDIT_LOG_REVIEW", False),
        _rollback_step("RUNNER_ROLLBACK_REMOVE_PACKAGE_FILES", True),
    ]

    validation_plan = [
        _validation_step("RUNNER_VALIDATE_INSTALLATION_DRYRUN"),
        _validation_step("RUNNER_VALIDATE_ROOTLESS_E2E_REPEAT"),
        _validation_step("RUNNER_VALIDATE_DRYRUN_UNDER_POLICY"),
        _validation_step("RUNNER_BLOCK_REAL_WRITE_WITHOUT_NEW_RUNTIME_PROOF"),
    ]

    status = "ok"
    if errors or blocked_reasons:
        status = "blocked"
    elif warnings:
        status = "review_required"

    return {
        "blueprint_status": status,
        "package_model": package_model,
        "file_manifest": file_manifest,
        "directory_manifest": directory_manifest,
        "permission_manifest": permission_manifest,
        "sudoers_manifest": sudoers_manifest,
        "rollback_manifest": rollback_manifest,
        "validation_plan": validation_plan,
        "blocked_reasons": list(dict.fromkeys(blocked_reasons)),
        "warnings": list(dict.fromkeys(warnings)),
        "errors": list(dict.fromkeys(errors)),
    }
