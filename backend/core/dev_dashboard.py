"""
Development Cockpit: read-only Aggregation aus Repo-Dateien, Gates und Laufzeit-Snapshots.

Keine externen Netzwerkzugriffe. Fehlende Dateien/Rechte fuehren nicht zu 500 — es werden
Warnungen/Eintraege in ``warnings``/``errors`` gesetzt.
"""

from __future__ import annotations

import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

UTC = timezone.utc


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent


def _safe_read_json(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    try:
        if not path.is_file():
            return None, f"missing:{path}"
        raw = path.read_text(encoding="utf-8", errors="replace")
        return json.loads(raw), None
    except Exception as exc:  # noqa: BLE001
        return None, f"read_error:{path}:{exc}"


def _walk_files_under(base: Path, *, rel_root: Path | None, max_files: int = 400) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    if not base.exists():
        return out
    try:
        for root, _dirs, files in os.walk(base):
            for fn in files:
                if len(out) >= max_files:
                    return out
                fp = Path(root) / fn
                rel_s: str
                if rel_root is not None:
                    try:
                        rel_s = str(fp.relative_to(rel_root)).replace("\\", "/")
                    except ValueError:
                        rel_s = str(fp)
                else:
                    rel_s = str(fp)
                try:
                    st = fp.stat()
                    out.append(
                        {
                            "path": rel_s,
                            "abs_path": str(fp),
                            "size": int(st.st_size),
                            "mtime_iso": datetime.fromtimestamp(st.st_mtime, tz=UTC).isoformat(),
                        }
                    )
                except OSError:
                    out.append({"path": rel_s, "abs_path": str(fp), "size": None, "mtime_iso": None})
    except OSError:
        return out
    return out


def _git_summary(repo: Path) -> dict[str, Any] | None:
    try:
        proc = subprocess.run(
            ["git", "-C", str(repo), "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            timeout=0.5,
            check=False,
        )
        if proc.returncode != 0:
            return None
        h = (proc.stdout or "").strip()
        if not h:
            return None
        return {"commit_short": h[:40]}
    except Exception:
        return None


def _mount_summary_minimal() -> list[dict[str, str]]:
    """Read-only: erste Zeilen von /proc/mounts (kein findmnt/sudo)."""
    out: list[dict[str, str]] = []
    try:
        lines = Path("/proc/mounts").read_text(encoding="utf-8", errors="replace").splitlines()[:40]
    except OSError:
        return out
    for ln in lines:
        parts = ln.split()
        if len(parts) >= 2:
            out.append({"device": parts[0][:80], "mountpoint": parts[1][:120], "fstype": parts[2] if len(parts) > 2 else ""})
    return out


def _load_module_definitions(repo: Path) -> tuple[list[dict[str, Any]], list[str]]:
    mods_dir = repo / "docs" / "dev-dashboard" / "modules"
    warns: list[str] = []
    modules: list[dict[str, Any]] = []
    if not mods_dir.is_dir():
        warns.append(f"modules_dir_missing:{mods_dir}")
        return modules, warns
    for jp in sorted(mods_dir.glob("*.json")):
        data, err = _safe_read_json(jp)
        if err or not data:
            warns.append(err or f"invalid_json:{jp}")
            continue
        if not isinstance(data, dict):
            warns.append(f"module_not_object:{jp}")
            continue
        data = dict(data)
        data["_source_file"] = str(jp.relative_to(repo)).replace("\\", "/")
        modules.append(data)
    return modules, warns


def _enrich_artifacts(repo: Path, mod: dict[str, Any]) -> dict[str, Any]:
    """Ergaenzt Modul-JSON um exists-Flags fuer Pfade (read-only)."""
    out = dict(mod)
    arts: list[dict[str, Any]] = []
    for spec in mod.get("artifacts") or []:
        if not isinstance(spec, dict):
            continue
        rel = str(spec.get("path") or "").strip()
        kind = str(spec.get("kind") or "doc")
        lang = spec.get("language")
        p = (repo / rel).resolve()
        exists = False
        try:
            exists = p.is_file() or p.is_dir()
        except OSError:
            exists = False
        arts.append(
            {
                "path": rel,
                "exists": exists,
                "kind": kind,
                "language": lang,
                "status": spec.get("status"),
            }
        )
    out["artifact_status"] = arts
    return out


def build_dashboard_status(
    *,
    repo_root: Path | None = None,
    running_jobs: list[dict[str, Any]] | None = None,
    package_activity: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    repo = repo_root or _repo_root()
    warnings: list[str] = []
    errors: list[str] = []
    generated = datetime.now(tz=UTC).isoformat()

    backend_version = None
    install_profile = None
    app_edition = None
    try:
        from core.versioning import load_project_version

        vi = load_project_version()
        backend_version = vi.project_version
    except Exception as exc:  # noqa: BLE001
        warnings.append(f"version_load:{exc}")

    try:
        from core.settings import get_app_edition, get_install_profile

        install_profile = str(get_install_profile())
        app_edition = str(get_app_edition())
    except Exception as exc:  # noqa: BLE001
        warnings.append(f"edition_load:{exc}")

    gate_path = repo / "docs" / "evidence" / "release-gates" / "backup_restore_release_gate.json"
    gate, gerr = _safe_read_json(gate_path)
    if gerr:
        warnings.append(gerr)
    release_gate_status = "unknown"
    if isinstance(gate, dict):
        release_gate_status = str(gate.get("ampel") or gate.get("status") or "unknown")

    matrix_hint: dict[str, Any] = {}
    for rel in ("docs/roadmap/STATUS_MATRIX.md", "docs/testing/BACKUP_RESTORE_TEST_MATRIX.md"):
        p = repo / rel
        try:
            if p.is_file():
                txt = p.read_text(encoding="utf-8", errors="replace")
                matrix_hint[rel] = {"exists": True, "lines": len(txt.splitlines())}
            else:
                matrix_hint[rel] = {"exists": False}
        except OSError as exc:
            matrix_hint[rel] = {"exists": False, "error": str(exc)}

    return {
        "generated_at": generated,
        "backend_version": backend_version,
        "install_profile": install_profile,
        "app_edition": app_edition,
        "backend_running": True,
        "release_gate_status": release_gate_status,
        "release_gate_path": str(gate_path.relative_to(repo)).replace("\\", "/") if gate_path.is_file() else str(gate_path),
        "active_backup_jobs": list(running_jobs or []),
        "mount_summary": _mount_summary_minimal(),
        "package_activity_summary": {"count": len(package_activity or []), "samples": (package_activity or [])[:5]},
        "git_summary": _git_summary(repo),
        "matrix_files": matrix_hint,
        "warnings": warnings,
        "errors": errors,
    }


def build_modules_list(repo_root: Path | None = None) -> dict[str, Any]:
    repo = repo_root or _repo_root()
    warnings: list[str] = []
    modules, w = _load_module_definitions(repo)
    warnings.extend(w)
    enriched = [_enrich_artifacts(repo, m) for m in modules]
    return {"status": "success", "modules": enriched, "warnings": warnings}


def build_module_detail(module_id: str, repo_root: Path | None = None) -> dict[str, Any]:
    repo = repo_root or _repo_root()
    mid = (module_id or "").strip()
    if not mid:
        return {"status": "error", "module_id": "", "warnings": ["empty_module_id"], "module": None}
    mods_dir = repo / "docs" / "dev-dashboard" / "modules"
    if not mods_dir.is_dir():
        return {"status": "error", "module_id": mid, "warnings": ["modules_dir_missing"], "module": None}
    for jp in sorted(mods_dir.glob("*.json")):
        data, err = _safe_read_json(jp)
        if err or not isinstance(data, dict):
            continue
        if str(data.get("id") or "").strip() == mid or jp.stem == mid:
            return {"status": "success", "module_id": str(data.get("id") or mid), "module": _enrich_artifacts(repo, data), "warnings": []}
    return {"status": "error", "module_id": mid, "warnings": ["module_not_found"], "module": None}


def build_evidence_index(repo_root: Path | None = None, *, max_files: int = 400) -> dict[str, Any]:
    repo = repo_root or _repo_root()
    warnings: list[str] = []
    buckets: list[dict[str, Any]] = []

    doc_ev = repo / "docs" / "evidence"
    if doc_ev.exists():
        items = _walk_files_under(doc_ev, rel_root=repo, max_files=max_files)
        buckets.append({"root": str(doc_ev.relative_to(repo)).replace("\\", "/"), "count": len(items), "files": items})
    else:
        warnings.append("docs_evidence_missing")

    var_ev = Path("/var/lib/setuphelfer/evidence")
    if var_ev.exists():
        try:
            var_items = _walk_files_under(var_ev, rel_root=None, max_files=min(120, max_files))
            buckets.append({"root": str(var_ev), "count": len(var_items), "files": var_items})
        except OSError as exc:
            warnings.append(f"var_evidence_list:{exc}")
    else:
        buckets.append({"root": str(var_ev), "count": 0, "files": [], "note": "not_present_or_no_access"})

    return {"status": "success", "buckets": buckets, "warnings": warnings}


def action_placeholder_response(action: str) -> dict[str, Any]:
    if action == "restart-backend":
        return {
            "status": "success",
            "action": action,
            "result": "not_implemented_safe",
            "confirm_required": True,
            "message_key": "devDashboard.actions.restartBackendNotImplemented",
        }
    if action == "start-backup":
        return {
            "status": "success",
            "action": action,
            "result": "use_existing_backup_api",
            "confirm_required": True,
            "message_key": "devDashboard.actions.startBackupUseExistingApi",
        }
    return {
        "status": "error",
        "action": action,
        "result": "unknown_action",
        "confirm_required": False,
        "message_key": "devDashboard.actions.unknownAction",
    }
