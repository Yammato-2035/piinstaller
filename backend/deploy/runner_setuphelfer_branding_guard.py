from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
_HANDOFF_ROOT = (_REPO_ROOT / "docs/evidence/runtime-results/handoff").resolve(strict=False)

_INVENTORY_REL = "docs/evidence/runtime-results/handoff/legacy_identifier_inventory.json"
_ZERO_STATE_REL = "docs/evidence/runtime-results/handoff/runtime_identifier_zero_state_verification.json"
_ALIAS_REL = "docs/evidence/runtime-results/handoff/compatibility_aliases.json"
_CFG_VERSION_REL = "config/version.json"
_OUT_REL = "docs/evidence/runtime-results/handoff/setuphelfer_branding_guard_check.json"
_MAX_OUTPUT_BYTES = 512 * 1024

_RUNTIME_PREFIXES = (
    "backend/",
    "frontend/",
    "config/",
    ".github/",
    "scripts/",
)
_ROOT_RUNTIME_FILES = frozenset(
    {
        "package.json",
        "package-lock.json",
        "Cargo.toml",
        "Cargo.lock",
        "Dockerfile",
        "docker-compose.yml",
        "docker-compose.yaml",
        "Makefile",
        "pyproject.toml",
    }
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


def _resolve_repo(rel_path: str, prefix: str) -> tuple[Path | None, str | None]:
    raw = str(rel_path or "").strip().replace("\\", "/")
    if not raw or ".." in raw or raw.startswith("/"):
        return None, f"{prefix}_REPO_PATH_INVALID"
    unresolved = _REPO_ROOT / raw
    try:
        resolved = unresolved.resolve(strict=False)
        resolved.relative_to(_REPO_ROOT.resolve(strict=False))
    except (OSError, ValueError):
        return None, f"{prefix}_OUTSIDE_REPO"
    return resolved, None


def _atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(content, encoding="utf-8")
    tmp.replace(path)


def _load_json_handoff(rel: str, prefix: str) -> tuple[Any | None, str | None]:
    p, err = _resolve_handoff(rel, prefix)
    if err or p is None or not p.is_file():
        return None, err or f"{prefix}_MISSING"
    try:
        return json.loads(p.read_text(encoding="utf-8")), None
    except Exception:
        return None, f"{prefix}_JSON_INVALID"


def _load_json_repo(rel: str) -> tuple[Any | None, str | None]:
    p, err = _resolve_repo(rel, "BRANDING_CFG")
    if err or p is None or not p.is_file():
        return None, err or "BRANDING_CFG_MISSING"
    try:
        return json.loads(p.read_text(encoding="utf-8")), None
    except Exception:
        return None, "BRANDING_CFG_JSON_INVALID"


def _branding_tool_whitelist(rel: str) -> bool:
    p = rel.replace("\\", "/")
    return p in (
        "scripts/check-setuphelfer-branding-guard.sh",
        "backend/deploy/runner_setuphelfer_branding_guard.py",
        "backend/tests/test_deploy_runner_setuphelfer_branding_guard_v1.py",
    )


def _allowed_legacy_context(rel: str) -> bool:
    pl = rel.replace("\\", "/")
    base = Path(pl).name

    if _branding_tool_whitelist(pl):
        return True
    if pl.startswith("docs/evidence/"):
        return True
    if pl.startswith("docs/history/"):
        return True
    if pl.startswith("changelog/") or "/changelog/" in pl:
        return True
    if pl.startswith("docs/migration/"):
        return True
    if base.lower() == "compatibility_aliases.json":
        return True
    if pl == "docs/developer/SETUPHELFER_BRANDING_GUARD.md":
        return True
    if pl.startswith("docs/knowledge-base/deploy/"):
        return True
    u = base.upper()
    markers = (
        "BRANDING_GUARD",
        "ZERO_STATE",
        "RUNTIME_IDENTIFIER",
        "LEGACY_IDENTIFIER",
        "COMPATIBILITY_ALIAS",
        "SETUPHELFER_IDENTIFIER",
        "ELIMINATION",
        "MIGRATION",
    )
    if pl.startswith("docs/deploy/") and any(m in u for m in markers):
        return True
    return False


def _is_runtime_path(rel: str) -> bool:
    if _branding_tool_whitelist(rel):
        return False
    p = rel.replace("\\", "/")
    if p.startswith("docs/") or p.startswith("changelog/"):
        return False
    if "/" not in p and p in _ROOT_RUNTIME_FILES:
        return True
    for pref in _RUNTIME_PREFIXES:
        if p.startswith(pref):
            return True
    return False


def _forbidden_hits_in_token(tok: str) -> list[str]:
    t = str(tok)
    tl = t.lower()
    hits: list[str] = []
    if "PI_INSTALLER_" in t:
        hits.append("PI_INSTALLER_")
    if "pi-installer-frontend" in tl:
        hits.append("pi-installer-frontend")
    if "de.pi-installer.app" in tl:
        hits.append("de.pi-installer.app")
    if "/opt/pi-installer" in tl:
        hits.append("/opt/pi-installer")
    if "pi-installer.service" in tl:
        hits.append("pi-installer.service")
    if "pi-installer" in tl:
        hits.append("pi-installer")
    if re.search(r"piinstaller", tl):
        hits.append("piinstaller")
    return list(dict.fromkeys(hits))


def _max_severity(*statuses: str) -> str:
    if any(s == "blocked" for s in statuses):
        return "blocked"
    if any(s == "review_required" for s in statuses):
        return "review_required"
    return "ok"


def _zero_state_gate(zero_body: dict[str, Any] | None, zerr: str | None) -> tuple[str, list[str]]:
    reasons: list[str] = []
    if zerr or not isinstance(zero_body, dict):
        reasons.append(str(zerr or "BRANDING_GUARD_ZERO_STATE_HANDOFF_MISSING"))
        return "review_required", reasons
    st = str(zero_body.get("zero_state_status") or "")
    if st == "blocked":
        reasons.append("BRANDING_GUARD_ZERO_STATE_BLOCKED")
        return "blocked", reasons
    if st == "review_required":
        reasons.append("BRANDING_GUARD_ZERO_STATE_REVIEW_REQUIRED")
        return "review_required", reasons
    if st != "ok":
        reasons.append("BRANDING_GUARD_ZERO_STATE_UNKNOWN")
        return "review_required", reasons
    return "ok", []


def _run_branding_guard_analysis() -> tuple[str, dict[str, Any], list[str], list[str]]:
    warnings: list[str] = []
    errors: list[str] = []

    inv, ierr = _load_json_handoff(_INVENTORY_REL, "INVENTORY")
    zero_raw, zerr = _load_json_handoff(_ZERO_STATE_REL, "ZERO_STATE")
    alias_raw, aerr = _load_json_handoff(_ALIAS_REL, "ALIAS")
    cfg, cerr = _load_json_repo(_CFG_VERSION_REL)

    zero_body: dict[str, Any] | None = zero_raw if isinstance(zero_raw, dict) else None
    zs_status, zs_reasons = _zero_state_gate(zero_body, zerr)

    blocked_hits: list[dict[str, Any]] = []
    review_hits: list[dict[str, Any]] = []
    allowed_samples: list[dict[str, Any]] = []

    if ierr or not isinstance(inv, dict):
        errors.append(str(ierr or "BRANDING_GUARD_INVENTORY_MISSING"))
    if aerr or alias_raw is None:
        warnings.append(str(aerr or "BRANDING_GUARD_ALIAS_HANDOFF_MISSING"))
    elif not isinstance(alias_raw, (dict, list)):
        warnings.append("BRANDING_GUARD_ALIAS_JSON_UNEXPECTED")

    if cerr or not isinstance(cfg, dict):
        warnings.append(str(cerr or "BRANDING_GUARD_CONFIG_VERSION_MISSING"))

    if isinstance(inv, dict):
        findings = inv.get("findings")
        if not isinstance(findings, list):
            errors.append("BRANDING_GUARD_INVENTORY_FINDINGS_INVALID")
        else:
            for row in findings:
                if not isinstance(row, dict):
                    continue
                path = str(row.get("path") or "").replace("\\", "/")
                toks = row.get("tokens")
                tokens = [str(x) for x in toks] if isinstance(toks, list) else []
                cls = str(row.get("classification") or "")
                line = row.get("line")
                for tok in tokens:
                    forb = _forbidden_hits_in_token(tok)
                    if not forb:
                        continue
                    entry = {
                        "path": path,
                        "line": line,
                        "classification": cls,
                        "token": tok,
                        "forbidden_rules": forb,
                    }
                    if _allowed_legacy_context(path):
                        if len(allowed_samples) < 40:
                            allowed_samples.append(entry)
                        continue
                    if _is_runtime_path(path):
                        blocked_hits.append(entry)
                    else:
                        review_hits.append(entry)

    inv_status = "ok"
    if errors:
        inv_status = "blocked"
    elif blocked_hits:
        inv_status = "blocked"
    elif review_hits:
        inv_status = "review_required"

    base_status = _max_severity(inv_status, zs_status)
    if zs_reasons and base_status != "blocked":
        for r in zs_reasons:
            if r not in warnings:
                warnings.append(r)

    body: dict[str, Any] = {
        "branding_guard_schema_version": 1,
        "strict_mode": "setuphelfer_branding_guard",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "branding_guard_status": base_status,
        "current_project_version": str(cfg.get("project_version") or "") if isinstance(cfg, dict) else "",
        "zero_state_handoff": {
            "path": _ZERO_STATE_REL,
            "zero_state_status": str(zero_body.get("zero_state_status") or "") if isinstance(zero_body, dict) else "",
            "gate": zs_status,
        },
        "counts": {
            "blocked_hits": len(blocked_hits),
            "review_hits": len(review_hits),
            "allowed_samples_captured": len(allowed_samples),
        },
        "blocked_hits": blocked_hits[:200],
        "review_hits": review_hits[:200],
        "allowed_hits_sample": allowed_samples,
        "inputs": {
            "legacy_identifier_inventory": _INVENTORY_REL,
            "runtime_identifier_zero_state_verification": _ZERO_STATE_REL,
            "compatibility_aliases": _ALIAS_REL,
            "config_version": _CFG_VERSION_REL,
        },
    }
    if base_status == "blocked" and not errors:
        if blocked_hits:
            errors.extend([f"BRANDING_GUARD_BLOCKED:{h.get('path')}:{h.get('token')}" for h in blocked_hits[:50]])
        elif zs_status == "blocked":
            errors.extend(zs_reasons)
        else:
            errors.append("BRANDING_GUARD_BLOCKED")
    return base_status, body, warnings, errors


def check_setuphelfer_branding_guard() -> dict[str, Any]:
    """Read-only branding analysis; does not write the handoff JSON."""
    status, body, warnings, errors = _run_branding_guard_analysis()
    return _emit(status, body, warnings, errors, wrote_file=False)


def build_setuphelfer_branding_guard_report(*, explicit_overwrite: bool = False) -> dict[str, Any]:
    """Writes ``setuphelfer_branding_guard_check.json`` under the evidence handoff directory."""
    out_path, oerr = _resolve_handoff(_OUT_REL, "BRANDING_GUARD")
    if oerr or out_path is None:
        return _emit("blocked", {}, [oerr or "BRANDING_GUARD_OUTPUT_INVALID"], [], wrote_file=False)
    if out_path.exists() and out_path.is_file() and not explicit_overwrite:
        return _emit("blocked", {}, ["BRANDING_GUARD_EXISTS_NO_OVERWRITE"], [], wrote_file=False)

    status, body, warnings, errors = _run_branding_guard_analysis()
    text = json.dumps(body, indent=2, sort_keys=True)
    if len(text.encode("utf-8")) > _MAX_OUTPUT_BYTES:
        return _emit("blocked", {}, ["BRANDING_GUARD_OUTPUT_TOO_LARGE"], warnings, wrote_file=False)
    try:
        _atomic_write(out_path, text)
    except OSError:
        return _emit("blocked", {}, ["BRANDING_GUARD_WRITE_FAILED"], warnings, wrote_file=False)
    return _emit(status, body, warnings, errors, wrote_file=True)


def _emit(
    status: str,
    body: dict[str, Any],
    errors: list[str],
    warnings: list[str],
    *,
    wrote_file: bool,
) -> dict[str, Any]:
    return {
        "setuphelfer_branding_guard_check_status": status,
        "setuphelfer_branding_guard_check_file_path": _OUT_REL,
        "setuphelfer_branding_guard_check": body,
        "setuphelfer_branding_guard_handoff_written": bool(wrote_file),
        "warnings": list(dict.fromkeys(warnings)),
        "errors": list(dict.fromkeys(errors)) if status == "blocked" else [],
        "blocked_reasons": list(dict.fromkeys(errors)),
    }
