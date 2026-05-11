from __future__ import annotations

import hashlib
import os
import secrets
import stat
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from deploy.cache_execute import _ALLOWED_CACHE_PREFIXES
from deploy.final_confirmation import _DEPLOY_FINAL_CONFIRMATION_STORE

_DEPLOY_WRITE_HARNESS_SESSION_STORE: dict[str, dict[str, Any]] = {}
_DEPLOY_WRITE_HARNESS_TTL_SECONDS = 600
_MAX_BYTES_LIMIT = 10 * 1024 * 1024
_ALLOWED_TEST_PREFIXES = [
    "/tmp/setuphelfer-deploy-test",
    "/mnt/setuphelfer/test-targets",
]
_TEST_MODE_CACHE_PREFIX = "/tmp/setuphelfer-deploy-test/cache"


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _under_any_prefix(path: Path, prefixes: list[str]) -> bool:
    for pref in prefixes:
        pref_path = Path(pref).resolve(strict=False)
        try:
            path.relative_to(pref_path)
            return True
        except ValueError:
            continue
    return False


def _allowed_cache_prefixes() -> list[str]:
    prefixes = list(_ALLOWED_CACHE_PREFIXES)
    if os.environ.get("SETUPHELFER_DEPLOY_TEST_MODE") == "1":
        prefixes.append(_TEST_MODE_CACHE_PREFIX)
    return prefixes


def _is_allowed_test_target(path: str) -> bool:
    if not path or str(path).startswith("/dev/"):
        return False
    return _under_any_prefix(Path(path).resolve(strict=False), _ALLOWED_TEST_PREFIXES)


def _is_allowed_cached_image(path: str) -> bool:
    if not path or str(path).startswith("/dev/"):
        return False
    return _under_any_prefix(Path(path).resolve(strict=False), _allowed_cache_prefixes())


def _is_regular_safe_file_or_new(path: str) -> bool:
    p = Path(path)
    if p.is_symlink():
        return False
    rp = p.resolve(strict=False)
    if not _is_allowed_test_target(str(rp)):
        return False
    parent = rp.parent
    if not parent.exists() or not parent.is_dir() or parent.is_symlink():
        return False
    if not _under_any_prefix(parent.resolve(strict=False), _ALLOWED_TEST_PREFIXES):
        return False
    if rp.exists():
        if rp.is_symlink() or (not rp.is_file()):
            return False
        st = rp.stat()
        if stat.S_ISBLK(st.st_mode) or stat.S_ISCHR(st.st_mode) or stat.S_ISFIFO(st.st_mode) or stat.S_ISSOCK(st.st_mode):
            return False
    return True


def _image_ok(image_inspect: dict[str, Any]) -> bool:
    code = str(image_inspect.get("code") or "")
    if code not in {"DEPLOY_IMAGE_INSPECT_OK", "DEPLOY_IMAGE_INSPECT_WARNING"}:
        return False
    errs = image_inspect.get("errors")
    return not (isinstance(errs, list) and errs)


def _copy_limited_bytes(source: Path, target: Path, max_bytes: int) -> tuple[int, str]:
    copied = 0
    h = hashlib.sha256()
    with source.open("rb") as src, target.open("wb") as dst:
        while copied < max_bytes:
            chunk = src.read(min(1024 * 1024, max_bytes - copied))
            if not chunk:
                break
            dst.write(chunk)
            h.update(chunk)
            copied += len(chunk)
    return copied, h.hexdigest()


def create_deploy_write_harness_session(request: dict[str, Any]) -> dict[str, Any]:
    final_confirmation_result = request.get("final_confirmation_result") if isinstance(request.get("final_confirmation_result"), dict) else {}
    image_inspect = request.get("image_inspect") if isinstance(request.get("image_inspect"), dict) else {}
    test_target_path = str(request.get("test_target_path") or "")
    out = {
        "code": "DEPLOY_WRITE_HARNESS_BLOCKED",
        "harness_session_id": None,
        "confirmation_token": None,
        "expires_at": None,
        "warnings": [],
        "errors": [],
    }

    if str(final_confirmation_result.get("code") or "") != "DEPLOY_FINAL_CONFIRMATION_READY":
        out["code"] = "DEPLOY_WRITE_HARNESS_INVALID_FINAL_CONFIRMATION"
        out["errors"].append("DEPLOY_WRITE_HARNESS_INVALID_FINAL_CONFIRMATION")
        return out
    snapshot = final_confirmation_result.get("target_snapshot") if isinstance(final_confirmation_result.get("target_snapshot"), dict) else {}
    fingerprint = str(snapshot.get("fingerprint") or "")
    final_confirmation_id = str(final_confirmation_result.get("final_confirmation_id") or "")
    if not snapshot or not fingerprint or not final_confirmation_id:
        out["code"] = "DEPLOY_WRITE_HARNESS_INVALID_FINAL_CONFIRMATION"
        out["errors"].append("DEPLOY_WRITE_HARNESS_INVALID_FINAL_CONFIRMATION")
        return out
    sess_fc = _DEPLOY_FINAL_CONFIRMATION_STORE.get(final_confirmation_id)
    if not sess_fc or str(sess_fc.get("target_snapshot_fingerprint") or "") != fingerprint:
        out["code"] = "DEPLOY_WRITE_HARNESS_INVALID_FINAL_CONFIRMATION"
        out["errors"].append("DEPLOY_WRITE_HARNESS_INVALID_FINAL_CONFIRMATION")
        return out
    image_path = str(sess_fc.get("image_path") or "")

    if not _image_ok(image_inspect):
        out["code"] = "DEPLOY_WRITE_HARNESS_INVALID_IMAGE"
        out["errors"].append("DEPLOY_WRITE_HARNESS_INVALID_IMAGE")
        return out
    if not image_path or not _is_allowed_cached_image(image_path):
        out["code"] = "DEPLOY_WRITE_HARNESS_INVALID_IMAGE"
        out["errors"].append("DEPLOY_WRITE_HARNESS_INVALID_IMAGE")
        return out
    ip = Path(image_path)
    if not ip.exists() or not ip.is_file() or ip.is_symlink():
        out["code"] = "DEPLOY_WRITE_HARNESS_INVALID_IMAGE"
        out["errors"].append("DEPLOY_WRITE_HARNESS_INVALID_IMAGE")
        return out

    if not _is_regular_safe_file_or_new(test_target_path):
        out["code"] = "DEPLOY_WRITE_HARNESS_INVALID_TEST_TARGET"
        out["errors"].append("DEPLOY_WRITE_HARNESS_INVALID_TEST_TARGET")
        return out

    sid = secrets.token_hex(8)
    tok = secrets.token_urlsafe(24)
    created = _now()
    expires = created + timedelta(seconds=_DEPLOY_WRITE_HARNESS_TTL_SECONDS)
    _DEPLOY_WRITE_HARNESS_SESSION_STORE[sid] = {
        "harness_session_id": sid,
        "confirmation_token": tok,
        "final_confirmation_id": final_confirmation_id,
        "target_snapshot_fingerprint": fingerprint,
        "image_path": str(ip.resolve(strict=False)),
        "test_target_path": str(Path(test_target_path).resolve(strict=False)),
        "created_at": created.isoformat(),
        "expires_at": expires.isoformat(),
        "used": False,
    }
    out["code"] = "DEPLOY_WRITE_HARNESS_SESSION_CREATED"
    out["harness_session_id"] = sid
    out["confirmation_token"] = tok
    out["expires_at"] = expires.isoformat()
    return out


def execute_deploy_write_harness(request: dict[str, Any]) -> dict[str, Any]:
    sid = str(request.get("harness_session_id") or "")
    tok = str(request.get("confirmation_token") or "")
    image_path = str(request.get("image_path") or "")
    test_target_path = str(request.get("test_target_path") or "")
    try:
        max_bytes = int(request.get("max_bytes"))
    except Exception:
        max_bytes = -1
    out = {
        "code": "DEPLOY_WRITE_HARNESS_FAILED",
        "harness_session_id": sid or None,
        "write_result": {"bytes_written": 0, "sha256": "", "test_target_path": test_target_path or None},
        "warnings": [],
        "errors": [],
    }
    sess = _DEPLOY_WRITE_HARNESS_SESSION_STORE.get(sid)
    if not sess:
        out["code"] = "DEPLOY_WRITE_HARNESS_SESSION_NOT_FOUND"
        out["errors"].append("DEPLOY_WRITE_HARNESS_SESSION_NOT_FOUND")
        return out
    if bool(sess.get("used")):
        out["code"] = "DEPLOY_WRITE_HARNESS_SESSION_ALREADY_USED"
        out["errors"].append("DEPLOY_WRITE_HARNESS_SESSION_ALREADY_USED")
        return out
    if tok != str(sess.get("confirmation_token") or ""):
        out["code"] = "DEPLOY_WRITE_HARNESS_TOKEN_INVALID"
        out["errors"].append("DEPLOY_WRITE_HARNESS_TOKEN_INVALID")
        return out
    try:
        expires = datetime.fromisoformat(str(sess.get("expires_at") or ""))
    except Exception:
        expires = _now() - timedelta(seconds=1)
    if _now() >= expires:
        out["code"] = "DEPLOY_WRITE_HARNESS_SESSION_EXPIRED"
        out["errors"].append("DEPLOY_WRITE_HARNESS_SESSION_EXPIRED")
        return out
    if image_path != str(sess.get("image_path") or ""):
        out["code"] = "DEPLOY_WRITE_HARNESS_IMAGE_MISMATCH"
        out["errors"].append("DEPLOY_WRITE_HARNESS_IMAGE_MISMATCH")
        return out
    if test_target_path != str(sess.get("test_target_path") or ""):
        out["code"] = "DEPLOY_WRITE_HARNESS_TARGET_MISMATCH"
        out["errors"].append("DEPLOY_WRITE_HARNESS_TARGET_MISMATCH")
        return out
    if max_bytes <= 0 or max_bytes > _MAX_BYTES_LIMIT:
        out["code"] = "DEPLOY_WRITE_HARNESS_MAX_BYTES_INVALID"
        out["errors"].append("DEPLOY_WRITE_HARNESS_MAX_BYTES_INVALID")
        return out
    if not _is_allowed_cached_image(image_path):
        out["code"] = "DEPLOY_WRITE_HARNESS_IMAGE_MISMATCH"
        out["errors"].append("DEPLOY_WRITE_HARNESS_IMAGE_MISMATCH")
        return out
    if not _is_regular_safe_file_or_new(test_target_path):
        out["code"] = "DEPLOY_WRITE_HARNESS_TARGET_MISMATCH"
        out["errors"].append("DEPLOY_WRITE_HARNESS_TARGET_MISMATCH")
        return out

    sess["used"] = True
    try:
        bytes_written, sha = _copy_limited_bytes(Path(image_path), Path(test_target_path), max_bytes)
    except Exception:
        out["code"] = "DEPLOY_WRITE_HARNESS_FAILED"
        out["errors"].append("DEPLOY_WRITE_HARNESS_FAILED")
        return out
    out["code"] = "DEPLOY_WRITE_HARNESS_COMPLETED"
    out["write_result"] = {"bytes_written": bytes_written, "sha256": sha, "test_target_path": test_target_path}
    return out
