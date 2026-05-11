from __future__ import annotations

import hashlib
import json
import re
import secrets
import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

_DEPLOY_CACHE_SESSION_STORE: dict[str, dict[str, Any]] = {}
_DEPLOY_CACHE_TTL_SECONDS = 900
# Repo layout: backend/cache/deploy (unabhängig vom CWD; ./cache/deploy nur wenn CWD=Backend-Root).
_BACKEND_CACHE_DEPLOY = str(Path(__file__).resolve().parent.parent / "cache" / "deploy")
_ALLOWED_CACHE_PREFIXES = [
    "/mnt/setuphelfer/cache/deploy",
    "/var/cache/setuphelfer/deploy",
    "./cache/deploy",
    _BACKEND_CACHE_DEPLOY,
]
_VALID_EXTS = {".img", ".iso", ".qcow2"}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _hash_payload(payload: dict[str, Any]) -> str:
    raw = json.dumps(payload or {}, sort_keys=True, ensure_ascii=True)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _is_allowed_cache_path(path: str) -> bool:
    if not path:
        return False
    target = Path(path).resolve(strict=False)
    for pref in _ALLOWED_CACHE_PREFIXES:
        pref_path = Path(pref).resolve(strict=False)
        try:
            target.relative_to(pref_path)
            return True
        except ValueError:
            continue
    return False


def _sanitize_name(name: str) -> str:
    base = Path(name).name
    cleaned = re.sub(r"[^A-Za-z0-9._-]", "_", base)
    return cleaned or "image.img"


def _validate_local_source(source: dict[str, Any]) -> tuple[bool, str]:
    if str(source.get("type") or "") != "local_image":
        return False, "DEPLOY_CACHE_SOURCE_NOT_LOCAL"
    lp = str(source.get("local_path") or "")
    if not lp:
        return False, "DEPLOY_CACHE_LOCAL_IMAGE_MISSING"
    p = Path(lp)
    if not p.exists():
        return False, "DEPLOY_CACHE_LOCAL_IMAGE_MISSING"
    if not p.is_file():
        return False, "DEPLOY_CACHE_LOCAL_IMAGE_INVALID"
    if p.suffix.lower() not in _VALID_EXTS:
        return False, "DEPLOY_CACHE_LOCAL_IMAGE_INVALID"
    return True, ""


def _selected_cache_path_from_plan(cache_plan: dict[str, Any]) -> str:
    cache = cache_plan.get("cache") if isinstance(cache_plan.get("cache"), dict) else {}
    selected = str(cache.get("selected_cache_target") or "")
    if selected:
        return selected
    targets = cache.get("cache_targets") if isinstance(cache.get("cache_targets"), list) else []
    return str(targets[0] or "") if targets else ""


def create_deploy_cache_session(request: dict[str, Any]) -> dict[str, Any]:
    source = request.get("source") if isinstance(request.get("source"), dict) else {}
    cache_plan = request.get("cache_plan") if isinstance(request.get("cache_plan"), dict) else {}

    out = {
        "code": "DEPLOY_CACHE_PLAN_INVALID",
        "cache_session_id": None,
        "confirmation_token": None,
        "expires_at": None,
        "warnings": [],
        "errors": [],
    }

    st = str(cache_plan.get("plan_status") or "")
    if st in {"blocked", "not_applicable", ""}:
        out["errors"].append("DEPLOY_CACHE_PLAN_INVALID")
        return out

    ok_source, source_err = _validate_local_source(source)
    if not ok_source:
        out["code"] = source_err
        out["errors"].append(source_err)
        return out

    selected_cache_path = _selected_cache_path_from_plan(cache_plan)
    if not _is_allowed_cache_path(selected_cache_path):
        out["code"] = "DEPLOY_CACHE_TARGET_INVALID"
        out["errors"].append("DEPLOY_CACHE_TARGET_INVALID")
        return out

    sid = secrets.token_hex(8)
    token = secrets.token_urlsafe(24)
    created = _now()
    expires = created + timedelta(seconds=_DEPLOY_CACHE_TTL_SECONDS)

    _DEPLOY_CACHE_SESSION_STORE[sid] = {
        "cache_session_id": sid,
        "confirmation_token": token,
        "source_snapshot_hash": _hash_payload(source),
        "selected_cache_path": selected_cache_path,
        "created_at": created.isoformat(),
        "expires_at": expires.isoformat(),
        "used": False,
    }

    out["code"] = "DEPLOY_CACHE_SESSION_CREATED"
    out["cache_session_id"] = sid
    out["confirmation_token"] = token
    out["expires_at"] = expires.isoformat()
    return out


def _verify_checksum(source: dict[str, Any]) -> tuple[bool, str, dict[str, Any]]:
    expected = str(source.get("checksum") or "")
    if not expected:
        return True, "", {"checksum_checked": False}
    file_path = Path(str(source.get("local_path") or ""))
    h = hashlib.sha256()
    with file_path.open("rb") as f:
        while True:
            chunk = f.read(1024 * 1024)
            if not chunk:
                break
            h.update(chunk)
    actual = h.hexdigest()
    exp = expected.lower().strip()
    if exp.startswith("sha256:"):
        exp = exp.split(":", 1)[1]
    if actual.lower() == exp:
        return True, "DEPLOY_CACHE_CHECKSUM_OK", {"checksum_checked": True, "checksum": actual}
    return False, "DEPLOY_CACHE_CHECKSUM_FAILED", {"checksum_checked": True, "checksum": actual}


def execute_deploy_cache(request: dict[str, Any]) -> dict[str, Any]:
    sid = str(request.get("cache_session_id") or "")
    token = str(request.get("confirmation_token") or "")
    source = request.get("source") if isinstance(request.get("source"), dict) else {}
    cache_plan = request.get("cache_plan") if isinstance(request.get("cache_plan"), dict) else {}

    out = {
        "code": "DEPLOY_CACHE_EXECUTE_FAILED",
        "cache_session_id": sid or None,
        "source": {"source_id": source.get("source_id"), "local_path": source.get("local_path")},
        "cache_result": {},
        "verification": {},
        "warnings": [],
        "errors": [],
    }

    sess = _DEPLOY_CACHE_SESSION_STORE.get(sid)
    if not sess:
        out["code"] = "DEPLOY_CACHE_SESSION_NOT_FOUND"
        out["errors"].append("DEPLOY_CACHE_SESSION_NOT_FOUND")
        return out
    if bool(sess.get("used")):
        out["code"] = "DEPLOY_CACHE_SESSION_ALREADY_USED"
        out["errors"].append("DEPLOY_CACHE_SESSION_ALREADY_USED")
        return out
    if token != str(sess.get("confirmation_token") or ""):
        out["code"] = "DEPLOY_CACHE_TOKEN_INVALID"
        out["errors"].append("DEPLOY_CACHE_TOKEN_INVALID")
        return out

    try:
        expires = datetime.fromisoformat(str(sess.get("expires_at") or ""))
    except Exception:
        expires = _now() - timedelta(seconds=1)
    if _now() >= expires:
        out["code"] = "DEPLOY_CACHE_SESSION_EXPIRED"
        out["errors"].append("DEPLOY_CACHE_SESSION_EXPIRED")
        return out

    source_hash = _hash_payload(source)
    if source_hash != str(sess.get("source_snapshot_hash") or ""):
        out["code"] = "DEPLOY_CACHE_SOURCE_MISMATCH"
        out["errors"].append("DEPLOY_CACHE_SOURCE_MISMATCH")
        return out

    # Consume single-use at start of execution path.
    sess["used"] = True

    ok_source, source_err = _validate_local_source(source)
    if not ok_source:
        out["code"] = source_err
        out["errors"].append(source_err)
        return out

    selected_cache_path = str(sess.get("selected_cache_path") or "")
    if not _is_allowed_cache_path(selected_cache_path):
        out["code"] = "DEPLOY_CACHE_TARGET_INVALID"
        out["errors"].append("DEPLOY_CACHE_TARGET_INVALID")
        return out

    # Ensure requested cache plan still matches session path when provided.
    planned_selected = _selected_cache_path_from_plan(cache_plan)
    if planned_selected and planned_selected != selected_cache_path:
        out["code"] = "DEPLOY_CACHE_TARGET_INVALID"
        out["errors"].append("DEPLOY_CACHE_TARGET_INVALID")
        return out

    checksum_ok, checksum_code, checksum_details = _verify_checksum(source)
    out["verification"] = checksum_details
    if checksum_code:
        out["verification"]["code"] = checksum_code
    if not checksum_ok:
        out["code"] = "DEPLOY_CACHE_EXECUTE_FAILED"
        out["errors"].append("DEPLOY_CACHE_CHECKSUM_FAILED")
        return out

    src_path = Path(str(source.get("local_path") or "")).resolve(strict=True)
    cache_root = Path(selected_cache_path).resolve(strict=False)
    cache_root.mkdir(parents=True, exist_ok=True)
    resolved_root = cache_root.resolve(strict=True)
    if not _is_allowed_cache_path(str(resolved_root)):
        out["code"] = "DEPLOY_CACHE_TARGET_INVALID"
        out["errors"].append("DEPLOY_CACHE_TARGET_INVALID")
        return out

    dest_name = _sanitize_name(src_path.name)
    dest = (resolved_root / dest_name).resolve(strict=False)
    try:
        dest.relative_to(resolved_root)
    except ValueError:
        out["code"] = "DEPLOY_CACHE_TARGET_INVALID"
        out["errors"].append("DEPLOY_CACHE_TARGET_INVALID")
        return out

    if dest.exists() and dest.is_dir():
        out["code"] = "DEPLOY_CACHE_TARGET_INVALID"
        out["errors"].append("DEPLOY_CACHE_TARGET_INVALID")
        return out

    if src_path == dest:
        out["cache_result"] = {"code": "DEPLOY_CACHE_READY", "cache_path": str(dest)}
        out["code"] = "DEPLOY_CACHE_EXECUTE_COMPLETED"
        return out

    shutil.copy2(str(src_path), str(dest))
    out["cache_result"] = {"code": "DEPLOY_CACHE_COPY_COMPLETED", "cache_path": str(dest)}
    out["code"] = "DEPLOY_CACHE_EXECUTE_COMPLETED"
    return out
