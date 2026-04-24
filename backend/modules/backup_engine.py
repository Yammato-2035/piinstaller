"""
Backup-Engine: Rohabbild, Dateiarchiv, Manifest (Checksummen, sfdisk, Metadaten).
Alle Pfade und Blockgeräte über Allowlists; offlinefähig.
"""

from __future__ import annotations

import hashlib
import json
import os
import posixpath
import shutil
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
    K_BACKUP_FAILED_MANIFEST_MISSING,
    K_DD_FAILED,
    K_MANIFEST_WRITE_FAILED,
    K_OPERATION_OK,
    K_OUTPUT_NOT_ALLOWED,
    K_SFDISK_FAILED,
    K_TAR_FAILED,
    tr,
)
from core.safe_device import WriteTargetProtectionError, validate_write_target
from modules.storage_detection import BackupTargetValidationError, validate_backup_target

MANIFEST_NAME = "MANIFEST.json"
MANIFEST_KIND = "setuphelfer-backup-manifest"
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


def _public_manifest_entry(ent: Mapping[str, Any]) -> dict[str, Any]:
    """Nur stabile Felder für MANIFEST.json (kein source_path, keine internen Keys)."""
    typ = str(ent.get("type") or "file")
    out: dict[str, Any] = {"path": str(ent.get("path") or ""), "type": typ}
    if typ == "file":
        if ent.get("size") is not None:
            out["size"] = str(ent.get("size"))
        if ent.get("sha256"):
            out["sha256"] = str(ent.get("sha256"))
    elif typ == "symlink":
        if ent.get("link_target") is not None:
            out["link_target"] = str(ent.get("link_target"))
    elif typ == "hardlink":
        if ent.get("link_target") is not None:
            out["link_target"] = str(ent.get("link_target"))
    elif typ == "dir":
        pass
    return out


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

    Öffentliches Schema: ``entries`` (Liste von Objekten mit path/type/…),
    ``created_at``, ``skipped`` (konsolidiert). Legacy-Reader können
    ``manifest.get("entries") or manifest.get("files")`` nutzen.
    """
    raw_entries: list[dict[str, Any]] = []
    if backup_entries is not None:
        raw_entries.extend(dict(e) for e in backup_entries)
    else:
        for raw in file_paths or []:
            p = Path(raw)
            if not p.is_file():
                continue
            resolved = str(p.absolute())
            arc_path = archive_paths.get(resolved) if archive_paths else None
            st = os.lstat(p)
            raw_entries.append(
                {
                    "path": arc_path or resolved,
                    "source_path": resolved,
                    "type": "file",
                    "sha256": _sha256_file(p),
                    "size": str(st.st_size),
                }
            )
    entries = [_public_manifest_entry(e) for e in raw_entries]
    skipped_list: list[dict[str, Any]] = []
    for s in skipped_inputs or []:
        skipped_list.append({"kind": "superseded_input", "path": str(s)})
    for d in skipped_members or []:
        row = dict(d)
        row.setdefault("kind", "skipped_member")
        skipped_list.append(row)

    layout = ""
    if partition_device is not None:
        validate_write_target(partition_device, runner=runner)
        dev = str(partition_device)
        r = _run_capture(["sfdisk", "-d", dev], runner=runner, timeout=120)
        if r.returncode != 0:
            raise RuntimeError(tr(K_SFDISK_FAILED))
        layout = r.stdout or ""

    created = datetime.now(timezone.utc).isoformat()
    manifest: dict[str, Any] = {
        "version": 1,
        "kind": MANIFEST_KIND,
        "created_at": created,
        "entries": entries,
        "skipped": skipped_list,
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
    try:
        validate_write_target(target_device, runner=runner)
    except WriteTargetProtectionError as e:
        return ImageBackupResult(False, None, K_DD_FAILED, f"{e.diagnosis_id}: {e}")
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

    Vor dem Packen: ``validate_backup_target`` (Mount/Gerät/Dateisystem) für
    ``archive_path``; bei Verstoß Abbruch mit i18n-Schlüssel, kein Archiv.
    """
    assert_paths_allowed(paths, allowed_source_prefixes)
    arch = Path(archive_path)
    _assert_output_allowed(arch, allowed_output_prefixes)

    try:
        validate_backup_target(arch, runner=runner)
    except BackupTargetValidationError as e:
        msg = tr(e.message_key)
        detail = f"{msg}: {e.detail}" if e.detail else msg
        return FileBackupResult(False, None, None, e.message_key, detail)

    try:
        members, skipped_inputs, skipped_special = _collect_archive_members(paths)
        backup_entries: list[dict[str, Any]] = []
        for src, arc, kind in members:
            src_abs = str(src.absolute())
            if kind == "file":
                st = os.lstat(src)
                backup_entries.append(
                    {
                        "path": arc,
                        "source_path": src_abs,
                        "type": "file",
                        "sha256": _sha256_file(src),
                        "size": str(st.st_size),
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

        if not archive_contains_manifest(arch):
            try:
                arch.unlink()
            except OSError:
                pass
            return FileBackupResult(
                False,
                None,
                None,
                K_BACKUP_FAILED_MANIFEST_MISSING,
                tr(K_BACKUP_FAILED_MANIFEST_MISSING),
            )

        return FileBackupResult(True, str(arch), manifest, K_OPERATION_OK, None)
    except Exception as e:
        try:
            if arch.exists():
                arch.unlink()
        except OSError:
            pass
        return FileBackupResult(False, None, None, K_TAR_FAILED, f"{tr(K_TAR_FAILED)}: {e!s}")


def write_manifest_to_file(manifest: Mapping[str, Any], path: str | Path) -> tuple[bool, str | None]:
    """Hilfsfunktion: Manifest als JSON schreiben (prüfbarer Schritt)."""
    try:
        Path(path).write_text(json.dumps(dict(manifest), indent=2), encoding="utf-8")
        return True, None
    except OSError as e:
        return False, f"{tr(K_MANIFEST_WRITE_FAILED)}: {e!s}"


def _gnu_meta_tar_types() -> set[int]:
    out: set[int] = set()
    for _attr in ("GNUTYPE_LONGNAME", "GNUTYPE_LONGLINK", "GNUTYPE_SPARSE"):
        if hasattr(tarfile, _attr):
            out.add(getattr(tarfile, _attr))
    return out


def _norm_tar_arcname(name: str) -> str:
    n = (name or "").strip()
    while n.startswith("./"):
        n = n[2:]
    return n.lstrip("/")


def archive_contains_manifest(archive_path: str | Path) -> bool:
    """True, wenn das Archiv ein lesbares Mitglied ``MANIFEST.json`` enthält (Pfad-normalisiert)."""
    p = Path(archive_path)
    if not p.is_file():
        return False
    try:
        with tarfile.open(p, "r:*") as tf:
            for raw in tf.getnames():
                if _norm_tar_arcname(raw) == MANIFEST_NAME:
                    return True
    except (OSError, tarfile.TarError, EOFError):
        return False
    return False


def _tar_member_path_unsafe(name: str) -> bool:
    n = name.lstrip("./")
    if not n:
        return True
    if n.startswith("/") or posixpath.isabs(n):
        return True
    norm = posixpath.normpath(n)
    if norm in {".", ".."} or norm.startswith("../"):
        return True
    if "/../" in f"/{norm}/":
        return True
    return False


def embed_manifest_in_tar_gz(archive_path: str | Path) -> tuple[bool, str | None]:
    """
    Liest ein bestehendes .tar.gz (z. B. klassisches Root-Backup per ``tar -czf``),
    erzeugt ein MANIFEST.json aus den Archiv-Metadaten (TarInfo wie lstat; SHA-256
    für reguläre Dateien per Stream aus dem Archiv) und schreibt ein neues Archiv
    (MANIFEST.json zuerst, dann alle bisherigen Mitglieder außer einer vorhandenen
    MANIFEST.json). Temporäre Dateien liegen unter ``tempfile.gettempdir()`` (typisch
    ``/tmp``), damit der Dienst-User auch schreiben kann, wenn das Archiv z. B. unter
    ``/mnt/…`` (root:root) liegt; abschließend per ``shutil.move`` an den Zielpfad.
    """
    path = Path(archive_path)
    if not path.is_file():
        return False, "archive not found"
    gnu_skip = _gnu_meta_tar_types()

    def _embed_temp_base() -> Path:
        for d in (path.parent, Path(tempfile.gettempdir())):
            try:
                if d.is_dir() and os.access(d, os.W_OK | os.X_OK):
                    return d
            except OSError:
                continue
        return Path(tempfile.gettempdir())

    tmp_dir = _embed_temp_base()
    tmp_path = tmp_dir / f"setuphelfer.embed.{os.getpid()}.{path.name}.tmp"

    def pass1_build_entries() -> tuple[list[dict[str, Any]], str | None]:
        entries: list[dict[str, Any]] = []
        try:
            with tarfile.open(path, "r:gz") as tf:
                for m in tf.getmembers():
                    if m.type in gnu_skip:
                        continue
                    name_raw = m.name or ""
                    # Root-Backups (tar -czf … /) enthalten oft ein Mitglied „.“ — wie im Restore überspringen.
                    if (name_raw or "").strip() in (".", "./"):
                        continue
                    if _tar_member_path_unsafe(name_raw):
                        return [], f"unsafe archive member name: {name_raw!r}"
                    arc = _norm_tar_arcname(name_raw)
                    if not arc or arc == MANIFEST_NAME:
                        continue
                    if m.isdir():
                        entries.append({"path": arc, "type": "dir"})
                    elif m.issym():
                        entries.append(
                            {
                                "path": arc,
                                "type": "symlink",
                                "link_target": m.linkname or "",
                            }
                        )
                    elif m.islnk() and not m.issym():
                        entries.append(
                            {
                                "path": arc,
                                "type": "hardlink",
                                "link_target": m.linkname or "",
                            }
                        )
                    elif m.isfile():
                        h = hashlib.sha256()
                        fobj = tf.extractfile(m)
                        if fobj is None:
                            return [], f"cannot read archive member: {arc!r}"
                        try:
                            for chunk in iter(lambda: fobj.read(1024 * 1024), b""):
                                h.update(chunk)
                        finally:
                            fobj.close()
                        entries.append(
                            {
                                "path": arc,
                                "type": "file",
                                "size": str(m.size),
                                "sha256": h.hexdigest(),
                            }
                        )
                    elif getattr(tarfile, "CONTTYPE", None) is not None and m.type == tarfile.CONTTYPE:
                        continue
                    elif m.isdev() or m.isfifo():
                        return [], f"unsupported member for manifest ingest: {arc!r}"
                    else:
                        return [], f"unsupported tar type for member: {arc!r}"
        except (OSError, tarfile.TarError) as e:
            return [], str(e)
        return entries, None

    entries, err = pass1_build_entries()
    if err:
        return False, err

    skipped: list[dict[str, Any]] = []
    manifest_body = create_manifest(
        None,
        skipped_inputs=[],
        skipped_members=skipped,
        backup_entries=entries,
        partition_device=None,
        runner=None,
    )

    try:
        if tmp_path.exists():
            tmp_path.unlink()
    except OSError:
        pass

    try:
        with tempfile.TemporaryDirectory(prefix="setuphelfer_mf_", dir=str(tmp_dir)) as tdir:
            man_path = Path(tdir) / MANIFEST_NAME
            man_path.write_text(json.dumps(manifest_body, indent=2), encoding="utf-8")

            with tarfile.open(path, "r:gz") as src, tarfile.open(tmp_path, "w:gz") as dst:
                dst.add(man_path, arcname=MANIFEST_NAME)
                for m in src.getmembers():
                    if m.type in gnu_skip:
                        continue
                    arc = _norm_tar_arcname(m.name or "")
                    if not arc or arc == MANIFEST_NAME:
                        continue
                    if m.isdir() or m.issym():
                        dst.addfile(m)
                    else:
                        fobj = src.extractfile(m)
                        dst.addfile(m, fobj)
    except (OSError, tarfile.TarError) as e:
        try:
            if tmp_path.exists():
                tmp_path.unlink()
        except OSError:
            pass
        return False, str(e)

    try:
        path.unlink(missing_ok=True)
        if tmp_path.resolve().parent == path.resolve().parent:
            os.replace(tmp_path, path)
        else:
            shutil.move(str(tmp_path), str(path))
    except OSError as e:
        try:
            if tmp_path.exists():
                tmp_path.unlink()
        except OSError:
            pass
        return False, str(e)

    if not archive_contains_manifest(path):
        try:
            path.unlink()
        except OSError:
            pass
        return False, "MANIFEST.json missing after embed rebuild"

    return True, None


__all__ = [
    "MANIFEST_NAME",
    "MANIFEST_KIND",
    "archive_contains_manifest",
    "create_image_backup",
    "create_file_backup",
    "create_manifest",
    "embed_manifest_in_tar_gz",
    "write_manifest_to_file",
    "ImageBackupResult",
    "FileBackupResult",
]
