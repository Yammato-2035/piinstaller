from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
_HANDOFF_ROOT = (_REPO_ROOT / "docs/evidence/runtime-results/handoff").resolve(strict=False)
_HOTSPOT_ANALYSIS_REL = "docs/evidence/runtime-results/handoff/legacy_identifier_hotspot_analysis.json"
_SAFE_PLAN_REL = "docs/evidence/runtime-results/handoff/setuphelfer_safe_rewrite_plan.json"
_COMPAT_ALIASES_REL = "docs/evidence/runtime-results/handoff/compatibility_aliases.json"
_CYCLE2_PLAN_REL = "docs/evidence/runtime-results/handoff/setuphelfer_identifier_cleanup_cycle_2_plan.json"
_CYCLE2_RESULT_REL = "docs/evidence/runtime-results/handoff/setuphelfer_identifier_cleanup_cycle_2_result.json"
_CYCLE2_POSTCHECK_REL = "docs/evidence/runtime-results/handoff/setuphelfer_identifier_cleanup_cycle_2_postcheck.json"
_BACKUP_DIR_REL = "docs/evidence/runtime-results/handoff/legacy-backups"

_MAX_HOTSPOT_CYCLE_CHANGES = 50
_MAX_OUTPUT_BYTES = 512 * 1024

_CYCLE_EXCLUDED_SUBSTR = (
    "docs/evidence/",
    "docs/history/",
    "legacy-backups/",
    "/node_modules/",
    "/.git/",
    "/dist/",
)


def _changelog_or_history_path(rel: str) -> bool:
    pl = rel.replace("\\", "/").lower()
    return "/changelog" in pl or pl.startswith("docs/history/") or "debian/changelog" in pl


def _resolve_handoff(rel_path: str, prefix: str) -> tuple[Path | None, str | None]:
    raw = str(rel_path or "").strip()
    if not raw:
        return None, f"{prefix}_PATH_INVALID"
    p = Path(raw)
    if p.is_absolute() or ".." in p.parts:
        return None, f"{prefix}_PATH_INVALID"
    unresolved = _REPO_ROOT / p
    cur = unresolved
    while True:
        if cur.exists() and cur.is_symlink():
            return None, f"{prefix}_SYMLINK_BLOCKED"
        if cur.parent == cur:
            break
        cur = cur.parent
    resolved = unresolved.resolve(strict=False)
    if not (str(resolved).startswith(str(_HANDOFF_ROOT) + os.sep) or str(resolved) == str(_HANDOFF_ROOT)):
        return None, f"{prefix}_OUTSIDE_HANDOFF"
    return resolved, None


def _atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(content, encoding="utf-8")
    tmp.replace(path)


def _in_hotspot_cycle2_scope(rel: str) -> bool:
    raw = rel.replace("\\", "/")
    pl = raw.lower()
    if _changelog_or_history_path(raw):
        return False
    if any(x in pl for x in _CYCLE_EXCLUDED_SUBSTR):
        return False
    if raw in ("package.json", "frontend/package.json", "frontend/src-tauri/tauri.conf.json"):
        return True
    if raw.startswith("debian/"):
        return True
    if raw.startswith("backend/"):
        return True
    if raw.startswith("frontend/"):
        return True
    if raw.startswith("scripts/"):
        return True
    if raw.startswith("config/"):
        return True
    if raw.startswith("systemd/"):
        return True
    return False


def _resolve_repo_write_target(rel: str) -> tuple[Path | None, str | None]:
    raw = str(rel or "").strip().replace("\\", "/")
    if not raw or ".." in raw or raw.startswith("/"):
        return None, "HOTSPOT_CYCLE2_REPO_PATH_INVALID"
    pl = raw.lower()
    if _changelog_or_history_path(raw):
        return None, "HOTSPOT_CYCLE2_CHANGELOG_OR_HISTORY_BLOCKED"
    if pl.startswith("docs/evidence/") or "/docs/evidence/" in pl:
        return None, "HOTSPOT_CYCLE2_EVIDENCE_WRITE_BLOCKED"
    if pl.startswith("docs/history/") or "/docs/history/" in pl:
        return None, "HOTSPOT_CYCLE2_HISTORY_WRITE_BLOCKED"
    if "legacy-backups/" in pl:
        return None, "HOTSPOT_CYCLE2_BACKUP_TREE_BLOCKED"
    unresolved = _REPO_ROOT / raw
    cur = unresolved
    while True:
        if cur.exists() and cur.is_symlink():
            return None, "HOTSPOT_CYCLE2_REPO_SYMLINK_BLOCKED"
        if cur.parent == cur:
            break
        cur = cur.parent
    try:
        resolved = unresolved.resolve(strict=False)
        resolved.relative_to(_REPO_ROOT.resolve(strict=False))
    except (OSError, ValueError):
        return None, "HOTSPOT_CYCLE2_OUTSIDE_REPO"
    return resolved, None


def _is_probably_text_file(path: Path) -> bool:
    try:
        chunk = path.read_bytes()[:8192]
    except OSError:
        return False
    if b"\x00" in chunk:
        return False
    try:
        path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return False
    return True


def _hotspot_target_sort_key(cluster: str, criticality: str) -> tuple[int, int]:
    """User priority: env_config critical … packaging high."""
    c = str(cluster or "")
    cr = str(criticality or "")
    order: list[tuple[tuple[str, str], tuple[int, int]]] = [
        (("env_config", "critical"), (0, 0)),
        (("api", "critical"), (1, 0)),
        (("backend_runtime", "critical"), (2, 0)),
        (("tauri", "critical"), (3, 0)),
        (("frontend_runtime", "critical"), (4, 0)),
        (("scripts", "high"), (5, 0)),
        (("packaging", "high"), (6, 0)),
    ]
    for (cc, crc), rank in order:
        if c == cc and cr == crc:
            return rank
    if cr == "critical":
        return (7, 0)
    if cr == "high":
        return (8, 0)
    return (99, 99)


def _read_hotspot_remaining_count() -> int:
    p = _REPO_ROOT / _HOTSPOT_ANALYSIS_REL
    if not p.is_file():
        return 0
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return 0
    return int(data.get("remaining_identifier_count") or 0)


def _read_inventory_active_count() -> int:
    inv_path = _REPO_ROOT / "docs/evidence/runtime-results/handoff/legacy_identifier_inventory.json"
    if not inv_path.is_file():
        return 0
    try:
        data = json.loads(inv_path.read_text(encoding="utf-8"))
    except Exception:
        return 0
    counts = data.get("counts")
    if isinstance(counts, dict):
        return int(counts.get("active_runtime_identifier") or 0)
    return 0


def _count_critical_high_in_hotspot_body(body: dict[str, Any]) -> tuple[int, int]:
    crit = high = 0
    clusters = body.get("clusters")
    if not isinstance(clusters, dict):
        return 0, 0
    for rows in clusters.values():
        if not isinstance(rows, list):
            continue
        for row in rows:
            if not isinstance(row, dict):
                continue
            sev = str(row.get("criticality") or "")
            if sev == "critical":
                crit += 1
            elif sev == "high":
                high += 1
    return crit, high


def _load_json_handoff(rel: str, prefix: str) -> tuple[Any | None, str | None]:
    p, err = _resolve_handoff(rel, prefix)
    if err or p is None or not p.is_file():
        return None, err or f"{prefix}_INPUT_MISSING"
    try:
        return json.loads(p.read_text(encoding="utf-8")), None
    except Exception:
        return None, f"{prefix}_INPUT_JSON_INVALID"


def _apply_entry_pairs(content: str, entries: list[dict[str, Any]]) -> str:
    pairs: list[tuple[str, str]] = []
    for ent in entries:
        if not isinstance(ent, dict):
            continue
        leg = str(ent.get("legacy_token") or "")
        repl = str(ent.get("replacement") or "")
        if not leg:
            continue
        pairs.append((leg, repl))
    pairs.sort(key=lambda x: len(x[0]), reverse=True)
    out = content
    for leg, repl in pairs:
        out = out.replace(leg, repl)
    return out


def build_setuphelfer_identifier_hotspot_cleanup_cycle(*, explicit_overwrite: bool = False) -> dict[str, Any]:
    hot, herr = _load_json_handoff(_HOTSPOT_ANALYSIS_REL, "HOTSPOT_CYCLE2_HOTSPOT")
    if herr or not isinstance(hot, dict):
        return _plan_ret("blocked", {}, [herr or "HOTSPOT_CYCLE2_HOTSPOT_ANALYSIS_INVALID"], [])

    rec = hot.get("recommended_next_cleanup_targets")
    if not isinstance(rec, list):
        return _plan_ret("blocked", {}, ["HOTSPOT_CYCLE2_RECOMMENDED_TARGETS_INVALID"], [])

    path_meta: dict[str, dict[str, str]] = {}
    for row in rec:
        if not isinstance(row, dict):
            continue
        path = str(row.get("path") or "").strip().replace("\\", "/")
        if not path:
            continue
        cluster = str(row.get("cluster") or "")
        crit = str(row.get("criticality") or "")
        if cluster == "unknown":
            continue
        if crit not in ("critical", "high"):
            continue
        if path not in path_meta:
            path_meta[path] = {"cluster": cluster, "criticality": crit}

    safe, serr = _load_json_handoff(_SAFE_PLAN_REL, "HOTSPOT_CYCLE2_SAFE")
    if serr or not isinstance(safe, dict):
        return _plan_ret("blocked", {}, [serr or "HOTSPOT_CYCLE2_SAFE_PLAN_INVALID"], [])

    entries_in = safe.get("entries")
    if not isinstance(entries_in, list):
        return _plan_ret("blocked", {}, ["HOTSPOT_CYCLE2_SAFE_PLAN_SHAPE_INVALID"], [])

    _compat, _ = _load_json_handoff(_COMPAT_ALIASES_REL, "HOTSPOT_CYCLE2_COMPAT")

    candidates: list[dict[str, Any]] = []
    for ent in entries_in:
        if not isinstance(ent, dict):
            continue
        if not bool(ent.get("write_allowed")):
            continue
        rel = str(ent.get("source_file") or "").strip().replace("\\", "/")
        if not rel or rel not in path_meta:
            continue
        if not _in_hotspot_cycle2_scope(rel):
            continue
        meta = path_meta[rel]
        ent_copy = dict(ent)
        ent_copy["_hotspot_cluster"] = meta["cluster"]
        ent_copy["_hotspot_criticality"] = meta["criticality"]
        candidates.append(ent_copy)

    candidates.sort(
        key=lambda e: (
            _hotspot_target_sort_key(str(e.get("_hotspot_cluster") or ""), str(e.get("_hotspot_criticality") or "")),
            str(e.get("source_file") or ""),
            -len(str(e.get("legacy_token") or "")),
        )
    )

    planned_raw = candidates[:_MAX_HOTSPOT_CYCLE_CHANGES]
    deferred_raw = candidates[_MAX_HOTSPOT_CYCLE_CHANGES:]

    planned_entries: list[dict[str, Any]] = []
    for e in planned_raw:
        clean = {k: v for k, v in e.items() if not str(k).startswith("_hotspot_")}
        planned_entries.append(clean)

    deferred_entries: list[dict[str, Any]] = []
    for e in deferred_raw:
        clean = {k: v for k, v in e.items() if not str(k).startswith("_hotspot_")}
        deferred_entries.append(clean)

    plan_status = "ok"
    if deferred_entries:
        plan_status = "review_required"

    out_path, oerr = _resolve_handoff(_CYCLE2_PLAN_REL, "HOTSPOT_CYCLE2_PLAN")
    if oerr or out_path is None:
        return _plan_ret("blocked", {}, [oerr or "HOTSPOT_CYCLE2_PLAN_OUTPUT_INVALID"], [])
    if out_path.exists() and out_path.is_file() and not explicit_overwrite:
        return _plan_ret("blocked", {}, ["HOTSPOT_CYCLE2_PLAN_EXISTS_NO_OVERWRITE"], [])

    body = {
        "cycle_schema_version": 1,
        "cycle": 2,
        "strict_mode": "setuphelfer_identifier_hotspot_cleanup_cycle",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "plan_status": plan_status,
        "max_changes_per_cycle": _MAX_HOTSPOT_CYCLE_CHANGES,
        "hotspot_analysis_file": _HOTSPOT_ANALYSIS_REL,
        "source_safe_plan_file": _SAFE_PLAN_REL,
        "source_compatibility_aliases_file": _COMPAT_ALIASES_REL,
        "recommended_paths_matched": len(path_meta),
        "candidate_entries_total": len(candidates),
        "planned_changes": len(planned_entries),
        "deferred_changes": len(deferred_entries),
        "planned_entries": planned_entries,
        "deferred_entries": deferred_entries,
    }
    text = json.dumps(body, indent=2, sort_keys=True)
    if len(text.encode("utf-8")) > _MAX_OUTPUT_BYTES:
        return _plan_ret("blocked", {}, ["HOTSPOT_CYCLE2_PLAN_OUTPUT_TOO_LARGE"], [])
    try:
        _atomic_write(out_path, text)
    except OSError:
        return _plan_ret("blocked", {}, ["HOTSPOT_CYCLE2_PLAN_WRITE_FAILED"], [])
    return _plan_ret(plan_status, body, [], [])


def _plan_ret(status: str, body: dict[str, Any], errors: list[str], warnings: list[str]) -> dict[str, Any]:
    return {
        "hotspot_cleanup_cycle_plan_status": status,
        "hotspot_cleanup_cycle_plan_file_path": _CYCLE2_PLAN_REL,
        "hotspot_cleanup_cycle_plan": body,
        "warnings": list(dict.fromkeys(warnings)),
        "errors": list(dict.fromkeys(errors)) if status == "blocked" else [],
        "blocked_reasons": list(dict.fromkeys(errors)),
    }


def apply_setuphelfer_identifier_hotspot_cleanup_cycle(*, explicit_overwrite: bool = False) -> dict[str, Any]:
    plan_path, perr = _resolve_handoff(_CYCLE2_PLAN_REL, "HOTSPOT_CYCLE2_PLAN")
    if perr or plan_path is None or not plan_path.is_file():
        return _apply_ret("blocked", {}, [perr or "HOTSPOT_CYCLE2_PLAN_MISSING"], [])

    out_path, oerr = _resolve_handoff(_CYCLE2_RESULT_REL, "HOTSPOT_CYCLE2_RESULT")
    if oerr or out_path is None:
        return _apply_ret("blocked", {}, [oerr or "HOTSPOT_CYCLE2_RESULT_OUTPUT_INVALID"], [])
    if out_path.exists() and out_path.is_file() and not explicit_overwrite:
        return _apply_ret("blocked", {}, ["HOTSPOT_CYCLE2_RESULT_EXISTS_NO_OVERWRITE"], [])

    try:
        cycle_plan = json.loads(plan_path.read_text(encoding="utf-8"))
    except Exception:
        return _apply_ret("blocked", {}, ["HOTSPOT_CYCLE2_PLAN_JSON_INVALID"], [])

    planned = cycle_plan.get("planned_entries")
    if not isinstance(planned, list):
        return _apply_ret("blocked", {}, ["HOTSPOT_CYCLE2_PLAN_ENTRIES_INVALID"], [])

    before_remaining = _read_hotspot_remaining_count()
    if before_remaining == 0:
        before_remaining = _read_inventory_active_count()

    backup_root = _HANDOFF_ROOT / "legacy-backups"
    cur = backup_root
    while True:
        if cur.exists() and cur.is_symlink():
            return _apply_ret("blocked", {}, ["HOTSPOT_CYCLE2_BACKUP_DIR_SYMLINK_BLOCKED"], [])
        if cur.parent == cur:
            break
        cur = cur.parent
    backup_root.mkdir(parents=True, exist_ok=True)

    files_to_touch: dict[str, list[dict[str, Any]]] = {}
    for ent in planned:
        if not isinstance(ent, dict) or not bool(ent.get("write_allowed")):
            continue
        rel = str(ent.get("source_file") or "").strip().replace("\\", "/")
        if not rel or not _in_hotspot_cycle2_scope(rel):
            continue
        files_to_touch.setdefault(rel, []).append(ent)

    for rel in files_to_touch:
        files_to_touch[rel].sort(key=lambda e: -len(str(e.get("legacy_token") or "")))

    file_results: list[dict[str, Any]] = []
    warnings: list[str] = []

    for rel in sorted(files_to_touch.keys()):
        ents = files_to_touch[rel]
        abs_path, err = _resolve_repo_write_target(rel)
        if err or abs_path is None:
            warnings.append(f"HOTSPOT_CYCLE2_SKIP_PATH:{rel}:{err}")
            continue
        if not abs_path.is_file():
            warnings.append(f"HOTSPOT_CYCLE2_SKIP_NOT_FILE:{rel}")
            continue
        if not _is_probably_text_file(abs_path):
            warnings.append(f"HOTSPOT_CYCLE2_SKIP_BINARY:{rel}")
            continue
        try:
            original = abs_path.read_text(encoding="utf-8")
        except OSError as exc:
            warnings.append(f"HOTSPOT_CYCLE2_SKIP_READ:{rel}:{exc}")
            continue
        new_content = _apply_entry_pairs(original, ents)
        if new_content == original:
            file_results.append({"source_file": rel, "status": "skipped_no_change", "backup_file": None})
            continue

        digest = hashlib.sha256(f"cycle2:{rel}".encode("utf-8")).hexdigest()[:24]
        backup_name = f"{digest}.legacy-backup"
        backup_abs = backup_root / backup_name
        backup_payload = json.dumps(
            {"cycle": 2, "original_text": original, "source_file": rel},
            indent=2,
            sort_keys=True,
        )
        try:
            _atomic_write(backup_abs, backup_payload)
        except OSError as exc:
            return _apply_ret("blocked", {}, [f"HOTSPOT_CYCLE2_BACKUP_FAILED:{rel}:{exc}"], warnings)

        try:
            _atomic_write(abs_path, new_content)
        except OSError as exc:
            warnings.append(f"HOTSPOT_CYCLE2_WRITE_FAILED:{rel}:{exc}")
            continue

        file_results.append(
            {
                "source_file": rel,
                "status": "rewritten",
                "backup_file": f"{_BACKUP_DIR_REL}/{backup_name}",
            }
        )

    apply_status = "ok" if not warnings else "review_required"
    body = {
        "result_schema_version": 1,
        "cycle": 2,
        "strict_mode": "setuphelfer_identifier_hotspot_cleanup_cycle_apply",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "apply_status": apply_status,
        "before_remaining_identifier_count": before_remaining,
        "files_planned": sorted(files_to_touch.keys()),
        "file_results": file_results,
    }
    text = json.dumps(body, indent=2, sort_keys=True)
    if len(text.encode("utf-8")) > _MAX_OUTPUT_BYTES:
        return _apply_ret("blocked", {}, ["HOTSPOT_CYCLE2_RESULT_OUTPUT_TOO_LARGE"], warnings)
    try:
        _atomic_write(out_path, text)
    except OSError:
        return _apply_ret("blocked", {}, ["HOTSPOT_CYCLE2_RESULT_WRITE_FAILED"], warnings)
    return _apply_ret(apply_status, body, [], warnings)


def _apply_ret(status: str, body: dict[str, Any], errors: list[str], warnings: list[str]) -> dict[str, Any]:
    return {
        "hotspot_cleanup_cycle_apply_status": status,
        "hotspot_cleanup_cycle_result_file_path": _CYCLE2_RESULT_REL,
        "hotspot_cleanup_cycle_apply": body,
        "warnings": list(dict.fromkeys(warnings)),
        "errors": list(dict.fromkeys(errors)) if status == "blocked" else [],
        "blocked_reasons": list(dict.fromkeys(errors)),
    }


def build_setuphelfer_identifier_hotspot_cleanup_cycle_postcheck(*, explicit_overwrite: bool = False) -> dict[str, Any]:
    from deploy.runner_legacy_identifier_hotspot_analysis import build_legacy_identifier_hotspot_analysis
    from deploy.runner_legacy_identifier_inventory import build_legacy_identifier_inventory
    from deploy.runner_setuphelfer_identifier_consistency_check import check_setuphelfer_identifier_consistency

    out_path, oerr = _resolve_handoff(_CYCLE2_POSTCHECK_REL, "HOTSPOT_CYCLE2_POSTCHECK")
    if oerr or out_path is None:
        return _post_ret("blocked", {}, [oerr or "HOTSPOT_CYCLE2_POSTCHECK_OUTPUT_INVALID"], [])
    if out_path.exists() and out_path.is_file() and not explicit_overwrite:
        return _post_ret("blocked", {}, ["HOTSPOT_CYCLE2_POSTCHECK_EXISTS_NO_OVERWRITE"], [])

    before_remaining = _read_hotspot_remaining_count()
    if before_remaining == 0:
        before_remaining = _read_inventory_active_count()

    inv_res = build_legacy_identifier_inventory(explicit_overwrite=True)
    chk = check_setuphelfer_identifier_consistency(explicit_overwrite=True)
    hot_res = build_legacy_identifier_hotspot_analysis(explicit_overwrite=True)

    analysis = hot_res.get("analysis") if isinstance(hot_res.get("analysis"), dict) else {}
    after_remaining = int(analysis.get("remaining_identifier_count") or 0)
    crit_rem, high_rem = _count_critical_high_in_hotspot_body(analysis)

    consistency_status = str(chk.get("check_status") or "blocked")
    hotspot_status = str(hot_res.get("analysis_status") or "blocked")

    deferred = 0
    plan_p = _REPO_ROOT / _CYCLE2_PLAN_REL
    if plan_p.is_file():
        try:
            pl = json.loads(plan_p.read_text(encoding="utf-8"))
            deferred = int(pl.get("deferred_changes") or 0)
        except Exception:
            deferred = 0

    next_cycle = (
        after_remaining > 0
        or crit_rem > 0
        or high_rem > 0
        or deferred > 0
        or str(inv_res.get("inventory_status") or "") == "review_required"
        or consistency_status == "review_required"
        or hotspot_status == "review_required"
    )

    post_status = "ok"
    if consistency_status == "blocked" or hotspot_status == "blocked":
        post_status = "blocked"
    elif (
        consistency_status == "review_required"
        or hotspot_status == "review_required"
        or next_cycle
    ):
        post_status = "review_required"

    body = {
        "cycle": 2,
        "before_remaining_identifier_count": before_remaining,
        "after_remaining_identifier_count": after_remaining,
        "critical_remaining": crit_rem,
        "high_remaining": high_rem,
        "consistency_status": consistency_status,
        "hotspot_status": hotspot_status,
        "next_cycle_required": bool(next_cycle),
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "strict_mode": "setuphelfer_identifier_hotspot_cleanup_cycle_postcheck",
    }
    text = json.dumps(body, indent=2, sort_keys=True)
    if len(text.encode("utf-8")) > _MAX_OUTPUT_BYTES:
        return _post_ret("blocked", {}, ["HOTSPOT_CYCLE2_POSTCHECK_OUTPUT_TOO_LARGE"], [])
    try:
        _atomic_write(out_path, text)
    except OSError:
        return _post_ret("blocked", {}, ["HOTSPOT_CYCLE2_POSTCHECK_WRITE_FAILED"], [])
    return _post_ret(post_status, body, [], [])


def _post_ret(status: str, body: dict[str, Any], errors: list[str], warnings: list[str]) -> dict[str, Any]:
    return {
        "hotspot_cleanup_cycle_postcheck_status": status,
        "hotspot_cleanup_cycle_postcheck_file_path": _CYCLE2_POSTCHECK_REL,
        "hotspot_cleanup_cycle_postcheck": body,
        "warnings": list(dict.fromkeys(warnings)),
        "errors": list(dict.fromkeys(errors)) if status == "blocked" else [],
        "blocked_reasons": list(dict.fromkeys(errors)),
    }
