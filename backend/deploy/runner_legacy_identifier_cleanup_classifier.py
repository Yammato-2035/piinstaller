from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
_HANDOFF_ROOT = (_REPO_ROOT / "docs/evidence/runtime-results/handoff").resolve(strict=False)
_INVENTORY_REL = "docs/evidence/runtime-results/handoff/legacy_identifier_inventory.json"
_OUT_REL = "docs/evidence/runtime-results/handoff/legacy_identifier_cleanup_classification.json"
_MAX_OUTPUT_BYTES = 512 * 1024


def _resolve_handoff(rel_path: str) -> tuple[Path | None, str | None]:
    raw = str(rel_path or "").strip()
    if not raw:
        return None, "LEGACY_CLEANUP_CLASSIFIER_PATH_INVALID"
    p = Path(raw)
    if p.is_absolute() or ".." in p.parts:
        return None, "LEGACY_CLEANUP_CLASSIFIER_PATH_INVALID"
    unresolved = _REPO_ROOT / p
    cur = unresolved
    while True:
        if cur.exists() and cur.is_symlink():
            return None, "LEGACY_CLEANUP_CLASSIFIER_SYMLINK_BLOCKED"
        if cur.parent == cur:
            break
        cur = cur.parent
    resolved = unresolved.resolve(strict=False)
    if not (str(resolved).startswith(str(_HANDOFF_ROOT) + os.sep) or str(resolved) == str(_HANDOFF_ROOT)):
        return None, "LEGACY_CLEANUP_CLASSIFIER_OUTSIDE_HANDOFF"
    return resolved, None


def _atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(content, encoding="utf-8")
    tmp.replace(path)


def _is_historical_path(rel: str) -> bool:
    pl = rel.lower().replace("\\", "/")
    if pl.startswith("docs/evidence/") or "/docs/evidence/" in pl:
        return True
    if pl.startswith("docs/history/") or "/docs/history/" in pl:
        return True
    if "changelog" in pl:
        return True
    return False


def _is_code_or_config_path(rel: str) -> bool:
    pl = rel.replace("\\", "/")
    if pl == "package.json":
        return True
    prefixes = ("backend/", "frontend/", "scripts/", "systemd/", "config/")
    return any(pl.startswith(p) for p in prefixes)


def _is_localstorage_context(rel: str, line_lower: str) -> bool:
    pl = rel.lower().replace("\\", "/")
    if ".local/share" in pl or "appdata" in pl:
        return True
    return "localstorage" in line_lower or "appdata" in line_lower or "de.pi-installer.app" in line_lower


def _classify_one(
    *,
    rel_path: str,
    line_no: int,
    tokens: list[str],
    line_preview: str,
) -> tuple[str, str]:
    """Returns (cleanup_classification, reason)."""
    inv_line = (line_preview or "").lower()
    rel = rel_path.replace("\\", "/")

    if _is_historical_path(rel):
        return "historical_keep", "path_under_evidence_history_or_changelog"

    if rel.startswith("docs/"):
        return "needs_manual_review", "active_hit_in_general_docs_requires_operator_review"

    if "/opt/pi-installer" in tokens or "pi-installer.service" in tokens:
        if _is_code_or_config_path(rel):
            return "rename_now", "runtime_path_or_service_token_in_allowed_code_tree"
        return "needs_manual_review", "runtime_path_or_service_token_outside_known_code_roots"

    if _is_localstorage_context(rel, inv_line):
        return "alias_required", "localstorage_or_appdata_context_requires_read_only_alias"

    if _is_code_or_config_path(rel):
        if any(t == "PI_INSTALLER_" for t in tokens):
            return "rename_now", "env_prefix_in_code_or_config"
        if any(t in ("de.pi-installer", "de.pi-installer.app") for t in tokens) and (
            "localstorage" in inv_line or "appdata" in inv_line
        ):
            return "alias_required", "identifier_in_storage_context"
        return "rename_now", "legacy_token_in_allowed_code_or_config_path"

    ext = Path(rel).suffix.lower()
    if ext in {".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".woff", ".woff2", ".ttf", ".eot", ".pdf", ".zip"}:
        return "blocked_unknown", "binary_or_unknown_asset_extension"

    if not _is_code_or_config_path(rel) and not rel.startswith("docs/"):
        return "needs_manual_review", "hit_outside_standard_scan_roots"

    return "blocked_unknown", "unclassified_hit"


def classify_active_legacy_identifiers(*, explicit_overwrite: bool = False) -> dict[str, Any]:
    inv_path, ierr = _resolve_handoff(_INVENTORY_REL)
    if ierr or inv_path is None or not inv_path.is_file():
        return _ret(
            "blocked",
            {},
            [ierr or "LEGACY_CLEANUP_CLASSIFIER_INVENTORY_MISSING"],
            [],
        )

    out_path, oerr = _resolve_handoff(_OUT_REL)
    if oerr or out_path is None:
        return _ret("blocked", {}, [oerr or "LEGACY_CLEANUP_CLASSIFIER_OUTPUT_PATH_INVALID"], [])
    if out_path.exists() and out_path.is_file() and not explicit_overwrite:
        return _ret("blocked", {}, ["LEGACY_CLEANUP_CLASSIFIER_EXISTS_NO_OVERWRITE"], [])

    try:
        inv = json.loads(inv_path.read_text(encoding="utf-8"))
    except Exception:
        return _ret("blocked", {}, ["LEGACY_CLEANUP_CLASSIFIER_INVENTORY_JSON_INVALID"], [])

    findings = inv.get("findings")
    if not isinstance(findings, list):
        return _ret("blocked", {}, ["LEGACY_CLEANUP_CLASSIFIER_INVENTORY_SHAPE_INVALID"], [])

    items: list[dict[str, Any]] = []
    for row in findings:
        if not isinstance(row, dict):
            continue
        if str(row.get("classification") or "") != "active_runtime_identifier":
            continue
        rel = str(row.get("path") or "").strip().replace("\\", "/")
        if not rel:
            continue
        tokens_raw = row.get("tokens")
        tokens = [str(t) for t in tokens_raw] if isinstance(tokens_raw, list) else []
        line_no = int(row.get("line") or 0)
        preview = str(row.get("line_preview") or "")
        if not preview and line_no > 0:
            try:
                lines = (_REPO_ROOT / rel).read_text(encoding="utf-8").splitlines()
                if 0 < line_no <= len(lines):
                    preview = lines[line_no - 1]
            except OSError:
                preview = ""
        cls, reason = _classify_one(rel_path=rel, line_no=line_no, tokens=tokens, line_preview=preview)
        items.append(
            {
                "path": rel,
                "line": line_no,
                "tokens": tokens,
                "inventory_classification": "active_runtime_identifier",
                "cleanup_classification": cls,
                "reason": reason,
            }
        )

    counts: dict[str, int] = {}
    for it in items:
        c = str(it.get("cleanup_classification") or "blocked_unknown")
        counts[c] = counts.get(c, 0) + 1

    blocked_unknown = counts.get("blocked_unknown", 0)
    manual = counts.get("needs_manual_review", 0)
    if blocked_unknown > 0:
        status = "blocked"
    elif manual > 0:
        status = "review_required"
    else:
        status = "ok"

    body = {
        "classification_schema_version": 1,
        "strict_mode": "legacy_identifier_cleanup_classification",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "classification_status": status,
        "source_inventory_file": _INVENTORY_REL,
        "counts": counts,
        "items": items,
    }
    text = json.dumps(body, indent=2, sort_keys=True)
    if len(text.encode("utf-8")) > _MAX_OUTPUT_BYTES:
        return _ret("blocked", {}, ["LEGACY_CLEANUP_CLASSIFIER_OUTPUT_TOO_LARGE"], [])
    try:
        _atomic_write(out_path, text)
    except OSError:
        return _ret("blocked", {}, ["LEGACY_CLEANUP_CLASSIFIER_WRITE_FAILED"], [])
    return _ret(status, body, [], [])


def _ret(status: str, body: dict[str, Any], errors: list[str], warnings: list[str]) -> dict[str, Any]:
    return {
        "classification_status": status,
        "classification_file_path": _OUT_REL,
        "classification": body,
        "warnings": list(dict.fromkeys(warnings)),
        "errors": list(dict.fromkeys(errors)) if status == "blocked" else [],
        "blocked_reasons": list(dict.fromkeys(errors)),
    }
