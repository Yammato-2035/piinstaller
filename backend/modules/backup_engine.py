"""
Backup-Engine: Rohabbild, Dateiarchiv, Manifest (Checksummen, sfdisk, Metadaten).
Alle Pfade und Blockgeräte über Allowlists; offlinefähig.
"""

from __future__ import annotations

import hashlib
import json
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
    rp = path.resolve()
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
        rp = Path(raw).resolve()
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


def _collect_archive_members(paths: Sequence[str | Path]) -> tuple[list[tuple[Path, str, bool]], list[str]]:
    top_level_sources, skipped = _iter_top_level_sources(paths)
    members: list[tuple[Path, str, bool]] = []
    seen_arcnames: dict[str, Path] = {}

    def add_member(src: Path, *, is_dir: bool) -> None:
        if src.is_symlink():
            raise ValueError(f"Symlink source is not supported: {src}")
        mode = src.stat().st_mode
        if is_dir:
            if not stat.S_ISDIR(mode):
                raise ValueError(f"Expected directory source: {src}")
        elif not stat.S_ISREG(mode):
            raise ValueError(f"Special file is not supported: {src}")

        arc = _to_archive_path(src)
        other = seen_arcnames.get(arc)
        if other is not None and other != src:
            raise ValueError(f"Archive path collision detected: {arc} ({other} vs {src})")
        seen_arcnames[arc] = src
        members.append((src, arc, is_dir))

    for src in top_level_sources:
        if src.is_file():
            add_member(src, is_dir=False)
            continue
        if src.is_dir():
            add_member(src, is_dir=True)
            for child in sorted(src.rglob("*")):
                if child.is_symlink():
                    raise ValueError(f"Symlink source is not supported: {child}")
                if child.is_dir():
                    add_member(child, is_dir=True)
                elif child.is_file():
                    add_member(child, is_dir=False)
                else:
                    raise ValueError(f"Special file is not supported: {child}")
            continue
        raise ValueError(f"Unsupported backup source type: {src}")

    return members, skipped


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
    file_paths: Sequence[str | Path],
    *,
    archive_paths: Mapping[str, str] | None = None,
    skipped_inputs: Sequence[str] | None = None,
    partition_device: str | Path | None = None,
    runner: Callable[..., subprocess.CompletedProcess[str]] | None = None,
) -> dict[str, Any]:
    """
    Erzeugt Manifest-Dict mit sha256, optional sfdisk -d, System-Metadaten.
    """
    entries: list[dict[str, str]] = []
    for raw in file_paths:
        p = Path(raw)
        if not p.is_file():
            continue
        resolved = str(p.resolve())
        arc_path = archive_paths.get(resolved) if archive_paths else None
        entries.append(
            {
                "path": arc_path or resolved,
                "source_path": resolved,
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
        members, skipped_inputs = _collect_archive_members(paths)
        file_members = [src for (src, _, is_dir) in members if not is_dir]
        archive_paths = {str(src.resolve()): arc for (src, arc, is_dir) in members if not is_dir}
        manifest = create_manifest(
            file_members,
            archive_paths=archive_paths,
            skipped_inputs=skipped_inputs,
            partition_device=partition_device,
            runner=runner,
        )

        with tempfile.TemporaryDirectory(prefix="setuphelfer_bak_") as tmp:
            tdir = Path(tmp)
            man_path = tdir / MANIFEST_NAME
            man_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

            with tarfile.open(arch, "w:gz") as tf:
                tf.add(man_path, arcname=MANIFEST_NAME)
                for src, arc, is_dir in members:
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
