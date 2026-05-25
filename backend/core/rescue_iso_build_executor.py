from __future__ import annotations

import json
import os
import re
import shutil
import signal
import subprocess
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.rescue_iso_build_state import (
    build_rescue_iso_dashboard_state,
    detect_live_build_stale_state,
    redact_rescue_log_text,
    summarize_rescue_iso_artifacts,
)
from core.rescue_iso_operator_commands import (
    build_operator_build_commands,
    build_sudo_clean_commands,
    resolve_rescue_iso_paths,
)

UTC = timezone.utc

_BUILD_TREE_REL = "build/rescue/live-build/setuphelfer-rescue-live"
_BUNDLE_REL = "build/rescue/temp-runtime/setuphelfer-rescue-runtime"
_LOG_ROOT_REL = "build/rescue/logs/controlled-iso-build"
_ACTIONS_REL = f"{_LOG_ROOT_REL}/actions"
_SUMMARY_REL = "docs/evidence/runtime-results/rescue/controlled_iso_build_latest_summary.json"

_ALLOWED_STEPS = {
    "status",
    "toolcheck",
    "detect_stale_state",
    "clean_user_state",
    "dpkg_preflight",
    "prepare_bundle",
    "validate_bundle",
    "prepare_tree",
    "validate_tree",
    "prebuild_check",
    "build_iso_operator_required",
    "build_iso_with_sudo",
    "scan_iso",
    "summarize",
}
_FORBIDDEN_STEPS = {
    "usb_write",
    "dd",
    "mkfs",
    "parted_write",
    "restore",
    "backup",
    "verify_deep",
    "queue_apply",
    "apt_install",
    "apt_upgrade",
}
_TOOLCHECK_NAMES = ("lb", "xorriso", "mksquashfs", "sha256sum", "tar", "rsync")
_STATUS_TO_CODE = {
    "ok": "DEV_DASHBOARD_RESCUE_ISO_STEP_OK",
    "review_required": "DEV_DASHBOARD_RESCUE_ISO_STEP_REVIEW_REQUIRED",
    "blocked": "DEV_DASHBOARD_RESCUE_ISO_STEP_BLOCKED",
    "operator_required": "DEV_DASHBOARD_RESCUE_ISO_OPERATOR_REQUIRED",
    "forbidden": "DEV_DASHBOARD_RESCUE_ISO_FORBIDDEN_STEP",
    "cancelled": "DEV_DASHBOARD_RESCUE_ISO_STEP_BLOCKED",
}


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent


def _now_iso() -> str:
    return datetime.now(tz=UTC).isoformat()


def _repo_rel(repo: Path, path: Path) -> str:
    try:
        return path.resolve(strict=False).relative_to(repo.resolve(strict=False)).as_posix()
    except (OSError, ValueError):
        return str(path)


def _build_root(repo: Path) -> Path:
    return (repo / _BUILD_TREE_REL).resolve(strict=False)


def _bundle_root(repo: Path) -> Path:
    return (repo / _BUNDLE_REL).resolve(strict=False)


def _log_root(repo: Path) -> Path:
    return (repo / _LOG_ROOT_REL).resolve(strict=False)


def _actions_dir(repo: Path) -> Path:
    return (repo / _ACTIONS_REL).resolve(strict=False)


def _latest_log_path(repo: Path) -> Path:
    return (_log_root(repo) / "latest.log").resolve(strict=False)


def _summary_path(repo: Path) -> Path:
    return (repo / _SUMMARY_REL).resolve(strict=False)


def _action_root(runtime_root: Path, paths: dict[str, Any]) -> Path:
    if str(paths.get("path_status") or "") == "ok":
        return Path(str(paths["workspace_path"])).resolve(strict=False)
    return runtime_root


def _ensure_dirs(repo: Path) -> None:
    _actions_dir(repo).mkdir(parents=True, exist_ok=True)
    _summary_path(repo).parent.mkdir(parents=True, exist_ok=True)


def _action_log_path(repo: Path, action_id: str) -> Path:
    return (_actions_dir(repo) / f"{action_id}.log").resolve(strict=False)


def _action_status_path(repo: Path, action_id: str) -> Path:
    return (_actions_dir(repo) / f"{action_id}.json").resolve(strict=False)


def _write_json(path: Path, body: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(body, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    tmp.replace(path)


def _read_json(path: Path) -> dict[str, Any] | None:
    try:
        if not path.is_file():
            return None
        raw = json.loads(path.read_text(encoding="utf-8"))
        return raw if isinstance(raw, dict) else None
    except (OSError, json.JSONDecodeError):
        return None


def _backend_sudo_allowed() -> bool:
    raw = str(os.environ.get("SETUPHELFER_RESCUE_ISO_BACKEND_SUDO_ALLOWED") or "").strip().lower()
    return raw in {"1", "true", "yes", "on"}


def _new_action(repo: Path, step: str, operator_confirm: bool) -> dict[str, Any]:
    action_id = uuid.uuid4().hex
    action = {
        "action_id": action_id,
        "step": step,
        "operator_confirm": bool(operator_confirm),
        "status": "running",
        "code": "DEV_DASHBOARD_RESCUE_ISO_STEP_OK",
        "exit_code": None,
        "started_at": _now_iso(),
        "ended_at": None,
        "warnings": [],
        "errors": [],
        "details": {},
        "log_path": _repo_rel(repo, _action_log_path(repo, action_id)),
        "latest_log_path": _repo_rel(repo, _latest_log_path(repo)),
        "status_path": _repo_rel(repo, _action_status_path(repo, action_id)),
        "summary_path": _SUMMARY_REL,
        "pid": None,
    }
    _write_json(_action_status_path(repo, action_id), action)
    return action


def _persist_action(repo: Path, action: dict[str, Any]) -> None:
    _write_json(_action_status_path(repo, str(action["action_id"])), action)


def _write_logs(repo: Path, action_id: str, lines: list[str]) -> None:
    _ensure_dirs(repo)
    text = "".join(f"{line.rstrip()}\n" for line in lines)
    _action_log_path(repo, action_id).write_text(text, encoding="utf-8")
    _latest_log_path(repo).write_text(text, encoding="utf-8")


def _append_log(lines: list[str], text: str) -> None:
    for part in str(text or "").splitlines() or [""]:
        clean = redact_rescue_log_text(part.rstrip("\n"))
        lines.append(f"[{_now_iso()}] {clean}")


def _set_result(
    action: dict[str, Any],
    *,
    status: str,
    exit_code: int | None,
    details: dict[str, Any] | None = None,
    warnings: list[str] | None = None,
    errors: list[str] | None = None,
) -> dict[str, Any]:
    action["status"] = status
    action["code"] = _STATUS_TO_CODE.get(status, "DEV_DASHBOARD_RESCUE_ISO_STEP_BLOCKED")
    action["exit_code"] = exit_code
    action["ended_at"] = _now_iso()
    action["details"] = details or {}
    action["warnings"] = list(dict.fromkeys(warnings or []))
    action["errors"] = list(dict.fromkeys(errors or []))
    action["pid"] = None
    return action


def _finish(action_root: Path, runtime_root: Path, action: dict[str, Any], log_lines: list[str]) -> dict[str, Any]:
    _write_logs(action_root, str(action["action_id"]), log_lines)
    _persist_action(action_root, action)
    _write_summary(action_root, runtime_root, action)
    return action


def _write_summary(action_root: Path, runtime_root: Path, action: dict[str, Any]) -> None:
    state = build_rescue_iso_dashboard_state(repo_root=runtime_root)
    summary = {
        "schema_version": 2,
        "phase": "controlled_rescue_iso_build",
        "updated_at": _now_iso(),
        "status": action.get("status"),
        "last_action_id": action.get("action_id"),
        "last_step": action.get("step"),
        "last_action_status": action.get("status"),
        "last_exit_code": action.get("exit_code"),
        "last_error": (action.get("errors") or [None])[0] or state.get("summary"),
        "latest_log_path": action.get("latest_log_path"),
        "action_log_path": action.get("log_path"),
        "action_status_path": action.get("status_path"),
        "iso_found": ((state.get("iso_build") or {}).get("iso_found")),
        "iso_path": ((state.get("iso_build") or {}).get("iso_path")),
        "iso_abs_path": ((state.get("iso_build") or {}).get("iso_abs_path")),
        "iso_size_bytes": ((state.get("iso_build") or {}).get("iso_size_bytes")),
        "iso_sha256": ((state.get("iso_build") or {}).get("iso_sha256")),
        "usb_write_allowed": False,
        "dd_allowed": False,
        "warnings": list(action.get("warnings") or []),
        "errors": list(action.get("errors") or []),
        "details": action.get("details") or {},
        "dashboard_state": state,
    }
    _write_json(_summary_path(action_root), summary)


def _run_command(
    repo: Path,
    action: dict[str, Any],
    command: list[str],
    *,
    cwd: Path,
    extra_env: dict[str, str] | None = None,
) -> tuple[int, list[str]]:
    log_lines: list[str] = []
    _append_log(log_lines, f"COMMAND: {' '.join(command)}")
    env = os.environ.copy()
    if extra_env:
        env.update(extra_env)
    proc = subprocess.Popen(
        command,
        cwd=str(cwd),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
    )
    action["pid"] = proc.pid
    _persist_action(repo, action)
    assert proc.stdout is not None
    with proc.stdout:
        for line in proc.stdout:
            _append_log(log_lines, line.rstrip("\n"))
    rc = int(proc.wait())
    action["pid"] = None
    _append_log(log_lines, f"EXIT_CODE: {rc}")
    return rc, log_lines


def _execute_script_step(
    repo: Path,
    action: dict[str, Any],
    *,
    command: list[str],
    cwd: Path,
    success_status: str = "ok",
) -> tuple[dict[str, Any], list[str]]:
    rc, log_lines = _run_command(repo, action, command, cwd=cwd)
    status = success_status if rc == 0 else "blocked"
    action = _set_result(
        action,
        status=status,
        exit_code=0 if rc == 0 else 20,
        details={"command": command, "cwd": str(cwd)},
        errors=[] if rc == 0 else [f"command_failed:{' '.join(command)}"],
    )
    return action, log_lines


def _root_owned_under(path: Path) -> list[Path]:
    out: list[Path] = []
    if not path.exists():
        return out
    try:
        try:
            if path.lstat().st_uid == 0:
                out.append(path)
        except OSError:
            return out
        for root, dirs, files in os.walk(path):
            for name in [*dirs, *files]:
                p = Path(root) / name
                try:
                    if p.lstat().st_uid == 0:
                        out.append(p)
                except OSError:
                    continue
    except OSError:
        return out
    return out


def _safe_remove(path: Path) -> None:
    if not path.exists():
        return
    if path.is_symlink() or path.is_file():
        path.unlink(missing_ok=True)
        return
    shutil.rmtree(path)


def _toolcheck_details() -> dict[str, Any]:
    return {name: {"present": bool(shutil.which(name)), "path": shutil.which(name)} for name in _TOOLCHECK_NAMES}


def _scan_runtime_for_artifact_policy(repo: Path) -> dict[str, Any]:
    runtime_root = _build_root(repo) / "config/includes.chroot/opt/setuphelfer-rescue"
    secret_hits: list[str] = []
    cdn_hits: list[str] = []
    if not runtime_root.exists():
        return {"secret_hits": secret_hits, "cdn_hits": cdn_hits, "scan_root": _repo_rel(repo, runtime_root)}
    for root, dirs, files in os.walk(runtime_root):
        dirs[:] = [d for d in dirs if d not in {"venv", "node_modules", "__pycache__"}]
        for name in files:
            path = Path(root) / name
            try:
                data = path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            if re.search(r"API_KEY=|SECRET=|PASSWORD=|TOKEN=|PRIVATE KEY", data, re.I):
                secret_hits.append(_repo_rel(repo, path))
            if re.search(r"fonts\.googleapis\.com|fonts\.gstatic\.com", data, re.I):
                cdn_hits.append(_repo_rel(repo, path))
            if len(secret_hits) >= 8 and len(cdn_hits) >= 8:
                break
    return {
        "secret_hits": secret_hits[:8],
        "cdn_hits": cdn_hits[:8],
        "scan_root": _repo_rel(repo, runtime_root),
    }


def run_rescue_iso_step(step: str, operator_confirm: bool = False) -> dict[str, Any]:
    runtime_root = _repo_root().resolve(strict=False)
    paths = resolve_rescue_iso_paths(repo_root=runtime_root)
    repo = _action_root(runtime_root, paths)
    workspace_root = Path(str(paths["workspace_path"])).resolve(strict=False)
    _ensure_dirs(repo)
    step_name = str(step or "").strip()
    action = _new_action(repo, step_name, bool(operator_confirm))
    log_lines: list[str] = []
    _append_log(log_lines, f"STEP: {step_name}")
    _append_log(log_lines, f"RUNTIME_PATH: {runtime_root}")
    _append_log(log_lines, f"WORKSPACE_PATH: {workspace_root}")
    _append_log(log_lines, f"PATH_STATUS: {paths.get('path_status')}")

    if step_name in _FORBIDDEN_STEPS:
        action = _set_result(
            action,
            status="forbidden",
            exit_code=13,
            errors=[f"forbidden_step:{step_name}"],
        )
        return _finish(repo, runtime_root, action, log_lines)

    if step_name not in _ALLOWED_STEPS:
        action = _set_result(
            action,
            status="forbidden",
            exit_code=13,
            errors=[f"unsupported_step:{step_name}"],
        )
        return _finish(repo, runtime_root, action, log_lines)

    guarded_steps = {
        "detect_stale_state",
        "clean_user_state",
        "dpkg_preflight",
        "prepare_bundle",
        "validate_bundle",
        "prepare_tree",
        "validate_tree",
        "prebuild_check",
        "build_iso_operator_required",
        "build_iso_with_sudo",
        "scan_iso",
        "summarize",
    }
    if step_name in guarded_steps and paths.get("path_status") != "ok":
        action = _set_result(
            action,
            status="blocked",
            exit_code=40,
            details={"paths": paths},
            errors=[f"path_status:{paths.get('path_status')}"] + list(paths.get("errors") or []),
            warnings=list(paths.get("warnings") or []),
        )
        return _finish(repo, runtime_root, action, log_lines)

    if step_name == "status":
        state = build_rescue_iso_dashboard_state(repo_root=runtime_root)
        action = _set_result(action, status="ok", exit_code=0, details={"dashboard_state": state})
        return _finish(repo, runtime_root, action, log_lines)

    if step_name == "toolcheck":
        details = {"tools": _toolcheck_details()}
        missing = [name for name, item in (details["tools"] or {}).items() if not item.get("present")]
        status = "ok" if not missing else "blocked"
        action = _set_result(
            action,
            status=status,
            exit_code=0 if not missing else 10,
            details=details,
            errors=[] if not missing else [f"missing_tools:{', '.join(missing)}"],
        )
        return _finish(repo, runtime_root, action, log_lines)

    if step_name == "detect_stale_state":
        stale = detect_live_build_stale_state(repo_root=runtime_root)
        status = "review_required" if stale.get("present") else "ok"
        if stale.get("needs_sudo_clean"):
            status = "operator_required"
        action = _set_result(
            action,
            status=status,
            exit_code=12 if stale.get("needs_sudo_clean") else (11 if stale.get("present") else 0),
            details={"stale_state": stale},
        )
        return _finish(repo, runtime_root, action, log_lines)

    if step_name == "clean_user_state":
        build_root = _build_root(workspace_root)
        generated_opt_root = build_root / "config/includes.chroot/opt"
        targets = [build_root / name for name in (".build", "chroot", "cache", "binary", "local")]
        targets.append(generated_opt_root / "setuphelfer-rescue")
        targets.extend(sorted(generated_opt_root.glob("setuphelfer-rescue.old.*")))
        root_owned: list[str] = []
        for target in targets:
            root_owned.extend(_repo_rel(repo, p) for p in _root_owned_under(target))
        if root_owned:
            action = _set_result(
                action,
                status="operator_required",
                exit_code=12,
                details={"commands": build_sudo_clean_commands(repo_root=runtime_root).get("commands") or [], "paths": paths},
                errors=["root_owned_state_detected"],
            )
            return _finish(repo, runtime_root, action, log_lines)
        removed: list[str] = []
        for target in targets:
            if not target.exists():
                continue
            try:
                target.resolve(strict=False).relative_to(build_root)
            except (OSError, ValueError):
                action = _set_result(
                    action,
                    status="blocked",
                    exit_code=40,
                    errors=[f"path_outside_build_tree:{target}"],
                )
                return _finish(repo, runtime_root, action, log_lines)
            _safe_remove(target)
            removed.append(_repo_rel(repo, target))
        action = _set_result(action, status="ok", exit_code=0, details={"removed": removed, "paths": paths})
        return _finish(repo, runtime_root, action, log_lines)

    if step_name == "dpkg_preflight":
        rc, cmd_log = _run_command(
            repo,
            action,
            command=["scripts/rescue-live/validate-live-build-dpkg-preflight.sh"],
            cwd=workspace_root,
        )
        details = {"command": ["scripts/rescue-live/validate-live-build-dpkg-preflight.sh"], "cwd": str(workspace_root)}
        summary_path = workspace_root / "docs/evidence/runtime-results/rescue/live_build_dpkg_preflight_latest.json"
        if summary_path.is_file():
            try:
                details["result"] = json.loads(summary_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                pass
        if rc == 0:
            status = "ok"
            exit_code = 0
            errors: list[str] = []
        elif rc == 20:
            status = "review_required"
            exit_code = 20
            errors = ["dpkg_preflight_review_required"]
        else:
            status = "blocked"
            exit_code = rc
            errors = [f"dpkg_preflight_failed:{rc}"]
        action = _set_result(
            action,
            status=status,
            exit_code=exit_code,
            details=details,
            errors=errors,
        )
        return _finish(repo, runtime_root, action, log_lines + cmd_log)

    if step_name == "prepare_bundle":
        action, cmd_log = _execute_script_step(
            repo,
            action,
            command=["scripts/rescue-live/create-temp-runtime-bundle.sh"],
            cwd=workspace_root,
        )
        action["details"]["paths"] = paths
        return _finish(repo, runtime_root, action, log_lines + cmd_log)

    if step_name == "validate_bundle":
        action, cmd_log = _execute_script_step(
            repo,
            action,
            command=[
                "scripts/rescue-live/validate-temp-runtime-bundle.sh",
                "build/rescue/temp-runtime/setuphelfer-rescue-runtime",
            ],
            cwd=workspace_root,
        )
        action["details"]["paths"] = paths
        return _finish(repo, runtime_root, action, log_lines + cmd_log)

    if step_name == "prepare_tree":
        action, cmd_log = _execute_script_step(
            repo,
            action,
            command=["scripts/rescue-live/prepare-controlled-live-build-tree.sh"],
            cwd=workspace_root,
        )
        action["details"]["paths"] = paths
        return _finish(repo, runtime_root, action, log_lines + cmd_log)

    if step_name == "validate_tree":
        action, cmd_log = _execute_script_step(
            repo,
            action,
            command=[
                "scripts/rescue-live/validate-controlled-live-build-tree.sh",
                "build/rescue/live-build/setuphelfer-rescue-live",
            ],
            cwd=workspace_root,
        )
        action["details"]["paths"] = paths
        return _finish(repo, runtime_root, action, log_lines + cmd_log)

    if step_name == "prebuild_check":
        state = build_rescue_iso_dashboard_state(repo_root=runtime_root)
        missing = [name for name, item in (state.get("tools") or {}).items() if not item.get("present")]
        dpkg_preflight = state.get("dpkg_preflight") or {}
        dpkg_status = str(dpkg_preflight.get("status") or "unknown")
        if ((state.get("repo") or {}).get("runtime_gate")) != "green":
            action = _set_result(action, status="blocked", exit_code=14, errors=["runtime_gate_failed"], details=state)
        elif (state.get("stale_state") or {}).get("needs_sudo_clean"):
            action = _set_result(
                action,
                status="operator_required",
                exit_code=12,
                details={"commands": build_sudo_clean_commands(repo_root=runtime_root).get("commands") or [], "state": state},
                errors=["sudo_clean_required"],
            )
        elif (state.get("stale_state") or {}).get("present"):
            action = _set_result(action, status="review_required", exit_code=11, details=state, errors=["stale_state_detected"])
        elif missing:
            action = _set_result(action, status="blocked", exit_code=10, details=state, errors=[f"missing_tools:{', '.join(missing)}"])
        elif (state.get("temp_runtime_bundle") or {}).get("status") != "ok":
            action = _set_result(action, status="blocked", exit_code=10, details=state, errors=["bundle_not_ready"])
        elif (state.get("build_tree") or {}).get("validator_status") != "ok":
            action = _set_result(action, status="blocked", exit_code=10, details=state, errors=["build_tree_not_ready"])
        elif not (state.get("build_tree") or {}).get("auto_config_noauto"):
            action = _set_result(action, status="blocked", exit_code=10, details=state, errors=["auto_config_missing_noauto"])
        elif not (state.get("build_tree") or {}).get("auto_build_blocked"):
            action = _set_result(action, status="blocked", exit_code=10, details=state, errors=["auto_build_not_blocked"])
        elif dpkg_status in {"unknown"}:
            action = _set_result(action, status="review_required", exit_code=20, details=state, errors=["dpkg_preflight_not_run"])
        elif dpkg_status in {
            "unsafe_auto_config",
            "unsafe_auto_clean",
            "forbidden_package",
            "dangerous_path_override",
            "chroot_dpkg_missing",
            "chroot_start_stop_daemon_missing",
        }:
            action = _set_result(action, status="blocked", exit_code=16, details=state, errors=["dpkg_preflight_blocked"])
        elif dpkg_status == "review_required":
            action = _set_result(action, status="review_required", exit_code=20, details=state, errors=["dpkg_preflight_review_required"])
        else:
            action = _set_result(action, status="ok", exit_code=0, details=state)
        return _finish(repo, runtime_root, action, log_lines)

    if step_name == "build_iso_operator_required":
        details = build_operator_build_commands(repo_root=runtime_root)
        action = _set_result(action, status="operator_required", exit_code=12, details=details)
        return _finish(repo, runtime_root, action, log_lines)

    if step_name == "build_iso_with_sudo":
        if not operator_confirm:
            action = _set_result(action, status="blocked", exit_code=40, errors=["operator_confirm_required"])
            return _finish(repo, runtime_root, action, log_lines)
        if not _backend_sudo_allowed():
            details = build_operator_build_commands(repo_root=runtime_root)
            action = _set_result(action, status="operator_required", exit_code=12, details=details, errors=["backend_sudo_not_allowed"])
            return _finish(repo, runtime_root, action, log_lines)
        cfg_rc, cfg_lines = _run_command(repo, action, ["./auto/config"], cwd=_build_root(workspace_root))
        full_logs = log_lines + cfg_lines
        if cfg_rc != 0:
            action = _set_result(action, status="blocked", exit_code=20, errors=["auto_config_failed"])
            return _finish(repo, runtime_root, action, full_logs)
        build_rc, build_lines = _run_command(repo, action, ["sudo", "lb", "build", "noauto"], cwd=_build_root(workspace_root))
        full_logs.extend(build_lines)
        status = "ok" if build_rc == 0 else "blocked"
        exit_code = 0 if build_rc == 0 else 20
        action = _set_result(action, status=status, exit_code=exit_code, errors=[] if build_rc == 0 else ["sudo_lb_build_failed"])
        return _finish(repo, runtime_root, action, full_logs)

    if step_name == "scan_iso":
        artifacts = summarize_rescue_iso_artifacts(repo_root=runtime_root)
        scan = _scan_runtime_for_artifact_policy(workspace_root)
        if not artifacts.get("iso_found"):
            action = _set_result(action, status="review_required", exit_code=30, details={"artifacts": artifacts, "scan": scan})
        elif scan.get("secret_hits") or scan.get("cdn_hits"):
            action = _set_result(
                action,
                status="review_required",
                exit_code=10,
                details={"artifacts": artifacts, "scan": scan},
                errors=["artifact_policy_review_required"],
            )
        else:
            action = _set_result(action, status="ok", exit_code=0, details={"artifacts": artifacts, "scan": scan})
        return _finish(repo, runtime_root, action, log_lines)

    if step_name == "summarize":
        state = build_rescue_iso_dashboard_state(repo_root=runtime_root)
        action = _set_result(action, status="ok", exit_code=0, details={"dashboard_state": state})
        return _finish(repo, runtime_root, action, log_lines)

    action = _set_result(action, status="forbidden", exit_code=13, errors=[f"unhandled_step:{step_name}"])
    return _finish(repo, runtime_root, action, log_lines)


def get_rescue_iso_step_status(action_id: str) -> dict[str, Any]:
    runtime_root = _repo_root().resolve(strict=False)
    paths = resolve_rescue_iso_paths(repo_root=runtime_root)
    candidates = [
        _action_status_path(_action_root(runtime_root, paths), str(action_id).strip()),
        _action_status_path(runtime_root, str(action_id).strip()),
    ]
    body = None
    for path in candidates:
        body = _read_json(path)
        if body is not None:
            break
    if body is None:
        return {
            "action_id": action_id,
            "status": "blocked",
            "code": "DEV_DASHBOARD_RESCUE_ISO_STEP_BLOCKED",
            "errors": ["action_not_found"],
        }
    return body


def cancel_rescue_iso_step(action_id: str) -> dict[str, Any]:
    runtime_root = _repo_root().resolve(strict=False)
    paths = resolve_rescue_iso_paths(repo_root=runtime_root)
    repo = _action_root(runtime_root, paths)
    body = get_rescue_iso_step_status(action_id)
    if body.get("errors"):
        return body
    if body.get("status") != "running":
        return {
            **body,
            "code": "DEV_DASHBOARD_RESCUE_ISO_STEP_BLOCKED",
            "errors": ["action_not_running"],
        }
    pid = body.get("pid")
    if not isinstance(pid, int) or pid <= 0:
        return {
            **body,
            "code": "DEV_DASHBOARD_RESCUE_ISO_STEP_BLOCKED",
            "errors": ["cancel_not_possible"],
        }
    try:
        os.kill(pid, signal.SIGTERM)
    except OSError as exc:
        return {
            **body,
            "code": "DEV_DASHBOARD_RESCUE_ISO_STEP_BLOCKED",
            "errors": [f"cancel_failed:{exc}"],
        }
    body["status"] = "cancelled"
    body["code"] = _STATUS_TO_CODE["cancelled"]
    body["exit_code"] = 40
    body["ended_at"] = _now_iso()
    body["errors"] = ["cancelled_by_request"]
    body["pid"] = None
    _persist_action(repo, body)
    _write_summary(repo, runtime_root, body)
    return body
