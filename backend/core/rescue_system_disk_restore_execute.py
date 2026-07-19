"""Phase C — restore backup artifact onto Windows system disk (heavily gated)."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tarfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.rescue_payload_version import rescue_payload_version
from core.rescue_physical_e2e_evidence_import import find_setup_logs_mount
from core.rescue_system_disk_restore_gate import (
    consume_system_disk_restore_control,
    evaluate_system_disk_restore_gate,
    load_system_disk_restore_control,
)
from core.rescue_windows_backup_execute import verify_windows_backup

RESCUE_MEDIUM = Path("/run/live/medium")


def _booted_from_rescue() -> bool:
    return RESCUE_MEDIUM.is_dir() or os.environ.get("SETUPHELFER_FORCE_RESCUE_BOOT") == "1"


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def preview_system_disk_restore(body: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = dict(body or {})
    control = load_system_disk_restore_control()
    gate = evaluate_system_disk_restore_gate(
        control=control,
        payload_version=str(payload.get("payload_version") or rescue_payload_version()),
        machine_vendor=str(payload.get("machine_vendor") or ""),
        machine_model=str(payload.get("machine_model") or ""),
        operator_consent=str(payload.get("operator_consent") or ""),
    )
    return {
        "preview_only": True,
        "restore_executed": False,
        "production_ready": False,
        "gate": gate,
        "target_device": payload.get("target_device"),
        "artifact": payload.get("artifact"),
        "next_safe_step": "operator_consent_and_one_shot_control" if not gate.get("ok") else "execute_when_ready",
    }


def execute_system_disk_restore(body: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = dict(body or {})
    if not _booted_from_rescue():
        return {
            "success": False,
            "code": "not_rescue_boot",
            "restore_executed": False,
            "production_ready": False,
        }

    logs = find_setup_logs_mount()
    control = load_system_disk_restore_control(logs)
    gate = evaluate_system_disk_restore_gate(
        control=control,
        payload_version=str(payload.get("payload_version") or rescue_payload_version()),
        machine_vendor=str(payload.get("machine_vendor") or ""),
        machine_model=str(payload.get("machine_model") or ""),
        operator_consent=str(payload.get("operator_consent") or ""),
    )
    if not gate.get("allowed"):
        return {
            "success": False,
            "code": gate.get("code") or "restore_blocked",
            "errors": gate.get("errors"),
            "restore_executed": False,
            "production_ready": False,
            "gate": gate,
        }

    if str(payload.get("operator_consent") or "") != "explicit":
        return {
            "success": False,
            "code": "operator_consent_required",
            "restore_executed": False,
            "production_ready": False,
        }

    artifact = Path(str(payload.get("artifact") or (control or {}).get("backup_artifact") or ""))
    target = str(payload.get("target_partition") or payload.get("target_device") or "")
    if not artifact.is_file():
        return {"success": False, "code": "artifact_missing", "restore_executed": False}
    if not target.startswith("/dev/"):
        return {"success": False, "code": "target_invalid", "restore_executed": False}
    # Hard safety: never allow whole-disk wipe path here — partition only.
    if target.rstrip("0123456789") == target and "nvme" not in target:
        # e.g. /dev/sda without partition number
        if not any(ch.isdigit() for ch in target):
            return {"success": False, "code": "target_must_be_partition", "restore_executed": False}
    if target.endswith("n1") and "p" not in Path(target).name:
        return {"success": False, "code": "target_must_be_partition", "restore_executed": False}

    verify = verify_windows_backup(
        {
            "artifact": str(artifact),
            "sha256": payload.get("sha256"),
            "manifest": payload.get("manifest"),
        }
    )
    if not verify.get("verify_passed"):
        return {
            "success": False,
            "code": "pre_restore_verify_failed",
            "verify": verify,
            "restore_executed": False,
            "production_ready": False,
        }

    job_id = str(payload.get("job_id") or uuid.uuid4().hex[:16])
    mount_point = Path(f"/run/setuphelfer/windows-restore-{job_id}")
    mount_point.mkdir(parents=True, exist_ok=True)
    # RW mount of target NTFS partition for selective restore only.
    mount = subprocess.run(
        ["mount", "-t", "ntfs3", "-o", "rw,norecover", target, str(mount_point)],
        capture_output=True,
        text=True,
        check=False,
    )
    if mount.returncode != 0:
        mount = subprocess.run(
            ["mount", "-t", "ntfs-3g", "-o", "rw", target, str(mount_point)],
            capture_output=True,
            text=True,
            check=False,
        )
    if mount.returncode != 0:
        return {
            "success": False,
            "code": "target_mount_failed",
            "message": (mount.stderr or "")[:500],
            "restore_executed": False,
        }

    restored_files = 0
    try:
        if str(artifact).endswith(".tar.gz") or artifact.name.endswith(".tgz"):
            with tarfile.open(artifact, "r:gz") as tar:
                # Safe extract: no absolute paths / path escape.
                for member in tar.getmembers():
                    name = member.name.lstrip("/")
                    if ".." in Path(name).parts:
                        continue
                    tar.extract(member, path=mount_point)
                    if member.isfile():
                        restored_files += 1
        else:
            # Full image restore is not enabled in this phase without additional imaging tools.
            return {
                "success": False,
                "code": "full_image_restore_not_enabled",
                "message": "Vollimage-Restore auf Systemdisk ist noch nicht freigegeben; selektives Tar-Restore nutzen.",
                "restore_executed": False,
                "production_ready": False,
            }

        if logs:
            consume_system_disk_restore_control(
                logs,
                consumed_by_job_id=job_id,
                terminal_status="restore_completed",
            )

        # Post-verify: archive members that are files must exist under the mount.
        post_verify = {
            "verify_passed": True,
            "restored_files": restored_files,
            "checked_at": _utc_now(),
        }
        if str(artifact).endswith(".tar.gz") or artifact.name.endswith(".tgz"):
            missing = 0
            with tarfile.open(artifact, "r:gz") as tar:
                for member in tar.getmembers():
                    if not member.isfile():
                        continue
                    name = member.name.lstrip("/")
                    if ".." in Path(name).parts:
                        continue
                    if not (mount_point / name).is_file():
                        missing += 1
            post_verify["missing_files"] = missing
            post_verify["verify_passed"] = missing == 0

        evidence = {
            "schema": "setuphelfer.rescue.system-disk-restore-result.v1",
            "job_id": job_id,
            "artifact": str(artifact),
            "target_partition": target,
            "restored_files": restored_files,
            "completed_at": _utc_now(),
            "production_ready": False,
            "verify_before": verify,
            "verify_after": post_verify,
        }
        if logs:
            out = logs / "setuphelfer" / "evidence" / "restore" / job_id
            out.mkdir(parents=True, exist_ok=True)
            (out / "result.json").write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")

        return {
            "success": bool(post_verify.get("verify_passed")),
            "code": "restore_completed" if post_verify.get("verify_passed") else "restore_post_verify_failed",
            "restore_executed": True,
            "job_id": job_id,
            "restored_files": restored_files,
            "target_partition": target,
            "production_ready": False,
            "verify_after": post_verify,
            "evidence": evidence,
        }
    finally:
        subprocess.run(["umount", str(mount_point)], capture_output=True, check=False)
        shutil.rmtree(mount_point, ignore_errors=True)
