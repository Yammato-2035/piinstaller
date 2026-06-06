"""
Post-Deploy-Verifikation: kritische Runtime-Dateien und OpenAPI-Routen.

Wird von deploy-to-opt.sh nach rsync und nach Backend-Restart aufgerufen.
Keine Secrets, kein Schreibzugriff auf /opt.
"""

from __future__ import annotations

import hashlib
import json
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from core.deploy_manifest import DEPLOY_MANIFEST_REL_PATHS

# Zusaetzliche Backend-Module, die nach rsync in /opt existieren muessen
# (auch wenn sie noch nicht im generierten Manifest liegen).
DEPLOY_RUNTIME_EXTRA_BACKEND_PATHS: tuple[str, ...] = (
    "backend/core/dev_dashboard_compact_status.py",
    "backend/core/developer_capability.py",
    "backend/core/dev_dashboard_status_service.py",
    "backend/core/profile_deploy_manifest.py",
    "backend/core/rescue_telemetry_ingest.py",
    "backend/rescue_telemetry/__init__.py",
    "backend/rescue_telemetry/routers.py",
)

DEPLOY_RUNTIME_CRITICAL_REL_PATHS: tuple[str, ...] = tuple(
    dict.fromkeys(
        list(DEPLOY_MANIFEST_REL_PATHS) + list(DEPLOY_RUNTIME_EXTRA_BACKEND_PATHS)
    )
)

DEPLOY_OPENAPI_REQUIRED_PATHS: tuple[str, ...] = (
    "/api/dev-dashboard/compact-status",
)

APP_ROUTE_MARKERS: tuple[tuple[str, str], ...] = (
    ("/api/dev-dashboard/compact-status", "dev_dashboard_compact_status"),
)


class DeployRuntimeVerifyError(Exception):
    """Mindestens eine Post-Deploy-Pruefung ist fehlgeschlagen."""


def _sha256_file(path: Path) -> str | None:
    try:
        h = hashlib.sha256()
        with path.open("rb") as fh:
            while True:
                chunk = fh.read(65536)
                if not chunk:
                    break
                h.update(chunk)
        return h.hexdigest()
    except OSError:
        return None


def verify_runtime_files(
    *,
    workspace_root: Path,
    runtime_root: Path,
    rel_paths: tuple[str, ...] | None = None,
) -> dict[str, Any]:
    """
    Prueft, dass Runtime-Dateien existieren und (wenn in Workspace vorhanden)
    denselben SHA256 haben.
    """
    paths = rel_paths or DEPLOY_RUNTIME_CRITICAL_REL_PATHS
    missing_runtime: list[str] = []
    missing_workspace: list[str] = []
    sha256_mismatch: list[str] = []
    checked: list[dict[str, Any]] = []

    try:
        ws_root = workspace_root.expanduser().resolve()
        rt_root = runtime_root.expanduser().resolve()
    except OSError as exc:
        return {
            "ok": False,
            "error": f"root_resolve_failed:{exc}",
            "missing_runtime": [],
            "missing_workspace": [],
            "sha256_mismatch": [],
            "checked": [],
        }

    for rel in paths:
        clean = rel.replace("\\", "/").strip().lstrip("/")
        wp = ws_root / clean
        rp = rt_root / clean
        entry: dict[str, Any] = {"relative_path": clean}
        ws_exists = wp.is_file()
        rt_exists = rp.is_file()
        entry["workspace_exists"] = ws_exists
        entry["runtime_exists"] = rt_exists

        if not ws_exists:
            missing_workspace.append(clean)
        elif not rt_exists:
            missing_runtime.append(clean)

        if ws_exists and rt_exists:
            wh = _sha256_file(wp)
            rh = _sha256_file(rp)
            entry["workspace_sha256"] = wh
            entry["runtime_sha256"] = rh
            if wh and rh and wh != rh:
                sha256_mismatch.append(clean)
        checked.append(entry)

    ok = not missing_runtime and not sha256_mismatch
    return {
        "ok": ok,
        "missing_runtime": missing_runtime,
        "missing_workspace": missing_workspace,
        "sha256_mismatch": sha256_mismatch,
        "checked_count": len(checked),
        "checked": checked,
    }


def verify_app_route_markers(*, runtime_root: Path) -> dict[str, Any]:
    """Prueft, dass app.py die erwarteten Route-Deklarationen enthaelt."""
    try:
        rt_root = runtime_root.expanduser().resolve()
    except OSError as exc:
        return {"ok": False, "error": f"runtime_resolve_failed:{exc}", "missing_markers": []}

    app_py = rt_root / "backend" / "app.py"
    if not app_py.is_file():
        return {"ok": False, "missing_markers": ["backend/app.py"], "app_py_exists": False}

    try:
        text = app_py.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return {"ok": False, "missing_markers": ["backend/app.py:read_failed"], "error": str(exc)}

    missing: list[str] = []
    for route, marker in APP_ROUTE_MARKERS:
        if route not in text or marker not in text:
            missing.append(f"{route}:{marker}")
    return {"ok": not missing, "missing_markers": missing, "app_py_exists": True}


def verify_openapi_paths(*, base_url: str, paths: tuple[str, ...] | None = None) -> dict[str, Any]:
    """Liest /openapi.json und prueft, ob erwartete Pfade registriert sind."""
    required = paths or DEPLOY_OPENAPI_REQUIRED_PATHS
    url = base_url.rstrip("/") + "/openapi.json"
    try:
        with urllib.request.urlopen(url, timeout=8) as resp:
            raw = resp.read()
        data = json.loads(raw.decode("utf-8"))
    except urllib.error.HTTPError as exc:
        return {"ok": False, "error": f"http_error:{exc.code}", "missing_paths": list(required)}
    except Exception as exc:
        return {"ok": False, "error": f"fetch_failed:{exc}", "missing_paths": list(required)}

    openapi_paths = data.get("paths") if isinstance(data, dict) else None
    if not isinstance(openapi_paths, dict):
        return {"ok": False, "error": "openapi_paths_missing", "missing_paths": list(required)}

    registered = set(openapi_paths.keys())
    missing = [p for p in required if p not in registered]
    return {
        "ok": not missing,
        "missing_paths": missing,
        "registered_count": len(registered),
    }


def run_post_rsync_verify(*, workspace_root: Path, runtime_root: Path) -> dict[str, Any]:
    files = verify_runtime_files(workspace_root=workspace_root, runtime_root=runtime_root)
    routes = verify_app_route_markers(runtime_root=runtime_root)
    ok = bool(files.get("ok")) and bool(routes.get("ok"))
    return {"phase": "post_rsync", "ok": ok, "files": files, "app_routes": routes}


def run_post_restart_verify(
    *,
    base_url: str,
    workspace_root: Path | None = None,
    runtime_root: Path | None = None,
) -> dict[str, Any]:
    openapi = verify_openapi_paths(base_url=base_url)
    version_check: dict[str, Any] | None = None
    if workspace_root is not None and runtime_root is not None:
        from core.version_consistency import check_runtime_consistency

        api_pv: str | None = None
        try:
            url = base_url.rstrip("/") + "/api/version"
            with urllib.request.urlopen(url, timeout=8) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            if isinstance(data, dict):
                api_pv = str(data.get("project_version") or "").strip() or None
        except Exception:
            api_pv = None
        version_check = check_runtime_consistency(
            workspace_root=workspace_root,
            runtime_root=runtime_root,
            api_project_version=api_pv,
        )
    ok = bool(openapi.get("ok"))
    if version_check is not None:
        ok = ok and bool(version_check.get("ok"))
    return {
        "phase": "post_restart",
        "ok": ok,
        "openapi": openapi,
        "version_consistency": version_check,
    }


def run_verify(
    *,
    workspace_root: Path,
    runtime_root: Path,
    phase: str,
    base_url: str | None = None,
) -> tuple[bool, dict[str, Any]]:
    phase_norm = (phase or "").strip().lower().replace("-", "_")
    if phase_norm == "post_rsync":
        report = run_post_rsync_verify(workspace_root=workspace_root, runtime_root=runtime_root)
        return bool(report.get("ok")), report
    if phase_norm == "post_restart":
        if not base_url:
            return False, {"phase": "post_restart", "ok": False, "error": "base_url_required"}
        report = run_post_restart_verify(
            base_url=base_url,
            workspace_root=workspace_root,
            runtime_root=runtime_root,
        )
        return bool(report.get("ok")), report
    if phase_norm == "all":
        rsync_ok, rsync_report = run_verify(
            workspace_root=workspace_root,
            runtime_root=runtime_root,
            phase="post_rsync",
        )
        restart_ok, restart_report = run_verify(
            workspace_root=workspace_root,
            runtime_root=runtime_root,
            phase="post_restart",
            base_url=base_url or "http://127.0.0.1:8000",
        )
        report = {"phase": "all", "post_rsync": rsync_report, "post_restart": restart_report}
        return rsync_ok and restart_ok, report
    return False, {"ok": False, "error": f"unknown_phase:{phase!r}"}
