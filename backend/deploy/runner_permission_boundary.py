from __future__ import annotations

import os
from pathlib import Path
from typing import Any

_DEFAULT_RUNNER_PATH = "/opt/setuphelfer/backend/tools/deploy_write_runner.py"
_DEFAULT_JOB_DIRECTORY = "/var/lib/setuphelfer/deploy-jobs"
_DEFAULT_ALLOWED_ENVIRONMENT = ["LANG", "LC_ALL", "PATH", "HOME"]
_DEFAULT_BLOCKED_ENVIRONMENT = ["PYTHONPATH", "LD_PRELOAD", "LD_LIBRARY_PATH"]
_REQUIRED_RESTRICTIONS = [
    "RUNNER_REQUIRE_ABSOLUTE_PATH",
    "RUNNER_REQUIRE_FIXED_JOB_DIRECTORY",
    "RUNNER_REQUIRE_ENV_RESET",
    "RUNNER_BLOCK_PYTHONPATH",
    "RUNNER_BLOCK_LD_PRELOAD",
    "RUNNER_BLOCK_DYNAMIC_PATH",
    "RUNNER_BLOCK_WILDCARDS",
    "RUNNER_REQUIRE_NOINTERACTIVE",
    "RUNNER_REQUIRE_NO_SHELL",
]


def _is_world_writable(path: Path) -> bool:
    try:
        mode = path.stat().st_mode
    except OSError:
        return False
    world_writable = bool(mode & 0o002)
    sticky = bool(mode & 0o1000)
    # /tmp-artige Verzeichnisse mit sticky bit sind erwartbar und weniger riskant.
    return world_writable and not sticky


def _collect_world_writable_ancestors(path: Path) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    cur = path
    while True:
        key = str(cur)
        if key in seen:
            break
        seen.add(key)
        if _is_world_writable(cur):
            out.append(str(cur))
        parent = cur.parent
        if parent == cur:
            break
        cur = parent
    return out


def build_runner_sudoers_policy_example(
    *,
    allowed_runner_path: str = _DEFAULT_RUNNER_PATH,
    allowed_job_directory: str = _DEFAULT_JOB_DIRECTORY,
    allowed_environment: list[str] | None = None,
) -> dict[str, Any]:
    warns: list[str] = []
    errs: list[str] = []
    aenv = list(allowed_environment or _DEFAULT_ALLOWED_ENVIRONMENT)
    blocked = list(_DEFAULT_BLOCKED_ENVIRONMENT)

    rpath = str(allowed_runner_path or "").strip()
    jdir = str(allowed_job_directory or "").strip()
    if not rpath.startswith("/"):
        errs.append("runner_path_not_absolute")
    if not jdir.startswith("/"):
        errs.append("job_directory_not_absolute")
    if "*" in rpath or "*" in jdir:
        errs.append("wildcard_in_policy_paths")
    if "PYTHONPATH" in aenv:
        warns.append("allowed_environment_contains_pythonpath")
    if "LD_PRELOAD" in aenv:
        errs.append("allowed_environment_contains_ld_preload")

    status = "ok"
    if errs:
        status = "blocked"
    elif warns:
        status = "warning"

    return {
        "policy_status": status,
        "allowed_runner_path": rpath,
        "allowed_job_directory": jdir,
        "allowed_environment": aenv,
        "blocked_environment": blocked,
        "required_restrictions": list(_REQUIRED_RESTRICTIONS),
        "warnings": warns,
        "errors": errs,
    }


def audit_runner_environment(env: dict[str, str] | None = None) -> dict[str, Any]:
    src: dict[str, str] = dict(os.environ if env is None else env)
    detected: list[str] = []
    blocked: list[str] = []
    warns: list[str] = []
    errs: list[str] = []

    keys = ["PATH", "PYTHONPATH", "LD_PRELOAD", "LD_LIBRARY_PATH", "VIRTUAL_ENV"] + sorted(
        [k for k in src.keys() if k.startswith("SUDO_")]
    )
    seen: set[str] = set()
    for k in keys:
        if k in seen:
            continue
        seen.add(k)
        if k in src:
            detected.append(k)

    path = str(src.get("PATH") or "")
    if not path:
        warns.append("PATH_EMPTY")
    else:
        segs = path.split(":")
        if "" in segs:
            warns.append("PATH_CONTAINS_EMPTY_SEGMENT")
        rel = [s for s in segs if s and not s.startswith("/")]
        if rel:
            warns.append("PATH_CONTAINS_RELATIVE_SEGMENT")

    if str(src.get("PYTHONPATH") or "").strip():
        blocked.append("PYTHONPATH")
        warns.append("PYTHONPATH_SET")
    if str(src.get("LD_PRELOAD") or "").strip():
        blocked.append("LD_PRELOAD")
        errs.append("LD_PRELOAD_SET")
    if str(src.get("LD_LIBRARY_PATH") or "").strip():
        blocked.append("LD_LIBRARY_PATH")
        warns.append("LD_LIBRARY_PATH_SET")

    status = "ok"
    if errs:
        status = "blocked"
    elif warns:
        status = "warning"

    return {
        "environment_status": status,
        "detected_variables": detected,
        "blocked_variables": blocked,
        "warnings": warns,
        "errors": errs,
    }


def audit_runner_binary_path(runner_path: str) -> dict[str, Any]:
    warns: list[str] = []
    errs: list[str] = []
    rp = str(runner_path or "").strip()
    if not rp:
        errs.append("runner_path_empty")
        return {"path_status": "blocked", "resolved_runner_path": None, "warnings": warns, "errors": errs}
    p = Path(rp)
    if not p.is_absolute():
        errs.append("runner_path_not_absolute")
    if ".." in p.parts or "." in p.parts:
        errs.append("runner_path_contains_relative_parts")
    try:
        if p.is_symlink():
            errs.append("runner_path_symlink")
    except OSError:
        errs.append("runner_path_symlink_check_failed")
    resolved = p.resolve(strict=False)
    if str(resolved) != str(p):
        warns.append("runner_path_resolved_differs")
    if _collect_world_writable_ancestors(resolved.parent):
        errs.append("runner_path_parent_world_writable")

    status = "ok"
    if errs:
        status = "blocked"
    elif warns:
        status = "warning"
    return {
        "path_status": status,
        "resolved_runner_path": str(resolved),
        "warnings": warns,
        "errors": errs,
    }


def audit_runner_job_directory(
    job_directory: str,
    *,
    allowed_prefixes: list[str] | None = None,
) -> dict[str, Any]:
    warns: list[str] = []
    errs: list[str] = []
    raw = str(job_directory or "").strip()
    if not raw:
        errs.append("job_directory_empty")
        return {"path_status": "blocked", "resolved_job_directory": None, "warnings": warns, "errors": errs}

    p = Path(raw)
    if not p.is_absolute():
        errs.append("job_directory_not_absolute")
    if ".." in p.parts or "." in p.parts:
        errs.append("job_directory_contains_relative_parts")

    cur = p
    while True:
        try:
            if cur.is_symlink():
                errs.append("job_directory_symlink_chain")
                break
        except OSError:
            errs.append("job_directory_symlink_check_failed")
            break
        if cur.parent == cur:
            break
        cur = cur.parent

    resolved = p.resolve(strict=False)
    prefixes = [Path(x).resolve(strict=False) for x in (allowed_prefixes or [_DEFAULT_JOB_DIRECTORY])]
    allowed = False
    for pref in prefixes:
        try:
            resolved.relative_to(pref)
            allowed = True
            break
        except ValueError:
            continue
    if not allowed:
        errs.append("job_directory_outside_allowed_prefixes")

    if _collect_world_writable_ancestors(resolved):
        errs.append("job_directory_world_writable_parent")

    status = "ok"
    if errs:
        status = "blocked"
    elif warns:
        status = "warning"
    return {
        "path_status": status,
        "resolved_job_directory": str(resolved),
        "warnings": warns,
        "errors": errs,
    }
