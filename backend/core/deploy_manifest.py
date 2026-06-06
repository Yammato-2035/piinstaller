"""
Deployment-Manifest: kanonische Whitelist kleiner relevanter Dateien fuer Runtime-vs-Workspace.

Nur Metadaten/Hashes — keine Secrets, keine node_modules, keine Backups/Archive.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

UTC = timezone.utc

MANIFEST_VERSION = 1
MANIFEST_BASENAME = "setuphelfer-deploy-manifest.json"

# Relativ zum Repo-/Installationsroot; Reihenfolge stabil halten.
DEPLOY_MANIFEST_REL_PATHS: tuple[str, ...] = (
    "backend/app.py",
    "backend/core/versioning.py",
    "backend/core/install_paths.py",
    "backend/core/dev_dashboard.py",
    "backend/core/dev_dashboard_compact_status.py",
    "backend/core/dev_dashboard_status_service.py",
    "backend/core/developer_capability.py",
    "backend/core/profile_deploy_manifest.py",
    "backend/core/rescue_telemetry_ingest.py",
    "backend/rescue_telemetry/__init__.py",
    "backend/rescue_telemetry/routers.py",
    "backend/tools/backup_runner.py",
    "packaging/helpers/setuphelfer-backup-starter.py",
    "config/version.json",
    "frontend/package.json",
    "frontend/src/components/ApiRuntimeConsistencyBanner.tsx",
    "frontend/src/pages/DevDashboardBody.tsx",
)

# Voller SHA256 nur bis zu dieser Groesse; groessere Dateien sind fuer das Manifest nicht zulaessig.
DEPLOY_MANIFEST_MAX_FILE_BYTES = 2 * 1024 * 1024

_FORBIDDEN_REL_PARTS = (
    "node_modules",
    ".tar.gz",
    ".tar.bz2",
    ".partial",
    "/secrets/",
    ".pem",
    ".key",
)
_FORBIDDEN_EXACT = frozenset({".env"})


class DeployManifestError(Exception):
    """Pflichtdatei fehlt oder Pfad ist nicht erlaubt."""


def workspace_manifest_path(repo_root: Path) -> Path:
    return repo_root / "build" / "deploy" / MANIFEST_BASENAME


def runtime_manifest_candidates(runtime_root: Path) -> tuple[Path, Path]:
    """Zwei uebliche Ablageorte unter /opt/setuphelfer (nur lesend im Cockpit)."""
    return (
        runtime_root / "build" / "deploy" / MANIFEST_BASENAME,
        runtime_root / "deploy" / MANIFEST_BASENAME,
    )


def validate_manifest_relative_path(rel: str) -> str:
    r = rel.replace("\\", "/").strip().lstrip("/")
    if not r or ".." in r.split("/"):
        raise DeployManifestError(f"invalid_relative_path:{rel!r}")
    seg0 = r.split("/")[0].lower()
    if seg0 in _FORBIDDEN_EXACT or r.lower() in _FORBIDDEN_EXACT:
        raise DeployManifestError(f"forbidden_path:{rel!r}")
    low = r.lower()
    for bad in _FORBIDDEN_REL_PARTS:
        if bad in low:
            raise DeployManifestError(f"forbidden_segment:{rel!r}:{bad}")
    if re.search(r"\.env$", low) and not low.endswith(".env.example"):
        raise DeployManifestError(f"forbidden_env_file:{rel!r}")
    return r


def infer_file_kind(rel: str) -> str:
    if rel.startswith("backend/"):
        return "backend"
    if rel.startswith("frontend/"):
        return "frontend"
    if rel.startswith("config/"):
        return "config"
    if rel.startswith("packaging/"):
        return "packaging"
    if rel.endswith(".service") or "/systemd/" in rel:
        return "service"
    if rel.startswith("docs/"):
        return "docs"
    return "packaging"


def _sha256_file(path: Path, *, max_bytes: int) -> str:
    try:
        st = path.stat()
    except OSError as exc:
        raise DeployManifestError(f"stat_failed:{path}:{exc}") from exc
    if st.st_size > max_bytes:
        raise DeployManifestError(f"file_too_large_for_manifest:{path}:{st.st_size}>{max_bytes}")
    h = hashlib.sha256()
    with path.open("rb") as fh:
        while True:
            chunk = fh.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def _read_version_meta(repo_root: Path) -> tuple[str | None, str | None, str | None]:
    vf = repo_root / "config" / "version.json"
    try:
        raw = json.loads(vf.read_text(encoding="utf-8"))
    except Exception:
        return None, None, None
    if not isinstance(raw, dict):
        return None, None, None
    return (
        str(raw.get("project_version") or "").strip() or None,
        str(raw.get("release_stage") or "").strip() or None,
        str(raw.get("version_track") or "").strip() or None,
    )


def _git_head_branch(repo_root: Path) -> tuple[str | None, str | None]:
    commit: str | None = None
    branch: str | None = None
    try:
        p = subprocess.run(
            ["git", "-C", str(repo_root), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            timeout=0.45,
            check=False,
        )
        if p.returncode == 0:
            hx = (p.stdout or "").strip()
            if hx:
                commit = hx[:64]
        b = subprocess.run(
            ["git", "-C", str(repo_root), "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            timeout=0.35,
            check=False,
        )
        if b.returncode == 0:
            bx = (b.stdout or "").strip()
            if bx and bx != "HEAD":
                branch = bx
    except Exception:
        pass
    return commit, branch


def _app_edition_safe() -> str:
    try:
        from core.settings import get_app_edition

        return str(get_app_edition())
    except Exception:
        return "unknown"


def build_manifest_data(repo_root: Path) -> dict[str, Any]:
    """Baut das Manifest-Dict; wirft DeployManifestError bei fehlender Pflichtdatei oder Verbots-Pfad."""
    try:
        root = repo_root.expanduser().resolve()
    except OSError as exc:
        raise DeployManifestError(f"repo_resolve_failed:{exc}") from exc
    files_out: list[dict[str, Any]] = []
    for rel in DEPLOY_MANIFEST_REL_PATHS:
        clean = validate_manifest_relative_path(rel)
        fp = (root / clean).resolve()
        if not _path_under_root(root, fp):
            raise DeployManifestError(f"path_escape:{clean}")
        if not fp.is_file():
            raise DeployManifestError(f"missing_required_file:{clean}")
        digest = _sha256_file(fp, max_bytes=DEPLOY_MANIFEST_MAX_FILE_BYTES)
        st = fp.stat()
        files_out.append(
            {
                "relative_path": clean,
                "sha256": digest,
                "size_bytes": int(st.st_size),
                "kind": infer_file_kind(clean),
                "required_runtime": True,
                "runtime_path_hint": None,
            }
        )
    pv, stage, track = _read_version_meta(root)
    commit, branch = _git_head_branch(root)
    return {
        "manifest_version": MANIFEST_VERSION,
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "project_version": pv,
        "release_stage": stage,
        "version_track": track,
        "git_commit": commit,
        "git_branch": branch,
        "workspace_root": str(root),
        "app_edition": _app_edition_safe(),
        "files": files_out,
    }


def _path_under_root(root: Path, candidate: Path) -> bool:
    try:
        candidate.resolve().relative_to(root.resolve())
        return True
    except (ValueError, OSError):
        return False


def safe_path_is_file(path: Path) -> bool:
    """
    Zuverlaessiger als Path.is_file() unter systemd ProtectHome+ReadOnlyPaths:
    is_file() kann false liefern, obwohl os.stat/open lesbar ist.
    """
    try:
        return stat.S_ISREG(os.stat(path, follow_symlinks=True).st_mode)
    except OSError:
        return False


def safe_path_is_dir(path: Path) -> bool:
    try:
        return stat.S_ISDIR(os.stat(path, follow_symlinks=True).st_mode)
    except OSError:
        return False


def _safe_read_manifest(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    try:
        if not safe_path_is_file(path):
            return None, "missing"
        raw = path.read_text(encoding="utf-8", errors="replace")
        data = json.loads(raw)
        if not isinstance(data, dict):
            return None, "not_object"
        return data, None
    except json.JSONDecodeError as exc:
        return None, f"json_error:{exc}"
    except OSError as exc:
        return None, f"os_error:{exc}"


def file_hashes_from_manifest(data: dict[str, Any]) -> dict[str, str]:
    out: dict[str, str] = {}
    files = data.get("files")
    if not isinstance(files, list):
        return out
    for item in files:
        if not isinstance(item, dict):
            continue
        rel = str(item.get("relative_path") or "").strip().replace("\\", "/")
        hx = str(item.get("sha256") or "").strip().lower()
        if rel and len(hx) == 64:
            out[rel] = hx
    return out


def compare_manifest_payloads(ws: dict[str, Any] | None, rt: dict[str, Any] | None) -> tuple[bool | None, list[str]]:
    """Vergleicht Datei-Hashes; None wenn nicht vergleichbar."""
    warns: list[str] = []
    if ws is None and rt is None:
        return None, warns
    if ws is None or rt is None:
        return None, warns
    mv_ws = ws.get("manifest_version")
    mv_rt = rt.get("manifest_version")
    if mv_ws != mv_rt:
        warns.append(f"manifest_version_mismatch:{mv_ws!r}!={mv_rt!r}")
    hw = file_hashes_from_manifest(ws)
    hr = file_hashes_from_manifest(rt)
    if not hw or not hr:
        warns.append("manifest_files_empty")
        return None, warns
    if hw == hr:
        return True, warns
    only_ws = sorted(set(hw) - set(hr))
    only_rt = sorted(set(hr) - set(hw))
    diff = sorted(rel for rel in set(hw) & set(hr) if hw[rel] != hr[rel])
    if only_ws:
        warns.append(f"manifest_paths_only_workspace:{','.join(only_ws[:12])}")
    if only_rt:
        warns.append(f"manifest_paths_only_runtime:{','.join(only_rt[:12])}")
    if diff:
        warns.append(f"manifest_sha256_mismatch:{','.join(diff[:12])}")
    return False, warns


def manifest_drift_for_roots(*, workspace_root: Path, runtime_root: Path | None) -> dict[str, Any]:
    """Read-only: Pfade und Vergleich fuer deploy_drift (keine Exceptions nach außen)."""
    manifest_warnings: list[str] = []
    try:
        ws_r = workspace_root.expanduser().resolve()
    except OSError as exc:
        return {
            "workspace_manifest_path": None,
            "runtime_manifest_path": None,
            "manifest_available_workspace": False,
            "manifest_available_runtime": False,
            "manifest_match": None,
            "manifest_warnings": [f"workspace_root_resolve:{exc}"],
        }

    ws_mp = workspace_manifest_path(ws_r)
    workspace_manifest_path_str = str(ws_mp)
    ws_data, ws_err = _safe_read_manifest(ws_mp)
    manifest_available_workspace = ws_data is not None
    if not manifest_available_workspace:
        if ws_err == "missing":
            manifest_warnings.append("workspace_manifest_missing")
        elif ws_err:
            manifest_warnings.append("workspace_manifest_unreadable")

    rt_mp: Path | None = None
    rt_data: dict[str, Any] | None = None
    if runtime_root is not None:
        try:
            rt_r = runtime_root.expanduser().resolve()
        except OSError:
            rt_r = None
        if rt_r is not None and rt_r.is_dir():
            for cand in runtime_manifest_candidates(rt_r):
                d, _err = _safe_read_manifest(cand)
                if d is not None:
                    rt_mp = cand
                    rt_data = d
                    break
            if rt_data is None:
                manifest_warnings.append("runtime_manifest_missing")

    manifest_available_runtime = rt_data is not None
    runtime_manifest_path_str = str(rt_mp) if rt_mp else None

    if ws_data is not None and rt_data is not None:
        match, cmp_warns = compare_manifest_payloads(ws_data, rt_data)
        manifest_warnings.extend(cmp_warns)
    else:
        match = None

    return {
        "workspace_manifest_path": workspace_manifest_path_str,
        "runtime_manifest_path": runtime_manifest_path_str,
        "manifest_available_workspace": manifest_available_workspace,
        "manifest_available_runtime": manifest_available_runtime,
        "manifest_match": match,
        "manifest_warnings": manifest_warnings,
    }
