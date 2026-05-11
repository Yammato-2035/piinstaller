from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
_HANDOFF_ROOT = (_REPO_ROOT / "docs/evidence/runtime-results/handoff").resolve(strict=False)
_OUT_REL = "docs/evidence/runtime-results/handoff/setuphelfer_identifier_consistency_check.json"
_MAX_OUTPUT_BYTES = 256 * 1024
_MAX_FINDINGS = 600
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
        return None, "SETUPHELFER_IDENTIFIER_CONSISTENCY_PATH_INVALID"
    p = Path(raw)
    if p.is_absolute() or ".." in p.parts:
        return None, "SETUPHELFER_IDENTIFIER_CONSISTENCY_PATH_INVALID"
    unresolved = _REPO_ROOT / p
    cur = unresolved
    while True:
        if cur.exists() and cur.is_symlink():
            return None, "SETUPHELFER_IDENTIFIER_CONSISTENCY_SYMLINK_BLOCKED"
        if cur.parent == cur:
            break
        cur = cur.parent
    resolved = unresolved.resolve(strict=False)
    if not (str(resolved).startswith(str(_HANDOFF_ROOT) + os.sep) or str(resolved) == str(_HANDOFF_ROOT)):
        return None, "SETUPHELFER_IDENTIFIER_CONSISTENCY_OUTSIDE_HANDOFF"
    return resolved, None


def _atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(content, encoding="utf-8")
    tmp.replace(path)


def _allowed_legacy_path(rel_path: str) -> bool:
    p = rel_path.lower()
    return (
        p.startswith("historical/")
        or p.startswith("docs/history/")
        or p.startswith("docs/evidence/")
        or p.startswith("evidence/")
        or "migration" in p
        or "changelog" in p
    )


def check_setuphelfer_identifier_consistency(*, explicit_overwrite: bool = False) -> dict[str, Any]:
    out_path, err = _resolve_handoff(_OUT_REL)
    if err or out_path is None:
        return _ret("blocked", {}, [err or "SETUPHELFER_IDENTIFIER_CONSISTENCY_OUTPUT_PATH_INVALID"], [])
    if out_path.exists() and out_path.is_file() and not explicit_overwrite:
        return _ret("blocked", {}, ["SETUPHELFER_IDENTIFIER_CONSISTENCY_EXISTS_NO_OVERWRITE"], [])

    blocked_reasons: list[str] = []
    findings: list[dict[str, Any]] = []
    scan_roots = ("docs", "backend", "frontend", "scripts", "systemd", "package.json")
    for root in scan_roots:
        p = _REPO_ROOT / root
        if not p.exists():
            continue
        files = [p] if p.is_file() else [x for x in p.rglob("*") if x.is_file()]
        for fp in files:
            rel = str(fp.relative_to(_REPO_ROOT)).replace("\\", "/")
            try:
                txt = fp.read_text(encoding="utf-8")
            except Exception:
                continue
            for line_no, line in enumerate(txt.splitlines(), start=1):
                matched = [token for token in _TOKENS if token in line]
                if not matched:
                    continue
                allowed = _allowed_legacy_path(rel)
                findings.append({"path": rel, "line": line_no, "tokens": matched, "allowed": allowed})
                if not allowed:
                    if "PI_INSTALLER_" in matched:
                        blocked_reasons.append("SETUPHELFER_IDENTIFIER_CONSISTENCY_NEW_PI_INSTALLER_ENV")
                    if "pi-installer.service" in matched:
                        blocked_reasons.append("SETUPHELFER_IDENTIFIER_CONSISTENCY_NEW_PI_INSTALLER_SERVICE")
                    if "/opt/pi-installer" in matched:
                        blocked_reasons.append("SETUPHELFER_IDENTIFIER_CONSISTENCY_HARD_LEGACY_PATH")
                    if any(token in matched for token in ("pi-installer", "piinstaller", "de.pi-installer", "pi-installer-backend", "pi-installer-frontend")):
                        blocked_reasons.append("SETUPHELFER_IDENTIFIER_CONSISTENCY_ACTIVE_LEGACY_IDENTIFIER")
                if len(findings) >= _MAX_FINDINGS:
                    break
            if len(findings) >= _MAX_FINDINGS:
                break
        if len(findings) >= _MAX_FINDINGS:
            break

    status = "ok"
    if blocked_reasons:
        offending_paths: list[str] = []
        for row in findings:
            if not isinstance(row, dict) or row.get("allowed"):
                continue
            p = str(row.get("path") or "").replace("\\", "/")
            if p:
                offending_paths.append(p)
        has_runtime = any(not p.startswith("docs/") for p in offending_paths)
        status = "blocked" if has_runtime else "review_required"

    body = {
        "check_schema_version": 1,
        "strict_mode": "setuphelfer_identifier_consistency_check",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "check_status": status,
        "findings": findings,
        "findings_truncated": len(findings) >= _MAX_FINDINGS,
        "blocked_reasons": list(dict.fromkeys(blocked_reasons)),
        "allowed_path_rules": [
            "historical/*",
            "docs/history/*",
            "docs/evidence/*",
            "evidence/*",
            "*migration*",
            "*changelog*",
        ],
    }
    text = json.dumps(body, indent=2, sort_keys=True)
    if len(text.encode("utf-8")) > _MAX_OUTPUT_BYTES:
        return _ret("blocked", {}, ["SETUPHELFER_IDENTIFIER_CONSISTENCY_OUTPUT_TOO_LARGE"], [])
    try:
        _atomic_write(out_path, text)
    except OSError:
        return _ret("blocked", {}, ["SETUPHELFER_IDENTIFIER_CONSISTENCY_WRITE_FAILED"], [])
    return _ret(status, body, list(dict.fromkeys(blocked_reasons)), [])


def _ret(status: str, check: dict[str, Any], reason_codes: list[str], warnings: list[str]) -> dict[str, Any]:
    rc = list(dict.fromkeys(reason_codes))
    return {
        "check_status": status,
        "check_file_path": _OUT_REL,
        "check": check,
        "warnings": list(dict.fromkeys(warnings)),
        "errors": rc if status == "blocked" else [],
        "blocked_reasons": rc,
    }
