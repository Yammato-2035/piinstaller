from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
_HANDOFF_ROOT = (_REPO_ROOT / "docs/evidence/runtime-results/handoff").resolve(strict=False)
_SAFE_PLAN_REL = "docs/evidence/runtime-results/handoff/setuphelfer_safe_rewrite_plan.json"
_CYCLE1_PLAN_REL = "docs/evidence/runtime-results/handoff/setuphelfer_identifier_cleanup_cycle_1_plan.json"
_CYCLE1_RESULT_REL = "docs/evidence/runtime-results/handoff/setuphelfer_identifier_cleanup_cycle_1_result.json"
_CYCLE1_POSTCHECK_REL = "docs/evidence/runtime-results/handoff/setuphelfer_identifier_cleanup_cycle_1_postcheck.json"
_INVENTORY_REL = "docs/evidence/runtime-results/handoff/legacy_identifier_inventory.json"
_BACKUP_DIR_REL = "docs/evidence/runtime-results/handoff/legacy-backups"

_MAX_CYCLE_CHANGES = 100
_MAX_OUTPUT_BYTES = 512 * 1024

_TOKEN_REPLACEMENTS_ORDERED: tuple[tuple[str, str], ...] = (
    ("pi-installer-frontend", "setuphelfer-frontend"),
    ("pi-installer-backend", "setuphelfer-backend"),
    ("pi-installer.service", "setuphelfer.service"),
    ("PI_INSTALLER_", "SETUPHELFER_"),
    ("de.pi-installer.app", "de.setuphelfer.app"),
    ("de.pi-installer", "de.setuphelfer"),
    ("/opt/pi-installer", "/opt/setuphelfer"),
    ("pi-installer", "setuphelfer"),
    ("piinstaller", "setuphelfer"),
)

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


def _resolve_handoff(rel_path: str) -> tuple[Path | None, str | None]:
    raw = str(rel_path or "").strip()
    if not raw:
        return None, "CLEANUP_CYCLE_PATH_INVALID"
    p = Path(raw)
    if p.is_absolute() or ".." in p.parts:
        return None, "CLEANUP_CYCLE_PATH_INVALID"
    unresolved = _REPO_ROOT / p
    cur = unresolved
    while True:
        if cur.exists() and cur.is_symlink():
            return None, "CLEANUP_CYCLE_SYMLINK_BLOCKED"
        if cur.parent == cur:
            break
        cur = cur.parent
    resolved = unresolved.resolve(strict=False)
    if not (str(resolved).startswith(str(_HANDOFF_ROOT) + os.sep) or str(resolved) == str(_HANDOFF_ROOT)):
        return None, "CLEANUP_CYCLE_OUTSIDE_HANDOFF"
    return resolved, None


def _atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(content, encoding="utf-8")
    tmp.replace(path)


def _in_cycle1_scope(rel: str) -> bool:
    pl = rel.replace("\\", "/").lower()
    raw = rel.replace("\\", "/")
    if _changelog_or_history_path(raw):
        return False
    if any(x in pl for x in _CYCLE_EXCLUDED_SUBSTR):
        return False
    if raw in ("package.json", "frontend/package.json", "frontend/src-tauri/tauri.conf.json"):
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
        return None, "CLEANUP_CYCLE_REPO_PATH_INVALID"
    pl = raw.lower()
    if _changelog_or_history_path(raw):
        return None, "CLEANUP_CYCLE_CHANGELOG_OR_HISTORY_BLOCKED"
    if pl.startswith("docs/evidence/") or "/docs/evidence/" in pl:
        return None, "CLEANUP_CYCLE_EVIDENCE_WRITE_BLOCKED"
    if pl.startswith("docs/history/") or "/docs/history/" in pl:
        return None, "CLEANUP_CYCLE_HISTORY_WRITE_BLOCKED"
    if "legacy-backups/" in pl:
        return None, "CLEANUP_CYCLE_BACKUP_TREE_BLOCKED"
    unresolved = _REPO_ROOT / raw
    cur = unresolved
    while True:
        if cur.exists() and cur.is_symlink():
            return None, "CLEANUP_CYCLE_REPO_SYMLINK_BLOCKED"
        if cur.parent == cur:
            break
        cur = cur.parent
    try:
        resolved = unresolved.resolve(strict=False)
        resolved.relative_to(_REPO_ROOT.resolve(strict=False))
    except (OSError, ValueError):
        return None, "CLEANUP_CYCLE_OUTSIDE_REPO"
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


def _apply_allowed_replacements(content: str) -> str:
    out = content
    for legacy, repl in _TOKEN_REPLACEMENTS_ORDERED:
        out = out.replace(legacy, repl)
    return out


def _read_inventory_active_count() -> int:
    inv_path = _REPO_ROOT / _INVENTORY_REL
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


def build_setuphelfer_identifier_cleanup_cycle(*, explicit_overwrite: bool = False) -> dict[str, Any]:
    plan_path, perr = _resolve_handoff(_SAFE_PLAN_REL)
    if perr or plan_path is None or not plan_path.is_file():
        return _plan_ret("blocked", {}, [perr or "CLEANUP_CYCLE_SAFE_PLAN_MISSING"], [])

    out_path, oerr = _resolve_handoff(_CYCLE1_PLAN_REL)
    if oerr or out_path is None:
        return _plan_ret("blocked", {}, [oerr or "CLEANUP_CYCLE_PLAN_OUTPUT_INVALID"], [])
    if out_path.exists() and out_path.is_file() and not explicit_overwrite:
        return _plan_ret("blocked", {}, ["CLEANUP_CYCLE_PLAN_EXISTS_NO_OVERWRITE"], [])

    try:
        safe_plan = json.loads(plan_path.read_text(encoding="utf-8"))
    except Exception:
        return _plan_ret("blocked", {}, ["CLEANUP_CYCLE_SAFE_PLAN_JSON_INVALID"], [])

    entries_in = safe_plan.get("entries")
    if not isinstance(entries_in, list):
        return _plan_ret("blocked", {}, ["CLEANUP_CYCLE_SAFE_PLAN_SHAPE_INVALID"], [])

    eligible: list[dict[str, Any]] = []
    for ent in entries_in:
        if not isinstance(ent, dict):
            continue
        if not bool(ent.get("write_allowed")):
            continue
        rel = str(ent.get("source_file") or "").strip().replace("\\", "/")
        if not rel or not _in_cycle1_scope(rel):
            continue
        eligible.append(dict(ent))

    deferred = eligible[_MAX_CYCLE_CHANGES:]
    selected = eligible[:_MAX_CYCLE_CHANGES]

    plan_status = "ok"
    if deferred:
        plan_status = "review_required"

    body = {
        "cycle_schema_version": 1,
        "cycle": 1,
        "strict_mode": "setuphelfer_identifier_cleanup_cycle",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "plan_status": plan_status,
        "max_changes_per_cycle": _MAX_CYCLE_CHANGES,
        "eligible_total": len(eligible),
        "planned_changes": len(selected),
        "deferred_changes": len(deferred),
        "planned_entries": selected,
        "deferred_entries": deferred,
        "source_safe_plan_file": _SAFE_PLAN_REL,
    }
    text = json.dumps(body, indent=2, sort_keys=True)
    if len(text.encode("utf-8")) > _MAX_OUTPUT_BYTES:
        return _plan_ret("blocked", {}, ["CLEANUP_CYCLE_PLAN_OUTPUT_TOO_LARGE"], [])
    try:
        _atomic_write(out_path, text)
    except OSError:
        return _plan_ret("blocked", {}, ["CLEANUP_CYCLE_PLAN_WRITE_FAILED"], [])
    return _plan_ret(plan_status, body, [], [])


def _plan_ret(status: str, body: dict[str, Any], errors: list[str], warnings: list[str]) -> dict[str, Any]:
    return {
        "cycle_plan_status": status,
        "cycle_plan_file_path": _CYCLE1_PLAN_REL,
        "cycle_plan": body,
        "warnings": list(dict.fromkeys(warnings)),
        "errors": list(dict.fromkeys(errors)) if status == "blocked" else [],
        "blocked_reasons": list(dict.fromkeys(errors)),
    }


def apply_setuphelfer_identifier_cleanup_cycle(*, explicit_overwrite: bool = False) -> dict[str, Any]:
    cycle_plan_path, perr = _resolve_handoff(_CYCLE1_PLAN_REL)
    if perr or cycle_plan_path is None or not cycle_plan_path.is_file():
        return _apply_ret("blocked", {}, [perr or "CLEANUP_CYCLE_PLAN_MISSING"], [])

    out_path, oerr = _resolve_handoff(_CYCLE1_RESULT_REL)
    if oerr or out_path is None:
        return _apply_ret("blocked", {}, [oerr or "CLEANUP_CYCLE_RESULT_OUTPUT_INVALID"], [])
    if out_path.exists() and out_path.is_file() and not explicit_overwrite:
        return _apply_ret("blocked", {}, ["CLEANUP_CYCLE_RESULT_EXISTS_NO_OVERWRITE"], [])

    try:
        cycle_plan = json.loads(cycle_plan_path.read_text(encoding="utf-8"))
    except Exception:
        return _apply_ret("blocked", {}, ["CLEANUP_CYCLE_PLAN_JSON_INVALID"], [])

    planned = cycle_plan.get("planned_entries")
    if not isinstance(planned, list):
        return _apply_ret("blocked", {}, ["CLEANUP_CYCLE_PLAN_ENTRIES_INVALID"], [])

    before_active = _read_inventory_active_count()
    if before_active == 0:
        from deploy.runner_legacy_identifier_inventory import build_legacy_identifier_inventory

        inv_res = build_legacy_identifier_inventory(explicit_overwrite=True)
        if str(inv_res.get("inventory_status") or "") == "blocked":
            return _apply_ret("blocked", {}, list(inv_res.get("errors") or ["CLEANUP_CYCLE_INVENTORY_FAILED"]), [])
        before_active = _read_inventory_active_count()

    backup_root = _HANDOFF_ROOT / "legacy-backups"
    cur = backup_root
    while True:
        if cur.exists() and cur.is_symlink():
            return _apply_ret("blocked", {}, ["CLEANUP_CYCLE_BACKUP_DIR_SYMLINK_BLOCKED"], [])
        if cur.parent == cur:
            break
        cur = cur.parent
    backup_root.mkdir(parents=True, exist_ok=True)

    files_to_touch: dict[str, list[dict[str, Any]]] = {}
    for ent in planned:
        if not isinstance(ent, dict) or not bool(ent.get("write_allowed")):
            continue
        rel = str(ent.get("source_file") or "").strip().replace("\\", "/")
        if not rel or not _in_cycle1_scope(rel):
            continue
        files_to_touch.setdefault(rel, []).append(ent)

    file_results: list[dict[str, Any]] = []
    warnings: list[str] = []

    for rel, _ents in sorted(files_to_touch.items()):
        abs_path, err = _resolve_repo_write_target(rel)
        if err or abs_path is None:
            warnings.append(f"CLEANUP_CYCLE_SKIP_PATH:{rel}:{err}")
            continue
        if not abs_path.is_file():
            warnings.append(f"CLEANUP_CYCLE_SKIP_NOT_FILE:{rel}")
            continue
        if not _is_probably_text_file(abs_path):
            warnings.append(f"CLEANUP_CYCLE_SKIP_BINARY:{rel}")
            continue
        try:
            original = abs_path.read_text(encoding="utf-8")
        except OSError as exc:
            warnings.append(f"CLEANUP_CYCLE_SKIP_READ:{rel}:{exc}")
            continue
        new_content = _apply_allowed_replacements(original)
        if new_content == original:
            file_results.append({"source_file": rel, "status": "skipped_no_change", "backup_file": None})
            continue

        digest = hashlib.sha256(f"cycle1:{rel}".encode("utf-8")).hexdigest()[:24]
        backup_name = f"{digest}.legacy-backup"
        backup_abs = backup_root / backup_name
        backup_payload = json.dumps({"source_file": rel, "cycle": 1, "original_text": original}, indent=2, sort_keys=True)
        try:
            _atomic_write(backup_abs, backup_payload)
        except OSError as exc:
            return _apply_ret("blocked", {}, [f"CLEANUP_CYCLE_BACKUP_FAILED:{rel}:{exc}"], warnings)

        try:
            _atomic_write(abs_path, new_content)
        except OSError as exc:
            warnings.append(f"CLEANUP_CYCLE_WRITE_FAILED:{rel}:{exc}")
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
        "cycle": 1,
        "strict_mode": "setuphelfer_identifier_cleanup_cycle_apply",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "apply_status": apply_status,
        "before_active_runtime_identifier_count": before_active,
        "files_planned": sorted(files_to_touch.keys()),
        "file_results": file_results,
    }
    text = json.dumps(body, indent=2, sort_keys=True)
    if len(text.encode("utf-8")) > _MAX_OUTPUT_BYTES:
        return _apply_ret("blocked", {}, ["CLEANUP_CYCLE_RESULT_OUTPUT_TOO_LARGE"], warnings)
    try:
        _atomic_write(out_path, text)
    except OSError:
        return _apply_ret("blocked", {}, ["CLEANUP_CYCLE_RESULT_WRITE_FAILED"], warnings)
    return _apply_ret(apply_status, body, [], warnings)


def _apply_ret(status: str, body: dict[str, Any], errors: list[str], warnings: list[str]) -> dict[str, Any]:
    return {
        "cycle_apply_status": status,
        "cycle_result_file_path": _CYCLE1_RESULT_REL,
        "cycle_apply": body,
        "warnings": list(dict.fromkeys(warnings)),
        "errors": list(dict.fromkeys(errors)) if status == "blocked" else [],
        "blocked_reasons": list(dict.fromkeys(errors)),
    }


def build_setuphelfer_identifier_cleanup_cycle_postcheck(*, explicit_overwrite: bool = False) -> dict[str, Any]:
    from deploy.runner_legacy_identifier_inventory import build_legacy_identifier_inventory
    from deploy.runner_setuphelfer_identifier_consistency_check import check_setuphelfer_identifier_consistency

    out_path, oerr = _resolve_handoff(_CYCLE1_POSTCHECK_REL)
    if oerr or out_path is None:
        return _post_ret("blocked", {}, [oerr or "CLEANUP_CYCLE_POSTCHECK_OUTPUT_INVALID"], [])
    if out_path.exists() and out_path.is_file() and not explicit_overwrite:
        return _post_ret("blocked", {}, ["CLEANUP_CYCLE_POSTCHECK_EXISTS_NO_OVERWRITE"], [])

    result_path = _REPO_ROOT / _CYCLE1_RESULT_REL
    before_active = 0
    if result_path.is_file():
        try:
            prev = json.loads(result_path.read_text(encoding="utf-8"))
            cap = prev.get("cycle_apply") if isinstance(prev.get("cycle_apply"), dict) else {}
            before_active = int(cap.get("before_active_runtime_identifier_count") or 0)
        except Exception:
            before_active = _read_inventory_active_count()
    else:
        before_active = _read_inventory_active_count()

    inv_res = build_legacy_identifier_inventory(explicit_overwrite=True)
    chk = check_setuphelfer_identifier_consistency(explicit_overwrite=True)

    after_active = _read_inventory_active_count()
    inv_body = inv_res.get("inventory") or {}
    findings = inv_body.get("findings") if isinstance(inv_body, dict) else []
    remaining: list[dict[str, Any]] = []
    if isinstance(findings, list):
        for row in findings:
            if not isinstance(row, dict):
                continue
            if str(row.get("classification") or "") != "active_runtime_identifier":
                continue
            remaining.append(
                {
                    "path": row.get("path"),
                    "line": row.get("line"),
                    "tokens": row.get("tokens"),
                }
            )
            if len(remaining) >= 200:
                break

    consistency_status = str(chk.get("check_status") or "blocked")
    deferred = 0
    plan_path = _REPO_ROOT / _CYCLE1_PLAN_REL
    if plan_path.is_file():
        try:
            pl = json.loads(plan_path.read_text(encoding="utf-8"))
            deferred = int(pl.get("deferred_changes") or 0)
        except Exception:
            deferred = 0

    next_cycle = after_active > 0 or deferred > 0 or str(inv_res.get("inventory_status") or "") == "review_required"

    post_status = "ok"
    if consistency_status == "blocked":
        post_status = "blocked"
    elif consistency_status == "review_required" or next_cycle:
        post_status = "review_required"

    body = {
        "cycle": 1,
        "before_active_runtime_identifier_count": before_active,
        "after_active_runtime_identifier_count": after_active,
        "remaining_runtime_identifiers": remaining,
        "consistency_status": consistency_status,
        "next_cycle_required": bool(next_cycle),
        "inventory_status": str(inv_res.get("inventory_status") or ""),
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "strict_mode": "setuphelfer_identifier_cleanup_cycle_postcheck",
    }
    text = json.dumps(body, indent=2, sort_keys=True)
    if len(text.encode("utf-8")) > _MAX_OUTPUT_BYTES:
        return _post_ret("blocked", {}, ["CLEANUP_CYCLE_POSTCHECK_OUTPUT_TOO_LARGE"], [])
    try:
        _atomic_write(out_path, text)
    except OSError:
        return _post_ret("blocked", {}, ["CLEANUP_CYCLE_POSTCHECK_WRITE_FAILED"], [])
    return _post_ret(post_status, body, [], [])


def _post_ret(status: str, body: dict[str, Any], errors: list[str], warnings: list[str]) -> dict[str, Any]:
    return {
        "cycle_postcheck_status": status,
        "cycle_postcheck_file_path": _CYCLE1_POSTCHECK_REL,
        "cycle_postcheck": body,
        "warnings": list(dict.fromkeys(warnings)),
        "errors": list(dict.fromkeys(errors)) if status == "blocked" else [],
        "blocked_reasons": list(dict.fromkeys(errors)),
    }
