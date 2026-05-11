from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
_HANDOFF_ROOT = (_REPO_ROOT / "docs/evidence/runtime-results/handoff").resolve(strict=False)

_ELIM_POST_REL = "docs/evidence/runtime-results/handoff/runtime_identifier_elimination_postcheck.json"
_ALIAS_VAL_REL = "docs/evidence/runtime-results/handoff/runtime_compatibility_alias_validation.json"
_CONSISTENCY_REL = "docs/evidence/runtime-results/handoff/setuphelfer_identifier_consistency_check.json"
_INVENTORY_REL = "docs/evidence/runtime-results/handoff/legacy_identifier_inventory.json"
_HOTSPOT_REL = "docs/evidence/runtime-results/handoff/legacy_identifier_hotspot_analysis.json"
_CFG_VERSION_REL = "config/version.json"
_OUT_REL = "docs/evidence/runtime-results/handoff/runtime_identifier_zero_state_verification.json"
_MAX_OUTPUT_BYTES = 256 * 1024


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
    p, err = _resolve_repo(rel, "ZERO_STATE_CFG")
    if err or p is None or not p.is_file():
        return None, err or "ZERO_STATE_CFG_MISSING"
    try:
        return json.loads(p.read_text(encoding="utf-8")), None
    except Exception:
        return None, "ZERO_STATE_CFG_JSON_INVALID"


def _allowed_alias_history_context_path(rel: str) -> bool:
    pl = rel.replace("\\", "/").lower()
    return (
        pl.startswith("docs/history/")
        or pl.startswith("docs/evidence/")
        or "compatibility_aliases" in pl
        or "compat_aliases" in pl
        or "changelog" in pl
        or pl.startswith("historical/")
    )


def _token_hits_runtime_contract(tok: str) -> bool:
    t = str(tok)
    if "PI_INSTALLER_" in t or t.startswith("PI_INSTALLER_"):
        return True
    if "/opt/pi-installer" in t:
        return True
    if "pi-installer.service" in t:
        return True
    if "de.pi-installer.app" in t:
        return True
    if "pi-installer-frontend" in t:
        return True
    return False


def _inventory_runtime_violations(inv: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    findings = inv.get("findings")
    if not isinstance(findings, list):
        return out
    for row in findings:
        if not isinstance(row, dict):
            continue
        if str(row.get("classification") or "") != "active_runtime_identifier":
            continue
        path = str(row.get("path") or "").replace("\\", "/")
        if _allowed_alias_history_context_path(path):
            continue
        toks = row.get("tokens")
        tokens = [str(x) for x in toks] if isinstance(toks, list) else []
        bad = [t for t in tokens if _token_hits_runtime_contract(t)]
        if bad:
            out.append({"path": path, "line": row.get("line"), "tokens": bad})
    return out


def _hotspot_crit_high(hot: dict[str, Any]) -> tuple[int, int]:
    crit = high = 0
    clusters = hot.get("clusters")
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


def verify_runtime_identifier_zero_state(*, explicit_overwrite: bool = False) -> dict[str, Any]:
    out_path, oerr = _resolve_handoff(_OUT_REL, "ZERO_STATE")
    if oerr or out_path is None:
        return _emit("blocked", {}, [oerr or "ZERO_STATE_OUTPUT_INVALID"], [])
    if out_path.exists() and out_path.is_file() and not explicit_overwrite:
        return _emit("blocked", {}, ["ZERO_STATE_EXISTS_NO_OVERWRITE"], [])

    elim, eerr = _load_json_handoff(_ELIM_POST_REL, "ELIM_POST")
    alias_body, aerr = _load_json_handoff(_ALIAS_VAL_REL, "ALIAS_VAL")
    cons, cerr = _load_json_handoff(_CONSISTENCY_REL, "CONSISTENCY")
    inv, ierr = _load_json_handoff(_INVENTORY_REL, "INVENTORY")
    hot, herr = _load_json_handoff(_HOTSPOT_REL, "HOTSPOT")
    cfg, gerr = _load_json_repo(_CFG_VERSION_REL)

    violations: list[str] = []
    if eerr or not isinstance(elim, dict):
        violations.append(str(eerr or "ELIMINATION_POSTCHECK_MISSING"))
    if cerr or not isinstance(cons, dict):
        violations.append(str(cerr or "CONSISTENCY_HANDOFF_MISSING"))
    if ierr or not isinstance(inv, dict):
        violations.append(str(ierr or "INVENTORY_MISSING"))
    if herr or not isinstance(hot, dict):
        violations.append(str(herr or "HOTSPOT_MISSING"))
    if gerr or not isinstance(cfg, dict):
        violations.append(str(gerr or "CONFIG_VERSION_MISSING"))

    after = int(elim.get("after_runtime_identifier_count") or 0) if isinstance(elim, dict) else -1
    crit_post = int(elim.get("critical_remaining") or 0) if isinstance(elim, dict) else -1
    high_post = int(elim.get("high_remaining") or 0) if isinstance(elim, dict) else -1
    elim_cons = str(elim.get("consistency_status") or "") if isinstance(elim, dict) else ""
    cons_live = str(cons.get("check_status") or "") if isinstance(cons, dict) else ""

    crit_hot, high_hot = _hotspot_crit_high(hot) if isinstance(hot, dict) else (0, 0)
    remaining_hot = int(hot.get("remaining_identifier_count") or 0) if isinstance(hot, dict) else -1

    inv_viol = _inventory_runtime_violations(inv) if isinstance(inv, dict) else []

    alias_contract_ok = False
    alias_issues_non_empty = False
    if aerr or not isinstance(alias_body, dict):
        violations.append(str(aerr or "ALIAS_VALIDATION_MISSING"))
    else:
        alias_contract_ok = bool(alias_body.get("legacy_identifiers_only_in_compat_contract"))
        iss = alias_body.get("issues")
        alias_issues_non_empty = isinstance(iss, list) and len(iss) > 0
        if not alias_contract_ok:
            violations.append("ZERO_STATE_ALIAS_CONTRACT_BROKEN")

    if after > 0:
        violations.append("ZERO_STATE_AFTER_RUNTIME_NONZERO")
    if crit_post > 0 or high_post > 0:
        violations.append("ZERO_STATE_ELIMINATION_POSTCHECK_SEVERITY")
    if crit_hot > 0 or high_hot > 0:
        violations.append("ZERO_STATE_HOTSPOT_SEVERITY")
    if remaining_hot > 0:
        violations.append("ZERO_STATE_HOTSPOT_REMAINING_NONZERO")
    if elim_cons == "blocked" or cons_live == "blocked":
        violations.append("ZERO_STATE_CONSISTENCY_BLOCKED")
    if inv_viol:
        violations.append("ZERO_STATE_INVENTORY_ACTIVE_RUNTIME_OUTSIDE_ALLOWED")

    input_broken = bool(eerr or cerr or ierr or herr or gerr or aerr)
    runtime_remain = (
        after != 0
        or crit_post > 0
        or high_post > 0
        or crit_hot > 0
        or high_hot > 0
        or remaining_hot > 0
        or bool(inv_viol)
    )
    consistency_blocked = elim_cons == "blocked" or cons_live == "blocked"
    hard_blocked = bool(input_broken or runtime_remain or consistency_blocked or not alias_contract_ok)

    if hard_blocked:
        zero_state_status = "blocked"
    elif alias_issues_non_empty:
        zero_state_status = "review_required"
    else:
        zero_state_status = "ok"

    body = {
        "zero_state_schema_version": 1,
        "strict_mode": "runtime_identifier_zero_state_verification",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "zero_state_status": zero_state_status,
        "current_project_version": str(cfg.get("project_version") or "") if isinstance(cfg, dict) else "",
        "checks": {
            "after_runtime_identifier_count": after,
            "critical_remaining_elimination_post": crit_post,
            "high_remaining_elimination_post": high_post,
            "elimination_postcheck_consistency_status": elim_cons,
            "handoff_consistency_check_status": cons_live,
            "hotspot_remaining_identifier_count": remaining_hot,
            "hotspot_critical_hits": crit_hot,
            "hotspot_high_hits": high_hot,
            "alias_validation_contract_ok": bool(alias_contract_ok),
            "alias_validation_has_warnings": bool(alias_issues_non_empty),
            "inventory_forbidden_hits": len(inv_viol),
        },
        "violations": list(dict.fromkeys(violations)),
        "inventory_violation_samples": inv_viol[:25],
        "inputs": {
            "elimination_postcheck": _ELIM_POST_REL,
            "alias_validation": _ALIAS_VAL_REL,
            "consistency_check": _CONSISTENCY_REL,
            "inventory": _INVENTORY_REL,
            "hotspot_analysis": _HOTSPOT_REL,
            "config_version": _CFG_VERSION_REL,
        },
    }
    text = json.dumps(body, indent=2, sort_keys=True)
    if len(text.encode("utf-8")) > _MAX_OUTPUT_BYTES:
        return _emit("blocked", {}, ["ZERO_STATE_OUTPUT_TOO_LARGE"], [])
    try:
        _atomic_write(out_path, text)
    except OSError:
        return _emit("blocked", {}, ["ZERO_STATE_WRITE_FAILED"], [])
    return _emit(zero_state_status, body, [], [])


def _emit(status: str, body: dict[str, Any], errors: list[str], warnings: list[str]) -> dict[str, Any]:
    return {
        "runtime_identifier_zero_state_verification_status": status,
        "runtime_identifier_zero_state_verification_file_path": _OUT_REL,
        "runtime_identifier_zero_state_verification": body,
        "warnings": list(dict.fromkeys(warnings)),
        "errors": list(dict.fromkeys(errors)) if status == "blocked" else [],
        "blocked_reasons": list(dict.fromkeys(errors)),
    }
