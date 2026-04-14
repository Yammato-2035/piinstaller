"""
Verify-Engine: Basisprüfung und Tiefenprüfung (Extraktion, Lesbarkeit, optional Loop+mount).
"""

from __future__ import annotations

import json
import os
import posixpath
import subprocess
import tarfile
from pathlib import Path
from typing import Any, Callable

from core.backup_recovery_i18n import (
    K_CHECKSUM_MISMATCH,
    K_EXTRACT_FAILED,
    K_LOOP_FAILED,
    K_MISSING_MANIFEST,
    K_MOUNT_FAILED,
    K_OPERATION_OK,
    tr,
)

from modules.backup_engine import MANIFEST_NAME, _sha256_file
from modules.backup_symlink_safety import tar_symlink_linkname_allowed

VERIFY_STAGING_SUBDIR = "setuphelfer_verify"


def _is_safe_member_name(name: str) -> bool:
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
    n = name.lstrip("./")
    return posixpath.normpath(n)


def _validate_archive_members(tf: tarfile.TarFile) -> tuple[bool, str | None]:
    for m in tf.getmembers():
        if not _is_safe_member_name(m.name):
            return False, f"unsafe path: {m.name}"
        if m.issym():
            if "\x00" in (m.linkname or ""):
                return False, f"unsafe symlink target: {m.name}"
            continue
        if m.islnk() or m.isdev() or m.isfifo():
            return False, f"unsupported member type: {m.name}"
    return True, None


def _manifest_path_to_staging(path_value: str, staging: Path) -> Path:
    p = Path(path_value)
    if p.is_absolute():
        parts = list(p.parts)
        if parts and parts[0] == "/":
            parts = parts[1:]
        p = Path(*parts)
    # Kein resolve(): würde Symlinks im Archiv-Pfad auflösen und z.B. Verifikation von Symlink-Einträgen zerstören.
    target = (staging / p).absolute()
    target.relative_to(staging.absolute())
    return target


def _run(
    argv: list[str],
    runner: Callable[..., subprocess.CompletedProcess[str]] | None = None,
    timeout: int = 600,
) -> subprocess.CompletedProcess[str]:
    run = runner or subprocess.run
    return run(argv, capture_output=True, text=True, timeout=timeout, check=False)


def verify_basic(
    archive_path: str | Path,
    *,
    runner: Callable[..., subprocess.CompletedProcess[str]] | None = None,
) -> tuple[bool, str, str | None]:
    """
    Prüft: Archiv lesbar, MANIFEST.json vorhanden und parsbar, tar-Test.
    """
    p = Path(archive_path)
    if not p.is_file():
        return False, K_MISSING_MANIFEST, str(p)
    try:
        with tarfile.open(p, "r:*") as tf:
            ok_members, err = _validate_archive_members(tf)
            if not ok_members:
                return False, K_EXTRACT_FAILED, err
            names = tf.getnames()
            if MANIFEST_NAME not in names and f"./{MANIFEST_NAME}" not in names:
                return False, K_MISSING_MANIFEST, None
            # Mitglied lesen
            m = tf.extractfile(MANIFEST_NAME) or tf.extractfile(f"./{MANIFEST_NAME}")
            if m is None:
                return False, K_MISSING_MANIFEST, None
            raw = m.read()
            json.loads(raw.decode("utf-8"))
    except Exception as e:
        return False, K_EXTRACT_FAILED, str(e)
    # optional: gzip -t
    if str(p).endswith(".gz"):
        r = _run(["gzip", "-t", str(p)], runner=runner, timeout=60)
        if r.returncode != 0:
            return False, K_EXTRACT_FAILED, (r.stderr or "")[:500]
    return True, K_OPERATION_OK, None


def verify_deep(
    archive_path: str | Path,
    *,
    extract_root: str | Path | None = None,
    verify_checksums: bool = True,
    try_loop_mount_image: bool = False,
    image_glob: str = "*.img",
    runner: Callable[..., subprocess.CompletedProcess[str]] | None = None,
) -> tuple[bool, str, dict[str, Any]]:
    """
    Extrahiert nach extract_root (default /tmp/setuphelfer_verify/<pid>), prüft Checksummen.
    try_loop_mount_image: nur mit CAP_SYS_ADMIN sinnvoll; bei Fehler kein harter Abbruch.
    """
    base = Path(extract_root) if extract_root else Path(os.environ.get("TMPDIR", "/tmp"))
    staging = base / VERIFY_STAGING_SUBDIR / str(os.getpid())
    details: dict[str, Any] = {"staging": str(staging)}
    try:
        staging.mkdir(parents=True, exist_ok=True)
        with tarfile.open(archive_path, "r:*") as tf:
            ok_members, err = _validate_archive_members(tf)
            if not ok_members:
                return False, K_EXTRACT_FAILED, {**details, "error": err}
            try:
                # "tar" erhält Symlinks wie klassisches tar; "data" kann Symlinks materialisieren.
                tf.extractall(path=staging, filter="tar")
            except TypeError:
                try:
                    tf.extractall(path=staging, filter="data")
                except TypeError:
                    tf.extractall(path=staging)
    except Exception as e:
        return False, K_EXTRACT_FAILED, {**details, "error": str(e)}

    man_path = staging / MANIFEST_NAME
    if not man_path.is_file():
        return False, K_MISSING_MANIFEST, details

    try:
        manifest = json.loads(man_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        return False, K_MISSING_MANIFEST, {**details, "error": str(e)}

    files = manifest.get("files") or []
    if verify_checksums and isinstance(files, list):
        staging_root = staging.absolute()
        for ent in files:
            if not isinstance(ent, dict):
                continue
            name = ent.get("path") or ent.get("name")
            if not name:
                continue
            typ = str(ent.get("type") or "file")
            try:
                fp = _manifest_path_to_staging(str(name), staging)
            except ValueError:
                return False, K_CHECKSUM_MISMATCH, {**details, "file": str(name), "error": "path traversal"}

            if typ == "dir":
                if not fp.is_dir():
                    return False, K_CHECKSUM_MISMATCH, {**details, "file": str(name), "error": "expected directory"}
                continue

            if typ == "symlink":
                expect_tgt = ent.get("link_target")
                if expect_tgt is None:
                    return False, K_CHECKSUM_MISMATCH, {**details, "file": str(name), "error": "missing link_target"}
                if not fp.is_symlink():
                    return False, K_CHECKSUM_MISMATCH, {**details, "file": str(name), "error": "expected symlink"}
                got_tgt = os.readlink(fp)
                if got_tgt != str(expect_tgt):
                    return False, K_CHECKSUM_MISMATCH, {
                        **details,
                        "file": str(name),
                        "expected_link": str(expect_tgt),
                        "got_link": got_tgt,
                    }
                if not tar_symlink_linkname_allowed(got_tgt, _safe_member_name(str(name)), staging_root):
                    return False, K_CHECKSUM_MISMATCH, {
                        **details,
                        "file": str(name),
                        "error": "symlink target escapes staging root",
                    }
                continue

            expect = ent.get("sha256")
            if not expect:
                continue
            if not fp.is_file():
                return False, K_CHECKSUM_MISMATCH, {**details, "file": str(name)}
            got = _sha256_file(fp)
            if got.lower() != str(expect).lower():
                return False, K_CHECKSUM_MISMATCH, {**details, "file": str(fp), "expected": expect, "got": got}

    if try_loop_mount_image:
        imgs = list(staging.glob(image_glob))
        for img in imgs[:1]:
            r = _run(["losetup", "-f", "-P", "--show", str(img)], runner=runner, timeout=30)
            if r.returncode != 0:
                details["loop"] = tr(K_LOOP_FAILED)
                break
            loop_dev = (r.stdout or "").strip()
            if not loop_dev:
                details["loop"] = tr(K_LOOP_FAILED)
                break
            mdir = staging / "mnt_ro"
            mdir.mkdir(exist_ok=True)
            mr = _run(["mount", "-o", "ro", loop_dev + "p1", str(mdir)], runner=runner, timeout=30)
            if mr.returncode != 0:
                mr2 = _run(["mount", "-o", "ro", loop_dev, str(mdir)], runner=runner, timeout=30)
                if mr2.returncode != 0:
                    details["mount"] = tr(K_MOUNT_FAILED)
            _run(["losetup", "-d", loop_dev], runner=runner, timeout=30)

    return True, K_OPERATION_OK, details


__all__ = ["verify_basic", "verify_deep", "VERIFY_STAGING_SUBDIR"]
