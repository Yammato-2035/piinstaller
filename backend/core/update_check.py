"""
Lokale Versions-/Deploy-Konsistenz fuer das Development Dashboard.

Kein Netzwerk, kein Paketmanager, kein automatisches Update.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

from core.deploy_job_state import DEFAULT_RUNTIME_PATH, build_deploy_job_state
from core.deploy_manifest import _safe_read_manifest, runtime_manifest_candidates


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent


def _git_head(repo_root: Path) -> str | None:
    try:
        proc = subprocess.run(
            ["git", "-C", str(repo_root), "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            timeout=2,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if proc.returncode != 0:
        return None
    value = (proc.stdout or "").strip()
    return value or None


def _workspace_version(repo_root: Path) -> str | None:
    path = repo_root / "config" / "version.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(data, dict):
        return None
    value = str(data.get("project_version") or "").strip()
    return value or None


def _runtime_manifest(runtime_root: Path) -> dict[str, Any] | None:
    for candidate in runtime_manifest_candidates(runtime_root):
        payload, _ = _safe_read_manifest(candidate)
        if payload is not None:
            return payload
    return None


def build_update_status() -> dict[str, Any]:
    repo = _repo_root()
    deploy_state = build_deploy_job_state()
    drift = dict(deploy_state.get("deploy_drift") or {})
    runtime_manifest = _runtime_manifest(DEFAULT_RUNTIME_PATH)
    runtime_head = None
    package_version = None
    if isinstance(runtime_manifest, dict):
        runtime_head = str(runtime_manifest.get("git_commit") or "").strip() or None
        package_version = str(runtime_manifest.get("project_version") or "").strip() or None

    workspace_head = _git_head(repo)
    local_version = _workspace_version(repo)
    deploy_required = bool(
        deploy_state.get("runtime_gate", {}).get("exit_code") in {14, 15, 16}
        or drift.get("status") != "green"
        or drift.get("manifest_match") is False
    )

    status = "ok"
    if deploy_required:
        status = "deploy_required"
    if not workspace_head and not local_version:
        status = "blocked"

    return {
        "status": status,
        "local_version": local_version,
        "workspace_head": workspace_head,
        "runtime_head": runtime_head,
        "deploy_required": deploy_required,
        "update_available": "unknown",
        "automatic_update_allowed": False,
        "package_manager_update_allowed": False,
        "package_version": package_version,
        "next_action": "controlled_deploy" if deploy_required else "none",
    }
