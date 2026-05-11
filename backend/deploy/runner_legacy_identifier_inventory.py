from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
_HANDOFF_ROOT = (_REPO_ROOT / "docs/evidence/runtime-results/handoff").resolve(strict=False)
_OUT_REL = "docs/evidence/runtime-results/handoff/legacy_identifier_inventory.json"
_MAX_OUTPUT_BYTES = 256 * 1024
_MAX_FINDINGS = 400
_SCAN_TARGETS = (
    "docs",
    "backend",
    "frontend",
    "scripts",
    "systemd",
    "src-tauri",
    "package.json",
)
_TOKENS = (
    "pi-installer",
    "piinstaller",
    "PI_INSTALLER_",
    "de.pi-installer",
    "/opt/pi-installer",
    "pi-installer.service",
    "pi-installer-backend",
    "pi-installer-frontend",
)


def _resolve_handoff(rel_path: str) -> tuple[Path | None, str | None]:
    raw = str(rel_path or "").strip()
    if not raw:
        return None, "LEGACY_IDENTIFIER_INVENTORY_PATH_INVALID"
    p = Path(raw)
    if p.is_absolute() or ".." in p.parts:
        return None, "LEGACY_IDENTIFIER_INVENTORY_PATH_INVALID"
    unresolved = _REPO_ROOT / p
    cur = unresolved
    while True:
        if cur.exists() and cur.is_symlink():
            return None, "LEGACY_IDENTIFIER_INVENTORY_SYMLINK_BLOCKED"
        if cur.parent == cur:
            break
        cur = cur.parent
    resolved = unresolved.resolve(strict=False)
    if not (str(resolved).startswith(str(_HANDOFF_ROOT) + os.sep) or str(resolved) == str(_HANDOFF_ROOT)):
        return None, "LEGACY_IDENTIFIER_INVENTORY_OUTSIDE_HANDOFF"
    return resolved, None


def _atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(content, encoding="utf-8")
    tmp.replace(path)


def _classify(path: str, line_text: str) -> str:
    p = path.lower()
    t = line_text.lower()
    if "/docs/evidence/" in p:
        return "historical_evidence_reference"
    if "/docs/" in p and ("history" in p or "changelog" in p):
        return "legacy_doc_reference"
    if "migration" in p or "alias" in p:
        return "migration_alias"
    if "deprecated" in t or "legacy" in t:
        return "deprecated_runtime_reference"
    return "active_runtime_identifier"


def build_legacy_identifier_inventory(*, explicit_overwrite: bool = False) -> dict[str, Any]:
    out_path, err = _resolve_handoff(_OUT_REL)
    if err or out_path is None:
        return _ret("blocked", {}, [err or "LEGACY_IDENTIFIER_INVENTORY_OUTPUT_PATH_INVALID"], [])
    if out_path.exists() and out_path.is_file() and not explicit_overwrite:
        return _ret("blocked", {}, ["LEGACY_IDENTIFIER_INVENTORY_EXISTS_NO_OVERWRITE"], [])

    findings: list[dict[str, Any]] = []
    seen_path_line: set[tuple[str, int]] = set()

    def _append_token_hits(rel: str, line_no: int, line: str, matched: list[str]) -> None:
        nonlocal findings
        key = (rel, line_no)
        if key in seen_path_line:
            return
        seen_path_line.add(key)
        findings.append(
            {
                "path": rel,
                "line": line_no,
                "tokens": matched,
                "classification": _classify(rel, line),
            }
        )

    # Handoff zuerst: sonst kann das Findings-Limit durch große docs-Bäume erreicht werden,
    # bevor runtime-results/handoff-Dateien gescannt werden.
    if _HANDOFF_ROOT.is_dir():
        for fp in sorted(_HANDOFF_ROOT.rglob("*")):
            if not fp.is_file():
                continue
            try:
                rel = str(fp.relative_to(_REPO_ROOT)).replace("\\", "/")
                content = fp.read_text(encoding="utf-8")
            except Exception:
                continue
            for line_no, line in enumerate(content.splitlines(), start=1):
                matched = [token for token in _TOKENS if token in line]
                if matched:
                    _append_token_hits(rel, line_no, line, matched)
                if len(findings) >= _MAX_FINDINGS:
                    break
            if len(findings) >= _MAX_FINDINGS:
                break

    for target in _SCAN_TARGETS:
        start = _REPO_ROOT / target
        if not start.exists():
            continue
        files = [start] if start.is_file() else [p for p in start.rglob("*") if p.is_file()]
        for fp in files:
            try:
                rel = str(fp.relative_to(_REPO_ROOT)).replace("\\", "/")
                content = fp.read_text(encoding="utf-8")
            except Exception:
                continue
            for line_no, line in enumerate(content.splitlines(), start=1):
                matched = [token for token in _TOKENS if token in line]
                if matched:
                    _append_token_hits(rel, line_no, line, matched)
                if len(findings) >= _MAX_FINDINGS:
                    break
            if len(findings) >= _MAX_FINDINGS:
                break
        if len(findings) >= _MAX_FINDINGS:
            break

    counts: dict[str, int] = {}
    for item in findings:
        cls = str(item.get("classification") or "active_runtime_identifier")
        counts[cls] = counts.get(cls, 0) + 1
    status = "ok" if counts.get("active_runtime_identifier", 0) == 0 else "review_required"
    body = {
        "inventory_schema_version": 1,
        "strict_mode": "legacy_identifier_inventory",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "inventory_status": status,
        "scan_targets": list(_SCAN_TARGETS),
        "tokens": list(_TOKENS),
        "counts": counts,
        "findings_truncated": len(findings) >= _MAX_FINDINGS,
        "findings": findings,
    }
    text = json.dumps(body, indent=2, sort_keys=True)
    if len(text.encode("utf-8")) > _MAX_OUTPUT_BYTES:
        return _ret("blocked", {}, ["LEGACY_IDENTIFIER_INVENTORY_OUTPUT_TOO_LARGE"], [])
    try:
        _atomic_write(out_path, text)
    except OSError:
        return _ret("blocked", {}, ["LEGACY_IDENTIFIER_INVENTORY_WRITE_FAILED"], [])
    return _ret(status, body, [], [])


def _ret(status: str, inventory: dict[str, Any], errors: list[str], warnings: list[str]) -> dict[str, Any]:
    return {
        "inventory_status": status,
        "inventory_file_path": _OUT_REL,
        "inventory": inventory,
        "warnings": list(dict.fromkeys(warnings)),
        "errors": list(dict.fromkeys(errors)) if status == "blocked" else [],
        "blocked_reasons": list(dict.fromkeys(errors)),
    }
