from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
_HANDOFF_ROOT = (_REPO_ROOT / "docs/evidence/runtime-results/handoff").resolve(strict=False)
_CLASSIFICATION_REL = "docs/evidence/runtime-results/handoff/legacy_identifier_cleanup_classification.json"
_OUT_REL = "docs/evidence/runtime-results/handoff/setuphelfer_safe_rewrite_plan.json"
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


def _resolve_handoff(rel_path: str) -> tuple[Path | None, str | None]:
    raw = str(rel_path or "").strip()
    if not raw:
        return None, "SAFE_REWRITE_PLAN_PATH_INVALID"
    p = Path(raw)
    if p.is_absolute() or ".." in p.parts:
        return None, "SAFE_REWRITE_PLAN_PATH_INVALID"
    unresolved = _REPO_ROOT / p
    cur = unresolved
    while True:
        if cur.exists() and cur.is_symlink():
            return None, "SAFE_REWRITE_PLAN_SYMLINK_BLOCKED"
        if cur.parent == cur:
            break
        cur = cur.parent
    resolved = unresolved.resolve(strict=False)
    if not (str(resolved).startswith(str(_HANDOFF_ROOT) + os.sep) or str(resolved) == str(_HANDOFF_ROOT)):
        return None, "SAFE_REWRITE_PLAN_OUTSIDE_HANDOFF"
    return resolved, None


def _atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(content, encoding="utf-8")
    tmp.replace(path)


def _replacement_for_token(token: str) -> str | None:
    t = str(token)
    for legacy, repl in _TOKEN_REPLACEMENTS_ORDERED:
        if t == legacy:
            return repl
    return None


def _is_historical_or_evidence_path(rel: str) -> bool:
    pl = rel.lower().replace("\\", "/")
    if pl.startswith("docs/evidence/") or "/docs/evidence/" in pl:
        return True
    if pl.startswith("docs/history/") or "/docs/history/" in pl:
        return True
    if "changelog" in pl:
        return True
    return False


def _allowed_rewrite_root(rel: str) -> bool:
    pl = rel.replace("\\", "/")
    if pl == "package.json":
        return True
    prefixes = ("backend/", "frontend/", "scripts/", "systemd/", "config/")
    if any(pl.startswith(p) for p in prefixes):
        return not pl.startswith("docs/")
    return False


def build_setuphelfer_safe_rewrite_plan(*, explicit_overwrite: bool = False) -> dict[str, Any]:
    cls_path, cerr = _resolve_handoff(_CLASSIFICATION_REL)
    if cerr or cls_path is None or not cls_path.is_file():
        return _ret("blocked", {}, [cerr or "SAFE_REWRITE_PLAN_CLASSIFICATION_MISSING"], [])

    out_path, oerr = _resolve_handoff(_OUT_REL)
    if oerr or out_path is None:
        return _ret("blocked", {}, [oerr or "SAFE_REWRITE_PLAN_OUTPUT_PATH_INVALID"], [])
    if out_path.exists() and out_path.is_file() and not explicit_overwrite:
        return _ret("blocked", {}, ["SAFE_REWRITE_PLAN_EXISTS_NO_OVERWRITE"], [])

    try:
        cls_body = json.loads(cls_path.read_text(encoding="utf-8"))
    except Exception:
        return _ret("blocked", {}, ["SAFE_REWRITE_PLAN_CLASSIFICATION_JSON_INVALID"], [])

    items_in = cls_body.get("items")
    if not isinstance(items_in, list):
        return _ret("blocked", {}, ["SAFE_REWRITE_PLAN_CLASSIFICATION_SHAPE_INVALID"], [])

    plan_entries: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()

    for row in items_in:
        if not isinstance(row, dict):
            continue
        rel = str(row.get("path") or "").strip().replace("\\", "/")
        cleanup = str(row.get("cleanup_classification") or "")
        tokens_raw = row.get("tokens")
        tokens = [str(t) for t in tokens_raw] if isinstance(tokens_raw, list) else []

        for token in tokens:
            repl = _replacement_for_token(token)
            if repl is None:
                key = (rel, token)
                if key in seen:
                    continue
                seen.add(key)
                plan_entries.append(
                    {
                        "source_file": rel,
                        "legacy_token": token,
                        "replacement": "",
                        "classification": cleanup or "needs_manual_review",
                        "write_allowed": False,
                        "reason": "no_safe_replacement_mapping_for_token",
                    }
                )
                continue

            key = (rel, token)
            if key in seen:
                continue
            seen.add(key)

            write_allowed = False
            reason = ""
            if cleanup == "rename_now":
                if _is_historical_or_evidence_path(rel):
                    reason = "historical_or_evidence_path_no_write"
                elif not _allowed_rewrite_root(rel):
                    reason = "path_not_in_allowed_project_prefix"
                else:
                    write_allowed = True
                    reason = "rename_now_in_allowed_tree_with_mapped_token"
            elif cleanup == "alias_required":
                reason = "alias_required_no_direct_write_use_read_only_compat"
            elif cleanup == "historical_keep":
                reason = "historical_keep"
            elif cleanup == "needs_manual_review":
                reason = "needs_manual_review"
            elif cleanup == "blocked_unknown":
                reason = "blocked_unknown"
            else:
                reason = "unknown_cleanup_classification"

            plan_entries.append(
                {
                    "source_file": rel,
                    "legacy_token": token,
                    "replacement": repl,
                    "classification": cleanup,
                    "write_allowed": write_allowed,
                    "reason": reason,
                }
            )

    cls_status = str(cls_body.get("classification_status") or "blocked")
    plan_status = "blocked" if cls_status == "blocked" else ("review_required" if cls_status == "review_required" else "ok")
    if any(e.get("write_allowed") for e in plan_entries) and plan_status == "ok":
        pass
    elif any(e.get("write_allowed") for e in plan_entries) and plan_status == "review_required":
        plan_status = "review_required"

    body = {
        "plan_schema_version": 1,
        "strict_mode": "setuphelfer_safe_rewrite_plan",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "plan_status": plan_status,
        "source_classification_file": _CLASSIFICATION_REL,
        "token_replacements_order": [{"from": a, "to": b} for a, b in _TOKEN_REPLACEMENTS_ORDERED],
        "entries": plan_entries,
    }
    text = json.dumps(body, indent=2, sort_keys=True)
    if len(text.encode("utf-8")) > _MAX_OUTPUT_BYTES:
        return _ret("blocked", {}, ["SAFE_REWRITE_PLAN_OUTPUT_TOO_LARGE"], [])
    try:
        _atomic_write(out_path, text)
    except OSError:
        return _ret("blocked", {}, ["SAFE_REWRITE_PLAN_WRITE_FAILED"], [])
    return _ret(plan_status, body, [], [])


def _ret(status: str, body: dict[str, Any], errors: list[str], warnings: list[str]) -> dict[str, Any]:
    return {
        "plan_status": status,
        "plan_file_path": _OUT_REL,
        "plan": body,
        "warnings": list(dict.fromkeys(warnings)),
        "errors": list(dict.fromkeys(errors)) if status == "blocked" else [],
        "blocked_reasons": list(dict.fromkeys(errors)),
    }
