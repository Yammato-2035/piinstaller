from __future__ import annotations

import json
import os
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
_HANDOFF_ROOT = (_REPO_ROOT / "docs/evidence/runtime-results/handoff").resolve(strict=False)
_INVENTORY_REL = "docs/evidence/runtime-results/handoff/legacy_identifier_inventory.json"
_POSTCHECK_REL = "docs/evidence/runtime-results/handoff/setuphelfer_identifier_cleanup_cycle_1_postcheck.json"
_CONSISTENCY_REL = "docs/evidence/runtime-results/handoff/setuphelfer_identifier_consistency_check.json"
_OUT_REL = "docs/evidence/runtime-results/handoff/legacy_identifier_hotspot_analysis.json"
_MAX_OUTPUT_BYTES = 512 * 1024

_CLUSTERS_ORDERED = (
    "backend_runtime",
    "frontend_runtime",
    "env_config",
    "tauri",
    "scripts",
    "packaging",
    "api",
    "tests",
    "migration_alias",
    "historical_runtime_dependency",
    "unknown",
)


def _resolve_handoff(rel_path: str) -> tuple[Path | None, str | None]:
    raw = str(rel_path or "").strip()
    if not raw:
        return None, "HOTSPOT_ANALYSIS_PATH_INVALID"
    p = Path(raw)
    if p.is_absolute() or ".." in p.parts:
        return None, "HOTSPOT_ANALYSIS_PATH_INVALID"
    unresolved = _REPO_ROOT / p
    cur = unresolved
    while True:
        if cur.exists() and cur.is_symlink():
            return None, "HOTSPOT_ANALYSIS_SYMLINK_BLOCKED"
        if cur.parent == cur:
            break
        cur = cur.parent
    resolved = unresolved.resolve(strict=False)
    if not (str(resolved).startswith(str(_HANDOFF_ROOT) + os.sep) or str(resolved) == str(_HANDOFF_ROOT)):
        return None, "HOTSPOT_ANALYSIS_OUTSIDE_HANDOFF"
    return resolved, None


def _atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(content, encoding="utf-8")
    tmp.replace(path)


def _load_json_handoff(rel: str) -> tuple[Any | None, str | None]:
    p, err = _resolve_handoff(rel)
    if err or p is None or not p.is_file():
        return None, err or "HOTSPOT_ANALYSIS_INPUT_MISSING"
    try:
        return json.loads(p.read_text(encoding="utf-8")), None
    except Exception:
        return None, "HOTSPOT_ANALYSIS_INPUT_JSON_INVALID"


def _norm_hit(path: str, line: int | None, tokens: list[str], source: str) -> dict[str, Any]:
    rel = str(path or "").strip().replace("\\", "/")
    toks = [str(t) for t in tokens] if isinstance(tokens, list) else []
    ln = int(line or 0)
    return {"path": rel, "line": ln, "tokens": toks, "source": source}


def _hit_key(h: dict[str, Any]) -> tuple[str, int, tuple[str, ...]]:
    return (h["path"], int(h["line"]), tuple(sorted(h["tokens"])))


def _line_preview_for_hit(h: dict[str, Any]) -> str:
    rel = h.get("path") or ""
    line_no = int(h.get("line") or 0)
    if not rel or line_no <= 0:
        return ""
    fp = _REPO_ROOT / str(rel).replace("\\", "/")
    try:
        lines = fp.read_text(encoding="utf-8").splitlines()
        if 0 < line_no <= len(lines):
            return lines[line_no - 1]
    except OSError:
        return ""
    return ""


def _cluster(rel: str, tokens: list[str], line_preview: str) -> str:
    pl = rel.replace("\\", "/").lower()
    lt = (line_preview or "").lower()
    if (
        "migration" in pl
        or "compat_aliases" in pl
        or "compatibility_aliases" in pl
        or pl.endswith("compatibility_aliases.json")
        or pl.endswith("compat_aliases.json")
    ):
        return "migration_alias"
    if "historical" in lt and ("legacy" in lt or "deprecated" in lt):
        return "historical_runtime_dependency"
    if pl.startswith("backend/tests/") or "/test_" in pl or pl.endswith("_test.py") or "/tests/" in pl:
        return "tests"
    if pl.startswith("frontend/src-tauri/"):
        return "tauri"
    if pl.startswith("frontend/"):
        return "frontend_runtime"
    if pl in ("package.json", "frontend/package.json") or pl.startswith("debian/"):
        return "packaging"
    if pl.startswith("config/") or pl.endswith(".env") or "/.env" in pl:
        return "env_config"
    if "routes.py" in pl or "/api/" in pl or (pl.startswith("backend/") and "app.py" in pl):
        return "api"
    if pl.startswith("backend/"):
        return "backend_runtime"
    if pl.startswith("scripts/"):
        return "scripts"
    return "unknown"


def _is_comment_line(line_preview: str) -> bool:
    s = (line_preview or "").strip()
    return s.startswith("#") or s.startswith("//") or s.startswith("*")


def _criticality(rel: str, tokens: list[str], line_preview: str, cluster: str) -> str:
    pl = rel.replace("\\", "/").lower()
    lp = line_preview or ""
    stripped = lp.strip()
    if _is_comment_line(lp):
        if "PI_INSTALLER_" not in tokens and "/opt/pi-installer" not in tokens and "pi-installer.service" not in tokens:
            return "low"

    if "PI_INSTALLER_" in tokens or "/opt/pi-installer" in tokens or "pi-installer.service" in tokens:
        return "critical"
    if cluster == "tauri" or (cluster == "frontend_runtime" and "tauri" in pl):
        return "critical"
    if cluster == "api" or (cluster == "backend_runtime" and ("app.py" in pl or "routes.py" in pl)):
        return "critical"
    if cluster == "env_config":
        return "critical"

    if cluster == "scripts":
        base = Path(rel).name.lower()
        if "start" in base or "ensure" in base or "install" in base:
            return "high"
        if "dev" in base or "watch" in base:
            return "medium"
        return "high"

    if cluster == "packaging":
        return "high"

    if cluster == "tests":
        return "medium"

    if cluster == "migration_alias":
        return "low"

    if cluster == "historical_runtime_dependency":
        return "low"

    if cluster == "unknown":
        return "medium"

    if cluster == "backend_runtime" or cluster == "frontend_runtime":
        return "high"

    return "medium"


def _cleanup_priority_rank(hit: dict[str, Any]) -> tuple[int, int, int, str]:
    """Cleanup order: ENV, API/paths, Tauri, scripts, packaging, tests, comments last."""
    cluster_pri = {
        "env_config": 0,
        "api": 1,
        "backend_runtime": 2,
        "frontend_runtime": 3,
        "tauri": 4,
        "scripts": 5,
        "packaging": 6,
        "tests": 7,
        "migration_alias": 8,
        "historical_runtime_dependency": 9,
        "unknown": 10,
    }
    crit_pri = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    cl = str(hit.get("cluster") or "unknown")
    cr = str(hit.get("criticality") or "medium")
    comment_last = 1 if (cr == "low" and _is_comment_line(str(hit.get("line_preview") or ""))) else 0
    return (cluster_pri.get(cl, 99), crit_pri.get(cr, 9), comment_last, hit.get("path") or "")


def build_legacy_identifier_hotspot_analysis(*, explicit_overwrite: bool = False) -> dict[str, Any]:
    out_path, oerr = _resolve_handoff(_OUT_REL)
    if oerr or out_path is None:
        return _ret("blocked", {}, [oerr or "HOTSPOT_ANALYSIS_OUTPUT_PATH_INVALID"], [])
    if out_path.exists() and out_path.is_file() and not explicit_overwrite:
        return _ret("blocked", {}, ["HOTSPOT_ANALYSIS_EXISTS_NO_OVERWRITE"], [])

    inv, ierr = _load_json_handoff(_INVENTORY_REL)
    if ierr or not isinstance(inv, dict):
        return _ret("blocked", {}, [ierr or "HOTSPOT_ANALYSIS_INVENTORY_INVALID"], [])

    post, _ = _load_json_handoff(_POSTCHECK_REL)
    cons, _ = _load_json_handoff(_CONSISTENCY_REL)

    hits_raw: list[dict[str, Any]] = []

    findings = inv.get("findings")
    if isinstance(findings, list):
        for row in findings:
            if not isinstance(row, dict):
                continue
            if str(row.get("classification") or "") != "active_runtime_identifier":
                continue
            tr = row.get("tokens")
            toks = [str(x) for x in tr] if isinstance(tr, list) else []
            hits_raw.append(
                _norm_hit(str(row.get("path") or ""), int(row.get("line") or 0), toks, "legacy_identifier_inventory")
            )

    if isinstance(post, dict):
        rem = post.get("remaining_runtime_identifiers")
        if isinstance(rem, list):
            for row in rem:
                if not isinstance(row, dict):
                    continue
                tr = row.get("tokens")
                toks = [str(x) for x in tr] if isinstance(tr, list) else []
                hits_raw.append(
                    _norm_hit(str(row.get("path") or ""), int(row.get("line") or 0), toks, "cleanup_cycle_1_postcheck")
                )

    if isinstance(cons, dict):
        cf = cons.get("findings")
        if isinstance(cf, list):
            for row in cf:
                if not isinstance(row, dict) or row.get("allowed"):
                    continue
                tr = row.get("tokens")
                toks = [str(x) for x in tr] if isinstance(tr, list) else []
                hits_raw.append(
                    _norm_hit(str(row.get("path") or ""), int(row.get("line") or 0), toks, "setuphelfer_identifier_consistency_check")
                )

    dedup: dict[tuple[str, int, tuple[str, ...]], dict[str, Any]] = {}
    for h in hits_raw:
        if not h.get("path"):
            continue
        k = _hit_key(h)
        if k not in dedup:
            dedup[k] = h

    hits: list[dict[str, Any]] = []
    for h in dedup.values():
        preview = _line_preview_for_hit(h)
        cl = _cluster(h["path"], h["tokens"], preview)
        cr = _criticality(h["path"], h["tokens"], preview, cl)
        hits.append(
            {
                **h,
                "line_preview": preview[:200],
                "cluster": cl,
                "criticality": cr,
            }
        )

    clusters: dict[str, list[dict[str, Any]]] = {k: [] for k in _CLUSTERS_ORDERED}
    for h in hits:
        clusters.setdefault(h["cluster"], []).append(
            {
                "path": h["path"],
                "line": h["line"],
                "tokens": h["tokens"],
                "criticality": h["criticality"],
                "source": h["source"],
            }
        )

    crit_counts: dict[str, int] = defaultdict(int)
    for h in hits:
        crit_counts[str(h.get("criticality") or "medium")] += 1

    path_counts: dict[str, int] = defaultdict(int)
    path_crit: dict[str, str] = {}
    for h in hits:
        p = h["path"]
        path_counts[p] += 1
        prev = path_crit.get(p, "low")
        order = {"critical": 4, "high": 3, "medium": 2, "low": 1}
        if order.get(h["criticality"], 0) > order.get(prev, 0):
            path_crit[p] = h["criticality"]

    top_hotspots = [
        {"path": p, "hit_count": c, "max_criticality": path_crit.get(p, "low")}
        for p, c in sorted(path_counts.items(), key=lambda x: (-x[1], x[0]))[:25]
    ]

    sorted_hits = sorted(hits, key=_cleanup_priority_rank)
    recommended: list[dict[str, Any]] = []
    seen_paths: set[str] = set()
    for h in sorted_hits:
        p = h["path"]
        if p in seen_paths:
            continue
        seen_paths.add(p)
        recommended.append(
            {
                "path": p,
                "cluster": h["cluster"],
                "criticality": h["criticality"],
                "rationale": f"priority:{h['cluster']}:{h['criticality']}",
            }
        )
        if len(recommended) >= 40:
            break

    unknown_cluster_hits = sum(1 for h in hits if h.get("cluster") == "unknown")

    if unknown_cluster_hits > 0:
        analysis_status = "review_required"
    elif len(hits) > 0:
        analysis_status = "review_required"
    else:
        analysis_status = "ok"

    body = {
        "analysis_schema_version": 1,
        "strict_mode": "legacy_identifier_hotspot_analysis",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "analysis_status": analysis_status,
        "remaining_identifier_count": len(hits),
        "critical_count": int(crit_counts.get("critical") or 0),
        "high_count": int(crit_counts.get("high") or 0),
        "medium_count": int(crit_counts.get("medium") or 0),
        "low_count": int(crit_counts.get("low") or 0),
        "clusters": {k: clusters.get(k, []) for k in _CLUSTERS_ORDERED},
        "top_hotspots": top_hotspots,
        "recommended_next_cleanup_targets": recommended,
    }
    text = json.dumps(body, indent=2, sort_keys=True)
    if len(text.encode("utf-8")) > _MAX_OUTPUT_BYTES:
        return _ret("blocked", {}, ["HOTSPOT_ANALYSIS_OUTPUT_TOO_LARGE"], [])
    try:
        _atomic_write(out_path, text)
    except OSError:
        return _ret("blocked", {}, ["HOTSPOT_ANALYSIS_WRITE_FAILED"], [])
    return _ret(analysis_status, body, [], [])


def _ret(status: str, body: dict[str, Any], errors: list[str], warnings: list[str]) -> dict[str, Any]:
    return {
        "analysis_status": status,
        "analysis_file_path": _OUT_REL,
        "analysis": body,
        "warnings": list(dict.fromkeys(warnings)),
        "errors": list(dict.fromkeys(errors)) if status == "blocked" else [],
        "blocked_reasons": list(dict.fromkeys(errors)),
    }
