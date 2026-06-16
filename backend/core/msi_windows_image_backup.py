"""
MSI Windows image backup execution gate (Phase F.2).

Read from source block device only; write image FILE on external mount only.
No restore, wipe, format, partition writes, NTFS mount, or BitLocker operations.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

F2_SOURCE_DEVICE = "/dev/nvme0n1"
F2_BLOCKED_TARGET_DEVICES = frozenset({"/dev/nvme1n1", "/dev/sdb", "/dev/sda", "/dev/sda1"})
F2_ALLOWED_SOURCE = F2_SOURCE_DEVICE

OPERATOR_CONFIRMATION_1 = (
    "Ich bestätige: Quelle ist /dev/nvme0n1 und Ziel ist ausschließlich eine Image-Datei "
    "auf dem externen Backup-Mount von /dev/sda."
)
OPERATOR_CONFIRMATION_2 = (
    "Ich bestätige: Es wird kein Restore, kein Wipe, kein Formatieren, kein Partitionieren "
    "und kein Schreiben auf interne Datenträger ausgeführt."
)

CapacityBlockReason = Literal[
    "ok",
    "blocked_insufficient_target_capacity",
    "blocked_external_target_mount_missing",
    "blocked_operator_confirmation_missing",
    "blocked_invalid_source",
    "blocked_invalid_target",
    "blocked_target_is_blockdevice_path",
]


@dataclass
class F2PreflightResult:
    ok: bool
    status: str
    reason: CapacityBlockReason | str
    source_device: str
    source_size_bytes: int
    target_mount: str
    target_device: str
    backup_dir: str | None
    free_bytes: int
    required_bytes: int
    operator_confirmation_1: bool
    operator_confirmation_2: bool
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    paths: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "status": self.status,
            "reason": self.reason,
            "source_device": self.source_device,
            "source_size_bytes": self.source_size_bytes,
            "target_mount": self.target_mount,
            "target_device": self.target_device,
            "backup_dir": self.backup_dir,
            "free_bytes": self.free_bytes,
            "required_bytes": self.required_bytes,
            "operator_confirmation_1": self.operator_confirmation_1,
            "operator_confirmation_2": self.operator_confirmation_2,
            "warnings": self.warnings,
            "errors": self.errors,
            "paths": self.paths,
        }


def _utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _walk_findmnt_filesystems(nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    flat: list[dict[str, Any]] = []
    for node in nodes:
        flat.append(node)
        children = node.get("children") or []
        if children:
            flat.extend(_walk_findmnt_filesystems(children))
    return flat


def discover_external_backup_mount(
    findmnt_json: dict[str, Any],
    *,
    target_sources: frozenset[str] = frozenset({"/dev/sda1", "/dev/sda"}),
) -> tuple[str, str, str] | None:
    """Return (mount_path, source_device, fstype) for external /dev/sda backup mount."""
    for fs in _walk_findmnt_filesystems(findmnt_json.get("filesystems", [])):
        src = fs.get("source", "")
        tgt = fs.get("target", "")
        fst = fs.get("fstype", "")
        if src in target_sources and (
            tgt.startswith("/media/") or tgt.startswith("/run/media/") or tgt.startswith("/mnt/")
        ):
            return tgt, src, fst
    return None


def _parse_size_bytes(size_val: Any) -> int:
    if isinstance(size_val, int):
        return size_val
    s = str(size_val or "").strip()
    if s.isdigit():
        return int(s)
    return 0


def mount_path_is_active(mount_path: str) -> bool:
    if not mount_path:
        return False
    try:
        if Path(mount_path).exists():
            return True
    except OSError:
        pass
    try:
        subprocess.run(
            ["findmnt", "-n", mount_path],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def validate_operator_confirmations(
    confirmation_1: str | None,
    confirmation_2: str | None,
) -> tuple[bool, bool]:
    c1 = (confirmation_1 or "").strip() == OPERATOR_CONFIRMATION_1
    c2 = (confirmation_2 or "").strip() == OPERATOR_CONFIRMATION_2
    return c1, c2


def is_blockdevice_output_path(path: str) -> bool:
    p = path.strip()
    if re.match(r"^/dev/(sd[a-z]|nvme\d+n\d+|mmcblk\d+)(p?\d+)?$", p):
        return True
    return False


def validate_target_mount_path(mount_path: str) -> tuple[bool, list[str]]:
    errors: list[str] = []
    mp = Path(mount_path).resolve()
    mp_str = str(mp)
    forbidden_prefixes = ("/", "/home", "/tmp", "/var/tmp", "/boot", "/opt")
    for bad in forbidden_prefixes:
        if bad == "/":
            if mp_str == "/":
                errors.append("target_is_root")
        elif mp_str == bad or mp_str.startswith(bad + "/"):
            if not mp_str.startswith("/media/") and not mp_str.startswith("/run/media/"):
                errors.append(f"target_under_forbidden:{bad}")
    if not (mp_str.startswith("/media/") or mp_str.startswith("/run/media/") or mp_str.startswith("/mnt/")):
        errors.append("target_not_external_mount_pattern")
    return len(errors) == 0, errors


def compute_required_bytes(source_size_bytes: int, *, reserve_pct: float = 0.05) -> int:
    return int(source_size_bytes * (1.0 + reserve_pct))


def build_backup_paths(mount_path: str, timestamp: str | None = None) -> dict[str, str]:
    ts = timestamp or _utc_stamp()
    base = Path(mount_path) / "setuphelfer-msi-image-backups" / ts
    stem = f"windows_nvme0n1_{ts}"
    return {
        "backup_dir": str(base),
        "image_partial": str(base / f"{stem}.img.partial"),
        "image_final": str(base / f"{stem}.img"),
        "status_json": str(base / f"{stem}.status.json"),
        "progress_jsonl": str(base / f"{stem}.progress.jsonl"),
        "manifest_json": str(base / f"{stem}.manifest.json"),
        "sha256_file": str(base / f"{stem}.sha256"),
        "final_json": str(base / f"{stem}.final.json"),
    }


def run_f2_preflight(
    *,
    source_device: str,
    source_size_bytes: int,
    target_mount: str,
    target_device: str,
    free_bytes: int,
    fstype: str,
    operator_confirmation_1: str | None = None,
    operator_confirmation_2: str | None = None,
    timestamp: str | None = None,
) -> F2PreflightResult:
    warnings: list[str] = []
    errors: list[str] = []

    c1, c2 = validate_operator_confirmations(operator_confirmation_1, operator_confirmation_2)
    if not c1 or not c2:
        return F2PreflightResult(
            ok=False,
            status="blocked",
            reason="blocked_operator_confirmation_missing",
            source_device=source_device,
            source_size_bytes=source_size_bytes,
            target_mount=target_mount,
            target_device=target_device,
            backup_dir=None,
            free_bytes=free_bytes,
            required_bytes=compute_required_bytes(source_size_bytes),
            operator_confirmation_1=c1,
            operator_confirmation_2=c2,
            errors=["operator_confirmation_missing"],
        )

    if source_device != F2_ALLOWED_SOURCE:
        return F2PreflightResult(
            ok=False,
            status="blocked",
            reason="blocked_invalid_source",
            source_device=source_device,
            source_size_bytes=source_size_bytes,
            target_mount=target_mount,
            target_device=target_device,
            backup_dir=None,
            free_bytes=free_bytes,
            required_bytes=compute_required_bytes(source_size_bytes),
            operator_confirmation_1=c1,
            operator_confirmation_2=c2,
            errors=[f"source_must_be:{F2_ALLOWED_SOURCE}"],
        )

    if not mount_path_is_active(target_mount):
        return F2PreflightResult(
            ok=False,
            status="blocked",
            reason="blocked_external_target_mount_missing",
            source_device=source_device,
            source_size_bytes=source_size_bytes,
            target_mount=target_mount,
            target_device=target_device,
            backup_dir=None,
            free_bytes=free_bytes,
            required_bytes=compute_required_bytes(source_size_bytes),
            operator_confirmation_1=c1,
            operator_confirmation_2=c2,
            errors=["mount_missing"],
        )

    mount_ok, mount_errors = validate_target_mount_path(target_mount)
    if not mount_ok:
        return F2PreflightResult(
            ok=False,
            status="blocked",
            reason="blocked_invalid_target",
            source_device=source_device,
            source_size_bytes=source_size_bytes,
            target_mount=target_mount,
            target_device=target_device,
            backup_dir=None,
            free_bytes=free_bytes,
            required_bytes=compute_required_bytes(source_size_bytes),
            operator_confirmation_1=c1,
            operator_confirmation_2=c2,
            errors=mount_errors,
        )

    if fstype.lower() != "ext4":
        warnings.append(f"unexpected_fstype:{fstype}")

    paths = build_backup_paths(target_mount, timestamp)
    if is_blockdevice_output_path(paths["image_partial"]):
        return F2PreflightResult(
            ok=False,
            status="blocked",
            reason="blocked_target_is_blockdevice_path",
            source_device=source_device,
            source_size_bytes=source_size_bytes,
            target_mount=target_mount,
            target_device=target_device,
            backup_dir=None,
            free_bytes=free_bytes,
            required_bytes=compute_required_bytes(source_size_bytes),
            operator_confirmation_1=c1,
            operator_confirmation_2=c2,
            errors=["output_path_is_blockdevice"],
            paths=paths,
        )

    required = compute_required_bytes(source_size_bytes)
    if free_bytes < required:
        return F2PreflightResult(
            ok=False,
            status="blocked",
            reason="blocked_insufficient_target_capacity",
            source_device=source_device,
            source_size_bytes=source_size_bytes,
            target_mount=target_mount,
            target_device=target_device,
            backup_dir=paths["backup_dir"],
            free_bytes=free_bytes,
            required_bytes=required,
            operator_confirmation_1=c1,
            operator_confirmation_2=c2,
            warnings=warnings,
            errors=[
                f"free_bytes={free_bytes}",
                f"required_bytes={required}",
            ],
            paths=paths,
        )

    return F2PreflightResult(
        ok=True,
        status="ready",
        reason="ok",
        source_device=source_device,
        source_size_bytes=source_size_bytes,
        target_mount=target_mount,
        target_device=target_device,
        backup_dir=paths["backup_dir"],
        free_bytes=free_bytes,
        required_bytes=required,
        operator_confirmation_1=c1,
        operator_confirmation_2=c2,
        warnings=warnings,
        paths=paths,
    )


def initial_status_payload(preflight: F2PreflightResult, job_id: str) -> dict[str, Any]:
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    return {
        "job_id": job_id,
        "status": "running" if preflight.ok else "failed",
        "phase": "preflight" if not preflight.ok else "image_read_write",
        "source_device": preflight.source_device,
        "target_mount": preflight.target_mount,
        "target_image_partial": preflight.paths.get("image_partial", ""),
        "target_image_final": preflight.paths.get("image_final", ""),
        "started_at": now,
        "updated_at": now,
        "bytes_total": preflight.source_size_bytes,
        "bytes_read": 0,
        "bytes_written": 0,
        "read_rate_bps_30s": 0,
        "write_rate_bps_30s": 0,
        "last_progress_s": 0,
        "stall_detected": False,
        "operator_confirmation_1": preflight.operator_confirmation_1,
        "operator_confirmation_2": preflight.operator_confirmation_2,
        "restore_executed": False,
        "wipe_executed": False,
        "format_executed": False,
        "partition_write_executed": False,
        "ntfs_mounted": False,
        "bitlocker_action_executed": False,
        "warnings": preflight.warnings,
        "errors": preflight.errors,
    }


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fp:
        while chunk := fp.read(1024 * 1024):
            h.update(chunk)
    return h.hexdigest()
