"""
Backup-Engine: Rohabbild, Dateiarchiv, Manifest (Checksummen, sfdisk, Metadaten).
Alle Pfade und Blockgeräte über Allowlists; offlinefähig.
"""

from __future__ import annotations

import hashlib
import json
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
        entries.append(
            {
                "path": str(p),
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

    manifest = create_manifest(paths, partition_device=partition_device, runner=runner)

    try:
        with tempfile.TemporaryDirectory(prefix="setuphelfer_bak_") as tmp:
            tdir = Path(tmp)
            man_path = tdir / MANIFEST_NAME
            man_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

            with tarfile.open(arch, "w:gz") as tf:
                tf.add(man_path, arcname=MANIFEST_NAME)
                for raw in paths:
                    p = Path(raw).resolve()
                    if p.is_file():
                        tf.add(p, arcname=p.name)

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
