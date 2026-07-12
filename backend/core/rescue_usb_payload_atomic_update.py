"""PI-RS-USB-UPDATER-001 — atomic FAT32 ESP payload replace with version sync."""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

from core.rescue_fat32_esp_usb_writer import sha256_file
from core.rescue_payload_version_carriers import (
    build_rescue_payload_version_json,
    build_rescue_runtime_version_json,
    read_payload_version_carriers,
    verify_payload_version_carriers,
)

UPDATE_METHOD = "atomic_fat32_esp_payload_replace"
PAYLOAD_REL_PATH = "live/filesystem.squashfs"
VERSION_JSON_REL = "setuphelfer/rescue/version.json"
EVIDENCE_JSON_REL = "setuphelfer/rescue/evidence.json"
SETUP_LOGS_LABEL = "SETUP_LOGS"
MAX_PREV_PAYLOADS = 1

_FILENAME_VERSION_RE = re.compile(r"filesystem\.squashfs\.repacked-(\d+\.\d+\.\d+\.\d+)$")


def _now_iso() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


def parse_filename_version(squashfs_path: Path) -> str | None:
    m = _FILENAME_VERSION_RE.search(squashfs_path.name)
    return m.group(1) if m else None


def is_safe_regular_file(path: Path) -> tuple[bool, str | None]:
    if not path.exists():
        return False, "SOURCE_MISSING"
    if path.is_symlink():
        return False, "SOURCE_IS_SYMLINK"
    if not path.is_file():
        return False, "SOURCE_NOT_REGULAR_FILE"
    return True, None


def validate_source_payload(
    squashfs_path: Path,
    *,
    expected_sha256: str | None = None,
    expected_version: str | None = None,
) -> dict[str, Any]:
    """Read-only source preflight before any USB write."""
    errors: list[str] = []
    sq = squashfs_path.resolve()
    ok_file, file_err = is_safe_regular_file(sq)
    if not ok_file:
        errors.append(file_err or "SOURCE_INVALID")
        return _source_result(sq, errors=errors)

    actual_sha = sha256_file(sq)
    expected_sha = (expected_sha256 or "").strip().lower() or None
    if expected_sha and actual_sha.lower() != expected_sha:
        errors.append("source_payload_hash_mismatch")

    filename_version = parse_filename_version(sq)
    carrier_report = verify_payload_version_carriers(
        sq,
        expected_version=expected_version,
    )
    internal = carrier_report.get("payload_version_carriers") or {}
    canonical_version = str(internal.get("VERSION") or "").strip()
    if not canonical_version:
        errors.append("source_payload_version_missing")
    if not carrier_report.get("all_version_carriers_match"):
        errors.append("source_payload_version_drift")
    if filename_version and canonical_version and filename_version != canonical_version:
        errors.append("source_payload_filename_version_mismatch")
    if expected_version and canonical_version and canonical_version != expected_version.strip():
        errors.append("source_payload_expected_version_mismatch")

    missing = [k for k, v in internal.items() if not str(v).strip()]
    if missing:
        errors.append("source_payload_version_carrier_missing")

    return _source_result(
        sq,
        actual_sha256=actual_sha,
        filename_version=filename_version,
        internal_versions=internal,
        canonical_version=canonical_version,
        version_consistent=not errors and carrier_report.get("all_version_carriers_match"),
        errors=errors,
    )


def _source_result(
    sq: Path,
    *,
    actual_sha256: str = "",
    filename_version: str | None = None,
    internal_versions: Mapping[str, str] | None = None,
    canonical_version: str = "",
    version_consistent: bool = False,
    errors: Sequence[str] | None = None,
) -> dict[str, Any]:
    err_list = list(errors or [])
    return {
        "path": str(sq),
        "expected_sha256": actual_sha256,
        "actual_sha256": actual_sha256,
        "filename_version": filename_version,
        "internal_versions": dict(internal_versions or {}),
        "canonical_version": canonical_version,
        "version_consistent": version_consistent and not err_list,
        "errors": err_list,
        "blocked": bool(err_list),
    }


def build_atomic_esp_version_json(
    *,
    payload_version: str,
    payload_sha256: str,
    payload_filename: str = PAYLOAD_REL_PATH,
    existing: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """ESP setuphelfer/rescue/version.json from verified payload — never stale stick copy."""
    version = payload_version.strip()
    base = dict(existing or {})
    synced = build_rescue_runtime_version_json(version)
    base.update(synced)
    base["project_version"] = version
    base["rescue_payload_version"] = version
    base["payload_filename"] = payload_filename
    base["payload_sha256"] = payload_sha256.strip().lower()
    base["updated_at"] = _now_iso()
    base["update_method"] = UPDATE_METHOD
    base["content_verified"] = True
    base["version_source_of_truth"] = False
    base["payload_updated_at"] = base["updated_at"]
    return base


def build_atomic_esp_evidence_json(
    *,
    payload_version: str,
    payload_sha256: str,
    payload_size_bytes: int,
    existing: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """ESP setuphelfer/rescue/evidence.json aligned to payload version."""
    out = dict(existing or {})
    files = list(out.get("files") or [])
    replaced = False
    for entry in files:
        if entry.get("staging_path") == PAYLOAD_REL_PATH:
            entry["sha256"] = payload_sha256.strip().lower()
            entry["size_bytes"] = payload_size_bytes
            replaced = True
    if not replaced:
        files.append(
            {
                "iso_path": f"/{PAYLOAD_REL_PATH}",
                "staging_path": PAYLOAD_REL_PATH,
                "size_bytes": payload_size_bytes,
                "sha256": payload_sha256.strip().lower(),
            }
        )
    out["files"] = files
    out["project_version"] = payload_version.strip()
    out["rescue_payload_version"] = payload_version.strip()
    out["payload_updated_at"] = _now_iso()
    out["writer_mode"] = "fat32_esp"
    out["update_method"] = UPDATE_METHOD
    out["content_verified"] = True
    return out


def validate_esp_metadata(
    metadata: Mapping[str, Any],
    *,
    expected_version: str,
    expected_sha256: str,
) -> dict[str, Any]:
    version = str(metadata.get("project_version") or metadata.get("rescue_payload_version") or "")
    sha = str(metadata.get("payload_sha256") or "").strip().lower()
    expected_v = expected_version.strip()
    expected_s = expected_sha256.strip().lower()
    errors: list[str] = []
    if version != expected_v:
        errors.append("esp_metadata_version_mismatch")
    if sha != expected_s:
        errors.append("esp_metadata_sha_mismatch")
    if metadata.get("content_verified") is not True:
        errors.append("esp_metadata_content_verified_false")
    return {
        "ok": not errors,
        "project_version": version,
        "rescue_payload_version": str(metadata.get("rescue_payload_version") or ""),
        "payload_sha256": sha,
        "errors": errors,
    }


def read_mount_metadata(version_path: Path) -> dict[str, Any]:
    if not version_path.is_file():
        return {}
    return json.loads(version_path.read_text(encoding="utf-8"))


def classify_prev_payload_files(live_dir: Path) -> dict[str, Any]:
    prev_files = sorted(live_dir.glob("filesystem.squashfs.prev-*"))
    return {
        "prev_files": [p.name for p in prev_files],
        "prev_count": len(prev_files),
        "policy_max": MAX_PREV_PAYLOADS,
    }


def plan_prev_backup_name(old_version: str | None) -> str:
    ver = (old_version or "unknown").strip().replace("/", "_")
    return f"filesystem.squashfs.prev-{ver}"


def validate_path_safe_relative(rel_path: str) -> bool:
    if not rel_path or rel_path.startswith("/") or ".." in rel_path.split("/"):
        return False
    return True


@dataclass
class AtomicMountState:
    """In-memory / directory-backed ESP simulation for tests."""

    root: Path

    @property
    def live_dir(self) -> Path:
        return self.root / "live"

    @property
    def version_path(self) -> Path:
        return self.root / VERSION_JSON_REL

    @property
    def evidence_path(self) -> Path:
        return self.root / EVIDENCE_JSON_REL

    @property
    def active_payload(self) -> Path:
        return self.live_dir / "filesystem.squashfs"


def simulate_atomic_replace(
    mount: AtomicMountState,
    source_payload: Path,
    *,
    source_report: Mapping[str, Any],
    rollback_inject_after_payload: bool = False,
) -> dict[str, Any]:
    """Directory-based atomic replace without real USB (integration smoke)."""
    errors: list[str] = []
    warnings: list[str] = []
    rollback_required = False
    rollback_successful: bool | None = None
    atomic_replace = False
    before_sha = sha256_file(mount.active_payload) if mount.active_payload.is_file() else None
    before_meta = read_mount_metadata(mount.version_path)
    canonical = str(source_report.get("canonical_version") or "")
    new_sha = str(source_report.get("actual_sha256") or "")

    mount.live_dir.mkdir(parents=True, exist_ok=True)
    mount.evidence_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_dir = mount.live_dir / ".sqtmp"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    tmp_payload = tmp_dir / "filesystem.squashfs.new"
    tmp_payload.write_bytes(source_payload.read_bytes())
    if sha256_file(tmp_payload) != new_sha:
        errors.append("temporary_payload_hash_mismatch")
        return _sim_result(
            mount, before_sha, before_meta, errors=errors, warnings=warnings,
            rollback_required=False, rollback_successful=None, atomic_replace=False,
            source_report=source_report,
        )

    meta_tmp = mount.root / ".meta_tmp"
    meta_tmp.mkdir(parents=True, exist_ok=True)
    version_doc = build_atomic_esp_version_json(
        payload_version=canonical,
        payload_sha256=new_sha,
        existing=before_meta,
    )
    evidence_doc = build_atomic_esp_evidence_json(
        payload_version=canonical,
        payload_sha256=new_sha,
        payload_size_bytes=source_payload.stat().st_size,
        existing=read_mount_metadata(mount.evidence_path) if mount.evidence_path.is_file() else {},
    )
    (meta_tmp / "version.json").write_text(json.dumps(version_doc, indent=2) + "\n", encoding="utf-8")
    (meta_tmp / "evidence.json").write_text(json.dumps(evidence_doc, indent=2) + "\n", encoding="utf-8")
    meta_check = validate_esp_metadata(version_doc, expected_version=canonical, expected_sha256=new_sha)
    if not meta_check["ok"]:
        errors.extend(meta_check["errors"])
        return _sim_result(
            mount, before_sha, before_meta, errors=errors, warnings=warnings,
            rollback_required=False, rollback_successful=None, atomic_replace=False,
            source_report=source_report,
        )

    old_version = str(before_meta.get("project_version") or before_meta.get("rescue_payload_version") or "")
    if mount.active_payload.is_file() and old_version:
        prev_name = plan_prev_backup_name(old_version)
        prev_path = mount.live_dir / prev_name
        if not prev_path.exists():
            prev_path.write_bytes(mount.active_payload.read_bytes())

    tmp_payload.replace(mount.active_payload)
    if sha256_file(mount.active_payload) != new_sha:
        errors.append("activated_payload_hash_mismatch")
        rollback_required = True
    elif rollback_inject_after_payload:
        errors.append("simulated_metadata_activation_failure")
        rollback_required = True
    else:
        (meta_tmp / "version.json").replace(mount.version_path)
        (meta_tmp / "evidence.json").replace(mount.evidence_path)
        atomic_replace = True

    if rollback_required and mount.active_payload.is_file():
        prev_candidates = sorted(mount.live_dir.glob("filesystem.squashfs.prev-*"))
        if prev_candidates:
            prev_candidates[-1].replace(mount.active_payload)
            if before_meta:
                mount.version_path.write_text(json.dumps(before_meta, indent=2) + "\n", encoding="utf-8")
            rollback_successful = sha256_file(mount.active_payload) == (before_sha or "")
        else:
            rollback_successful = False

    if tmp_dir.exists():
        shutil.rmtree(tmp_dir, ignore_errors=True)
    if meta_tmp.exists():
        shutil.rmtree(meta_tmp, ignore_errors=True)

    after_sha = sha256_file(mount.active_payload) if mount.active_payload.is_file() else None
    after_meta = read_mount_metadata(mount.version_path)
    status = "success"
    if errors and rollback_required:
        status = "failed_rolled_back" if rollback_successful else "critical_manual_recovery_required"
    elif errors:
        status = "failed"

    return _sim_result(
        mount,
        before_sha,
        before_meta,
        after_sha=after_sha,
        after_meta=after_meta,
        errors=errors,
        warnings=warnings,
        rollback_required=rollback_required,
        rollback_successful=rollback_successful,
        atomic_replace=atomic_replace,
        source_report=source_report,
        status=status,
    )


def _sim_result(
    mount: AtomicMountState,
    before_sha: str | None,
    before_meta: Mapping[str, Any],
    *,
    after_sha: str | None = None,
    after_meta: Mapping[str, Any] | None = None,
    errors: Sequence[str] | None = None,
    warnings: Sequence[str] | None = None,
    rollback_required: bool = False,
    rollback_successful: bool | None = None,
    atomic_replace: bool = False,
    source_report: Mapping[str, Any] | None = None,
    status: str = "failed",
) -> dict[str, Any]:
    src = dict(source_report or {})
    after_meta = dict(after_meta or {})
    return {
        "status": status,
        "source": {
            "path": src.get("path", ""),
            "expected_sha256": src.get("actual_sha256", ""),
            "actual_sha256": src.get("actual_sha256", ""),
            "filename_version": src.get("filename_version"),
            "internal_versions": src.get("internal_versions", {}),
            "version_consistent": src.get("version_consistent", False),
        },
        "before": {
            "payload_version": str(before_meta.get("project_version") or ""),
            "payload_sha256": before_sha,
            "metadata": dict(before_meta),
        },
        "after": {
            "payload_version": str(after_meta.get("project_version") or ""),
            "payload_sha256": after_sha,
            "metadata": after_meta,
        },
        "atomic_replace": atomic_replace,
        "rollback_required": rollback_required,
        "rollback_successful": rollback_successful,
        "partition_table_modified": False,
        "setup_logs_modified": False,
        "internal_drive_touched": False,
        "physical_usb_tested": False,
        "simulated_esp_tested": True,
        "production_hardware_verified": False,
        "warnings": list(warnings or []),
        "errors": list(errors or []),
        "mount_root": str(mount.root),
    }


def build_usb_updater_result(
    *,
    status: str,
    source: Mapping[str, Any],
    target: Mapping[str, Any],
    before: Mapping[str, Any],
    after: Mapping[str, Any],
    atomic_replace: bool,
    rollback_required: bool,
    rollback_successful: bool | None,
    partition_table_modified: bool = False,
    setup_logs_modified: bool = False,
    internal_drive_touched: bool = False,
    warnings: Sequence[str] | None = None,
    errors: Sequence[str] | None = None,
    content_gate: str = "not_run",
    secret_gate: str = "not_run",
) -> dict[str, Any]:
    return {
        "status": status,
        "source": {
            "path": source.get("path", ""),
            "expected_sha256": source.get("expected_sha256", source.get("actual_sha256", "")),
            "actual_sha256": source.get("actual_sha256", ""),
            "filename_version": source.get("filename_version"),
            "internal_versions": source.get("internal_versions", {}),
            "version_consistent": source.get("version_consistent", False),
            "content_gate": content_gate,
            "secret_gate": secret_gate,
        },
        "target": dict(target),
        "before": dict(before),
        "after": dict(after),
        "atomic_replace": atomic_replace,
        "atomic_metadata_replace": atomic_replace and bool(after.get("metadata")),
        "rollback_required": rollback_required,
        "rollback_successful": rollback_successful,
        "partition_table_modified": partition_table_modified,
        "setup_logs_modified": setup_logs_modified,
        "internal_drive_touched": internal_drive_touched,
        "manual_metadata_fix_required": False,
        "warnings": list(warnings or []),
        "errors": list(errors or []),
        "generated_at": _now_iso(),
    }


def redact_serial(serial: str | None) -> str:
    s = (serial or "").strip()
    if len(s) <= 4:
        return "***"
    return f"{s[:4]}…{hashlib.sha256(s.encode()).hexdigest()[:8]}"


def validate_sibling_setup_logs_partition(
    *,
    parent_device: str,
    logs_label: str | None,
    logs_fstype: str | None,
) -> dict[str, Any]:
    ok_label = (logs_label or "").upper() == SETUP_LOGS_LABEL
    ok_fs = (logs_fstype or "").lower() in ("vfat", "msdos")
    blockers: list[str] = []
    if not ok_label:
        blockers.append("SETUP_LOGS_LABEL_MISSING")
    if not ok_fs:
        blockers.append("SETUP_LOGS_NOT_VFAT")
    return {
        "parent_device": parent_device,
        "setup_logs_label": logs_label,
        "sibling_setup_logs_detected": ok_label and ok_fs,
        "blockers": blockers,
        "blocked": bool(blockers),
    }
