"""Registered external test-medium marker for physical E2E (001D4)."""

from __future__ import annotations

import json
import secrets
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.rescue_backup_target_policy import RESCUE_STICK_LABELS

E2E_TARGET_SCHEMA = "setuphelfer.rescue.e2e-target.v1"
E2E_TARGET_FILENAME = "setuphelfer-e2e-target.json"
ALLOWED_ROOT = "setuphelfer-e2e"
DEFAULT_MAX_TEST_BYTES = 268_435_456  # 256 MiB


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _is_rescue_stick_label(label: str | None) -> bool:
    if not label:
        return False
    upper = label.upper()
    return upper in {x.upper() for x in RESCUE_STICK_LABELS} or "SETUPHELFER" in upper


def build_e2e_target_marker(
    *,
    filesystem_uuid: str,
    allowed_root: str = ALLOWED_ROOT,
    max_test_bytes: int = DEFAULT_MAX_TEST_BYTES,
) -> dict[str, Any]:
    return {
        "schema": E2E_TARGET_SCHEMA,
        "purpose": "setuphelfer_physical_e2e_test_only",
        "filesystem_uuid": filesystem_uuid,
        "allowed_root": allowed_root,
        "max_test_bytes": max_test_bytes,
        "allow_backup": True,
        "allow_restore": True,
        "allow_format": False,
        "allow_partition_write": False,
        "created_at": _utc_now(),
        "one_time_nonce": secrets.token_hex(16),
    }


def read_e2e_target_marker(mount_point: Path) -> dict[str, Any] | None:
    path = mount_point / E2E_TARGET_FILENAME
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    return data if isinstance(data, dict) else None


def write_e2e_target_marker(mount_point: Path, marker: dict[str, Any]) -> Path:
    mount_point.mkdir(parents=True, exist_ok=True)
    allowed = Path(marker.get("allowed_root") or ALLOWED_ROOT)
    if allowed.is_absolute() or ".." in allowed.parts:
        raise ValueError("invalid_allowed_root")
    (mount_point / allowed).mkdir(parents=True, exist_ok=True)
    out = mount_point / E2E_TARGET_FILENAME
    out.write_text(json.dumps(marker, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return out


def _partition_uuid(partition: Path) -> str:
    import subprocess

    proc = subprocess.run(
        ["blkid", "-o", "value", "-s", "UUID", str(partition)],
        capture_output=True,
        text=True,
        check=False,
    )
    return (proc.stdout or "").strip()


def validate_e2e_target_marker(
    marker: dict[str, Any] | None,
    *,
    mount_point: Path,
    partition_uuid: str = "",
    label: str | None = None,
    transport: str | None = None,
    removable: bool | None = None,
) -> dict[str, Any]:
    errors: list[str] = []
    if not marker:
        return {"ok": False, "code": "blocked_unregistered_test_target", "errors": ["marker_missing"]}

    if marker.get("schema") != E2E_TARGET_SCHEMA:
        errors.append("invalid_schema")
    if marker.get("purpose") != "setuphelfer_physical_e2e_test_only":
        errors.append("invalid_purpose")
    if marker.get("allow_format"):
        errors.append("format_not_allowed")
    if marker.get("allow_partition_write"):
        errors.append("partition_write_not_allowed")

    allowed_root = str(marker.get("allowed_root") or "")
    if not allowed_root or allowed_root != ALLOWED_ROOT or Path(allowed_root).is_absolute() or ".." in Path(allowed_root).parts:
        errors.append("invalid_allowed_root")

    fs_uuid = partition_uuid or ""
    if not fs_uuid and not str(mount_point).startswith("/dev"):
        import subprocess

        proc = subprocess.run(
            ["findmnt", "-no", "SOURCE", str(mount_point)],
            capture_output=True,
            text=True,
            check=False,
        )
        source = (proc.stdout or "").strip()
        if source:
            proc2 = subprocess.run(
                ["blkid", "-o", "value", "-s", "UUID", source],
                capture_output=True,
                text=True,
                check=False,
            )
            fs_uuid = (proc2.stdout or "").strip()

    marker_uuid = str(marker.get("filesystem_uuid") or "")
    if fs_uuid and marker_uuid and marker_uuid != fs_uuid:
        errors.append("filesystem_uuid_mismatch")

    if _is_rescue_stick_label(label):
        errors.append("blocked_rescue_stick_label")
    if label and label.upper() in {"SETUP_LOGS", "SETUPHELFER_LOGS"}:
        errors.append("blocked_setup_logs_label")

    if transport and transport not in {"usb", "sata", "nvme"} and transport != "usb":
        if transport in {"nvme", "sata"} and removable is not True:
            errors.append("blocked_internal_test_target")

    if transport in {"nvme", "sata"} and removable is False:
        errors.append("blocked_internal_test_target")

    code = "blocked_unregistered_test_target"
    if "filesystem_uuid_mismatch" in errors:
        code = "blocked_uuid_mismatch"
    elif "blocked_internal_test_target" in errors or "blocked_rescue_stick_label" in errors:
        code = "blocked_internal_test_target"

    return {"ok": not errors, "code": code if errors else "ok", "errors": errors, "marker": marker}


def discover_registered_test_targets(
    candidates: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, Any] | None]:
    """Return (valid_targets, ambiguity_blocker)."""
    valid: list[dict[str, Any]] = []
    for cand in candidates:
        mount = Path(cand["mount"])
        marker = read_e2e_target_marker(mount)
        gate = validate_e2e_target_marker(
            marker,
            mount_point=mount,
            partition_uuid=str(cand.get("uuid") or ""),
            label=cand.get("label"),
            transport=cand.get("transport"),
            removable=cand.get("removable"),
        )
        if gate.get("ok"):
            valid.append({**cand, "marker": marker, "allowed_root": mount / ALLOWED_ROOT})

    if len(valid) > 1:
        return valid, {"ok": False, "code": "blocked_ambiguous_test_target", "count": len(valid)}
    return valid, None


def prepare_run_paths(
    target: dict[str, Any],
    e2e_run_id: str,
) -> dict[str, Any]:
    root = Path(target["allowed_root"]) / e2e_run_id
    source = root / "source"
    backup_dir = root / "backup"
    restore_dir = root / "restore"
    for path in (backup_dir, restore_dir):
        if path.exists() and any(path.iterdir()):
            raise ValueError("restore_or_backup_not_empty")
    source.mkdir(parents=True, exist_ok=True)
    backup_dir.mkdir(parents=True, exist_ok=True)
    restore_dir.mkdir(parents=True, exist_ok=True)
    return {
        "layout_mode": "external_registered",
        "lab_tmpfs_mode": False,
        "automation_class": "physical_full",
        "work_root": root,
        "source": source,
        "backup_archive": backup_dir / "e2e-backup.tar.gz",
        "restore_dir": restore_dir,
        "external": target,
    }
