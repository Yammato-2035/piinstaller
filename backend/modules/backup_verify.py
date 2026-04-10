"""
Verify-Engine: Basisprüfung und Tiefenprüfung (Extraktion, Lesbarkeit, optional Loop+mount).
"""

from __future__ import annotations

import json
import os
import subprocess
import tarfile
import tempfile
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

VERIFY_STAGING_SUBDIR = "setuphelfer_verify"


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
        for ent in files:
            if not isinstance(ent, dict):
                continue
            name = ent.get("path") or ent.get("name")
            expect = ent.get("sha256")
            if not name or not expect:
                continue
            fp = Path(name)
            if not fp.is_file():
                alt = staging / fp.name
                fp = alt if alt.is_file() else fp
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
