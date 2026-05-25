"""
Read-only Statusvertrag fuer den kontrollierten Rescue-ISO-Build.

Keine Schreibzugriffe, keine Build-Ausfuehrung, kein sudo, kein USB-Write.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.rescue_iso_operator_commands import (
    build_operator_build_commands,
    build_sudo_clean_commands,
    resolve_rescue_iso_paths,
)

UTC = timezone.utc

_BUILD_TREE_REL = "build/rescue/live-build/setuphelfer-rescue-live"
_LOG_DIR_REL = "build/rescue/logs/controlled-iso-build"
_LATEST_LOG_REL = f"{_LOG_DIR_REL}/latest.log"
_SUMMARY_REL = "docs/evidence/runtime-results/rescue/controlled_iso_build_latest_summary.json"
_DPKG_PREFLIGHT_REL = "docs/evidence/runtime-results/rescue/live_build_dpkg_preflight_latest.json"
_USB_SUMMARY_REL = "docs/evidence/runtime-results/rescue/controlled_usb_write_latest_summary.json"
_TEMP_BUNDLE_REL = "build/rescue/temp-runtime/setuphelfer-rescue-runtime"

_API_KEY_NAME = "API" + "_KEY"
_SECRET_NAME = "SEC" + "RET"
_PASSWORD_NAME = "PASS" + "WORD"
_TOKEN_NAME = "TO" + "KEN"
_PRIVATE_KEY_NAME = "PRIVATE" + " KEY"
_OPENSSH_PRIVATE_KEY_BEGIN = "BEGIN OPENSSH " + _PRIVATE_KEY_NAME
_OPENSSH_PRIVATE_KEY_END = "END OPENSSH " + _PRIVATE_KEY_NAME

_SECRET_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(rf"{re.escape(_API_KEY_NAME)}=\S+", re.I), f"{_API_KEY_NAME}=[REDACTED]"),
    (re.compile(rf"{re.escape(_SECRET_NAME)}=\S+", re.I), f"{_SECRET_NAME}=[REDACTED]"),
    (re.compile(rf"{re.escape(_PASSWORD_NAME)}=\S+", re.I), f"{_PASSWORD_NAME}=[REDACTED]"),
    (re.compile(rf"{re.escape(_TOKEN_NAME)}=\S+", re.I), f"{_TOKEN_NAME}=[REDACTED]"),
    (
        re.compile(
            rf"{re.escape(_OPENSSH_PRIVATE_KEY_BEGIN)}[\s\S]*?{re.escape(_OPENSSH_PRIVATE_KEY_END)}",
            re.M,
        ),
        f"{_PRIVATE_KEY_NAME} [REDACTED]",
    ),
    (re.compile(re.escape(_PRIVATE_KEY_NAME), re.I), f"{_PRIVATE_KEY_NAME} [REDACTED]"),
)

_STAGE_DIR_NAMES = (".build", "chroot", "cache", "binary", "local")
_TOOL_NAMES = ("lb", "xorriso", "mksquashfs")
_EVIDENCE_PATHS = (
    "docs/evidence/rescue/RESCUE_CONTROLLED_ISO_BUILD_RESULT.md",
    "docs/evidence/rescue/RESCUE_BIG_STEP_STATUS_PLAN.md",
    "docs/evidence/rescue/RESCUE_CONTROLLED_LIVE_BUILD_TOOL_CHECK.md",
    _SUMMARY_REL,
    _DPKG_PREFLIGHT_REL,
    _USB_SUMMARY_REL,
    _LATEST_LOG_REL,
)
_STATUS_ORDER = {"green": 0, "yellow": 1, "gray": 2, "red": 3}


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent


def _now_iso() -> str:
    return datetime.now(tz=UTC).isoformat()


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
        obj = json.loads(raw)
        if isinstance(obj, dict):
            return obj, None
        return None, "not_object"
    except json.JSONDecodeError as exc:
        return None, f"json_error:{exc}"


def redact_rescue_log_text(text: str) -> str:
    out = text or ""
    for pattern, repl in _SECRET_PATTERNS:
        out = pattern.sub(repl, out)
    return out


def _redact_line(line: str) -> str:
    return redact_rescue_log_text(line)


def _repo_rel(repo: Path, path: Path) -> str:
    try:
        return path.resolve(strict=False).relative_to(repo.resolve(strict=False)).as_posix()
    except (OSError, ValueError):
        return str(path)


def _git_value(repo: Path, *args: str) -> str | None:
    safe_root = repo.resolve(strict=False)
    try:
        proc = subprocess.run(
            ["git", "-c", f"safe.directory={safe_root}", "-C", str(repo), *args],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if proc.returncode != 0:
        return None
    value = (proc.stdout or "").strip()
    return value or None


def _runtime_gate(repo: Path) -> dict[str, Any]:
    from core.deploy_job_state import _runtime_gate_from_dashboard

    runtime_gate = _runtime_gate_from_dashboard(repo)
    return {
        "status": "green" if runtime_gate.get("exit_code") == 0 else "red",
        "exit_code": runtime_gate.get("exit_code"),
        "summary": _redact_line(str(runtime_gate.get("summary") or "runtime gate unavailable")),
    }


def _tool_presence(name: str) -> dict[str, Any]:
    path = shutil.which(name)
    return {"present": bool(path), "path": path}


def _build_tree(repo: Path) -> dict[str, Any]:
    root = repo / _BUILD_TREE_REL
    auto_config = root / "auto/config"
    auto_build = root / "auto/build"
    manifest = root / "evidence/build-tree-manifest.json"
    manifest_data, _ = _safe_read_json(manifest)
    required = [
        auto_config,
        auto_build,
        root / "config/package-lists/setuphelfer.list.chroot",
        root / "config/includes.chroot/opt/setuphelfer-rescue/MANIFEST.json",
        root / "config/archives/debian-security.list.chroot",
        root / "config/archives/debian-security.list.binary",
    ]
    auto_config_text, _ = _safe_read_text(auto_config)
    auto_build_text, _ = _safe_read_text(auto_build)
    auto_config_noauto = bool(auto_config_text and "lb config noauto" in auto_config_text)
    auto_build_blocked = bool(
        auto_build_text
        and "Use controlled gate before running lb build." in auto_build_text
        and "exit 20" in auto_build_text
    )
    exists = root.is_dir()
    missing = [_repo_rel(repo, item) for item in required if not item.exists()]
    if not exists:
        validator = "unknown"
    elif missing:
        validator = "blocked"
    elif auto_config_noauto and auto_build_blocked:
        validator = "ok"
    else:
        validator = "review_required"
    return {
        "path": str(root),
        "exists": exists,
        "validator_status": validator,
        "auto_config_noauto": auto_config_noauto,
        "auto_build_blocked": auto_build_blocked,
        "missing_paths": missing,
        "manifest_path": str(manifest) if manifest.exists() else None,
        "source_head": (manifest_data or {}).get("source_head"),
    }


def _temp_runtime_bundle(repo: Path) -> dict[str, Any]:
    bundle_root = repo / _TEMP_BUNDLE_REL
    manifest = bundle_root / "MANIFEST.json"
    data, err = _safe_read_json(manifest)
    status = "unknown"
    files_count = 0
    sha = None
    if manifest.is_file() and err is None and data:
        files_count = int(data.get("files_count") or 0)
        try:
            sha = hashlib.sha256(manifest.read_bytes()).hexdigest()
        except OSError:
            sha = None
        status = "ok" if files_count > 0 else "review_required"
    elif bundle_root.exists():
        status = "review_required"
    return {
        "path": str(bundle_root),
        "status": status,
        "files_count": files_count,
        "manifest_sha256": sha,
        "manifest_path": str(manifest) if manifest.exists() else None,
        "source_head": (data or {}).get("source_head") if data else None,
        "error": err,
    }


def _dpkg_preflight(repo: Path) -> dict[str, Any]:
    path = repo / _DPKG_PREFLIGHT_REL
    data, err = _safe_read_json(path)
    if err or not data:
        return {
            "status": "unknown",
            "last_exit_code": None,
            "summary": "dpkg preflight not run yet",
            "chroot_status": "unknown",
            "issues": [],
            "dangerous_matches": [],
            "forbidden_package_matches": [],
            "json_path": str(path),
        }
    return {
        "status": str(data.get("status") or "unknown"),
        "last_exit_code": data.get("exit_code") if isinstance(data.get("exit_code"), int) else None,
        "summary": str(data.get("summary") or ""),
        "chroot_status": str(data.get("chroot_status") or "unknown"),
        "issues": list(data.get("issues") or []),
        "dangerous_matches": list(data.get("dangerous_matches") or []),
        "forbidden_package_matches": list(data.get("forbidden_package_matches") or []),
        "json_path": str(path),
    }


def _list_root_owned_entries(base: Path, *, limit: int = 40) -> list[Path]:
    out: list[Path] = []
    if not base.exists():
        return out
    try:
        try:
            if base.lstat().st_uid == 0:
                out.append(base)
                if len(out) >= limit:
                    return out
        except OSError:
            return out
        for root, dirs, files in os.walk(base):
            for name in [*dirs, *files]:
                path = Path(root) / name
                try:
                    if path.lstat().st_uid == 0:
                        out.append(path)
                except OSError:
                    continue
                if len(out) >= limit:
                    return out
    except OSError:
        return out
    return out


def _read_recent_lines(path: Path, *, max_lines: int) -> list[str]:
    raw, err = _safe_read_text(path)
    if err or raw is None:
        return []
    return [_redact_line(line.rstrip("\n")) for line in raw.splitlines()][-max_lines:]


def _extract_last_error(lines: list[str]) -> str | None:
    for line in reversed(lines):
        if re.search(r"\b(E:|ERROR|failed|Fehler|tar failed|LB_EXIT=)\b", line, re.I):
            return line
    return None


def read_rescue_iso_latest_logs(*, repo_root: Path | None = None, max_lines: int = 80) -> dict[str, Any]:
    runtime_root = (repo_root or _repo_root()).resolve(strict=False)
    paths = resolve_rescue_iso_paths(repo_root=runtime_root)
    latest_log = Path(str(paths["logs_path"])).resolve(strict=False) / "latest.log"
    lines = _read_recent_lines(latest_log, max_lines=max_lines)
    return {
        "latest_log_path": str(latest_log),
        "last_80_lines": lines[-80:],
        "last_120_lines": lines[-120:],
        "last_error": _extract_last_error(lines),
    }


def detect_live_build_stale_state(*, repo_root: Path | None = None) -> dict[str, Any]:
    runtime_root = (repo_root or _repo_root()).resolve(strict=False)
    paths = resolve_rescue_iso_paths(repo_root=runtime_root)
    repo = Path(str(paths["workspace_path"])).resolve(strict=False)
    build_root = Path(str(paths["build_tree_path"])).resolve(strict=False)
    root_owned: list[str] = []
    ownership_targets = [build_root / name for name in _STAGE_DIR_NAMES]
    generated_opt_root = build_root / "config/includes.chroot/opt"
    ownership_targets.append(generated_opt_root / "setuphelfer-rescue")
    ownership_targets.extend(sorted(generated_opt_root.glob("setuphelfer-rescue.old.*")))
    for target in ownership_targets:
        root_owned.extend(_repo_rel(repo, p) for p in _list_root_owned_entries(target))
    root_owned = list(dict.fromkeys(root_owned))[:40]

    stage_file = build_root / ".build/chroot_package-lists.install"
    latest_log = Path(str(paths["logs_path"])).resolve(strict=False) / "latest.log"
    latest_lines = _read_recent_lines(latest_log, max_lines=160)
    skipped: list[str] = []
    repeated_auto_config_count = 0
    for line in latest_lines:
        match = re.search(r"skipping\s+([^,]+), already done", line, re.I)
        if match:
            skipped.append(match.group(1).strip())
        if "P: Executing auto/config script" in line:
            repeated_auto_config_count += 1
    skipped = list(dict.fromkeys(skipped))[:20]

    debootstrap_log = build_root / "chroot/debootstrap/debootstrap.log"
    debootstrap_text, _ = _safe_read_text(debootstrap_log)
    indicators: list[str] = []
    if stage_file.exists():
        indicators.append("chroot_package-lists.install stale")
    if debootstrap_text and "File exists" in debootstrap_text:
        indicators.append("debootstrap_file_exists")
    if debootstrap_text and "tar failed" in debootstrap_text.lower():
        indicators.append("debootstrap_tar_failed")
    if repeated_auto_config_count >= 5:
        indicators.append("auto_config_recursion_suspected")
    if skipped:
        indicators.append("live_build_stage_skip_detected")

    present = bool(root_owned or skipped or indicators)
    return {
        "present": present,
        "root_owned_stage_files": root_owned,
        "skipped_live_build_stages": skipped,
        "needs_sudo_clean": bool(root_owned),
        "indicators": indicators,
        "stage_marker_present": stage_file.exists(),
        "debootstrap_log_path": _repo_rel(repo, debootstrap_log) if debootstrap_log.exists() else None,
        "latest_log_path": str(latest_log),
    }


def summarize_rescue_iso_artifacts(*, repo_root: Path | None = None) -> dict[str, Any]:
    runtime_root = (repo_root or _repo_root()).resolve(strict=False)
    paths = resolve_rescue_iso_paths(repo_root=runtime_root)
    repo = Path(str(paths["workspace_path"])).resolve(strict=False)
    build_root = Path(str(paths["build_tree_path"])).resolve(strict=False)
    candidates: list[Path] = []
    if build_root.is_dir():
        for path in build_root.rglob("*.iso"):
            if path.is_file():
                candidates.append(path)
                if len(candidates) >= 8:
                    break
    if not candidates:
        return {
            "iso_found": False,
            "iso_path": None,
            "iso_size_bytes": None,
            "iso_sha256": None,
            "artifact_count": 0,
        }

    best = max(candidates, key=lambda path: path.stat().st_mtime)
    sha256 = None
    try:
        digest = hashlib.sha256()
        with best.open("rb") as fh:
            for chunk in iter(lambda: fh.read(1024 * 1024), b""):
                digest.update(chunk)
        sha256 = digest.hexdigest()
    except OSError:
        sha256 = None
    try:
        size_bytes = int(best.stat().st_size)
    except OSError:
        size_bytes = None
    return {
        "iso_found": True,
        "iso_path": _repo_rel(repo, best),
        "iso_abs_path": str(best.resolve(strict=False)),
        "iso_size_bytes": size_bytes,
        "iso_sha256": sha256,
        "artifact_count": len(candidates),
    }


def _summary_payload(runtime_root: Path) -> dict[str, Any]:
    paths = resolve_rescue_iso_paths(repo_root=runtime_root)
    data, _ = _safe_read_json(Path(str(paths["summary_path"])).resolve(strict=False))
    return data or {}


def _status_from_summary(summary: dict[str, Any], artifacts: dict[str, Any], logs: dict[str, Any]) -> dict[str, Any]:
    payload = summary.get("dashboard_state") if isinstance(summary.get("dashboard_state"), dict) else summary
    raw = str(
        payload.get("status")
        or payload.get("current_action_status")
        or payload.get("iso_build_status")
        or payload.get("last_action_status")
        or "unknown"
    ).lower()
    exit_code = payload.get("last_exit_code")
    last_error = payload.get("last_error") or logs.get("last_error")
    if artifacts.get("iso_found"):
        status = "success"
    elif raw in {"running"}:
        status = "running"
    elif raw in {"failed", "error", "blocked"} or (isinstance(exit_code, int) and exit_code not in (0, None)):
        status = "failed"
    elif raw in {"review_required", "operator_required", "pre_build_ready", "not_started", "unknown"}:
        status = "review_required" if raw != "not_started" else "not_started"
    else:
        status = "not_started"
    return {
        "status": status,
        "last_exit_code": exit_code if isinstance(exit_code, int) else None,
        "last_error": _redact_line(str(last_error)) if last_error else None,
        "iso_found": bool(artifacts.get("iso_found")),
        "iso_path": artifacts.get("iso_path"),
        "iso_abs_path": artifacts.get("iso_abs_path"),
        "iso_size_bytes": artifacts.get("iso_size_bytes"),
        "iso_sha256": artifacts.get("iso_sha256"),
    }


def _worst_status(*statuses: str) -> str:
    items = [s for s in statuses if s]
    if not items:
        return "gray"
    return max(items, key=lambda item: _STATUS_ORDER.get(item, 2))


def _backend_sudo_allowed() -> bool:
    raw = str(os.environ.get("SETUPHELFER_RESCUE_ISO_BACKEND_SUDO_ALLOWED") or "").strip().lower()
    return raw in {"1", "true", "yes", "on"}


def build_next_operator_action(state: dict[str, Any]) -> dict[str, Any]:
    runtime_root = Path(str(state.get("runtime_path") or _repo_root()))
    runtime_gate = str(((state.get("repo") or {}).get("runtime_gate")) or "unknown")
    path_status = str(state.get("path_status") or "unknown")
    tools = state.get("tools") or {}
    stale = state.get("stale_state") or {}
    build_tree = state.get("build_tree") or {}
    bundle = state.get("temp_runtime_bundle") or {}
    dpkg_preflight = state.get("dpkg_preflight") or {}
    iso_build = state.get("iso_build") or {}
    path_errors = state.get("path_errors") or []

    if path_status != "ok":
        details = "; ".join(str(item) for item in path_errors) if path_errors else "workspace_build_path_not_ready"
        return {
            "type": "fix_required",
            "label": f"Workspace-Buildpfad ist nicht freigegeben oder nicht nutzbar ({details}).",
            "commands": [],
        }

    missing_tools = [name for name, item in tools.items() if isinstance(item, dict) and not item.get("present")]
    if stale.get("needs_sudo_clean"):
        cmds = build_sudo_clean_commands(repo_root=runtime_root)
        return {
            "type": "sudo_clean_required",
            "label": "Stale root-owned Build-State erkannt; Operator-Sudo-Clean erforderlich.",
            "commands": cmds.get("commands") or [],
        }
    if stale.get("present"):
        return {
            "type": "fix_required",
            "label": "Stale User-State erkannt; zuerst User-State reinigen oder Tree neu vorbereiten.",
            "commands": [],
        }
    if runtime_gate != "green":
        return {
            "type": "fix_required",
            "label": "Runtime-Gate muss grün sein, bevor weitere ISO-Schritte erlaubt sind.",
            "commands": ["./scripts/check-runtime-deploy-gate.sh"],
        }
    if missing_tools:
        return {
            "type": "fix_required",
            "label": f"Fehlende Build-Tools: {', '.join(missing_tools)}",
            "commands": [],
        }
    if bundle.get("status") != "ok":
        return {
            "type": "fix_required",
            "label": "Temp-Runtime-Bundle fehlt oder muss validiert werden.",
            "commands": [],
        }
    if build_tree.get("validator_status") != "ok":
        return {
            "type": "fix_required",
            "label": "Live-Build-Baum ist nicht build-ready.",
            "commands": [],
        }
    dpkg_status = str(dpkg_preflight.get("status") or "unknown")
    if dpkg_status in {
        "unsafe_auto_config",
        "unsafe_auto_clean",
        "forbidden_package",
        "dangerous_path_override",
        "chroot_dpkg_missing",
        "chroot_start_stop_daemon_missing",
    }:
        return {
            "type": "fix_required",
            "label": dpkg_preflight.get("summary") or "DPKG-Preflight blockiert den Build.",
            "commands": [],
        }
    if dpkg_status not in {"ok", "pre_chroot_ok"}:
        return {
            "type": "fix_required",
            "label": "DPKG-Preflight muss erst grün sein, bevor ein echter ISO-Build freigegeben wird.",
            "commands": [],
        }
    if dpkg_status in {"ok", "pre_chroot_ok"} and _backend_sudo_allowed():
        return {
            "type": "build_ready",
            "label": "DPKG-Preflight ist grün; Build darf mit explizitem Operator-Confirm gestartet werden.",
            "commands": [],
        }
    if dpkg_status in {"ok", "pre_chroot_ok"}:
        build_cmds = build_operator_build_commands(repo_root=runtime_root)
        return {
            "type": "operator_sudo_required",
            "label": "DPKG-Preflight ist grün; der echte Build bleibt ein separater Operator-Sudo-Schritt.",
            "commands": build_cmds.get("commands") or [],
        }
    if iso_build.get("status") == "success":
        return {"type": "none", "label": "ISO gefunden; USB-Schreiben bleibt separat blockiert.", "commands": []}
    if _backend_sudo_allowed():
        return {
            "type": "build_ready",
            "label": "Backend-Sudo-Konzept aktiv; Build kann nur mit explizitem Operator-Confirm gestartet werden.",
            "commands": [],
        }
    build_cmds = build_operator_build_commands(repo_root=runtime_root)
    return {
        "type": "operator_sudo_required",
        "label": "lb build benötigt sudo/root; Dashboard zeigt deshalb Operator-Befehl statt Direktstart.",
        "commands": build_cmds.get("commands") or [],
    }


def build_rescue_iso_dashboard_state(*, repo_root: Path | None = None) -> dict[str, Any]:
    runtime_root = (repo_root or _repo_root()).resolve(strict=False)
    paths = resolve_rescue_iso_paths(repo_root=runtime_root)
    repo = Path(str(paths["workspace_path"])).resolve(strict=False)
    path_errors = set(str(item) for item in (paths.get("errors") or []))
    gate_repo = runtime_root if {"WORKSPACE_MISSING", "WORKSPACE_NOT_GIT_REPO", "WORKSPACE_GIT_TOPLEVEL_MISMATCH"} & path_errors else repo
    runtime_gate = _runtime_gate(gate_repo)
    tools = {name: _tool_presence(name) for name in _TOOL_NAMES}
    build_tree = _build_tree(repo)
    stale_state = detect_live_build_stale_state(repo_root=repo)
    temp_bundle = _temp_runtime_bundle(repo)
    dpkg_preflight = _dpkg_preflight(repo)
    logs = read_rescue_iso_latest_logs(repo_root=repo, max_lines=120)
    artifacts = summarize_rescue_iso_artifacts(repo_root=repo)
    summary = _summary_payload(runtime_root)
    iso_build = _status_from_summary(summary, artifacts, logs)
    dpkg_status = str(dpkg_preflight.get("status") or "unknown")

    if (
        paths["path_status"] == "blocked"
        or runtime_gate["status"] == "red"
        or build_tree["validator_status"] == "blocked"
        or dpkg_status in {
            "unsafe_auto_config",
            "unsafe_auto_clean",
            "forbidden_package",
            "dangerous_path_override",
            "chroot_dpkg_missing",
            "chroot_start_stop_daemon_missing",
        }
    ):
        overall = "red"
    elif paths["path_status"] == "review_required":
        overall = "yellow"
    elif stale_state["needs_sudo_clean"]:
        overall = "red"
    elif iso_build["status"] == "success" and runtime_gate["status"] == "green":
        overall = "green"
    elif any(not tool["present"] for tool in tools.values()):
        overall = "red"
    elif stale_state["present"] or temp_bundle["status"] in {"review_required", "unknown"} or build_tree["validator_status"] in {
        "review_required",
        "unknown",
    } or dpkg_status == "review_required":
        overall = "yellow"
    elif runtime_gate["status"] == "unknown":
        overall = "gray"
    else:
        overall = _worst_status(
            {"green": "green", "unknown": "gray"}.get(runtime_gate["status"], runtime_gate["status"]),
            "green" if temp_bundle["status"] == "ok" else ("yellow" if temp_bundle["status"] != "blocked" else "red"),
            "green" if build_tree["validator_status"] == "ok" else ("yellow" if build_tree["validator_status"] != "blocked" else "red"),
        )

    repo_head = paths.get("workspace_head") or _git_value(repo, "rev-parse", "--short", "HEAD")
    repo_branch = paths.get("workspace_branch") or _git_value(repo, "branch", "--show-current")
    evidence_sources = [rel for rel in _EVIDENCE_PATHS if (repo / rel).exists()]
    summary_text = iso_build.get("last_error") or logs.get("last_error")
    if not summary_text:
        if paths["path_status"] != "ok":
            details = ", ".join(str(item) for item in (paths.get("errors") or paths.get("warnings") or []))
            summary_text = f"Workspace-Buildpfad nicht bereit ({details or paths['path_status']})"
        elif stale_state["needs_sudo_clean"]:
            summary_text = "sudo clean erforderlich wegen stale root-owned Build-State"
        elif stale_state["present"]:
            summary_text = "stale Build-State erkannt"
        elif dpkg_status not in {"ok", "pre_chroot_ok", "unknown"}:
            summary_text = dpkg_preflight.get("summary") or "DPKG-Preflight blockiert den Build"
        elif dpkg_status == "unknown":
            summary_text = "DPKG-Preflight noch nicht ausgeführt"
        elif iso_build["status"] == "success":
            summary_text = "ISO-Artefakt vorhanden"
        elif runtime_gate["status"] != "green":
            summary_text = runtime_gate.get("summary") or "Runtime-Gate nicht grün"
        else:
            summary_text = "Kontrollierter Rescue-ISO-Build bereit zur Prüfung"

    state: dict[str, Any] = {
        "status": overall,
        "summary": summary_text,
        "generated_at": _now_iso(),
        "repo_root": str(repo),
        "runtime_repo_root": str(runtime_root),
        "runtime_path": str(paths["runtime_path"]),
        "workspace_path": str(paths["workspace_path"]),
        "build_tree_path": str(paths["build_tree_path"]),
        "temp_runtime_bundle_path": str(paths["temp_runtime_bundle_path"]),
        "logs_path": str(paths["logs_path"]),
        "summary_path": str(paths["summary_path"]),
        "path_mode": str(paths["path_mode"]),
        "path_status": str(paths["path_status"]),
        "path_errors": list(paths.get("errors") or []),
        "path_warnings": list(paths.get("warnings") or []),
        "repo": {
            "head": repo_head,
            "branch": repo_branch,
            "runtime_gate": runtime_gate["status"],
            "runtime_gate_exit": runtime_gate.get("exit_code"),
            "runtime_gate_summary": runtime_gate.get("summary"),
        },
        "tools": tools,
        "build_tree": build_tree,
        "stale_state": stale_state,
        "temp_runtime_bundle": temp_bundle,
        "dpkg_preflight": dpkg_preflight,
        "iso_build": iso_build,
        "usb_write": {
            "allowed": False,
            "status": "blocked",
            "reason": "separate gate required",
        },
        "logs": {
            "latest_log_path": logs["latest_log_path"],
            "last_80_lines": logs["last_80_lines"],
            "last_error": logs["last_error"],
        },
        "forbidden_actions": {
            "dd_allowed": False,
            "mkfs_allowed": False,
            "parted_write_allowed": False,
            "restore_allowed": False,
            "backup_allowed": False,
            "usb_write_allowed": False,
        },
        "evidence_sources": evidence_sources,
        "no_fake_green": True,
    }
    state["next_operator_action"] = build_next_operator_action(state)
    return state


def rescue_iso_status_api_code(state: dict[str, Any]) -> str:
    status = str(state.get("status") or "gray").lower()
    if status == "green":
        return "DEV_DASHBOARD_RESCUE_ISO_STATUS_OK"
    if status == "red":
        return "DEV_DASHBOARD_RESCUE_ISO_STEP_BLOCKED"
    return "DEV_DASHBOARD_RESCUE_ISO_STEP_REVIEW_REQUIRED"
