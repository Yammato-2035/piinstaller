"""
Development Cockpit: read-only Aggregation aus Repo-Dateien, Gates und Laufzeit-Snapshots.

Keine externen Netzwerkzugriffe. Fehlende Dateien/Rechte fuehren nicht zu 500 — es werden
Warnungen/Eintraege in ``warnings``/``errors`` gesetzt.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

UTC = timezone.utc

# Deploy-Drift-Dateiliste = kanonisches Deployment-Manifest (core.deploy_manifest).
from core.deploy_manifest import (
    DEPLOY_MANIFEST_REL_PATHS,
    manifest_drift_for_roots,
    safe_path_is_dir,
    safe_path_is_file,
)

DEPLOY_DRIFT_REL_PATHS = DEPLOY_MANIFEST_REL_PATHS

# Read-only Deploy-Drift: nur kleine/mittlere Text-Dateien hashen; groessere per Groesse+mtime.
DEPLOY_DRIFT_MAX_HASH_BYTES = 384 * 1024


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent


def _safe_read_json(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    try:
        if not _safe_is_file(path):
            return None, f"missing:{path}"
        raw = path.read_text(encoding="utf-8", errors="replace")
        return json.loads(raw), None
    except Exception as exc:  # noqa: BLE001
        return None, f"read_error:{path}:{exc}"


def _safe_is_file(path: Path) -> bool:
    """Lesbarkeit unter ProtectHome+ReadOnlyPaths (siehe deploy_manifest.safe_path_is_file)."""
    return safe_path_is_file(path)


def _safe_is_dir(path: Path) -> bool:
    return safe_path_is_dir(path)


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


def _configured_workspace_path(raw: str) -> Path | None:
    """
    Workspace-Pfad aus Env oder .env.

    Unter systemd (ProtectHome=yes) kann is_dir() auf /home/... fehlschlagen, obwohl der Pfad
    per ReadOnlyPaths freigegeben ist — absoluter konfigurierter Pfad wird dann trotzdem genutzt.
    """
    s = (raw or "").strip()
    if not s:
        return None
    try:
        p = Path(s).expanduser()
        try:
            p = p.resolve()
        except OSError:
            pass
    except OSError:
        return None
    try:
        if p.is_dir():
            return p
    except OSError:
        pass
    try:
        if p.is_absolute() and len(p.parts) >= 2:
            return p
    except OSError:
        pass
    return None


def _workspace_root_from_dotenv(repo: Path) -> Path | None:
    """Liest SETUPHELFER_DEV_WORKSPACE_ROOT aus repo/.env (typ. /opt/setuphelfer/.env)."""
    env_path = repo / ".env"
    try:
        if not env_path.is_file():
            return None
        for line in env_path.read_text(encoding="utf-8", errors="replace").splitlines():
            s = line.strip()
            if not s or s.startswith("#") or "=" not in s:
                continue
            key, _, val = s.partition("=")
            if key.strip() != "SETUPHELFER_DEV_WORKSPACE_ROOT":
                continue
            raw = val.strip().strip('"').strip("'")
            return _configured_workspace_path(raw)
    except OSError:
        return None
    return None


def _effective_workspace_root(repo: Path) -> Path:
    """
    Optional: SETUPHELFER_DEV_WORKSPACE_ROOT zeigt auf einen Checkout (z. B. /home/.../piinstaller),
    während die API aus /opt/setuphelfer laeuft — dann unterscheiden sich Runtime- und Workspace-Version.
    """
    raw = (os.environ.get("SETUPHELFER_DEV_WORKSPACE_ROOT") or "").strip()
    if not raw:
        dot = _workspace_root_from_dotenv(repo)
        if dot is not None:
            return dot
        return repo
    cfg = _configured_workspace_path(raw)
    if cfg is not None:
        return cfg
    return repo


def _numeric_version_tuple(s: str) -> tuple[int, ...] | None:
    s = str(s).strip()
    if not s:
        return None
    nums: list[int] = []
    for chunk in s.replace("_", ".").split("."):
        if not chunk:
            continue
        acc = ""
        for ch in chunk:
            if ch.isdigit():
                acc += ch
            else:
                break
        if not acc:
            return None
        nums.append(int(acc))
    return tuple(nums) if nums else None


def _compare_dotted_versions(a: str, b: str) -> int | None:
    """-1 wenn a<b, 0 gleich, 1 wenn a>b; None wenn nicht vergleichbar."""
    ta, tb = _numeric_version_tuple(a), _numeric_version_tuple(b)
    if ta is None or tb is None:
        return None
    n = max(len(ta), len(tb))
    for i in range(n):
        va = ta[i] if i < len(ta) else 0
        vb = tb[i] if i < len(tb) else 0
        if va < vb:
            return -1
        if va > vb:
            return 1
    return 0


def _path_must_be_under(root: Path, candidate: Path) -> bool:
    try:
        candidate.resolve().relative_to(root.resolve())
        return True
    except (ValueError, OSError):
        return False


def _sha256_file_limited(path: Path, max_bytes: int) -> tuple[str | None, str | None]:
    """SHA256 des gesamten Files nur wenn size <= max_bytes; sonst (None, reason)."""
    try:
        st = path.stat()
    except OSError as exc:
        return None, f"stat_error:{exc}"
    if st.st_size > max_bytes:
        return None, "skipped_too_large_for_hash"
    try:
        digest = hashlib.sha256()
        with path.open("rb") as fh:
            while True:
                chunk = fh.read(65536)
                if not chunk:
                    break
                digest.update(chunk)
        return digest.hexdigest(), None
    except OSError as exc:
        return None, f"read_error:{exc}"


def _metadata_compare(wp: Path, rp: Path) -> tuple[bool | None, str | None]:
    """Groesse + mtime fuer grosse Dateien (kein Full-Hash)."""
    try:
        sw, sr = wp.stat(), rp.stat()
    except OSError as exc:
        return None, f"stat_error:{exc}"
    same_size = sw.st_size == sr.st_size
    same_mtime = int(sw.st_mtime) == int(sr.st_mtime)
    if same_size and same_mtime:
        return True, "compared_by_size_mtime"
    return False, "compared_by_size_mtime"


def _default_manifest_drift_slice() -> dict[str, Any]:
    return {
        "workspace_manifest_path": None,
        "runtime_manifest_path": None,
        "manifest_available_workspace": False,
        "manifest_available_runtime": False,
        "manifest_match": None,
        "manifest_warnings": [],
    }


def _append_manifest_suggestions(suggested: list[str], mw: list[str]) -> None:
    if not mw:
        return
    if "workspace_manifest_missing" in mw or "workspace_manifest_unreadable" in mw:
        if "generate_deploy_manifest" not in suggested:
            suggested.insert(0, "generate_deploy_manifest")
    if "runtime_manifest_missing" in mw:
        if "deploy_manifest_optional" not in suggested:
            suggested.append("deploy_manifest_optional")


def _dedupe_suggested_actions(suggested: list[str]) -> list[str]:
    out = list(dict.fromkeys(suggested))
    if any(x != "none" for x in out):
        out = [x for x in out if x != "none"]
    return out if out else ["none"]


def _merge_manifest_into_deploy_drift(
    *,
    drift_status: str,
    suggested: list[str],
    base: dict[str, Any],
    mf: dict[str, Any],
) -> dict[str, Any]:
    mw = mf.get("manifest_warnings") or []
    st = drift_status
    if mf.get("manifest_match") is False or (mw and st == "green"):
        st = "yellow"
    _append_manifest_suggestions(suggested, mw)
    sug = _dedupe_suggested_actions(suggested)
    out = {**base, **mf}
    out["status"] = st
    out["suggested_actions"] = sug
    return out


def _compute_deploy_drift(*, workspace_root: Path, runtime_root: Path) -> dict[str, Any]:
    """
    Read-only: Workspace-Checkout vs. produktiver Runtime-Baum (typ. /opt/setuphelfer).
    Drift → status yellow/gray; rot nur fuer globale Konsistenz, nicht hier.
    """
    dd_warnings: list[str] = []
    checked: list[dict[str, Any]] = []
    missing_rt: list[str] = []
    missing_ws: list[str] = []
    try:
        ws_r = workspace_root.expanduser().resolve()
    except OSError as exc:
        return {
            "status": "gray",
            "workspace_root": str(workspace_root),
            "runtime_root": str(runtime_root),
            "checked_files": [],
            "matching_files_count": 0,
            "differing_files_count": 0,
            "missing_runtime_files": [],
            "missing_workspace_files": [],
            "warnings": [f"workspace_root_resolve:{exc}"],
            "suggested_actions": ["none"],
            **_default_manifest_drift_slice(),
        }
    try:
        rt_r = runtime_root.expanduser().resolve()
    except OSError as exc:
        mf = manifest_drift_for_roots(workspace_root=ws_r, runtime_root=None)
        base = {
            "workspace_root": str(ws_r),
            "runtime_root": str(runtime_root),
            "checked_files": [],
            "matching_files_count": 0,
            "differing_files_count": 0,
            "missing_runtime_files": [],
            "missing_workspace_files": [],
            "warnings": [f"runtime_root_resolve:{exc}"],
        }
        return _merge_manifest_into_deploy_drift(
            drift_status="gray",
            suggested=["none"],
            base=base,
            mf=mf,
        )

    if ws_r == rt_r:
        mf = manifest_drift_for_roots(workspace_root=ws_r, runtime_root=ws_r)
        base = {
            "workspace_root": str(ws_r),
            "runtime_root": str(rt_r),
            "checked_files": [],
            "matching_files_count": 0,
            "differing_files_count": 0,
            "missing_runtime_files": [],
            "missing_workspace_files": [],
            "warnings": ["deploy_drift_same_workspace_and_runtime_root"],
        }
        return _merge_manifest_into_deploy_drift(
            drift_status="gray",
            suggested=["none"],
            base=base,
            mf=mf,
        )

    if not _safe_is_dir(rt_r):
        dd_warnings.append("runtime_root_not_a_directory")
        mf = manifest_drift_for_roots(workspace_root=ws_r, runtime_root=None)
        base = {
            "workspace_root": str(ws_r),
            "runtime_root": str(rt_r),
            "checked_files": [],
            "matching_files_count": 0,
            "differing_files_count": 0,
            "missing_runtime_files": [],
            "missing_workspace_files": [],
            "warnings": dd_warnings,
        }
        return _merge_manifest_into_deploy_drift(
            drift_status="gray",
            suggested=["none"],
            base=base,
            mf=mf,
        )

    match_n = 0
    diff_n = 0

    for rel in DEPLOY_DRIFT_REL_PATHS:
        rel = rel.replace("\\", "/").strip().lstrip("/")
        if ".." in rel.split("/"):
            dd_warnings.append(f"deploy_drift_invalid_rel:{rel}")
            continue
        try:
            wp = (ws_r / rel).resolve()
            rp = (rt_r / rel).resolve()
        except OSError as exc:
            checked.append(
                {
                    "relative_path": rel,
                    "workspace_path": str(ws_r / rel),
                    "runtime_path": str(rt_r / rel),
                    "workspace_sha256": None,
                    "runtime_sha256": None,
                    "matches": None,
                    "reason": f"resolve_error:{exc}",
                }
            )
            dd_warnings.append(f"resolve:{rel}:{exc}")
            continue
        if not _path_must_be_under(ws_r, wp) or not _path_must_be_under(rt_r, rp):
            checked.append(
                {
                    "relative_path": rel,
                    "workspace_path": str(wp),
                    "runtime_path": str(rp),
                    "workspace_sha256": None,
                    "runtime_sha256": None,
                    "matches": None,
                    "reason": "path_outside_root",
                }
            )
            dd_warnings.append(f"path_outside_root:{rel}")
            continue

        entry: dict[str, Any] = {
            "relative_path": rel,
            "workspace_path": str(wp),
            "runtime_path": str(rp),
            "workspace_sha256": None,
            "runtime_sha256": None,
            "matches": None,
            "reason": None,
        }
        ws_exists = _safe_is_file(wp)
        rt_exists = _safe_is_file(rp)
        if not ws_exists:
            missing_ws.append(rel)
            entry["reason"] = "missing_workspace"
            checked.append(entry)
            continue
        if not rt_exists:
            missing_rt.append(rel)
            entry["reason"] = "missing_runtime"
            checked.append(entry)
            continue

        try:
            wsz = wp.stat().st_size
            rsz = rp.stat().st_size
        except OSError as exc:
            entry["reason"] = f"stat_error:{exc}"
            entry["matches"] = None
            dd_warnings.append(f"stat:{rel}:{exc}")
            checked.append(entry)
            continue

        use_hash = max(wsz, rsz) <= DEPLOY_DRIFT_MAX_HASH_BYTES
        if use_hash:
            wh, werr = _sha256_file_limited(wp, DEPLOY_DRIFT_MAX_HASH_BYTES)
            rh, rerr = _sha256_file_limited(rp, DEPLOY_DRIFT_MAX_HASH_BYTES)
            entry["workspace_sha256"] = wh
            entry["runtime_sha256"] = rh
            if werr or rerr:
                entry["reason"] = werr or rerr
                entry["matches"] = None
                dd_warnings.append(f"hash_skipped:{rel}:{entry['reason']}")
            elif wh and rh:
                entry["matches"] = wh == rh
                entry["reason"] = "sha256" if entry["matches"] else "sha256_mismatch"
                if entry["matches"]:
                    match_n += 1
                else:
                    diff_n += 1
            else:
                entry["matches"] = None
                dd_warnings.append(f"hash_none:{rel}")
        else:
            meta_match, meta_reason = _metadata_compare(wp, rp)
            entry["matches"] = meta_match
            entry["reason"] = meta_reason
            if meta_match is True:
                match_n += 1
            elif meta_match is False:
                diff_n += 1
            else:
                dd_warnings.append(f"metadata:{rel}:{meta_reason}")

        checked.append(entry)

    suggested: list[str] = []
    rt_code_issue = (
        any(
            (
                str(e.get("relative_path", "")).startswith("backend/")
                or e.get("relative_path") == "config/version.json"
            )
            and e.get("matches") is False
            for e in checked
        )
        or any(m.startswith("backend/") or m == "config/version.json" for m in missing_rt)
    )
    fe_issue = any(
        str(e.get("relative_path", "")).startswith("frontend/") and e.get("matches") is False for e in checked
    ) or any(m.startswith("frontend/") for m in missing_rt)
    if missing_rt or rt_code_issue:
        suggested.extend(["deploy_backend_files", "restart_backend_manual"])
    if fe_issue:
        suggested.append("rebuild_frontend")
    if not suggested:
        suggested.append("none")
    suggested = list(dict.fromkeys(suggested))

    if diff_n == 0 and not missing_rt and not missing_ws and not dd_warnings and match_n > 0:
        drift_status = "green"
    elif not checked and not missing_rt and not missing_ws:
        drift_status = "gray"
    else:
        drift_status = "yellow"

    mf = manifest_drift_for_roots(workspace_root=ws_r, runtime_root=rt_r if _safe_is_dir(rt_r) else None)
    base = {
        "workspace_root": str(ws_r),
        "runtime_root": str(rt_r),
        "checked_files": checked,
        "matching_files_count": match_n,
        "differing_files_count": diff_n,
        "missing_runtime_files": missing_rt,
        "missing_workspace_files": missing_ws,
        "warnings": dd_warnings,
    }
    return _merge_manifest_into_deploy_drift(
        drift_status=drift_status,
        suggested=suggested,
        base=base,
        mf=mf,
    )


def _read_workspace_version_info(ws_root: Path) -> tuple[str | None, str | None, str | None]:
    """Liest config/version.json unter ws_root; keine Exceptions nach außen."""
    vf = ws_root / "config" / "version.json"
    try:
        from core.versioning import load_project_version

        vi = load_project_version(version_file=vf)
        return vi.project_version, vi.release_stage, vi.version_track
    except Exception:
        return None, None, None


def _git_workspace_detail(repo: Path) -> dict[str, Any]:
    """Git-Metadaten; fehlendes Git oder fehlende Upstream-Refs → null-Felder, kein Raise."""
    out: dict[str, Any] = {
        "git_head": None,
        "git_branch": None,
        "git_dirty_count": None,
        "git_unpushed_count": None,
    }
    try:
        hp = subprocess.run(
            ["git", "-C", str(repo), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            timeout=0.45,
            check=False,
        )
        if hp.returncode == 0:
            hx = (hp.stdout or "").strip()
            if hx:
                out["git_head"] = hx[:64]
        br = subprocess.run(
            ["git", "-C", str(repo), "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            timeout=0.35,
            check=False,
        )
        if br.returncode == 0:
            bx = (br.stdout or "").strip()
            if bx and bx != "HEAD":
                out["git_branch"] = bx
        st = subprocess.run(
            ["git", "-C", str(repo), "status", "--porcelain"],
            capture_output=True,
            text=True,
            timeout=0.55,
            check=False,
        )
        if st.returncode == 0:
            lines = [ln for ln in (st.stdout or "").splitlines() if ln.strip()]
            out["git_dirty_count"] = len(lines)
        up = subprocess.run(
            ["git", "-C", str(repo), "rev-list", "--count", "@{u}..HEAD"],
            capture_output=True,
            text=True,
            timeout=0.55,
            check=False,
        )
        if up.returncode == 0:
            raw_u = (up.stdout or "").strip()
            if raw_u.isdigit():
                out["git_unpushed_count"] = int(raw_u)
    except Exception:
        pass
    return out


def _normalize_frontend_runtime_source(raw: str | None) -> str:
    s = str(raw or "").strip().lower()
    if s in {"dev", "build", "unknown"}:
        return s
    return "unknown"


def _build_runtime_workspace_sections(
    *,
    repo: Path,
    warnings: list[str],
    backend_version: str | None,
    install_profile: str | None,
    app_edition: str | None,
    release_stage: str | None,
    version_track: str | None,
    frontend_build_version: str | None,
    frontend_runtime_source: str,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    ws_root = _effective_workspace_root(repo)
    if ws_root != repo:
        warnings.append("workspace_root_from_env:SETUPHELFER_DEV_WORKSPACE_ROOT")

    ws_pv, ws_rs, ws_vt = _read_workspace_version_info(ws_root)
    if ws_pv is None and _safe_is_file(ws_root / "config" / "version.json"):
        warnings.append("workspace_version_unreadable")

    git_detail = _git_workspace_detail(ws_root)
    try:
        from core.install_paths import get_backend_runtime_dir

        backend_runtime_path = str(get_backend_runtime_dir().resolve())
    except Exception as exc:  # noqa: BLE001
        warnings.append(f"backend_runtime_path:{exc}")
        backend_runtime_path = ""

    runtime: dict[str, Any] = {
        "backend_api_reachable": True,
        "backend_version": backend_version,
        "backend_project_version": backend_version,
        "release_stage": release_stage,
        "version_track": version_track,
        "install_profile": install_profile,
        "backend_runtime_path": backend_runtime_path or None,
        "app_edition": app_edition,
    }

    workspace: dict[str, Any] = {
        "workspace_path": str(ws_root),
        "workspace_version": ws_pv,
        "workspace_release_stage": ws_rs,
        "workspace_version_track": ws_vt,
        "git_head": git_detail.get("git_head"),
        "git_branch": git_detail.get("git_branch"),
        "git_dirty_count": git_detail.get("git_dirty_count"),
        "git_unpushed_count": git_detail.get("git_unpushed_count"),
    }

    fe_src = _normalize_frontend_runtime_source(frontend_runtime_source)
    fe_ver = (frontend_build_version or "").strip() or None
    fe_matches: bool | None
    if fe_src == "dev" or fe_ver is None:
        fe_matches = None
    else:
        fe_matches = bool(backend_version) and fe_ver == (backend_version or "")

    frontend: dict[str, Any] = {
        "frontend_build_version": fe_ver,
        "frontend_runtime_source": fe_src,
        "frontend_version_matches_backend": fe_matches,
    }

    cw: list[str] = []
    if not backend_version:
        cw.append("version_unknown")
    if not ws_pv:
        cw.append("version_unknown")

    bw_match: bool | None = None
    if backend_version and ws_pv:
        bw_match = backend_version == ws_pv
        if not bw_match:
            cmp = _compare_dotted_versions(backend_version, ws_pv)
            if cmp == -1:
                cw.append("backend_runtime_outdated")
            elif cmp == 1:
                cw.append("workspace_behind_runtime")
            else:
                cw.append("version_divergence")

    fb_match: bool | None = None
    if fe_src == "dev":
        fb_match = None
    elif fe_ver is None:
        fb_match = None
    elif not backend_version:
        fb_match = None
    else:
        fb_match = fe_ver == backend_version
        if not fb_match:
            cw.append("frontend_build_outdated")

    dirty = git_detail.get("git_dirty_count")
    if isinstance(dirty, int) and dirty > 0:
        cw.append("workspace_dirty")
    unpushed = git_detail.get("git_unpushed_count")
    if isinstance(unpushed, int) and unpushed > 0:
        cw.append("workspace_unpushed")

    if not backend_version:
        status = "red"
    elif cw:
        status = "yellow"
    else:
        status = "green"

    consistency: dict[str, Any] = {
        "backend_workspace_match": bw_match,
        "frontend_backend_match": fb_match,
        "status": status,
        "warnings": sorted(set(cw)),
    }

    return runtime, workspace, frontend, consistency


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


_ALLOWED_TRAFFIC = frozenset({"green", "yellow", "red", "gray"})


def _as_str_list(val: Any) -> list[str]:
    if val is None:
        return []
    if isinstance(val, list):
        return [str(x) for x in val if x is not None and str(x).strip()]
    if isinstance(val, str) and val.strip():
        return [val.strip()]
    return []


def _normalize_traffic(raw: Any) -> tuple[str, str | None]:
    s = str(raw or "").strip().lower()
    if s in _ALLOWED_TRAFFIC:
        return s, None
    if s:
        return "gray", f"invalid_traffic:{raw!r}"
    return "gray", None


def _normalize_module_dict(data: dict[str, Any], warns: list[str], *, _depth: int = 0) -> dict[str, Any]:
    """Kanonisiert Modul-JSON: Ampel, Listenfelder, Kinder rekursiv. Keine Exceptions bei Randfaellen."""
    if _depth > 12:
        warns.append("module_children_depth_exceeded")
        return dict(data)
    out = dict(data)
    st, wnote = _normalize_traffic(out.get("status"))
    out["status"] = st
    if wnote:
        mid = str(out.get("id") or "?")
        warns.append(f"module:{mid}:{wnote}")

    for lk in (
        "next_steps",
        "blockers",
        "evidence_files",
        "prompt_files",
        "report_files",
        "docs",
        "faq",
        "knowledge_base",
        "diagnostics",
        "i18n",
        "tests",
        "commits",
    ):
        out[lk] = _as_str_list(out.get(lk))

    children_raw = out.get("children")
    kids: list[dict[str, Any]] = []
    if isinstance(children_raw, list):
        for idx, ch in enumerate(children_raw):
            if isinstance(ch, dict):
                kids.append(_normalize_module_dict(dict(ch), warns, _depth=_depth + 1))
            else:
                warns.append(f"module_child_not_object:{out.get('id')}:{idx}")
    out["children"] = kids

    if not isinstance(out.get("artifacts"), list):
        out["artifacts"] = []
    return out


def _load_module_definitions(repo: Path) -> tuple[list[dict[str, Any]], list[str]]:
    mods_dir = repo / "docs" / "dev-dashboard" / "modules"
    warns: list[str] = []
    modules: list[dict[str, Any]] = []
    if not mods_dir.is_dir():
        warns.append(f"modules_dir_missing:{mods_dir}")
        return modules, warns
    seen_ids: set[str] = set()
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
        data = _normalize_module_dict(data, warns)
        mid = str(data.get("id") or jp.stem).strip()
        if mid in seen_ids:
            warns.append(f"duplicate_module_id:{mid}")
        seen_ids.add(mid)
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
    frontend_build_version: str | None = None,
    frontend_runtime_source: str | None = None,
) -> dict[str, Any]:
    repo = repo_root or _repo_root()
    warnings: list[str] = []
    errors: list[str] = []
    generated = datetime.now(tz=UTC).isoformat()

    backend_version = None
    release_stage_rt: str | None = None
    version_track_rt: str | None = None
    install_profile = None
    app_edition = None
    try:
        from core.versioning import load_project_version

        vi = load_project_version()
        backend_version = vi.project_version
        release_stage_rt = vi.release_stage
        version_track_rt = vi.version_track
    except Exception as exc:  # noqa: BLE001
        warnings.append(f"version_load:{exc}")

    try:
        from core.install_paths import get_install_profile

        install_profile = str(get_install_profile())
        raw_ed = (os.environ.get("APP_EDITION") or "").strip().lower()
        app_edition = raw_ed if raw_ed in ("repo", "release") else "release"
    except Exception as exc:  # noqa: BLE001
        warnings.append(f"edition_load:{exc}")

    fe_src = _normalize_frontend_runtime_source(frontend_runtime_source)
    runtime, workspace, frontend, consistency = _build_runtime_workspace_sections(
        repo=repo,
        warnings=warnings,
        backend_version=backend_version,
        install_profile=install_profile,
        app_edition=app_edition,
        release_stage=release_stage_rt,
        version_track=version_track_rt,
        frontend_build_version=frontend_build_version,
        frontend_runtime_source=fe_src,
    )

    try:
        from core.install_paths import get_opt_install_dir

        runtime_install_root = get_opt_install_dir().resolve()
    except OSError as exc:
        warnings.append(f"deploy_drift_opt_resolve:{exc}")
        try:
            runtime_install_root = Path("/opt/setuphelfer").resolve()
        except OSError:
            runtime_install_root = Path("/opt/setuphelfer")

    ws_for_drift = _effective_workspace_root(repo)
    deploy_drift = _compute_deploy_drift(workspace_root=ws_for_drift, runtime_root=runtime_install_root)

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

    body: dict[str, Any] = {
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
        "runtime": runtime,
        "workspace": workspace,
        "frontend": frontend,
        "consistency": consistency,
        "deploy_drift": deploy_drift,
        "warnings": warnings,
        "errors": errors,
    }
    try:
        from core.dev_dashboard_cockpit import enrich_dashboard_cockpit

        enrich_dashboard_cockpit(body, repo_root=repo)
    except Exception as exc:  # noqa: BLE001
        warnings.append(f"cockpit_enrich:{exc}")
        body["updated_at"] = generated
    return body


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
    warns: list[str] = []
    for jp in sorted(mods_dir.glob("*.json")):
        data, err = _safe_read_json(jp)
        if err or not isinstance(data, dict):
            continue
        if str(data.get("id") or "").strip() == mid or jp.stem == mid:
            norm = _normalize_module_dict(dict(data), warns)
            return {"status": "success", "module_id": str(data.get("id") or mid), "module": _enrich_artifacts(repo, norm), "warnings": warns}
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
