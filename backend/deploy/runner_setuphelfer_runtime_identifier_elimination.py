from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
_HANDOFF_ROOT = (_REPO_ROOT / "docs/evidence/runtime-results/handoff").resolve(strict=False)

_HOTSPOT_REL = "docs/evidence/runtime-results/handoff/legacy_identifier_hotspot_analysis.json"
_CYCLE2_POST_REL = "docs/evidence/runtime-results/handoff/setuphelfer_identifier_cleanup_cycle_2_postcheck.json"
_CONSISTENCY_REL = "docs/evidence/runtime-results/handoff/setuphelfer_identifier_consistency_check.json"
_SAFE_PLAN_REL = "docs/evidence/runtime-results/handoff/setuphelfer_safe_rewrite_plan.json"
_COMPAT_REL = "docs/evidence/runtime-results/handoff/compatibility_aliases.json"

_TARGETS_OUT = "docs/evidence/runtime-results/handoff/runtime_identifier_elimination_targets.json"
_PLAN_OUT = "docs/evidence/runtime-results/handoff/runtime_identifier_elimination_plan.json"
_RESULT_OUT = "docs/evidence/runtime-results/handoff/runtime_identifier_elimination_result.json"
_ALIAS_VAL_OUT = "docs/evidence/runtime-results/handoff/runtime_compatibility_alias_validation.json"
_POSTCHECK_OUT = "docs/evidence/runtime-results/handoff/runtime_identifier_elimination_postcheck.json"
_BACKUP_DIR_REL = "docs/evidence/runtime-results/handoff/legacy-backups"

_MAX_OUTPUT_BYTES = 512 * 1024

_EXCLUDED_CLUSTERS = frozenset(
    {
        "unknown",
        "tests",
        "migration_alias",
        "historical_runtime_dependency",
    }
)

_RUNTIME_TOKEN_PRIORITY: tuple[str, ...] = (
    "PI_INSTALLER_",
    "/opt/pi-installer",
    "pi-installer.service",
    "de.pi-installer.app",
    "pi-installer-backend",
    "pi-installer-frontend",
    "de.pi-installer",
    "pi-installer",
    "piinstaller",
)


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


def _load_json(rel: str, prefix: str) -> tuple[Any | None, str | None]:
    p, err = _resolve_handoff(rel, prefix)
    if err or p is None or not p.is_file():
        return None, err or f"{prefix}_MISSING"
    try:
        return json.loads(p.read_text(encoding="utf-8")), None
    except Exception:
        return None, f"{prefix}_JSON_INVALID"


def _is_test_path(rel: str) -> bool:
    pl = rel.replace("\\", "/").lower()
    return (
        pl.startswith("backend/tests/")
        or "/tests/" in pl
        or pl.endswith("_test.py")
        or "/test_" in pl
    )


def _is_docs_evidence_history(rel: str) -> bool:
    pl = rel.replace("\\", "/").lower()
    return (
        pl.startswith("docs/")
        or "/docs/evidence/" in pl
        or "/docs/history/" in pl
        or pl.startswith("docs/evidence/")
        or pl.startswith("docs/history/")
    )


def _line_preview(rel: str, line_no: int) -> str:
    if not rel or line_no <= 0:
        return ""
    fp = _REPO_ROOT / rel.replace("\\", "/")
    try:
        lines = fp.read_text(encoding="utf-8").splitlines()
        if 0 < line_no <= len(lines):
            return lines[line_no - 1]
    except OSError:
        return ""
    return ""


def _is_comment_only_line(line: str) -> bool:
    s = (line or "").strip()
    return s.startswith("#") or s.startswith("//") or s.startswith("*")


def _in_elimination_write_scope(rel: str) -> bool:
    raw = rel.replace("\\", "/")
    pl = raw.lower()
    if "legacy-backups/" in pl or "/.git/" in pl:
        return False
    if _is_docs_evidence_history(raw) or _is_test_path(raw):
        return False
    if raw in ("package.json", "frontend/package.json", "frontend/src-tauri/tauri.conf.json"):
        return True
    if raw.startswith(("backend/", "frontend/", "scripts/", "config/", "systemd/", "debian/")):
        return True
    return False


def _token_priority_index(token: str) -> int:
    t = str(token)
    for i, pref in enumerate(_RUNTIME_TOKEN_PRIORITY):
        if t == pref:
            return i
    if t.startswith("PI_INSTALLER_"):
        return 0
    return 99


def _infer_criticality_from_tokens(tokens: list[str]) -> str:
    if "PI_INSTALLER_" in tokens or "/opt/pi-installer" in tokens or "pi-installer.service" in tokens:
        return "critical"
    if "de.pi-installer.app" in tokens:
        return "critical"
    return "high"


def _collect_hotspot_rows(hot: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    clusters = hot.get("clusters")
    if not isinstance(clusters, dict):
        return out
    for cluster_name, rows in clusters.items():
        if cluster_name in _EXCLUDED_CLUSTERS:
            continue
        if not isinstance(rows, list):
            continue
        for row in rows:
            if not isinstance(row, dict):
                continue
            crit = str(row.get("criticality") or "")
            if crit not in ("critical", "high"):
                continue
            path = str(row.get("path") or "").strip().replace("\\", "/")
            if not path or _is_docs_evidence_history(path) or _is_test_path(path):
                continue
            if not _in_elimination_write_scope(path):
                continue
            line_no = int(row.get("line") or 0)
            lp = _line_preview(path, line_no)
            if _is_comment_only_line(lp):
                continue
            toks = row.get("tokens")
            tokens = [str(x) for x in toks] if isinstance(toks, list) else []
            out.append(
                {
                    "path": path,
                    "line": line_no,
                    "tokens": tokens,
                    "criticality": crit,
                    "cluster": cluster_name,
                    "source": "legacy_identifier_hotspot_analysis",
                }
            )
    return out


def _collect_postcheck_remaining(post: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    rem = post.get("remaining_runtime_identifiers")
    if not isinstance(rem, list):
        return out
    for row in rem:
        if not isinstance(row, dict):
            continue
        path = str(row.get("path") or "").strip().replace("\\", "/")
        if not path or _is_docs_evidence_history(path) or _is_test_path(path):
            continue
        if not _in_elimination_write_scope(path):
            continue
        line_no = int(row.get("line") or 0)
        lp = _line_preview(path, line_no)
        if _is_comment_only_line(lp):
            continue
        toks = row.get("tokens")
        tokens = [str(x) for x in toks] if isinstance(toks, list) else []
        crit = _infer_criticality_from_tokens(tokens)
        if crit not in ("critical", "high"):
            continue
        out.append(
            {
                "path": path,
                "line": line_no,
                "tokens": tokens,
                "criticality": crit,
                "cluster": "cycle2_postcheck_remaining",
                "source": "setuphelfer_identifier_cleanup_cycle_2_postcheck",
            }
        )
    return out


def _collect_consistency_blocked(cons: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    findings = cons.get("findings")
    if not isinstance(findings, list):
        return out
    for row in findings:
        if not isinstance(row, dict) or row.get("allowed"):
            continue
        path = str(row.get("path") or "").strip().replace("\\", "/")
        if not path or _is_docs_evidence_history(path) or _is_test_path(path):
            continue
        if not _in_elimination_write_scope(path):
            continue
        line_no = int(row.get("line") or 0)
        lp = _line_preview(path, line_no)
        if _is_comment_only_line(lp):
            continue
        toks = row.get("tokens")
        tokens = [str(x) for x in toks] if isinstance(toks, list) else []
        out.append(
            {
                "path": path,
                "line": line_no,
                "tokens": tokens,
                "criticality": "critical",
                "cluster": "consistency_blocked",
                "source": "setuphelfer_identifier_consistency_check",
            }
        )
    return out


def _dedupe_targets(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[tuple[str, int, tuple[str, ...]]] = set()
    out: list[dict[str, Any]] = []
    for r in rows:
        key = (r["path"], int(r["line"]), tuple(sorted(r.get("tokens") or [])))
        if key in seen:
            continue
        seen.add(key)
        out.append(r)
    def _row_pri(row: dict[str, Any]) -> int:
        toks = row.get("tokens") or []
        return min((_token_priority_index(str(x)) for x in toks), default=99)

    out.sort(
        key=lambda r: (
            _row_pri(r),
            0 if r.get("criticality") == "critical" else 1,
            r.get("path") or "",
            int(r.get("line") or 0),
        )
    )
    return out


def _ret(
    status: str,
    key: str,
    body: dict[str, Any],
    rel: str,
    errors: list[str],
    warnings: list[str],
) -> dict[str, Any]:
    return {
        f"{key}_status": status,
        f"{key}_file_path": rel,
        key: body,
        "warnings": list(dict.fromkeys(warnings)),
        "errors": list(dict.fromkeys(errors)) if status == "blocked" else [],
        "blocked_reasons": list(dict.fromkeys(errors)),
    }


def build_runtime_identifier_elimination_targets(*, explicit_overwrite: bool = False) -> dict[str, Any]:
    out_path, oerr = _resolve_handoff(_TARGETS_OUT, "RUNTIME_ELIM_TARGETS")
    if oerr or out_path is None:
        return _ret("blocked", "runtime_identifier_elimination_targets", {}, _TARGETS_OUT, [oerr or "INVALID"], [])
    if out_path.exists() and out_path.is_file() and not explicit_overwrite:
        return _ret("blocked", "runtime_identifier_elimination_targets", {}, _TARGETS_OUT, ["RUNTIME_ELIM_TARGETS_EXISTS_NO_OVERWRITE"], [])

    hot, herr = _load_json(_HOTSPOT_REL, "RUNTIME_ELIM_HOTSPOT")
    if herr or not isinstance(hot, dict):
        return _ret("blocked", "runtime_identifier_elimination_targets", {}, _TARGETS_OUT, [herr or "HOTSPOT_MISSING"], [])

    merged: list[dict[str, Any]] = []
    merged.extend(_collect_hotspot_rows(hot))

    post, _ = _load_json(_CYCLE2_POST_REL, "RUNTIME_ELIM_POST2")
    if isinstance(post, dict):
        merged.extend(_collect_postcheck_remaining(post))

    cons, _ = _load_json(_CONSISTENCY_REL, "RUNTIME_ELIM_CONS")
    if isinstance(cons, dict):
        merged.extend(_collect_consistency_blocked(cons))

    targets = _dedupe_targets(merged)
    body = {
        "targets_schema_version": 1,
        "strict_mode": "runtime_identifier_elimination_targets",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "targets_status": "review_required" if targets else "ok",
        "target_count": len(targets),
        "targets": targets,
    }
    text = json.dumps(body, indent=2, sort_keys=True)
    if len(text.encode("utf-8")) > _MAX_OUTPUT_BYTES:
        return _ret("blocked", "runtime_identifier_elimination_targets", {}, _TARGETS_OUT, ["RUNTIME_ELIM_TARGETS_TOO_LARGE"], [])
    try:
        _atomic_write(out_path, text)
    except OSError:
        return _ret("blocked", "runtime_identifier_elimination_targets", {}, _TARGETS_OUT, ["RUNTIME_ELIM_TARGETS_WRITE_FAILED"], [])
    st = "review_required" if targets else "ok"
    return _ret(st, "runtime_identifier_elimination_targets", body, _TARGETS_OUT, [], [])


def _alias_entries(compat: dict[str, Any]) -> list[dict[str, Any]]:
    a = compat.get("aliases")
    return [x for x in a if isinstance(x, dict)] if isinstance(a, list) else []


def _token_matches_alias(legacy_identifier: str, alias_legacy: str) -> bool:
    if not alias_legacy:
        return False
    if alias_legacy.endswith("*"):
        return legacy_identifier.startswith(alias_legacy[:-1])
    return legacy_identifier == alias_legacy


def _compatibility_alias_required_for_token(token: str, compat: dict[str, Any]) -> bool:
    for ent in _alias_entries(compat):
        leg = str(ent.get("legacy_identifier") or "")
        if _token_matches_alias(token, leg):
            return True
    return False


def build_runtime_identifier_elimination_plan(*, explicit_overwrite: bool = False) -> dict[str, Any]:
    out_path, oerr = _resolve_handoff(_PLAN_OUT, "RUNTIME_ELIM_PLAN")
    if oerr or out_path is None:
        return _ret("blocked", "runtime_identifier_elimination_plan", {}, _PLAN_OUT, [oerr or "INVALID"], [])
    if out_path.exists() and out_path.is_file() and not explicit_overwrite:
        return _ret("blocked", "runtime_identifier_elimination_plan", {}, _PLAN_OUT, ["RUNTIME_ELIM_PLAN_EXISTS_NO_OVERWRITE"], [])

    tg_data, terr = _load_json(_TARGETS_OUT, "RUNTIME_ELIM_TARGETS_IN")
    if terr or not isinstance(tg_data, dict):
        return _ret("blocked", "runtime_identifier_elimination_plan", {}, _PLAN_OUT, [terr or "TARGETS_MISSING"], [])

    safe, serr = _load_json(_SAFE_PLAN_REL, "RUNTIME_ELIM_SAFE")
    if serr or not isinstance(safe, dict):
        return _ret("blocked", "runtime_identifier_elimination_plan", {}, _PLAN_OUT, [serr or "SAFE_PLAN_MISSING"], [])

    compat, _ = _load_json(_COMPAT_REL, "RUNTIME_ELIM_COMPAT")

    entries_in = safe.get("entries")
    if not isinstance(entries_in, list):
        return _ret("blocked", "runtime_identifier_elimination_plan", {}, _PLAN_OUT, ["SAFE_PLAN_SHAPE_INVALID"], [])

    safe_index: dict[tuple[str, str], dict[str, Any]] = {}
    for ent in entries_in:
        if not isinstance(ent, dict):
            continue
        rel = str(ent.get("source_file") or "").strip().replace("\\", "/")
        tok = str(ent.get("legacy_token") or "")
        if rel and tok:
            safe_index[(rel, tok)] = ent

    targets = tg_data.get("targets")
    if not isinstance(targets, list):
        return _ret("blocked", "runtime_identifier_elimination_plan", {}, _PLAN_OUT, ["TARGETS_SHAPE_INVALID"], [])

    plan_rows: list[dict[str, Any]] = []
    for t in targets:
        if not isinstance(t, dict):
            continue
        path = str(t.get("path") or "").strip().replace("\\", "/")
        cluster = str(t.get("cluster") or "")
        crit = str(t.get("criticality") or "")
        if cluster in _EXCLUDED_CLUSTERS or cluster == "unknown":
            continue
        toks = t.get("tokens")
        tokens = [str(x) for x in toks] if isinstance(toks, list) else []
        for token in tokens:
            ent = safe_index.get((path, token))
            repl = str(ent.get("replacement") or "") if ent else ""
            cls = str(ent.get("classification") or "") if ent else ""
            write_ok = bool(ent and ent.get("write_allowed") and cls == "rename_now" and repl != "")
            write_ok = write_ok and _in_elimination_write_scope(path) and cluster not in _EXCLUDED_CLUSTERS
            line_no = int(t.get("line") or 0)
            lp = _line_preview(path, line_no)
            if _is_comment_only_line(lp):
                write_ok = False
            alias_req = _compatibility_alias_required_for_token(token, compat) if isinstance(compat, dict) else False
            reason = "mapped_rename_now" if write_ok else (str(ent.get("reason") or "no_safe_write") if ent else "not_in_safe_plan")
            plan_rows.append(
                {
                    "target_file": path,
                    "legacy_identifier": token,
                    "replacement": repl,
                    "criticality": crit,
                    "compatibility_alias_required": bool(alias_req),
                    "write_allowed": bool(write_ok),
                    "reason": reason,
                }
            )

    plan_rows.sort(key=lambda r: (_token_priority_index(r["legacy_identifier"]), -len(r["legacy_identifier"]), r["target_file"]))

    plan_status = "ok"
    if any(not r["write_allowed"] for r in plan_rows):
        plan_status = "review_required"
    if not plan_rows:
        plan_status = "ok"

    body = {
        "plan_schema_version": 1,
        "strict_mode": "runtime_identifier_elimination_plan",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "plan_status": plan_status,
        "entries": plan_rows,
        "write_allowed_count": sum(1 for r in plan_rows if r["write_allowed"]),
        "source_targets_file": _TARGETS_OUT,
        "source_safe_plan_file": _SAFE_PLAN_REL,
        "source_compatibility_aliases_file": _COMPAT_REL,
    }
    text = json.dumps(body, indent=2, sort_keys=True)
    if len(text.encode("utf-8")) > _MAX_OUTPUT_BYTES:
        return _ret("blocked", "runtime_identifier_elimination_plan", {}, _PLAN_OUT, ["RUNTIME_ELIM_PLAN_TOO_LARGE"], [])
    try:
        _atomic_write(out_path, text)
    except OSError:
        return _ret("blocked", "runtime_identifier_elimination_plan", {}, _PLAN_OUT, ["RUNTIME_ELIM_PLAN_WRITE_FAILED"], [])
    return _ret(plan_status, "runtime_identifier_elimination_plan", body, _PLAN_OUT, [], [])


def _resolve_repo_write(rel: str) -> tuple[Path | None, str | None]:
    raw = str(rel or "").strip().replace("\\", "/")
    if not raw or ".." in raw or raw.startswith("/"):
        return None, "REPO_PATH_INVALID"
    pl = raw.lower()
    if pl.startswith("docs/") or "/docs/evidence/" in pl or "/docs/history/" in pl:
        return None, "DOCS_WRITE_BLOCKED"
    if "legacy-backups/" in pl:
        return None, "BACKUP_TREE_BLOCKED"
    unresolved = _REPO_ROOT / raw
    cur = unresolved
    while True:
        if cur.exists() and cur.is_symlink():
            return None, "SYMLINK_BLOCKED"
        if cur.parent == cur:
            break
        cur = cur.parent
    try:
        resolved = unresolved.resolve(strict=False)
        resolved.relative_to(_REPO_ROOT.resolve(strict=False))
    except (OSError, ValueError):
        return None, "OUTSIDE_REPO"
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


def _apply_pairs(content: str, pairs: list[tuple[str, str]]) -> str:
    pairs = sorted(pairs, key=lambda x: len(x[0]), reverse=True)
    out = content
    for leg, repl in pairs:
        out = out.replace(leg, repl)
    return out


def apply_runtime_identifier_elimination(*, explicit_overwrite: bool = False) -> dict[str, Any]:
    plan_path, perr = _resolve_handoff(_PLAN_OUT, "RUNTIME_ELIM_PLAN")
    if perr or plan_path is None or not plan_path.is_file():
        return _ret("blocked", "runtime_identifier_elimination_apply", {}, _RESULT_OUT, [perr or "PLAN_MISSING"], [])

    out_path, oerr = _resolve_handoff(_RESULT_OUT, "RUNTIME_ELIM_RESULT")
    if oerr or out_path is None:
        return _ret("blocked", "runtime_identifier_elimination_apply", {}, _RESULT_OUT, [oerr or "RESULT_PATH_INVALID"], [])
    if out_path.exists() and out_path.is_file() and not explicit_overwrite:
        return _ret("blocked", "runtime_identifier_elimination_apply", {}, _RESULT_OUT, ["RUNTIME_ELIM_RESULT_EXISTS_NO_OVERWRITE"], [])

    try:
        plan_body = json.loads(plan_path.read_text(encoding="utf-8"))
    except Exception:
        return _ret("blocked", "runtime_identifier_elimination_apply", {}, _RESULT_OUT, ["PLAN_JSON_INVALID"], [])

    entries = plan_body.get("entries")
    if not isinstance(entries, list):
        return _ret("blocked", "runtime_identifier_elimination_apply", {}, _RESULT_OUT, ["PLAN_ENTRIES_INVALID"], [])

    by_file: dict[str, list[dict[str, Any]]] = {}
    for ent in entries:
        if not isinstance(ent, dict) or not ent.get("write_allowed"):
            continue
        rel = str(ent.get("target_file") or "").strip().replace("\\", "/")
        if not rel or not _in_elimination_write_scope(rel):
            continue
        by_file.setdefault(rel, []).append(ent)

    for rel in by_file:
        by_file[rel].sort(key=lambda e: -len(str(e.get("legacy_identifier") or "")))

    backup_root = _HANDOFF_ROOT / "legacy-backups"
    cur = backup_root
    while True:
        if cur.exists() and cur.is_symlink():
            return _ret("blocked", "runtime_identifier_elimination_apply", {}, _RESULT_OUT, ["BACKUP_DIR_SYMLINK"], [])
        if cur.parent == cur:
            break
        cur = cur.parent
    backup_root.mkdir(parents=True, exist_ok=True)

    file_results: list[dict[str, Any]] = []
    warnings: list[str] = []

    for rel in sorted(by_file.keys()):
        pairs: list[tuple[str, str]] = []
        for e in by_file[rel]:
            leg = str(e.get("legacy_identifier") or "")
            repl = str(e.get("replacement") or "")
            if leg:
                pairs.append((leg, repl))
        abs_path, err = _resolve_repo_write(rel)
        if err or abs_path is None:
            warnings.append(f"SKIP_PATH:{rel}:{err}")
            continue
        if not abs_path.is_file():
            warnings.append(f"SKIP_NOT_FILE:{rel}")
            continue
        if not _is_probably_text_file(abs_path):
            warnings.append(f"SKIP_BINARY:{rel}")
            continue
        try:
            original = abs_path.read_text(encoding="utf-8")
        except OSError as exc:
            warnings.append(f"SKIP_READ:{rel}:{exc}")
            continue
        new_content = _apply_pairs(original, pairs)
        if new_content == original:
            file_results.append({"target_file": rel, "status": "skipped_no_change", "backup_file": None})
            continue

        digest = hashlib.sha256(f"elim:{rel}".encode("utf-8")).hexdigest()[:24]
        backup_name = f"{digest}.legacy-backup"
        backup_abs = backup_root / backup_name
        payload = json.dumps(
            {"original_text": original, "source_file": rel, "strict_mode": "runtime_identifier_elimination_apply"},
            indent=2,
            sort_keys=True,
        )
        try:
            _atomic_write(backup_abs, payload)
        except OSError as exc:
            return _ret("blocked", "runtime_identifier_elimination_apply", {}, _RESULT_OUT, [f"BACKUP_FAILED:{rel}:{exc}"], warnings)

        try:
            _atomic_write(abs_path, new_content)
        except OSError as exc:
            warnings.append(f"WRITE_FAILED:{rel}:{exc}")
            continue

        file_results.append(
            {
                "target_file": rel,
                "status": "rewritten",
                "backup_file": f"{_BACKUP_DIR_REL}/{backup_name}",
            }
        )

    apply_status = "ok" if not warnings else "review_required"
    body = {
        "result_schema_version": 1,
        "strict_mode": "runtime_identifier_elimination_apply",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "apply_status": apply_status,
        "files_touched": sorted(by_file.keys()),
        "file_results": file_results,
    }
    text = json.dumps(body, indent=2, sort_keys=True)
    if len(text.encode("utf-8")) > _MAX_OUTPUT_BYTES:
        return _ret("blocked", "runtime_identifier_elimination_apply", {}, _RESULT_OUT, ["RESULT_TOO_LARGE"], warnings)
    try:
        _atomic_write(out_path, text)
    except OSError:
        return _ret("blocked", "runtime_identifier_elimination_apply", {}, _RESULT_OUT, ["RESULT_WRITE_FAILED"], warnings)
    return _ret(apply_status, "runtime_identifier_elimination_apply", body, _RESULT_OUT, [], warnings)


def validate_runtime_compatibility_aliases(*, explicit_overwrite: bool = False) -> dict[str, Any]:
    out_path, oerr = _resolve_handoff(_ALIAS_VAL_OUT, "RUNTIME_ALIAS_VAL")
    if oerr or out_path is None:
        return _ret("blocked", "runtime_compatibility_alias_validation", {}, _ALIAS_VAL_OUT, [oerr or "INVALID"], [])
    if out_path.exists() and out_path.is_file() and not explicit_overwrite:
        return _ret("blocked", "runtime_compatibility_alias_validation", {}, _ALIAS_VAL_OUT, ["ALIAS_VAL_EXISTS_NO_OVERWRITE"], [])

    compat, cerr = _load_json(_COMPAT_REL, "COMPAT")
    issues: list[str] = []
    all_ro = True
    all_no_new = True
    if cerr or not isinstance(compat, dict):
        issues.append(str(cerr or "COMPAT_MISSING"))
        all_ro = False
        all_no_new = False
    else:
        for ent in _alias_entries(compat):
            mode = str(ent.get("mode") or "")
            if mode != "read_only_compatibility":
                issues.append(f"ALIAS_MODE_NOT_READ_ONLY:{ent.get('legacy_identifier')}")
                all_ro = False
            if bool(ent.get("allow_new_writes")):
                issues.append(f"ALIAS_ALLOW_NEW_WRITES:{ent.get('legacy_identifier')}")
                all_no_new = False

    inv, _ = _load_json("docs/evidence/runtime-results/handoff/legacy_identifier_inventory.json", "INV")
    active_prod_hits = 0
    if isinstance(inv, dict):
        findings = inv.get("findings")
        if isinstance(findings, list):
            for row in findings:
                if not isinstance(row, dict):
                    continue
                if str(row.get("classification") or "") != "active_runtime_identifier":
                    continue
                p = str(row.get("path") or "").replace("\\", "/")
                if p.startswith("docs/") or "/docs/evidence/" in p.lower():
                    continue
                if _is_test_path(p):
                    continue
                active_prod_hits += 1

    no_active_runtime = active_prod_hits == 0
    st = "ok"
    if issues or not no_active_runtime:
        st = "review_required"
    if cerr:
        st = "blocked"

    body = {
        "validation_schema_version": 1,
        "strict_mode": "runtime_compatibility_alias_validation",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "aliases_all_read_only_mode": bool(all_ro),
        "aliases_all_disallow_new_writes": bool(all_no_new),
        "active_runtime_identifier_non_docs_hits": active_prod_hits,
        "legacy_identifiers_only_in_compat_contract": bool(no_active_runtime and all_ro and all_no_new),
        "issues": issues,
    }
    text = json.dumps(body, indent=2, sort_keys=True)
    if len(text.encode("utf-8")) > _MAX_OUTPUT_BYTES:
        return _ret("blocked", "runtime_compatibility_alias_validation", {}, _ALIAS_VAL_OUT, ["ALIAS_VAL_TOO_LARGE"], [])
    try:
        _atomic_write(out_path, text)
    except OSError:
        return _ret("blocked", "runtime_compatibility_alias_validation", {}, _ALIAS_VAL_OUT, ["ALIAS_VAL_WRITE_FAILED"], [])
    return _ret(st, "runtime_compatibility_alias_validation", body, _ALIAS_VAL_OUT, [], [])


def _read_inventory_active_runtime() -> int:
    p = _REPO_ROOT / "docs/evidence/runtime-results/handoff/legacy_identifier_inventory.json"
    if not p.is_file():
        return 0
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return 0
    c = data.get("counts")
    if isinstance(c, dict):
        return int(c.get("active_runtime_identifier") or 0)
    return 0


def _count_crit_high_from_hotspot_analysis(hot_body: dict[str, Any]) -> tuple[int, int]:
    crit = high = 0
    clusters = hot_body.get("clusters")
    if not isinstance(clusters, dict):
        return 0, 0
    for rows in clusters.values():
        if not isinstance(rows, list):
            continue
        for row in rows:
            if not isinstance(row, dict):
                continue
            if str(row.get("criticality") or "") == "critical":
                crit += 1
            elif str(row.get("criticality") or "") == "high":
                high += 1
    return crit, high


def build_runtime_identifier_elimination_postcheck(*, explicit_overwrite: bool = False) -> dict[str, Any]:
    from deploy.runner_legacy_identifier_hotspot_analysis import build_legacy_identifier_hotspot_analysis
    from deploy.runner_legacy_identifier_inventory import build_legacy_identifier_inventory
    from deploy.runner_setuphelfer_identifier_consistency_check import check_setuphelfer_identifier_consistency

    out_path, oerr = _resolve_handoff(_POSTCHECK_OUT, "RUNTIME_ELIM_POST")
    if oerr or out_path is None:
        return _ret("blocked", "runtime_identifier_elimination_postcheck", {}, _POSTCHECK_OUT, [oerr or "INVALID"], [])
    if out_path.exists() and out_path.is_file() and not explicit_overwrite:
        return _ret("blocked", "runtime_identifier_elimination_postcheck", {}, _POSTCHECK_OUT, ["POSTCHECK_EXISTS_NO_OVERWRITE"], [])

    before_cnt = _read_inventory_active_runtime()

    _ = build_legacy_identifier_inventory(explicit_overwrite=True)
    chk = check_setuphelfer_identifier_consistency(explicit_overwrite=True)
    hot_res = build_legacy_identifier_hotspot_analysis(explicit_overwrite=True)

    after_cnt = _read_inventory_active_runtime()
    hot_body = hot_res.get("analysis") if isinstance(hot_res.get("analysis"), dict) else {}
    crit_rem, high_rem = _count_crit_high_from_hotspot_analysis(hot_body)

    consistency_status = str(chk.get("check_status") or "blocked")
    hotspot_status = str(hot_res.get("analysis_status") or "blocked")

    elimination_complete = (
        crit_rem == 0
        and high_rem == 0
        and consistency_status != "blocked"
        and after_cnt == 0
    )

    version_bump_allowed = bool(elimination_complete)
    suggested = "1.7.1" if version_bump_allowed else "1.7.0"
    rationale = (
        "Runtime-Identifier-Bereinigung abgeschlossen; Patch 1.7.1 vorbereitet."
        if version_bump_allowed
        else "Noch aktive Runtime-Identifier oder Consistency blockiert; bei 1.7.0 bleiben."
    )

    body = {
        "before_runtime_identifier_count": before_cnt,
        "after_runtime_identifier_count": after_cnt,
        "critical_remaining": crit_rem,
        "high_remaining": high_rem,
        "consistency_status": consistency_status,
        "hotspot_status": hotspot_status,
        "runtime_identifier_elimination_complete": bool(elimination_complete),
        "version_bump_prepared": bool(version_bump_allowed),
        "suggested_next_version": suggested,
        "version_bump_rationale": rationale,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "strict_mode": "runtime_identifier_elimination_postcheck",
    }

    post_st = "ok"
    if consistency_status == "blocked" or hotspot_status == "blocked":
        post_st = "blocked"
    elif not elimination_complete or consistency_status == "review_required" or hotspot_status == "review_required":
        post_st = "review_required"

    text = json.dumps(body, indent=2, sort_keys=True)
    if len(text.encode("utf-8")) > _MAX_OUTPUT_BYTES:
        return _ret("blocked", "runtime_identifier_elimination_postcheck", {}, _POSTCHECK_OUT, ["POSTCHECK_TOO_LARGE"], [])
    try:
        _atomic_write(out_path, text)
    except OSError:
        return _ret("blocked", "runtime_identifier_elimination_postcheck", {}, _POSTCHECK_OUT, ["POSTCHECK_WRITE_FAILED"], [])
    return _ret(post_st, "runtime_identifier_elimination_postcheck", body, _POSTCHECK_OUT, [], [])
