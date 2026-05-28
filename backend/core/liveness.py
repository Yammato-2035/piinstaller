"""
Leichtgewichtige Liveness-/Versions-Payloads ohne Dashboard-, Git- oder Deploy-Drift-Pfade.

Ziel: /health und /api/version bleiben auch bei blockierten Dev-Dashboard-Workern erreichbar
(schnelle JSON-Antwort, keine Subprocess-Aufrufe im Health-Pfad).
"""

from __future__ import annotations

import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_UTC = timezone.utc
_VERSION_CACHE: dict[str, Any] | None = None


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent


def _version_json_path() -> Path:
    return _repo_root() / "config" / "version.json"


def _read_version_file_fast() -> dict[str, str] | None:
    """Einmaliges Lesen von config/version.json; Fehler → None (kein Raise im Health-Pfad)."""
    global _VERSION_CACHE
    if _VERSION_CACHE is not None:
        return _VERSION_CACHE
    env_pv = (os.environ.get("SETUPHELFER_PROJECT_VERSION") or "").strip()
    env_stage = (os.environ.get("SETUPHELFER_RELEASE_STAGE") or "").strip()
    env_track = (os.environ.get("SETUPHELFER_VERSION_TRACK") or "").strip()
    if env_pv and env_stage and env_track:
        _VERSION_CACHE = {
            "project_version": env_pv,
            "release_stage": env_stage,
            "version_track": env_track,
        }
        return _VERSION_CACHE
    vf = _version_json_path()
    try:
        raw = json.loads(vf.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            return None
        pv = str(raw.get("project_version") or "").strip()
        stage = str(raw.get("release_stage") or "").strip()
        track = str(raw.get("version_track") or "").strip()
        if not pv:
            return None
        _VERSION_CACHE = {
            "project_version": pv,
            "release_stage": stage or "internal_testing",
            "version_track": track or "main",
        }
        return _VERSION_CACHE
    except Exception:
        return None


def build_health_payload(*, runtime_path: str) -> dict[str, Any]:
    """Minimaler /health-Body: kein Git, kein Dashboard, kein subprocess."""
    version = "unknown"
    cached = _read_version_file_fast()
    if cached:
        version = cached["project_version"]
    return {
        "status": "ok",
        "service": "setuphelfer-backend",
        "version": version,
        "timestamp": datetime.now(tz=_UTC).isoformat(),
        "runtime_path": runtime_path,
    }


def _git_head_optional(repo_root: Path) -> str | None:
    if (os.environ.get("SETUPHELFER_VERSION_INCLUDE_GIT") or "").strip() not in ("1", "true", "yes"):
        return None
    try:
        proc = subprocess.run(
            ["git", "-C", str(repo_root), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            timeout=0.35,
            check=False,
        )
        if proc.returncode == 0:
            h = (proc.stdout or "").strip()
            if h:
                return h[:64]
    except Exception:
        pass
    return None


def build_version_api_payload(
    *,
    runtime_path: str,
    install_profile: str,
    app_edition: str,
) -> dict[str, Any]:
    """
    Schneller /api/version-Body ohne Dev-Dashboard.
    Git-Commit nur bei SETUPHELFER_VERSION_INCLUDE_GIT=1.
    """
    from core.versioning import api_version_error_code, load_project_version, version_config_path

    vf = version_config_path()
    try:
        info = load_project_version()
    except Exception as exc:  # noqa: BLE001
        code = api_version_error_code(exc)
        return {
            "_error": True,
            "status_code": 503,
            "body": {
                "status": "error",
                "code": code,
                "detail": str(exc),
                "version_config_path": str(vf),
                "blocked_update_required": True,
            },
        }

    build_time = (os.environ.get("SETUPHELFER_BUILD_TIME") or "").strip() or None
    git_commit = _git_head_optional(_repo_root())

    payload: dict[str, Any] = {
        "status": "success",
        "project_version": info.project_version,
        "version": info.project_version,
        "release_stage": info.release_stage,
        "version_track": info.version_track,
        "version_source_of_truth": True,
        "install_profile": install_profile,
        "app_edition": app_edition,
        "backend_runtime_path": runtime_path,
    }
    if build_time:
        payload["build_time"] = build_time
    if git_commit:
        payload["git_commit"] = git_commit
    return {"_error": False, "status_code": 200, "body": payload}
