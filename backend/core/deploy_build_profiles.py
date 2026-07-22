"""Deployment build profiles for /opt runtime vs desktop/Tauri (PI-OPT-DEPLOY-TAURI-001)."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEPLOY_PROFILES = (
    "runtime-opt",
    "desktop-development",
    "desktop-release",
    "rescue-payload",
    "package-release",
)

DEFAULT_DEPLOY_PROFILE = "runtime-opt"


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _read_project_version(repo_root: Path) -> str:
    path = repo_root / "config" / "version.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return str(data.get("project_version") or "").strip()
    except (OSError, json.JSONDecodeError, TypeError):
        return ""


def _read_payload_version(repo_root: Path) -> str:
    path = repo_root / "config" / "rescue_payload_version.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return str(data.get("rescue_payload_version") or "").strip()
    except (OSError, json.JSONDecodeError, TypeError):
        return ""


def _git_identity(repo_root: Path) -> tuple[str, str, bool]:
    import subprocess

    commit = ""
    branch = ""
    dirty = False
    try:
        p = subprocess.run(
            ["git", "-C", str(repo_root), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            timeout=2,
            check=False,
        )
        if p.returncode == 0:
            commit = (p.stdout or "").strip()
        b = subprocess.run(
            ["git", "-C", str(repo_root), "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            timeout=2,
            check=False,
        )
        if b.returncode == 0:
            bx = (b.stdout or "").strip()
            if bx and bx != "HEAD":
                branch = bx
        d = subprocess.run(
            ["git", "-C", str(repo_root), "status", "--porcelain"],
            capture_output=True,
            text=True,
            timeout=3,
            check=False,
        )
        if d.returncode == 0 and (d.stdout or "").strip():
            dirty = True
    except Exception:
        pass
    return commit, branch, dirty


def normalize_deploy_profile(raw: str | None) -> str:
    profile = (raw or DEFAULT_DEPLOY_PROFILE).strip().lower().replace("_", "-")
    aliases = {
        "runtime": "runtime-opt",
        "opt": "runtime-opt",
        "desktop-dev": "desktop-development",
        "desktop": "desktop-release",
        "rescue": "rescue-payload",
        "package": "package-release",
    }
    profile = aliases.get(profile, profile)
    if profile not in DEPLOY_PROFILES:
        raise ValueError(f"unknown_deploy_profile:{profile}")
    return profile


def tauri_required_for_profile(profile: str, *, with_tauri: bool = False) -> bool:
    if with_tauri:
        return True
    return profile in {"desktop-development", "desktop-release", "package-release"}


def web_frontend_required_for_profile(profile: str) -> bool:
    return profile in {
        "runtime-opt",
        "desktop-development",
        "desktop-release",
        "package-release",
    }


def backend_required_for_profile(profile: str) -> bool:
    return profile in {
        "runtime-opt",
        "desktop-development",
        "desktop-release",
        "package-release",
    }


def build_deploy_plan(
    *,
    repo_root: Path,
    profile: str,
    target: str = "/opt/setuphelfer",
    with_tauri: bool = False,
) -> dict[str, Any]:
    profile = normalize_deploy_profile(profile)
    commit, branch, dirty = _git_identity(repo_root)
    app_ver = _read_project_version(repo_root)
    payload_ver = _read_payload_version(repo_root)
    tauri_req = tauri_required_for_profile(profile, with_tauri=with_tauri)
    web_req = web_frontend_required_for_profile(profile)
    backend_req = backend_required_for_profile(profile)
    rescue_req = profile == "rescue-payload"

    tauri_reason = "not_required_for_runtime_opt"
    if profile.startswith("desktop") or profile == "package-release":
        tauri_reason = "required_for_desktop_or_package_profile"
    if with_tauri and profile == "runtime-opt":
        tauri_reason = "explicit_with_tauri"

    return {
        "schema_version": 1,
        "generated_at": _utc_now(),
        "profile": profile,
        "target": target if profile == "runtime-opt" else None,
        "source_commit": commit,
        "source_commit_short": commit[:12] if commit else "",
        "source_branch": branch,
        "source_dirty": dirty,
        "application_version": app_ver,
        "rescue_payload_version": payload_ver,
        "components": {
            "backend": {
                "required": backend_req,
                "action": "copy_or_install" if backend_req else "skip",
            },
            "web_frontend": {
                "required": web_req,
                "action": "build" if web_req else "skip",
            },
            "tauri": {
                "required": tauri_req,
                "action": "build" if tauri_req else "skip",
                "reason": tauri_reason if not tauri_req else "profile_requires_tauri",
            },
            "rescue_payload": {
                "required": rescue_req,
                "action": "build" if rescue_req else "skip",
                "version": payload_ver,
            },
            "systemd": {
                "required": profile == "runtime-opt",
                "action": "install_or_sync" if profile == "runtime-opt" else "skip",
            },
            "deploy_manifest": {
                "required": profile == "runtime-opt",
                "action": "generate" if profile == "runtime-opt" else "skip",
            },
        },
        "commands_forbidden_unless_tauri": [
            "npm run tauri:build",
            "tauri build",
            "cargo build --release (src-tauri)",
        ],
        "services_expected": (
            ["setuphelfer-backend.service", "setuphelfer.service"]
            if profile == "runtime-opt"
            else []
        ),
    }
