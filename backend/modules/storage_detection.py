"""
Blockgeräte und Mount-Punkte per lsblk/blkid/findmnt (keine neuen Abhängigkeiten).

Validierung des Datei-Backup-Ziels: nur gemountete Blockgeräte mit zulässigem
Dateisystem, nicht Root- und nicht Live-Medium.
"""

from __future__ import annotations

import grp
import json
import os
import re
import subprocess
from pathlib import Path

# Echte os.stat-Referenz (Tests patchen ggf. os.stat; Path.is_dir nutzt ebenfalls os.stat).
_os_stat = os.stat
from typing import Any, Callable, Mapping, Sequence

from core.safe_device import (
    WriteTargetProtectionError,
    resolve_mount_source_for_path,
    validate_write_target,
)
from core.backup_recovery_i18n import (
    K_BACKUP_TARGET_FILESYSTEM_NOT_PERMITTED,
    K_BACKUP_TARGET_LIVE_FILESYSTEM,
    K_BACKUP_TARGET_NON_BLOCK_SOURCE,
    K_BACKUP_TARGET_NOT_MOUNTED,
    K_BACKUP_TARGET_NOT_WRITABLE,
    K_BACKUP_TARGET_PARENT_MISSING,
    K_BACKUP_TARGET_ROOT_FILESYSTEM,
    K_BACKUP_TARGET_WRITE_PROTECTED,
)

Runner = Callable[..., subprocess.CompletedProcess[str]]

_LIVE_FSTYPES = frozenset({"squashfs", "iso9660", "overlay"})
_ALLOWED_BACKUP_FSTYPES = frozenset({"ext4", "xfs", "ntfs"})


class BackupTargetValidationError(ValueError):
    """Fehler bei validate_backup_target; message_key für i18n."""

    def __init__(self, message_key: str, detail: str | None = None) -> None:
        self.message_key = message_key
        self.detail = detail
        super().__init__(message_key)


def _run_capture(
    argv: list[str],
    *,
    runner: Runner | None = None,
    timeout: int = 60,
) -> subprocess.CompletedProcess[str]:
    run = runner or subprocess.run
    return run(argv, capture_output=True, text=True, timeout=timeout, check=False)


def detect_block_devices(*, runner: Runner | None = None) -> list[dict[str, Any]]:
    """
    Liest Blockgeräte per lsblk -J.

    Rückgabe: Liste von Dicts mit device, partitions, fstype, mountpoint, size, type.
    """
    r = _run_capture(
        ["lsblk", "-J", "-o", "NAME,FSTYPE,SIZE,MOUNTPOINT,TYPE"],
        runner=runner,
        timeout=30,
    )
    if r.returncode != 0 or not (r.stdout or "").strip():
        return []
    try:
        data = json.loads(r.stdout)
    except json.JSONDecodeError:
        return []
    raw = data.get("blockdevices")
    if not isinstance(raw, list):
        return []
    return [_normalize_lsblk_node(x) for x in raw if isinstance(x, dict)]


def _normalize_lsblk_node(node: Mapping[str, Any]) -> dict[str, Any]:
    name = node.get("name")
    name_s = name if isinstance(name, str) else ""
    devpath = name_s if name_s.startswith("/dev/") else (f"/dev/{name_s}" if name_s else "")
    children_raw = node.get("children")
    partitions: list[dict[str, Any]] = []
    if isinstance(children_raw, list):
        for ch in children_raw:
            if isinstance(ch, dict):
                partitions.append(_normalize_lsblk_node(ch))
    return {
        "device": devpath,
        "partitions": partitions,
        "fstype": node.get("fstype"),
        "mountpoint": node.get("mountpoint"),
        "size": node.get("size"),
        "type": node.get("type"),
    }


def detect_filesystems(*, runner: Runner | None = None) -> dict[str, dict[str, str]]:
    """
    Liest blkid-Ausgabe für alle gefundenen Geräte.

    Rückgabe: device-Pfad -> {"uuid": ..., "type": ...} (TYPE aus blkid als type).
    """
    r = _run_capture(["blkid"], runner=runner, timeout=60)
    if r.returncode != 0:
        return {}
    return _parse_blkid_output(r.stdout or "")


def _parse_blkid_output(text: str) -> dict[str, dict[str, str]]:
    out: dict[str, dict[str, str]] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or ":" not in line:
            continue
        dev_part, rest = line.split(":", 1)
        dev = dev_part.strip()
        if not dev.startswith("/dev/"):
            continue
        uuid_m = re.search(r'\bUUID="([^"]*)"', rest)
        type_m = re.search(r'\bTYPE="([^"]*)"', rest)
        entry: dict[str, str] = {}
        if uuid_m:
            entry["uuid"] = uuid_m.group(1)
        if type_m:
            entry["type"] = type_m.group(1)
        if entry:
            out[dev] = entry
    return out


def classify_devices(devices: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """
    Ordnet jedem Knoten (rekursiv in partitions) eine Kategorie zu:
    system_disk | backup_candidate | live_system | unknown
    """

    def classify_one(node: Mapping[str, Any]) -> str:
        mp = node.get("mountpoint")
        mp_s = mp if isinstance(mp, str) and mp else ""
        ft_raw = node.get("fstype")
        ft = (ft_raw.lower() if isinstance(ft_raw, str) else "") or ""

        if mp_s == "/":
            return "system_disk"
        if ft in _LIVE_FSTYPES:
            return "live_system"
        if ft in _ALLOWED_BACKUP_FSTYPES:
            return "backup_candidate"
        return "unknown"

    def walk(node: Mapping[str, Any]) -> dict[str, Any]:
        d = {k: v for k, v in dict(node).items() if k != "partitions"}
        d["category"] = classify_one(node)
        parts = node.get("partitions")
        if isinstance(parts, list):
            d["partitions"] = [walk(p) for p in parts if isinstance(p, dict)]
        else:
            d["partitions"] = []
        return d

    return [walk(d) for d in devices if isinstance(d, dict)]


def _findmnt_json_for_path(path: Path, *, runner: Runner | None = None) -> list[dict[str, Any]]:
    r = _run_capture(["findmnt", "-J", str(path)], runner=runner, timeout=30)
    if r.returncode != 0:
        return []
    try:
        data = json.loads(r.stdout or "{}")
    except json.JSONDecodeError:
        return []
    fss = data.get("filesystems")
    if not isinstance(fss, list):
        return []
    return [x for x in fss if isinstance(x, dict)]


def _pick_mount_for_path(path: Path, filesystems: Sequence[Mapping[str, Any]]) -> dict[str, Any] | None:
    """Wählt den spezifischsten Mount (längstes target-Prefix von path)."""
    try:
        sp = str(path.resolve())
    except OSError:
        sp = str(path.absolute())
    best: dict[str, Any] | None = None
    best_len = -1
    for fs in filesystems:
        tgt = fs.get("target")
        if not isinstance(tgt, str) or not tgt:
            continue
        tnorm = tgt.rstrip("/") or "/"
        if sp == tnorm or sp.startswith(tnorm + "/"):
            ln = len(tnorm)
            if ln > best_len:
                best_len = ln
                best = dict(fs)
    if best is not None:
        return best
    if filesystems:
        return dict(filesystems[-1])
    return None


def _source_is_block_device(source: str) -> bool:
    s = source.strip()
    if s.startswith("/dev/"):
        return True
    return False


def validate_backup_target(
    archive_path: str | Path,
    *,
    runner: Runner | None = None,
) -> None:
    """
    Harte Prüfungen vor Datei-Backup: Zielverzeichnis muss auf gemountetem
    Blockgerät mit ext4/xfs/ntfs liegen; Root-, Live- und Pseudo-Quellen sind verboten.

    Raises:
        BackupTargetValidationError: Backup darf nicht starten.
    """
    raw = Path(archive_path)
    try:
        resolved = raw.resolve()
    except OSError as e:
        raise BackupTargetValidationError(K_BACKUP_TARGET_PARENT_MISSING, str(e)) from e

    write_base = resolved.parent
    if not write_base.exists() or not write_base.is_dir():
        raise BackupTargetValidationError(
            K_BACKUP_TARGET_PARENT_MISSING,
            str(write_base),
        )

    mount_info = resolve_mount_source_for_path(write_base, runner=runner)
    tnorm = (mount_info.get("target") or "").rstrip("/") or "/"
    if tnorm == "/":
        raise BackupTargetValidationError(
            K_BACKUP_TARGET_ROOT_FILESYSTEM,
            str(write_base),
        )

    fst = (mount_info.get("fstype") or "").strip().lower()
    source_s = (mount_info.get("resolved_source") or "").strip()
    reason_s = (mount_info.get("reason") or "").strip()
    if not source_s:
        if reason_s == "findmnt_t_no_entries":
            raise BackupTargetValidationError(
                K_BACKUP_TARGET_NOT_MOUNTED,
                str(write_base),
            )
        if fst in _LIVE_FSTYPES:
            raise BackupTargetValidationError(
                K_BACKUP_TARGET_LIVE_FILESYSTEM,
                fst,
            )
        detail = (mount_info.get("mount_source_seen") or "(empty)") + " | " + (
            mount_info.get("reason") or "unknown"
        )
        raise BackupTargetValidationError(
            K_BACKUP_TARGET_NON_BLOCK_SOURCE,
            detail,
        )

    if fst in _LIVE_FSTYPES:
        raise BackupTargetValidationError(
            K_BACKUP_TARGET_LIVE_FILESYSTEM,
            fst,
        )

    if fst not in _ALLOWED_BACKUP_FSTYPES:
        raise BackupTargetValidationError(
            K_BACKUP_TARGET_FILESYSTEM_NOT_PERMITTED,
            fst or "(unknown)",
        )

    try:
        validate_write_target(write_base, runner=runner)
    except WriteTargetProtectionError as e:
        raise BackupTargetValidationError(
            K_BACKUP_TARGET_WRITE_PROTECTED,
            f"{e.diagnosis_id}: {e}",
        ) from e

    assert_backup_target_dir_writable(write_base)


def assert_backup_target_dir_writable(write_base: Path) -> None:
    """
    Effektiver Schreibtest im Zielverzeichnis (berücksichtigt Supplementary Groups).

    Raises:
        BackupTargetValidationError: Verzeichnis fehlt oder Schreiben schlägt fehl.
    """
    if not write_base.exists() or not write_base.is_dir():
        raise BackupTargetValidationError(
            K_BACKUP_TARGET_PARENT_MISSING,
            str(write_base),
        )
    probe = write_base / f".setuphelfer-wtest-{os.getpid()}-{os.urandom(4).hex()}"
    fd: int | None = None
    try:
        fd = os.open(str(probe), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except OSError as e:
        detail = str(e)
        try:
            gname = (os.environ.get("SETUPHELFER_BACKUP_GROUP") or "setuphelfer").strip() or "setuphelfer"
            st = _os_stat(write_base, follow_symlinks=False)
            grec = grp.getgrnam(gname)
            if grec is not None and st.st_gid != grec.gr_gid:
                detail = (
                    f"{write_base}: nicht beschreibbar; Verzeichnis gehört nicht der Gruppe "
                    f"'{gname}' (ist gid {st.st_gid}, erwartet {grec.gr_gid}). Ursprünglicher Fehler: {e}"
                )
        except (KeyError, OSError, TypeError):
            pass
        raise BackupTargetValidationError(K_BACKUP_TARGET_NOT_WRITABLE, detail) from e
    finally:
        if fd is not None and fd >= 0:
            try:
                os.close(fd)
            except OSError:
                pass
        try:
            probe.unlink(missing_ok=True)
        except OSError:
            pass


__all__ = [
    "BackupTargetValidationError",
    "assert_backup_target_dir_writable",
    "classify_devices",
    "detect_block_devices",
    "detect_filesystems",
    "validate_backup_target",
]
