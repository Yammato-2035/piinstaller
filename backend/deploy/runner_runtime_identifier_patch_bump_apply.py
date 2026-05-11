from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
_HANDOFF_ROOT = (_REPO_ROOT / "docs/evidence/runtime-results/handoff").resolve(strict=False)

_PREP_REL = "docs/evidence/runtime-results/handoff/runtime_identifier_patch_bump_preparation.json"
_ZERO_REL = "docs/evidence/runtime-results/handoff/runtime_identifier_zero_state_verification.json"
_RESULT_REL = "docs/evidence/runtime-results/handoff/runtime_identifier_patch_bump_apply_result.json"
_POSTCHECK_REL = "docs/evidence/runtime-results/handoff/runtime_identifier_patch_bump_postcheck.json"

_CFG = "config/version.json"
_PKG = "package.json"
_PKGF = "frontend/package.json"
_TAURI = "frontend/src-tauri/tauri.conf.json"
_VSTATE = "docs/evidence/runtime-results/handoff/version_state.json"
_PTRACK = "docs/evidence/runtime-results/handoff/phase_release_tracking.json"

_MAX_OUTPUT_BYTES = 512 * 1024


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


def _resolve_repo(rel_path: str) -> tuple[Path | None, str | None]:
    raw = str(rel_path or "").strip().replace("\\", "/")
    if not raw or ".." in raw or raw.startswith("/"):
        return None, "PATCH_APPLY_REPO_PATH_INVALID"
    unresolved = _REPO_ROOT / raw
    cur = unresolved
    while True:
        if cur.exists() and cur.is_symlink():
            return None, "PATCH_APPLY_SYMLINK_BLOCKED"
        if cur.parent == cur:
            break
        cur = cur.parent
    try:
        resolved = unresolved.resolve(strict=False)
        resolved.relative_to(_REPO_ROOT.resolve(strict=False))
    except (OSError, ValueError):
        return None, "PATCH_APPLY_OUTSIDE_REPO"
    return resolved, None


def _atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(content, encoding="utf-8")
    tmp.replace(path)


def _parse_semver(v: str) -> tuple[int, int, int] | None:
    parts = str(v).strip().split(".")
    if len(parts) != 3:
        return None
    try:
        return int(parts[0]), int(parts[1]), int(parts[2])
    except ValueError:
        return None


def _semver_gt(a: str, b: str) -> bool:
    pa, pb = _parse_semver(a), _parse_semver(b)
    if pa is None or pb is None:
        return False
    return pa > pb


def apply_runtime_identifier_patch_bump(
    *,
    explicit_overwrite: bool = False,
    explicit_apply_patch_bump: bool = False,
) -> dict[str, Any]:
    out_path, oerr = _resolve_handoff(_RESULT_REL, "PATCH_APPLY")
    if oerr or out_path is None:
        return _emit_apply("blocked", {}, [oerr or "PATCH_APPLY_OUTPUT_INVALID"], [])
    if out_path.exists() and out_path.is_file() and not explicit_overwrite:
        return _emit_apply("blocked", {}, ["PATCH_APPLY_EXISTS_NO_OVERWRITE"], [])

    if not explicit_apply_patch_bump:
        return _emit_apply("blocked", {}, ["PATCH_APPLY_EXPLICIT_FLAG_REQUIRED"], [])

    pp, perr = _resolve_handoff(_PREP_REL, "PREP")
    zp, zerr = _resolve_handoff(_ZERO_REL, "ZERO")
    if perr or pp is None or not pp.is_file():
        return _emit_apply("blocked", {}, [perr or "PREPARATION_MISSING"], [])
    if zerr or zp is None or not zp.is_file():
        return _emit_apply("blocked", {}, [zerr or "ZERO_STATE_MISSING"], [])

    try:
        prep = json.loads(pp.read_text(encoding="utf-8"))
        zero = json.loads(zp.read_text(encoding="utf-8"))
    except Exception:
        return _emit_apply("blocked", {}, ["PATCH_APPLY_INPUT_JSON_INVALID"], [])

    if str(zero.get("zero_state_status") or "") != "ok":
        return _emit_apply("blocked", {}, ["PATCH_APPLY_ZERO_STATE_NOT_OK"], [])

    if str(prep.get("preparation_status") or "") != "ok":
        return _emit_apply("blocked", {}, ["PATCH_APPLY_PREPARATION_NOT_OK"], [])

    cur = str(prep.get("previous_version") or "")
    nxt = str(prep.get("suggested_next_version") or "")
    if not cur or not nxt or not _semver_gt(nxt, cur):
        return _emit_apply("blocked", {}, ["PATCH_APPLY_VERSION_NOT_INCREASING"], [])

    updated: list[str] = []
    errors: list[str] = []

    def _bump_file(rel: str, *, sort_keys: bool = False) -> None:
        rp, rerr = _resolve_repo(rel)
        if rerr or rp is None or not rp.is_file():
            errors.append(f"{rel}:{rerr or 'missing'}")
            return
        try:
            data = json.loads(rp.read_text(encoding="utf-8"))
            if rel == _CFG:
                data["project_version"] = nxt
                data["generated_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            else:
                data["version"] = nxt
            out = json.dumps(data, indent=2, sort_keys=sort_keys) + "\n"
            _atomic_write(rp, out)
            updated.append(rel)
        except Exception as exc:
            errors.append(f"{rel}:{exc}")

    _bump_file(_CFG, sort_keys=True)
    for rel in (_PKG, _PKGF, _TAURI):
        _bump_file(rel, sort_keys=False)

    vs_path, vserr = _resolve_handoff(_VSTATE, "VSTATE")
    if vserr or vs_path is None or not vs_path.is_file():
        errors.append(_VSTATE)
    else:
        try:
            vs = json.loads(vs_path.read_text(encoding="utf-8"))
            old_cur = str(vs.get("current_version") or cur)
            vs["previous_version"] = old_cur
            vs["current_version"] = nxt
            _atomic_write(vs_path, json.dumps(vs, indent=2, sort_keys=True) + "\n")
            updated.append(_VSTATE)
        except Exception as exc:
            errors.append(f"{_VSTATE}:{exc}")

    tr_path, terr = _resolve_handoff(_PTRACK, "PTRACK")
    if terr or tr_path is None or not tr_path.is_file():
        errors.append(_PTRACK)
    else:
        try:
            tr = json.loads(tr_path.read_text(encoding="utf-8"))
            phases = tr.get("tracked_phases")
            if isinstance(phases, list):
                for it in phases:
                    if isinstance(it, dict) and str(it.get("version") or "") == cur:
                        it["version"] = nxt
            _atomic_write(tr_path, json.dumps(tr, indent=2, sort_keys=True) + "\n")
            updated.append(_PTRACK)
        except Exception as exc:
            errors.append(f"{_PTRACK}:{exc}")

    st = "ok" if not errors else "blocked"
    body = {
        "apply_schema_version": 1,
        "strict_mode": "runtime_identifier_patch_bump_apply",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "apply_status": st,
        "from_version": cur,
        "to_version": nxt,
        "updated_files": updated,
        "errors": errors,
    }
    text = json.dumps(body, indent=2, sort_keys=True)
    if len(text.encode("utf-8")) > _MAX_OUTPUT_BYTES:
        return _emit_apply("blocked", {}, ["PATCH_APPLY_RESULT_TOO_LARGE"], [])
    try:
        _atomic_write(out_path, text)
    except OSError:
        return _emit_apply("blocked", {}, ["PATCH_APPLY_RESULT_WRITE_FAILED"], [])
    return _emit_apply(st, body, errors, [])


def _emit_apply(status: str, body: dict[str, Any], errors: list[str], warnings: list[str]) -> dict[str, Any]:
    return {
        "runtime_identifier_patch_bump_apply_status": status,
        "runtime_identifier_patch_bump_apply_file_path": _RESULT_REL,
        "runtime_identifier_patch_bump_apply": body,
        "warnings": list(dict.fromkeys(warnings)),
        "errors": list(dict.fromkeys(errors)) if status == "blocked" else [],
        "blocked_reasons": list(dict.fromkeys(errors)),
    }


def build_runtime_identifier_patch_bump_postcheck(*, explicit_overwrite: bool = False) -> dict[str, Any]:
    from deploy.runner_version_consistency_check import check_version_consistency
    from deploy.runner_version_source_of_truth_check import check_version_source_of_truth_consistency

    out_path, oerr = _resolve_handoff(_POSTCHECK_REL, "PATCH_POST")
    if oerr or out_path is None:
        return _emit_post("blocked", {}, [oerr or "PATCH_POST_OUTPUT_INVALID"], [])
    if out_path.exists() and out_path.is_file() and not explicit_overwrite:
        return _emit_post("blocked", {}, ["PATCH_POST_EXISTS_NO_OVERWRITE"], [])

    sot = check_version_source_of_truth_consistency(explicit_overwrite=True)
    vcc = check_version_consistency(explicit_overwrite=True)

    sot_st = str(sot.get("check_status") or "blocked")
    vc_st = str(vcc.get("check_status") or "blocked")

    post_st = "ok"
    if sot_st == "blocked" or vc_st == "blocked":
        post_st = "blocked"
    elif sot_st == "review_required" or vc_st == "review_required":
        post_st = "review_required"

    body = {
        "postcheck_schema_version": 1,
        "strict_mode": "runtime_identifier_patch_bump_postcheck",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "postcheck_status": post_st,
        "version_source_of_truth_check_status": sot_st,
        "version_consistency_check_status": vc_st,
        "version_source_of_truth_check": sot.get("check") or sot,
        "version_consistency_check": vcc.get("check") or vcc,
    }
    text = json.dumps(body, indent=2, sort_keys=True)
    if len(text.encode("utf-8")) > _MAX_OUTPUT_BYTES:
        return _emit_post("blocked", {}, ["PATCH_POST_TOO_LARGE"], [])
    try:
        _atomic_write(out_path, text)
    except OSError:
        return _emit_post("blocked", {}, ["PATCH_POST_WRITE_FAILED"], [])
    return _emit_post(post_st, body, [], [])


def _emit_post(status: str, body: dict[str, Any], errors: list[str], warnings: list[str]) -> dict[str, Any]:
    return {
        "runtime_identifier_patch_bump_postcheck_status": status,
        "runtime_identifier_patch_bump_postcheck_file_path": _POSTCHECK_REL,
        "runtime_identifier_patch_bump_postcheck": body,
        "warnings": list(dict.fromkeys(warnings)),
        "errors": list(dict.fromkeys(errors)) if status == "blocked" else [],
        "blocked_reasons": list(dict.fromkeys(errors)),
    }
