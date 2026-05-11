from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from deploy.cache_execute import _ALLOWED_CACHE_PREFIXES

_VALID_EXT_MAP = {".img": "img", ".iso": "iso", ".qcow2": "qcow2"}


def _under_allowed_cache(path: Path) -> bool:
    for pref in _ALLOWED_CACHE_PREFIXES:
        pref_path = Path(pref).resolve(strict=False)
        try:
            path.relative_to(pref_path)
            return True
        except ValueError:
            continue
    return False


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            chunk = f.read(1024 * 1024)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def inspect_deploy_image(request: dict[str, Any]) -> dict[str, Any]:
    image_path = str(request.get("image_path") or "")
    expected_checksum = str(request.get("expected_checksum") or "")
    expected_arch = str(request.get("expected_architecture") or "unknown")
    expected_type = str(request.get("expected_type") or "unknown")

    out: dict[str, Any] = {
        "code": "DEPLOY_IMAGE_INSPECT_FAILED",
        "image": {
            "path": image_path or None,
            "exists": False,
            "is_regular_file": False,
            "extension": "",
            "size_bytes": 0,
        },
        "verification": {
            "checksum_checked": False,
            "checksum_expected": bool(expected_checksum),
            "checksum_ok": None,
        },
        "compatibility": {
            "expected_architecture": expected_arch,
            "expected_type": expected_type,
            "architecture_verified": False,
            "type_matches": None,
        },
        "warnings": [],
        "errors": [],
    }

    if not image_path:
        out["code"] = "DEPLOY_IMAGE_PATH_INVALID"
        out["errors"].append("DEPLOY_IMAGE_PATH_INVALID")
        return out

    p = Path(image_path).resolve(strict=False)
    if not _under_allowed_cache(p):
        out["code"] = "DEPLOY_IMAGE_CACHE_PATH_BLOCKED"
        out["errors"].append("DEPLOY_IMAGE_CACHE_PATH_BLOCKED")
        return out

    if not p.exists():
        out["errors"].append("DEPLOY_IMAGE_NOT_FOUND")
        return out
    out["image"]["exists"] = True

    if not p.is_file():
        out["errors"].append("DEPLOY_IMAGE_NOT_REGULAR_FILE")
        return out
    out["image"]["is_regular_file"] = True

    ext = p.suffix.lower()
    out["image"]["extension"] = ext
    if ext not in _VALID_EXT_MAP:
        out["errors"].append("DEPLOY_IMAGE_EXTENSION_INVALID")
        return out

    size = int(p.stat().st_size)
    out["image"]["size_bytes"] = size
    if size <= 0:
        out["errors"].append("DEPLOY_IMAGE_EMPTY")
        return out

    actual_type = _VALID_EXT_MAP[ext]
    type_matches = expected_type in {"", "unknown", actual_type}
    out["compatibility"]["type_matches"] = bool(type_matches)
    if not type_matches:
        out["warnings"].append("DEPLOY_IMAGE_TYPE_MISMATCH")

    # Architecture cannot be proven without image parsing/mounting in this phase.
    out["warnings"].append("DEPLOY_IMAGE_ARCHITECTURE_UNVERIFIED")

    if expected_checksum:
        actual = _sha256(p)
        out["verification"]["checksum_checked"] = True
        out["verification"]["checksum_actual"] = actual
        chk = expected_checksum.lower().strip()
        if chk.startswith("sha256:"):
            chk = chk.split(":", 1)[1]
        if actual.lower() == chk:
            out["verification"]["checksum_ok"] = True
            out["verification"]["code"] = "DEPLOY_IMAGE_CHECKSUM_OK"
        else:
            out["verification"]["checksum_ok"] = False
            out["verification"]["code"] = "DEPLOY_IMAGE_CHECKSUM_FAILED"
            out["errors"].append("DEPLOY_IMAGE_CHECKSUM_FAILED")
            return out

    out["code"] = "DEPLOY_IMAGE_INSPECT_WARNING" if out["warnings"] else "DEPLOY_IMAGE_INSPECT_OK"
    return out
