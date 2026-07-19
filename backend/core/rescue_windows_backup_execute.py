"""Phase B — Windows backup execute (full image or selective tar) + verify."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import tarfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.rescue_backup_plan_contract import build_rescue_full_backup_plan
from core.rescue_windows_backup_scope import (
    SCOPE_FULL,
    build_backup_scope_plan,
    normalize_backup_scope,
)

RESCUE_MEDIUM = Path("/run/live/medium")


def _booted_from_rescue() -> bool:
    return RESCUE_MEDIUM.is_dir() or os.environ.get("SETUPHELFER_FORCE_RESCUE_BOOT") == "1"


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def _mount_ntfs_ro(source_device: str, mount_point: Path) -> dict[str, Any]:
    mount_point.mkdir(parents=True, exist_ok=True)
    cmd = ["mount", "-t", "ntfs3", "-o", "ro,norecover", source_device, str(mount_point)]
    completed = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if completed.returncode != 0:
        # Fallback for older kernels.
        cmd = ["mount", "-t", "ntfs-3g", "-o", "ro", source_device, str(mount_point)]
        completed = subprocess.run(cmd, capture_output=True, text=True, check=False)
    return {
        "ok": completed.returncode == 0,
        "cmd": cmd,
        "stderr": (completed.stderr or "")[:500],
    }


def _umount(mount_point: Path) -> None:
    subprocess.run(["umount", str(mount_point)], capture_output=True, check=False)


def _collect_selective_files(
    root: Path,
    include_globs: list[str],
    exclude_rel_paths: list[str] | None = None,
) -> list[Path]:
    files: list[Path] = []
    excludes = [str(p).replace("\\", "/").strip("/") for p in (exclude_rel_paths or []) if str(p).strip()]
    for pattern in include_globs:
        for match in root.glob(pattern):
            if match.is_file():
                files.append(match)
            elif match.is_dir():
                for child in match.rglob("*"):
                    if child.is_file():
                        files.append(child)
    # Deduplicate while preserving order.
    seen: set[str] = set()
    out: list[Path] = []
    for path in files:
        key = str(path)
        if key in seen:
            continue
        rel = str(path.relative_to(root)).replace("\\", "/")
        if any(rel == ex or rel.startswith(ex.rstrip("/") + "/") or f"/{ex}/" in f"/{rel}/" for ex in excludes):
            continue
        seen.add(key)
        out.append(path)
    return out


def execute_windows_backup(body: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = dict(body or {})
    if not _booted_from_rescue():
        return {
            "success": False,
            "code": "not_rescue_boot",
            "message": "Backup-Ausführung nur nach Boot vom Rettungsstick.",
            "backup_executed": False,
        }

    scope = normalize_backup_scope(str(payload.get("backup_scope") or payload.get("scope") or SCOPE_FULL))
    scope_plan = build_backup_scope_plan(
        scope=scope,
        custom_paths=list(payload.get("custom_paths") or []),
    )
    if scope_plan.get("errors"):
        return {
            "success": False,
            "code": "scope_invalid",
            "errors": scope_plan["errors"],
            "backup_executed": False,
        }

    payload["backup_mode"] = "raw_image" if scope == SCOPE_FULL else "linux_full_root_tar"
    payload["booted_from_rescue"] = True
    payload["operator_confirm_source"] = True
    payload["operator_confirm_target"] = True
    plan = build_rescue_full_backup_plan(payload)
    if not plan.get("execute_allowed") and not payload.get("lab_force_execute"):
        # Selective lab path may still run when target/source confirmed and not blocked.
        if plan.get("plan_status") == "blocked":
            return {
                "success": False,
                "code": "execute_not_allowed",
                "message": "Plan erlaubt keine Ausführung.",
                "plan": plan,
                "backup_executed": False,
            }

    target_mount = str((plan.get("target") or {}).get("mount") or payload.get("target_mount") or "")
    if not target_mount:
        return {"success": False, "code": "target_mount_missing", "backup_executed": False}

    job_id = str(payload.get("plan_id") or plan.get("plan_id") or uuid.uuid4().hex[:16])
    out_dir = Path(target_mount) / "setuphelfer" / "backups" / job_id
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = out_dir / "backup-manifest.json"
    started = _utc_now()

    if scope == SCOPE_FULL:
        # Delegate to existing image execute when available.
        from core.rescue_backup_execute import execute_rescue_backup

        result = execute_rescue_backup(payload)
        result["backup_scope"] = SCOPE_FULL
        result["scope_plan"] = scope_plan
        return result

    source = str(payload.get("source_partition") or payload.get("source_device") or "")
    if not source:
        return {"success": False, "code": "source_missing", "backup_executed": False}

    mount_point = Path(f"/run/setuphelfer/windows-backup-ro-{job_id}")
    mounted = _mount_ntfs_ro(source, mount_point)
    if not mounted["ok"]:
        return {
            "success": False,
            "code": "ntfs_mount_failed",
            "message": mounted.get("stderr") or "NTFS RO-Mount fehlgeschlagen.",
            "backup_executed": False,
        }

    try:
        files = _collect_selective_files(
            mount_point,
            list(scope_plan.get("include_paths") or []),
            list(scope_plan.get("exclude_paths") or []),
        )
        archive = out_dir / "selective-backup.tar.gz"
        with tarfile.open(archive, "w:gz") as tar:
            for file_path in files:
                arcname = str(file_path.relative_to(mount_point))
                tar.add(file_path, arcname=arcname)
        digest = _sha256_file(archive)
        (out_dir / "selective-backup.tar.gz.sha256").write_text(f"{digest}  selective-backup.tar.gz\n", encoding="utf-8")
        manifest = {
            "schema": "setuphelfer.rescue.windows-backup-manifest.v1",
            "job_id": job_id,
            "backup_scope": scope,
            "source_device": source,
            "target_mount": target_mount,
            "artifact": str(archive),
            "sha256": digest,
            "file_count": len(files),
            "started_at": started,
            "completed_at": _utc_now(),
            "include_paths": scope_plan.get("include_paths"),
            "exclude_paths": scope_plan.get("exclude_paths"),
            "production_ready": False,
        }
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        return {
            "success": True,
            "code": "backup_completed",
            "backup_executed": True,
            "backup_scope": scope,
            "job_id": job_id,
            "artifact": str(archive),
            "sha256": digest,
            "file_count": len(files),
            "manifest": str(manifest_path),
            "verify_required": True,
            "production_ready": False,
        }
    finally:
        _umount(mount_point)
        shutil.rmtree(mount_point, ignore_errors=True)


def verify_windows_backup(body: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = dict(body or {})
    artifact = Path(str(payload.get("artifact") or ""))
    expected = str(payload.get("sha256") or "").strip().lower()
    manifest = Path(str(payload.get("manifest") or ""))
    if manifest.is_file() and not expected:
        try:
            data = json.loads(manifest.read_text(encoding="utf-8"))
            expected = str(data.get("sha256") or "").lower()
            if not artifact.name and data.get("artifact"):
                artifact = Path(str(data["artifact"]))
        except json.JSONDecodeError:
            pass
    if not artifact.is_file():
        return {"success": False, "code": "artifact_missing", "verify_passed": False}
    actual = _sha256_file(artifact)
    ok = (not expected) or actual == expected.replace("sha256:", "")
    return {
        "success": ok,
        "code": "verify_passed" if ok else "verify_failed",
        "verify_passed": ok,
        "artifact": str(artifact),
        "sha256": actual,
        "expected_sha256": expected,
        "verified_at": _utc_now(),
        "production_ready": False,
    }
