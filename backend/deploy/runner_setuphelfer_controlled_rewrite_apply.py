from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
_HANDOFF_ROOT = (_REPO_ROOT / "docs/evidence/runtime-results/handoff").resolve(strict=False)
_PLAN_REL = "docs/evidence/runtime-results/handoff/setuphelfer_safe_rewrite_plan.json"
_OUT_REL = "docs/evidence/runtime-results/handoff/setuphelfer_controlled_rewrite_result.json"
_BACKUP_DIR_REL = "docs/evidence/runtime-results/handoff/legacy-backups"

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
        return None, "CONTROLLED_REWRITE_PATH_INVALID"
    p = Path(raw)
    if p.is_absolute() or ".." in p.parts:
        return None, "CONTROLLED_REWRITE_PATH_INVALID"
    unresolved = _REPO_ROOT / p
    cur = unresolved
    while True:
        if cur.exists() and cur.is_symlink():
            return None, "CONTROLLED_REWRITE_SYMLINK_BLOCKED"
        if cur.parent == cur:
            break
        cur = cur.parent
    resolved = unresolved.resolve(strict=False)
    if not (str(resolved).startswith(str(_HANDOFF_ROOT) + os.sep) or str(resolved) == str(_HANDOFF_ROOT)):
        return None, "CONTROLLED_REWRITE_OUTSIDE_HANDOFF"
    return resolved, None


def _resolve_repo_relative(rel: str) -> tuple[Path | None, str | None]:
    raw = str(rel or "").strip().replace("\\", "/")
    if not raw or ".." in raw or raw.startswith("/"):
        return None, "CONTROLLED_REWRITE_REPO_PATH_INVALID"
    pl = raw
    if pl.startswith("docs/evidence/"):
        return None, "CONTROLLED_REWRITE_EVIDENCE_WRITE_BLOCKED"
    if pl.startswith("docs/history/") or "changelog" in pl.lower():
        return None, "CONTROLLED_REWRITE_HISTORICAL_WRITE_BLOCKED"
    unresolved = _REPO_ROOT / pl
    cur = unresolved
    while True:
        if cur.exists() and cur.is_symlink():
            return None, "CONTROLLED_REWRITE_REPO_SYMLINK_BLOCKED"
        if cur.parent == cur:
            break
        cur = cur.parent
    try:
        resolved = unresolved.resolve(strict=False)
    except OSError:
        return None, "CONTROLLED_REWRITE_REPO_RESOLVE_FAILED"
    try:
        resolved.relative_to(_REPO_ROOT.resolve(strict=False))
    except ValueError:
        return None, "CONTROLLED_REWRITE_OUTSIDE_REPO"
    return resolved, None


def _atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(content, encoding="utf-8")
    tmp.replace(path)


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


def _allowed_target(rel: str) -> bool:
    pl = rel.replace("\\", "/")
    if pl == "package.json":
        return True
    prefixes = ("backend/", "frontend/", "scripts/", "systemd/", "config/")
    return any(pl.startswith(p) for p in prefixes)


def _apply_allowed_replacements(content: str) -> str:
    out = content
    for legacy, repl in _TOKEN_REPLACEMENTS_ORDERED:
        out = out.replace(legacy, repl)
    return out


def apply_setuphelfer_controlled_rewrite(
    *,
    explicit_overwrite: bool = False,
    run_post_consistency_check: bool = True,
) -> dict[str, Any]:
    from deploy.runner_setuphelfer_identifier_consistency_check import check_setuphelfer_identifier_consistency

    plan_path, perr = _resolve_handoff(_PLAN_REL)
    if perr or plan_path is None or not plan_path.is_file():
        return _ret("blocked", {}, [perr or "CONTROLLED_REWRITE_PLAN_MISSING"], [])

    out_path, oerr = _resolve_handoff(_OUT_REL)
    if oerr or out_path is None:
        return _ret("blocked", {}, [oerr or "CONTROLLED_REWRITE_OUTPUT_PATH_INVALID"], [])
    if out_path.exists() and out_path.is_file() and not explicit_overwrite:
        return _ret("blocked", {}, ["CONTROLLED_REWRITE_EXISTS_NO_OVERWRITE"], [])

    backup_root = _HANDOFF_ROOT / "legacy-backups"
    cur = backup_root
    while True:
        if cur.exists() and cur.is_symlink():
            return _ret("blocked", {}, ["CONTROLLED_REWRITE_BACKUP_DIR_SYMLINK_BLOCKED"], [])
        if cur.parent == cur:
            break
        cur = cur.parent

    try:
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
    except Exception:
        return _ret("blocked", {}, ["CONTROLLED_REWRITE_PLAN_JSON_INVALID"], [])

    entries = plan.get("entries")
    if not isinstance(entries, list):
        return _ret("blocked", {}, ["CONTROLLED_REWRITE_PLAN_SHAPE_INVALID"], [])

    backup_root.mkdir(parents=True, exist_ok=True)

    touched_files: set[str] = set()
    file_results: list[dict[str, Any]] = []
    warnings: list[str] = []

    for ent in entries:
        if not isinstance(ent, dict):
            continue
        if not bool(ent.get("write_allowed")):
            continue
        rel = str(ent.get("source_file") or "").strip().replace("\\", "/")
        if not rel or not _allowed_target(rel):
            warnings.append(f"CONTROLLED_REWRITE_SKIP_NOT_ALLOWED:{rel}")
            continue

        abs_path, err = _resolve_repo_relative(rel)
        if err or abs_path is None:
            warnings.append(f"CONTROLLED_REWRITE_SKIP_PATH:{rel}:{err}")
            continue
        if not abs_path.is_file():
            warnings.append(f"CONTROLLED_REWRITE_SKIP_NOT_FILE:{rel}")
            continue
        if not _is_probably_text_file(abs_path):
            warnings.append(f"CONTROLLED_REWRITE_SKIP_BINARY:{rel}")
            continue

        try:
            original = abs_path.read_text(encoding="utf-8")
        except OSError as exc:
            warnings.append(f"CONTROLLED_REWRITE_SKIP_READ:{rel}:{exc}")
            continue

        new_content = _apply_allowed_replacements(original)
        if new_content == original:
            file_results.append({"source_file": rel, "status": "skipped_no_change", "backup_file": None})
            continue

        digest = hashlib.sha256(rel.encode("utf-8")).hexdigest()[:24]
        backup_name = f"{digest}.legacy-backup"
        backup_abs = backup_root / backup_name
        backup_payload = json.dumps({"source_file": rel, "original_text": original}, indent=2, sort_keys=True)
        try:
            _atomic_write(backup_abs, backup_payload)
        except OSError as exc:
            return _ret("blocked", {}, [f"CONTROLLED_REWRITE_BACKUP_FAILED:{rel}:{exc}"], warnings)

        try:
            _atomic_write(abs_path, new_content)
        except OSError as exc:
            warnings.append(f"CONTROLLED_REWRITE_WRITE_FAILED:{rel}:{exc}")
            continue

        touched_files.add(rel)
        file_results.append(
            {
                "source_file": rel,
                "status": "rewritten",
                "backup_file": f"{_BACKUP_DIR_REL}/{backup_name}",
            }
        )

    apply_status = "ok" if not warnings else "review_required"
    post_check: dict[str, Any] | None = None
    if run_post_consistency_check:
        post_check = check_setuphelfer_identifier_consistency(explicit_overwrite=True)
        pcs = str(post_check.get("check_status") or "blocked")
        if pcs == "blocked":
            apply_status = "review_required"

    body = {
        "result_schema_version": 1,
        "strict_mode": "setuphelfer_controlled_rewrite_apply",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "apply_status": apply_status,
        "files_touched": sorted(touched_files),
        "file_results": file_results,
        "post_consistency_check": post_check,
    }
    text = json.dumps(body, indent=2, sort_keys=True)
    if len(text.encode("utf-8")) > 256 * 1024:
        return _ret("blocked", {}, ["CONTROLLED_REWRITE_OUTPUT_TOO_LARGE"], warnings)
    try:
        _atomic_write(out_path, text)
    except OSError:
        return _ret("blocked", {}, ["CONTROLLED_REWRITE_RESULT_WRITE_FAILED"], warnings)

    return _ret(apply_status, body, [], warnings)


def _ret(status: str, body: dict[str, Any], errors: list[str], warnings: list[str]) -> dict[str, Any]:
    return {
        "apply_status": status,
        "result_file_path": _OUT_REL,
        "result": body,
        "warnings": list(dict.fromkeys(warnings)),
        "errors": list(dict.fromkeys(errors)) if status == "blocked" else [],
        "blocked_reasons": list(dict.fromkeys(errors)),
    }
