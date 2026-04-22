"""
Restore-Engine: Partitionstabelle, Rohabbild, Dateien, Bootloader – nur Allowlist-Geräte.
"""

from __future__ import annotations

import posixpath
import subprocess
import tarfile
from pathlib import Path
from typing import Callable, Sequence

from core.backup_path_allowlist import path_under_any_prefix
from core.backup_recovery_i18n import (
    K_BOOTLOADER_FAILED,
    K_OPERATION_OK,
    K_RESTORE_FILES_FAILED,
    K_RESTORE_IMAGE_FAILED,
    K_RESTORE_PT_FAILED,
)
from core.block_device_allowlist import assert_allowed_block_device
from modules.backup_symlink_safety import tar_symlink_linkname_allowed


def _is_tar_root_placeholder(name: str | None) -> bool:
    """Klassische Root-Backups enthalten oft ein Verzeichnismitglied ``.`` / ``./`` — nicht extrahieren."""
    return (name or "").strip() in (".", "./")


def _is_safe_member_name(name: str) -> bool:
    if _is_tar_root_placeholder(name):
        return False
    n = name.lstrip("./")
    if not n:
        return False
    if n.startswith("/") or posixpath.isabs(n):
        return False
    normalized = posixpath.normpath(n)
    if normalized in {".", ".."} or normalized.startswith("../"):
        return False
    return True


def _safe_member_name(name: str) -> str:
    return posixpath.normpath(name.lstrip("./"))

def _run(
    argv: list[str],
    runner: Callable[..., subprocess.CompletedProcess[str]] | None = None,
    timeout: int = 86400,
) -> subprocess.CompletedProcess[str]:
    run = runner or subprocess.run
    return run(argv, capture_output=True, text=True, timeout=timeout, check=False)


def restore_partition_table(
    sfdisk_dump_text: str,
    target_device: str | Path,
    *,
    dry_run: bool = False,
    runner: Callable[..., subprocess.CompletedProcess[str]] | None = None,
) -> tuple[bool, str, str | None]:
    """Schreibt Layout mit sfdisk (Gerät allowlisted)."""
    assert_allowed_block_device(target_device)
    dev = str(target_device)
    if dry_run:
        return True, K_OPERATION_OK, None
    proc = subprocess.Popen(
        ["sfdisk", dev],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    assert proc.stdin is not None
    out, err = proc.communicate(input=sfdisk_dump_text, timeout=120)
    if proc.returncode != 0:
        return False, K_RESTORE_PT_FAILED, (err or out or "")[:2000]
    return True, K_OPERATION_OK, None


def restore_image(
    image_file: str | Path,
    target_device: str | Path,
    *,
    dry_run: bool = False,
    runner: Callable[..., subprocess.CompletedProcess[str]] | None = None,
    dd_bs: str = "4M",
) -> tuple[bool, str, str | None]:
    """dd von Abbild auf Zielgerät (destruktiv)."""
    assert_allowed_block_device(target_device)
    if dry_run:
        return True, K_OPERATION_OK, None
    img = Path(image_file)
    if not img.is_file():
        return False, K_RESTORE_IMAGE_FAILED, str(img)
    dev = str(target_device)
    argv = ["dd", f"if={img}", f"of={dev}", f"bs={dd_bs}", "conv=fsync", "status=progress"]
    r = _run(argv, runner=runner, timeout=86400)
    if r.returncode != 0:
        return False, K_RESTORE_IMAGE_FAILED, (r.stderr or r.stdout or "")[:2000]
    return True, K_OPERATION_OK, None


def restore_files(
    archive_path: str | Path,
    target_directory: str | Path,
    *,
    allowed_target_prefixes: Sequence[Path],
    dry_run: bool = False,
    runner: Callable[..., subprocess.CompletedProcess[str]] | None = None,
) -> tuple[bool, str, str | None]:
    """Entpackt tar.gz unter target_directory (muss unter erlaubten Präfixen liegen)."""
    td = Path(target_directory)
    if not path_under_any_prefix(td, allowed_target_prefixes):
        from core.backup_recovery_i18n import K_PATH_NOT_ALLOWED

        return False, K_PATH_NOT_ALLOWED, str(td)
    if dry_run:
        return True, K_OPERATION_OK, None
    try:
        from modules.backup_engine import MANIFEST_NAME

        td.mkdir(parents=True, exist_ok=True)
        root_resolved = td.absolute()
        with tarfile.open(archive_path, "r:*") as tf:
            allowed_members: list[tarfile.TarInfo] = []
            for member in tf.getmembers():
                if _is_tar_root_placeholder(member.name):
                    continue
                if not _is_safe_member_name(member.name):
                    return False, K_RESTORE_FILES_FAILED, f"unsafe archive path: {member.name}"
                safe_name = _safe_member_name(member.name)
                if safe_name == MANIFEST_NAME:
                    continue
                target_path = (td / safe_name).absolute()
                try:
                    target_path.relative_to(root_resolved.absolute())
                except ValueError:
                    return False, K_RESTORE_FILES_FAILED, f"path traversal detected: {member.name}"

                if member.issym():
                    if "\x00" in (member.linkname or ""):
                        return False, K_RESTORE_FILES_FAILED, f"unsafe symlink target: {member.name}"
                    if not tar_symlink_linkname_allowed(member.linkname or "", safe_name, root_resolved):
                        return False, K_RESTORE_FILES_FAILED, f"symlink target escapes restore root: {member.name}"
                    allowed_members.append(member)
                    continue
                if member.islnk() and not member.issym():
                    if "\x00" in (member.linkname or ""):
                        return False, K_RESTORE_FILES_FAILED, f"unsafe hardlink target: {member.name}"
                    allowed_members.append(member)
                    continue
                if member.isdev() or member.isfifo():
                    return False, K_RESTORE_FILES_FAILED, f"unsupported archive member: {member.name}"
                allowed_members.append(member)
            try:
                tf.extractall(path=td, members=allowed_members, filter="tar")
            except TypeError:
                try:
                    tf.extractall(path=td, members=allowed_members, filter="data")
                except TypeError:
                    tf.extractall(path=td, members=allowed_members)
        return True, K_OPERATION_OK, None
    except Exception as e:
        return False, K_RESTORE_FILES_FAILED, str(e)


def install_bootloader(
    target_device: str | Path,
    *,
    boot_directory: str | Path | None = None,
    dry_run: bool = False,
    runner: Callable[..., subprocess.CompletedProcess[str]] | None = None,
) -> tuple[bool, str, str | None]:
    """
    grub-install auf Zielgerät (nur allowlisted). boot_directory optional (z. B. /mnt/target/boot).
    Kein automatisches Paket-Install – grub muss vorhanden sein.
    """
    assert_allowed_block_device(target_device)
    dev = str(target_device)
    if dry_run:
        return True, K_OPERATION_OK, None
    which = _run(["which", "grub-install"], runner=runner, timeout=10)
    if which.returncode != 0:
        return False, K_BOOTLOADER_FAILED, "grub-install not found"
    argv = ["grub-install", dev]
    if boot_directory is not None:
        argv.extend(["--boot-directory", str(boot_directory)])
    r = _run(argv, runner=runner, timeout=600)
    if r.returncode != 0:
        return False, K_BOOTLOADER_FAILED, (r.stderr or r.stdout or "")[:2000]
    return True, K_OPERATION_OK, None


__all__ = [
    "restore_partition_table",
    "restore_image",
    "restore_files",
    "install_bootloader",
]
