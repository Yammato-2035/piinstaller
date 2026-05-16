"""
Automatische Vorbereitung service-kompatibler Backup-Ziele unter /media/setuphelfer/<label>.

Nur echte externe Blockgeräte (USB/removable, kein System/Boot/Windows).
Kein Formatieren, kein Löschen fremder Daten — nur /media/setuphelfer, Bind-Mount oder
direkter Mount und Rechte root:setuphelfer 0770.
"""

from __future__ import annotations

import json
import os
import re
import shlex
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Callable

from core.safe_device import (
    ClassifiedDevice,
    WriteTargetProtectionError,
    list_classified_devices,
    validate_write_target,
)

RunCmd = Callable[..., dict[str, Any]]

BACKUP_TARGET_AUTO_MOUNT_READY = "BACKUP-TARGET-AUTO-MOUNT-READY"
BACKUP_TARGET_AUTO_MOUNT_FAILED = "BACKUP-TARGET-AUTO-MOUNT-FAILED"

_SETUPHELFER_MEDIA_ROOT = Path("/media/setuphelfer")
_ALLOWED_FSTYPES = frozenset({"ext4", "xfs", "btrfs"})
_LABEL_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_-]{0,31}$")


@dataclass
class ExternalBackupCandidate:
    disk_id: str
    partition_id: str
    uuid: str | None
    fstype: str | None
    label: str | None
    size_human: str | None
    existing_mount: str | None
    transport: str
    removable: bool

    def to_public_dict(self) -> dict[str, Any]:
        return asdict(self)


def sanitize_setuphelfer_label(raw: str | None, *, fallback: str = "br001") -> str:
    s = (raw or "").strip().lower()
    if not s:
        return fallback
    out = []
    for ch in s.replace(" ", "-"):
        if ch.isalnum() or ch in "-_":
            out.append(ch)
    label = "".join(out)[:32].strip("-_") or fallback
    if not _LABEL_RE.match(label):
        raise ValueError(f"Ungültiges Label: {raw!r}")
    return label


def setuphelfer_backup_dir(label: str) -> Path:
    return _SETUPHELFER_MEDIA_ROOT / sanitize_setuphelfer_label(label)


def _partition_uuid(partition_path: str) -> str | None:
    import subprocess

    try:
        proc = subprocess.run(
            ["blkid", "-o", "value", "-s", "UUID", partition_path],
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if proc.returncode == 0 and (proc.stdout or "").strip():
        return (proc.stdout or "").strip()
    return None


def _is_user_session_mount(mp: str) -> bool:
    parts = Path(mp).parts
    if len(parts) >= 3 and parts[1] == "media" and parts[2] != "setuphelfer":
        return True
    if len(parts) >= 4 and parts[1] == "run" and parts[2] == "media" and parts[3] != "setuphelfer":
        return True
    return False


def discover_external_backup_candidates(*, run: RunCmd | None = None) -> list[ExternalBackupCandidate]:
    """
    Read-only: USB/removable Partitionen, die für BR-001-Ziele infrage kommen.
    """
    out: list[ExternalBackupCandidate] = []
    for dev in list_classified_devices(runner=None):
        if dev.is_system_disk or dev.is_boot_disk or dev.is_foreign_os_disk:
            continue
        if not (dev.removable or dev.type == "usb"):
            continue
        for part in dev.partitions:
            fst = (part.filesystem or "").strip().lower()
            if fst not in _ALLOWED_FSTYPES:
                continue
            mps = [m for m in (part.mountpoints or []) if m and m not in ("/", "/boot", "/boot/firmware")]
            existing = mps[0] if mps else None
            uuid = _partition_uuid(part.device_id)
            out.append(
                ExternalBackupCandidate(
                    disk_id=dev.id,
                    partition_id=part.device_id,
                    uuid=uuid,
                    fstype=part.filesystem,
                    label=None,
                    size_human=part.size,
                    existing_mount=existing,
                    transport=dev.type,
                    removable=bool(dev.removable),
                )
            )
    return out


def _pick_candidate(
    candidates: list[ExternalBackupCandidate],
    *,
    uuid: str | None = None,
    partition: str | None = None,
) -> ExternalBackupCandidate | None:
    if partition:
        for c in candidates:
            if c.partition_id == partition:
                return c
    if uuid:
        u = uuid.strip().lower()
        for c in candidates:
            if (c.uuid or "").lower() == u:
                return c
    for c in candidates:
        if c.existing_mount and _is_user_session_mount(c.existing_mount):
            return c
    for c in candidates:
        if c.existing_mount:
            return c
    return candidates[0] if candidates else None


def _findmnt_target_mounted(target: str, run: RunCmd) -> bool:
    r = run(f"findmnt -rn -T {shlex.quote(target)}", timeout=15)
    return bool(r.get("success") and (r.get("stdout") or "").strip())


def _target_already_valid(target: Path, *, run: RunCmd) -> bool:
    try:
        validate_write_target(target, runner=run)
        from core.backup_target_service_access import assert_backup_target_writable_for_service

        assert_backup_target_writable_for_service(target.resolve())
        return True
    except (WriteTargetProtectionError, ValueError, OSError):
        return False


def prepare_setuphelfer_external_target(
    *,
    label: str = "br001",
    sudo_password: str,
    run: RunCmd | None = None,
    uuid: str | None = None,
    partition: str | None = None,
    mode: str = "auto",
) -> dict[str, Any]:
    """
    Bereitet /media/setuphelfer/<label> vor (sudo). Gibt Diagnose und Pfade zurück.
    """
    if run is None:
        raise ValueError("run (run_command) ist erforderlich für prepare_setuphelfer_external_target")
    runner = run
    if not (sudo_password or "").strip():
        return _failed("sudo_password fehlt", step="sudo_required")

    safe_label = sanitize_setuphelfer_label(label)
    target = setuphelfer_backup_dir(safe_label)
    target_s = str(target)

    if _target_already_valid(target, run=runner):
        return {
            "status": "ready",
            "diagnosis_id": BACKUP_TARGET_AUTO_MOUNT_READY,
            "backup_dir": target_s,
            "label": safe_label,
            "action": "already_valid",
            "message": "Ziel bereits gültig und beschreibbar",
        }

    candidates = discover_external_backup_candidates(run=runner)
    if not candidates:
        return _failed("Kein geeignetes externes USB/removable-Laufwerk gefunden", step="discover")

    cand = _pick_candidate(candidates, uuid=uuid, partition=partition)
    if cand is None:
        return _failed("Kein Kandidat für uuid/partition", step="pick")

    steps: list[str] = []

    def sudo_cmd(cmd: str, *, timeout: int = 60) -> dict[str, Any]:
        return runner(cmd, sudo=True, sudo_password=sudo_password, timeout=timeout)

    r = sudo_cmd(f"install -d -m 0755 {shlex.quote(str(_SETUPHELFER_MEDIA_ROOT))}")
    if not r.get("success"):
        return _failed("install /media/setuphelfer fehlgeschlagen", step="mkdir_root", stderr=r)
    steps.append("mkdir_media_setuphelfer")

    use_bind = mode == "bind" or (mode == "auto" and cand.existing_mount and _is_user_session_mount(cand.existing_mount))
    use_direct = mode == "direct" or (mode == "auto" and not use_bind)

    if use_bind:
        if not cand.existing_mount:
            return _failed("Bind-Mount: keine bestehende Quelle", step="bind")
        src = cand.existing_mount
        r = sudo_cmd(f"install -d -m 0755 {shlex.quote(target_s)}")
        if not r.get("success"):
            return _failed("Zielverzeichnis anlegen fehlgeschlagen", step="mkdir_target", stderr=r)
        if not _findmnt_target_mounted(target_s, runner):
            r = sudo_cmd(f"mount --bind {shlex.quote(src)} {shlex.quote(target_s)}")
            if not r.get("success"):
                return _failed(f"bind mount {src} -> {target_s} fehlgeschlagen", step="bind_mount", stderr=r)
        steps.append(f"bind_mount:{src}")
    elif use_direct:
        if not cand.uuid:
            return _failed("Direkt-Mount: UUID unbekannt", step="uuid")
        r = sudo_cmd(f"install -d -m 0755 {shlex.quote(target_s)}")
        if not r.get("success"):
            return _failed("Zielverzeichnis anlegen fehlgeschlagen", step="mkdir_target", stderr=r)
        if not _findmnt_target_mounted(target_s, runner):
            r = sudo_cmd(
                f"mount -o nosuid,nodev,noatime UUID={shlex.quote(cand.uuid)} {shlex.quote(target_s)}",
                timeout=120,
            )
            if not r.get("success"):
                return _failed("direkter Mount fehlgeschlagen", step="direct_mount", stderr=r)
        steps.append(f"direct_mount:UUID={cand.uuid}")
    else:
        return _failed(f"Unbekannter mode={mode}", step="mode")

    r = sudo_cmd(
        f"chown root:setuphelfer {shlex.quote(target_s)} && chmod 0770 {shlex.quote(target_s)}",
    )
    if not r.get("success"):
        return _failed("chown/chmod fehlgeschlagen", step="permissions", stderr=r)
    steps.append("chown_chmod")

    touch = sudo_cmd(
        f"sudo -u setuphelfer touch {shlex.quote(target_s + '/.setuphelfer-auto-mount-probe')} "
        f"&& sudo -u setuphelfer rm -f {shlex.quote(target_s + '/.setuphelfer-auto-mount-probe')}",
    )
    if not touch.get("success"):
        return _failed("Schreibtest setuphelfer fehlgeschlagen", step="write_probe", stderr=touch)
    steps.append("write_probe_setuphelfer")

    if not _target_already_valid(target, run=runner):
        return _failed("validate_write_target nach Vorbereitung fehlgeschlagen", step="validate", candidate=cand)

    from core.safe_device import inspect_write_target_mount

    return {
        "status": "ready",
        "diagnosis_id": BACKUP_TARGET_AUTO_MOUNT_READY,
        "backup_dir": target_s,
        "label": safe_label,
        "action": "prepared",
        "steps": steps,
        "candidate": cand.to_public_dict(),
        "mount_inspection": inspect_write_target_mount(target_s),
        "message": "Externes Backup-Ziel vorbereitet",
    }


def _failed(
    message: str,
    *,
    step: str,
    stderr: dict[str, Any] | None = None,
    candidate: ExternalBackupCandidate | None = None,
) -> dict[str, Any]:
    det: dict[str, Any] = {"step": step, "message": message}
    if stderr:
        det["stderr"] = (stderr.get("stderr") or stderr.get("error") or "")[:400]
    if candidate:
        det["candidate"] = candidate.to_public_dict()
    return {
        "status": "failed",
        "diagnosis_id": BACKUP_TARGET_AUTO_MOUNT_FAILED,
        "message": message,
        "details": det,
    }


__all__ = [
    "BACKUP_TARGET_AUTO_MOUNT_FAILED",
    "BACKUP_TARGET_AUTO_MOUNT_READY",
    "ExternalBackupCandidate",
    "discover_external_backup_candidates",
    "prepare_setuphelfer_external_target",
    "sanitize_setuphelfer_label",
    "setuphelfer_backup_dir",
]
