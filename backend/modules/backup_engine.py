"""
Backup-Engine: Rohabbild, Dateiarchiv, Manifest (Checksummen, sfdisk, Metadaten).
Alle Pfade und Blockgeräte über Allowlists; offlinefähig.
"""

from __future__ import annotations

import hashlib
import json
import os
import stat
import platform
import subprocess
import sys
import tarfile
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from core.backup_path_allowlist import assert_paths_allowed, path_under_any_prefix
from core.backup_recovery_i18n import (
    K_DD_FAILED,
    K_MANIFEST_WRITE_FAILED,
    K_OPERATION_OK,
    K_OUTPUT_NOT_ALLOWED,
    K_SFDISK_FAILED,
    K_TAR_FAILED,
    tr,
)
from core.block_device_allowlist import assert_allowed_block_device

MANIFEST_NAME = "MANIFEST.json"
META_OS_RELEASE_MAX = 65536


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _read_os_release_limited() -> str:
    """Kontrolliertes Lesen für Metadaten (kein allgemeiner Backup-Pfad)."""
    p = Path("/etc/os-release")
    if not p.is_file():
        return ""
    try:
        return p.read_text(encoding="utf-8", errors="replace")[:META_OS_RELEASE_MAX]
    except OSError:
        return ""


def _run_capture(
    argv: list[str],
    runner: Callable[..., subprocess.CompletedProcess[str]] | None = None,
    timeout: int = 3600,
) -> subprocess.CompletedProcess[str]:
    run = runner or subprocess.run
    return run(
        argv,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )


def _to_archive_path(path: Path) -> str:
    """Archiv-Pfad ohne Symlink-Auflösung (logischer Pfad wie auf dem Quellsystem)."""
    rp = path.absolute()
    parts = list(rp.parts)
    if parts and parts[0] == "/":
        parts = parts[1:]
    rel = Path(*parts)
    rel_str = rel.as_posix().lstrip("/")
    if not rel_str or rel_str in {".", ".."}:
        raise ValueError("Invalid archive path")
    if "/../" in f"/{rel_str}/" or rel_str.startswith("../"):
        raise ValueError("Path traversal is not allowed in archive path")
    return rel_str


def _iter_top_level_sources(paths: Sequence[str | Path]) -> tuple[list[Path], list[str]]:
    resolved: list[Path] = []
    skipped: list[str] = []
    for raw in paths:
        rp = Path(raw).absolute()
        if not rp.exists():
            raise ValueError(f"Backup source does not exist: {rp}")
        if rp in resolved:
            continue
        resolved.append(rp)

    selected: list[Path] = []
    for rp in sorted(resolved, key=lambda p: (len(p.parts), str(p))):
        if any(rp != base and rp.is_relative_to(base) for base in selected):
            skipped.append(str(rp))
            continue
        selected.append(rp)
    return selected, skipped


def _walk_tree_no_follow(root: Path) -> list[Path]:
    """Alle Einträge unter root (ohne root selbst), ohne durch Symlink-Verzeichnisse zu wandern."""
    out: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(root, topdown=True, followlinks=False):
        base = Path(dirpath)
        for dn in dirnames:
            out.append(base / dn)
        for fn in filenames:
            out.append(base / fn)
    return sorted(out)


def _backup_entry_kind(path: Path) -> str | None:
    """Klassifiziert nur via lstat (kein Folgen von Symlinks)."""
    try:
        st = os.lstat(path)
    except OSError:
        return None
    if stat.S_ISLNK(st.st_mode):
        return "symlink"
    if stat.S_ISDIR(st.st_mode):
        return "dir"
    if stat.S_ISREG(st.st_mode):
        return "file"
    return None


def _collect_archive_members(
    paths: Sequence[str | Path],
) -> tuple[list[tuple[Path, str, str]], list[str], list[dict[str, str]]]:
    """Liefert (src, arcname, kind) mit kind in file|dir|symlink sowie skipped_special-Einträge."""
    top_level_sources, skipped = _iter_top_level_sources(paths)
    members: list[tuple[Path, str, str]] = []
    seen_arcnames: dict[str, Path] = {}
    skipped_special: list[dict[str, str]] = []

    def add_member(src: Path, *, kind: str) -> None:
        arc = _to_archive_path(src)
        other = seen_arcnames.get(arc)
        if other is not None and other != src:
            raise ValueError(f"Archive path collision detected: {arc} ({other} vs {src})")
        seen_arcnames[arc] = src
        members.append((src, arc, kind))

    for src in top_level_sources:
        top_kind = _backup_entry_kind(src)
        if top_kind == "symlink":
            add_member(src, kind="symlink")
            continue
        if top_kind == "file":
            add_member(src, kind="file")
            continue
        if top_kind == "dir":
            add_member(src, kind="dir")
            for child in _walk_tree_no_follow(src):
                ck = _backup_entry_kind(child)
                if ck == "symlink":
                    add_member(child, kind="symlink")
                elif ck == "dir":
                    add_member(child, kind="dir")
                elif ck == "file":
                    add_member(child, kind="file")
                else:
                    skipped_special.append(
                        {
                            "path": str(child.absolute()),
                            "archive_path": _to_archive_path(child),
                            "reason": "unsupported_special_file",
                        }
                    )
            continue
        raise ValueError(f"Unsupported backup source type: {src}")

    return members, skipped, skipped_special


def _system_metadata() -> dict[str, Any]:
    u = platform.uname()
    return {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "uname": {
            "system": u.system,
            "node": u.node,
            "release": u.release,
            "version": u.version,
            "machine": u.machine,
        },
        "os_release_snippet": _read_os_release_limited(),
    }


def create_manifest(
    file_paths: Sequence[str | Path] | None = None,
    *,
    archive_paths: Mapping[str, str] | None = None,
    skipped_inputs: Sequence[str] | None = None,
    skipped_members: Sequence[Mapping[str, str]] | None = None,
    backup_entries: Sequence[Mapping[str, Any]] | None = None,
    partition_device: str | Path | None = None,
    runner: Callable[..., subprocess.CompletedProcess[str]] | None = None,
) -> dict[str, Any]:
    """
    Erzeugt Manifest-Dict mit sha256, optional sfdisk -d, System-Metadaten.

    Entweder klassisch über ``file_paths`` + ``archive_paths`` oder über
    ``backup_entries`` (Dateien, Verzeichnisse, Symlinks mit ``type``).
    """
    entries: list[dict[str, Any]] = []
    if backup_entries is not None:
        entries.extend(dict(e) for e in backup_entries)
    else:
        for raw in file_paths or []:
            p = Path(raw)
            if not p.is_file():
                continue
            resolved = str(p.absolute())
            arc_path = archive_paths.get(resolved) if archive_paths else None
            entries.append(
                {
                    "path": arc_path or resolved,
                    "source_path": resolved,
                    "type": "file",
                    "sha256": _sha256_file(p),
                    "size": str(p.stat().st_size),
                }
            )
    layout = ""
    if partition_device is not None:
        assert_allowed_block_device(partition_device)
        dev = str(partition_device)
        r = _run_capture(["sfdisk", "-d", dev], runner=runner, timeout=120)
        if r.returncode != 0:
            raise RuntimeError(tr(K_SFDISK_FAILED))
        layout = r.stdout or ""

    manifest: dict[str, Any] = {
        "version": 1,
        "kind": "setuphelfer-backup-manifest",
        "files": entries,
        "skipped_inputs": list(skipped_inputs or []),
        "skipped_members": list(skipped_members or []),
        "partition_layout_sfdisk_d": layout,
        "system": _system_metadata(),
    }
    return manifest


def _assert_output_allowed(output_file: Path, allowed_prefixes: Sequence[Path]) -> None:
    outp = output_file if output_file.is_absolute() else Path.cwd() / output_file
    parent = outp.parent
    if not path_under_any_prefix(parent, allowed_prefixes):
        raise ValueError(tr(K_OUTPUT_NOT_ALLOWED))


@dataclass
class ImageBackupResult:
    ok: bool
    output_path: str | None
    message_key: str
    detail: str | None = None


def create_image_backup(
    target_device: str | Path,
    output_file: str | Path,
    *,
    allowed_output_prefixes: Sequence[Path],
    runner: Callable[..., subprocess.CompletedProcess[str]] | None = None,
    dd_bs: str = "4M",
) -> ImageBackupResult:
    """
    Rohabbild mit dd (nur allowlisted Blockgeräte). output_file muss unter allowed_output_prefixes liegen.
    """
    assert_allowed_block_device(target_device)
    out = Path(output_file)
    _assert_output_allowed(out, allowed_output_prefixes)

    dev = str(target_device)
    argv = [
        "dd",
        f"if={dev}",
        f"of={out}",
        f"bs={dd_bs}",
        "conv=fsync",
        "status=progress",
    ]
    r = _run_capture(argv, runner=runner, timeout=86400)
    if r.returncode != 0:
        err = (r.stderr or r.stdout or "")[:2000]
        return ImageBackupResult(False, str(out) if out.parent.exists() else None, K_DD_FAILED, err)
    return ImageBackupResult(True, str(out), K_OPERATION_OK, None)


@dataclass
class FileBackupResult:
    ok: bool
    archive_path: str | None
    manifest: dict[str, Any] | None
    message_key: str
    detail: str | None = None


def create_file_backup(
    paths: Sequence[str | Path],
    *,
    archive_path: str | Path,
    allowed_source_prefixes: Sequence[Path],
    allowed_output_prefixes: Sequence[Path],
    partition_device: str | None = None,
    runner: Callable[..., subprocess.CompletedProcess[str]] | None = None,
) -> FileBackupResult:
    """
    packt Dateien in tar.gz; Manifest enthält Checksummen und optional sfdisk.
    """
    assert_paths_allowed(paths, allowed_source_prefixes)
    arch = Path(archive_path)
    _assert_output_allowed(arch, allowed_output_prefixes)

    try:
        members, skipped_inputs, skipped_special = _collect_archive_members(paths)
        backup_entries: list[dict[str, Any]] = []
        for src, arc, kind in members:
            src_abs = str(src.absolute())
            if kind == "file":
                backup_entries.append(
                    {
                        "path": arc,
                        "source_path": src_abs,
                        "type": "file",
                        "sha256": _sha256_file(src),
                        "size": str(src.stat().st_size),
                    }
                )
            elif kind == "symlink":
                backup_entries.append(
                    {
                        "path": arc,
                        "source_path": src_abs,
                        "type": "symlink",
                        "link_target": os.readlink(src),
                    }
                )
            elif kind == "dir":
                backup_entries.append({"path": arc, "source_path": src_abs, "type": "dir"})
            else:
                raise ValueError(f"Unknown backup member kind: {kind}")

        manifest = create_manifest(
            None,
            skipped_inputs=skipped_inputs,
            skipped_members=skipped_special,
            backup_entries=backup_entries,
            partition_device=partition_device,
            runner=runner,
        )

        with tempfile.TemporaryDirectory(prefix="setuphelfer_bak_") as tmp:
            tdir = Path(tmp)
            man_path = tdir / MANIFEST_NAME
            man_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

            with tarfile.open(arch, "w:gz") as tf:
                tf.add(man_path, arcname=MANIFEST_NAME)
                for src, arc, _kind in members:
                    tf.add(src, arcname=arc, recursive=False)

        return FileBackupResult(True, str(arch), manifest, K_OPERATION_OK, None)
    except Exception as e:
        return FileBackupResult(False, None, None, K_TAR_FAILED, f"{tr(K_TAR_FAILED)}: {e!s}")


def write_manifest_to_file(manifest: Mapping[str, Any], path: str | Path) -> tuple[bool, str | None]:
    """Hilfsfunktion: Manifest als JSON schreiben (prüfbarer Schritt)."""
    try:
        Path(path).write_text(json.dumps(dict(manifest), indent=2), encoding="utf-8")
        return True, None
    except OSError as e:
        return False, f"{tr(K_MANIFEST_WRITE_FAILED)}: {e!s}"


__all__ = [
    "MANIFEST_NAME",
    "create_image_backup",
    "create_file_backup",
    "create_manifest",
    "write_manifest_to_file",
    "ImageBackupResult",
    "FileBackupResult",
]
