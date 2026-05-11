from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from deploy.image_inspect import _under_allowed_cache

SCHEMA_VERSION = 1
_BACKEND_ROOT = Path(__file__).resolve().parent.parent
_DEPLOY_JOB_CACHE_FALLBACK = _BACKEND_ROOT / "cache" / "deploy"

# Jobdateien nur unter diesen Wurzeln (Production + Repo-Testcache). Kein freies --job aus /tmp.
_PRODUCTION_JOB_ROOT = Path("/var/lib/setuphelfer/deploy-jobs")


def job_file_allowed_roots() -> list[Path]:
    """Aufgelöste erlaubte Präfixe für --job (Runner containment)."""
    return [_PRODUCTION_JOB_ROOT, _DEPLOY_JOB_CACHE_FALLBACK]


def validate_runner_job_file_location(path_user: str) -> tuple[Path | None, str | None]:
    """
    Pfad-Containment für die Jobdatei: kein Symlink auf Jobpfad, nur unter erlaubten Wurzeln.
    path_user: Rohargument von --job (nach expanduser).
    """
    raw = str(path_user or "").strip()
    if not raw:
        return None, "job_path_empty"
    p = Path(raw).expanduser()
    try:
        if p.is_symlink():
            return None, "job_path_symlink"
    except OSError:
        return None, "job_path_symlink_check_failed"
    try:
        resolved = p.resolve(strict=False)
    except OSError as e:
        return None, f"job_path_resolve_failed:{e}"
    for root in job_file_allowed_roots():
        try:
            root_r = root.resolve(strict=False)
            resolved.relative_to(root_r)
            return resolved, None
        except ValueError:
            continue
    return None, "job_path_outside_allowed_prefix"


def _path_allowed_for_runner_image(path: Path) -> bool:
    if _under_allowed_cache(path):
        return True
    try:
        path.resolve(strict=False).relative_to(_DEPLOY_JOB_CACHE_FALLBACK.resolve(strict=False))
        return True
    except ValueError:
        return False

_MAX_IMAGE_BYTES = 512 * 1024 * 1024

_GUARD_KEYS = (
    "real_write_guard_id",
    "snapshot_fingerprint",
    "hardware_gate_readiness",
    "final_confirmation_id",
    "harness_proof_hash",
)

_CONSTRAINT_KEYS = (
    "require_removable",
    "allowed_transports",
    "forbid_mounted",
    "forbid_system_disk",
    "forbid_windows_dualboot",
    "max_image_size_bytes",
)


def default_constraints() -> dict[str, Any]:
    return {
        "require_removable": True,
        "allowed_transports": ["usb", "sdcard"],
        "forbid_mounted": True,
        "forbid_system_disk": True,
        "forbid_windows_dualboot": True,
        "max_image_size_bytes": _MAX_IMAGE_BYTES,
    }


def _canonical_json_bytes(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def compute_job_hash(job_without_hash: dict[str, Any]) -> str:
    return hashlib.sha256(_canonical_json_bytes(job_without_hash)).hexdigest()


def _parse_iso_utc(s: str) -> datetime | None:
    raw = str(s or "").strip()
    if not raw:
        return None
    try:
        if raw.endswith("Z"):
            raw = raw[:-1] + "+00:00"
        dt = datetime.fromisoformat(raw)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except ValueError:
        return None


def _sha256_hex_ok(s: str) -> bool:
    t = str(s or "").strip().lower()
    if t.startswith("sha256:"):
        t = t.split(":", 1)[1]
    return bool(re.fullmatch(r"[0-9a-f]{64}", t))


def _target_ok(dev: str) -> bool:
    d = str(dev or "").strip()
    return bool(d.startswith("/dev/") and len(d) >= 6)


def build_real_write_job(
    *,
    job_id: str,
    created_at: datetime,
    expires_at: datetime,
    target_device: str,
    image_path: str,
    image_sha256: str,
    image_size_bytes: int,
    max_bytes: int,
    guard: dict[str, Any],
    constraints: dict[str, Any] | None = None,
) -> dict[str, Any]:
    c = dict(constraints) if isinstance(constraints, dict) else default_constraints()
    body: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "job_id": str(job_id),
        "created_at": created_at.astimezone(timezone.utc).isoformat(),
        "expires_at": expires_at.astimezone(timezone.utc).isoformat(),
        "target_device": str(target_device),
        "image_path": str(image_path),
        "image_sha256": str(image_sha256).strip(),
        "image_size_bytes": int(image_size_bytes),
        "max_bytes": int(max_bytes),
        "guard": dict(guard),
        "constraints": c,
    }
    body["job_hash"] = compute_job_hash(body)
    return body


def validate_real_write_job(job: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {"code": "DEPLOY_RUNNER_JOB_INVALID", "warnings": [], "errors": []}

    if not isinstance(job, dict):
        out["errors"].append("job_not_object")
        return out

    if int(job.get("schema_version") or 0) != SCHEMA_VERSION:
        out["errors"].append("schema_version")
        return out

    job_id = str(job.get("job_id") or "").strip()
    if len(job_id) < 4:
        out["errors"].append("job_id")
        return out

    exp = _parse_iso_utc(str(job.get("expires_at") or ""))
    if exp is None:
        out["errors"].append("expires_at_invalid")
        return out
    if datetime.now(timezone.utc) > exp:
        out["code"] = "DEPLOY_RUNNER_JOB_EXPIRED"
        out["errors"].append("expired")
        return out

    body_for_hash = {k: v for k, v in job.items() if k != "job_hash"}
    expected_hash = compute_job_hash(body_for_hash)
    got = str(job.get("job_hash") or "").strip().lower()
    if got != expected_hash.lower():
        out["code"] = "DEPLOY_RUNNER_JOB_HASH_MISMATCH"
        out["errors"].append("job_hash")
        return out

    target = str(job.get("target_device") or "").strip()
    if not _target_ok(target):
        out["code"] = "DEPLOY_RUNNER_JOB_TARGET_INVALID"
        out["errors"].append("target_device")
        return out

    img_path = str(job.get("image_path") or "").strip()
    if not img_path:
        out["code"] = "DEPLOY_RUNNER_JOB_IMAGE_INVALID"
        out["errors"].append("image_path_empty")
        return out
    p = Path(img_path).resolve(strict=False)
    if not _path_allowed_for_runner_image(p):
        out["code"] = "DEPLOY_RUNNER_JOB_IMAGE_INVALID"
        out["errors"].append("image_path_not_under_cache")
        return out

    if not _sha256_hex_ok(str(job.get("image_sha256") or "")):
        out["code"] = "DEPLOY_RUNNER_JOB_IMAGE_INVALID"
        out["errors"].append("image_sha256_format")
        return out

    try:
        isz = int(job.get("image_size_bytes") or 0)
        mb = int(job.get("max_bytes") or 0)
    except (TypeError, ValueError):
        out["code"] = "DEPLOY_RUNNER_JOB_IMAGE_INVALID"
        out["errors"].append("size_fields")
        return out

    if isz <= 0 or isz > _MAX_IMAGE_BYTES:
        out["code"] = "DEPLOY_RUNNER_JOB_IMAGE_INVALID"
        out["errors"].append("image_size_bytes")
        return out
    if mb <= 0 or mb > isz:
        out["code"] = "DEPLOY_RUNNER_JOB_IMAGE_INVALID"
        out["errors"].append("max_bytes")
        return out

    cons = job.get("constraints")
    if not isinstance(cons, dict):
        out["errors"].append("constraints_missing")
        return out
    for k in _CONSTRAINT_KEYS:
        if k not in cons:
            out["errors"].append(f"constraints.{k}")
            return out
    if cons.get("require_removable") is not True:
        out["errors"].append("constraints.require_removable")
        return out
    if cons.get("forbid_mounted") is not True:
        out["errors"].append("constraints.forbid_mounted")
        return out
    if cons.get("forbid_system_disk") is not True:
        out["errors"].append("constraints.forbid_system_disk")
        return out
    if cons.get("forbid_windows_dualboot") is not True:
        out["errors"].append("constraints.forbid_windows_dualboot")
        return out
    try:
        mic = int(cons.get("max_image_size_bytes") or 0)
    except (TypeError, ValueError):
        out["errors"].append("constraints.max_image_size_bytes")
        return out
    if mic != _MAX_IMAGE_BYTES:
        out["errors"].append("constraints.max_image_size_bytes_value")
        return out
    at = cons.get("allowed_transports")
    if not isinstance(at, list) or not at:
        out["errors"].append("constraints.allowed_transports")
        return out
    allowed = {str(x).lower() for x in at}
    if not allowed <= {"usb", "sdcard"} or not allowed:
        out["errors"].append("constraints.allowed_transports_values")
        return out

    g = job.get("guard")
    if not isinstance(g, dict):
        out["errors"].append("guard_missing")
        return out
    for k in _GUARD_KEYS:
        if k not in g or str(g.get(k) or "").strip() == "":
            out["errors"].append(f"guard.{k}")
            return out
    if str(g.get("hardware_gate_readiness") or "") != "test_ready":
        out["errors"].append("guard.hardware_gate_readiness")
        return out

    out["code"] = "DEPLOY_RUNNER_JOB_VALID"
    return out
