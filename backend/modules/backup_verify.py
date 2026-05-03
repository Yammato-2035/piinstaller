"""
Verify-Engine: Basisprüfung und Tiefenprüfung (Extraktion, Lesbarkeit, optional Loop+mount).
"""

from __future__ import annotations

import json
import os
import posixpath
import subprocess
import tarfile
import hashlib
from pathlib import Path
from typing import Any, Callable

from core.backup_recovery_i18n import (
    K_ARCHIVE_CORRUPT,
    K_EXTRACT_FAILED,
    K_LOOP_FAILED,
    K_MISSING_MANIFEST,
    K_MOUNT_FAILED,
    K_OPERATION_OK,
    K_VERIFY_INTEGRITY_FAILED,
    tr,
)

from modules.backup_engine import MANIFEST_NAME, _norm_tar_arcname, _sha256_file
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
        if m.islnk() and not m.issym():
            if "\x00" in (m.linkname or ""):
                return False, f"unsafe hardlink target: {m.name}"
            continue
        if m.isdev() or m.isfifo():
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


def _gzip_test_archive(p: Path, runner: Callable[..., subprocess.CompletedProcess[str]] | None) -> tuple[bool, str | None]:
    if not str(p).endswith(".gz"):
        return True, None
    r = _run(["gzip", "-t", str(p)], runner=runner, timeout=120)
    if r.returncode != 0:
        return False, ((r.stderr or r.stdout or "") or "")[:500]
    return True, None


def _gnu_skip_types() -> set[int]:
    out: set[int] = set()
    for _attr in ("GNUTYPE_LONGNAME", "GNUTYPE_LONGLINK", "GNUTYPE_SPARSE"):
        if hasattr(tarfile, _attr):
            out.add(getattr(tarfile, _attr))
    return out


def _manifest_row_key(path_value: str) -> str:
    x = _norm_tar_arcname(str(path_value or ""))
    if not x:
        return ""
    return posixpath.normpath(x.rstrip("/"))


def _member_arc_key(name: str | None) -> str:
    x = _norm_tar_arcname(name or "")
    if not x:
        return ""
    return posixpath.normpath(x.rstrip("/"))


def _sha256_archive_payload_without_manifest(archive_path: Path) -> str:
    h = hashlib.sha256()
    with tarfile.open(archive_path, "r:*") as tf:
        for m in tf.getmembers():
            mk = _member_arc_key(m.name)
            if not mk or mk == _manifest_row_key(MANIFEST_NAME):
                continue
            h.update(mk.encode("utf-8", errors="ignore"))
            h.update(b"\0")
            h.update(str(m.type).encode("ascii", errors="ignore"))
            h.update(b"\0")
            h.update(str(m.size).encode("ascii", errors="ignore"))
            h.update(b"\0")
            if m.isfile():
                fobj = tf.extractfile(m)
                if fobj is not None:
                    for chunk in iter(lambda: fobj.read(1024 * 1024), b""):
                        h.update(chunk)
            elif m.issym() or m.islnk():
                h.update((m.linkname or "").encode("utf-8", errors="ignore"))
    return h.hexdigest()


def verify_basic(
    archive_path: str | Path,
    *,
    runner: Callable[..., subprocess.CompletedProcess[str]] | None = None,
) -> tuple[bool, str, str | None]:
    """
    Prüft: gzip-Integrität (falls .gz), Archiv lesbar, MANIFEST.json vorhanden und parsbar.
    """
    p = Path(archive_path)
    if not p.is_file():
        return False, K_MISSING_MANIFEST, str(p)
    gz_ok, gz_err = _gzip_test_archive(p, runner)
    if not gz_ok:
        return False, K_ARCHIVE_CORRUPT, gz_err
    try:
        with tarfile.open(p, "r:*") as tf:
            ok_members, err = _validate_archive_members(tf)
            if not ok_members:
                return False, K_EXTRACT_FAILED, err
            names = tf.getnames()
            if MANIFEST_NAME not in names and f"./{MANIFEST_NAME}" not in names:
                if not any(_norm_tar_arcname(n) == MANIFEST_NAME for n in names):
                    return False, K_MISSING_MANIFEST, None
            m = tf.extractfile(MANIFEST_NAME) or tf.extractfile(f"./{MANIFEST_NAME}")
            if m is None:
                for cand in tf.getmembers():
                    if _norm_tar_arcname(cand.name) == MANIFEST_NAME:
                        m = tf.extractfile(cand)
                        break
            if m is None:
                return False, K_MISSING_MANIFEST, None
            raw = m.read()
            json.loads(raw.decode("utf-8"))
    except Exception as e:
        return False, K_EXTRACT_FAILED, str(e)
    return True, K_OPERATION_OK, None


def verify_deep(
    archive_path: str | Path,
    *,
    extract_root: str | Path | None = None,
    verify_checksums: bool = True,
    try_loop_mount_image: bool = False,
    strict_archive_manifest: bool = False,
    image_glob: str = "*.img",
    runner: Callable[..., subprocess.CompletedProcess[str]] | None = None,
) -> tuple[bool, str, dict[str, Any]]:
    """
    Extrahiert nach extract_root (default /tmp/setuphelfer_verify/<pid>), prüft Checksummen.

    Vor dem Öffnen: ``gzip -t`` bei ``.gz``. Fehler werden in ``details["errors"]`` gesammelt
    (``kind``: missing_file, hash_mismatch, invalid_symlink, invalid_hardlink, archive_extra_member, …).

    ``strict_archive_manifest``: jedes Archiv-Mitglied (außer ``MANIFEST.json`` und GNU-Metadaten)
    muss einen passenden Manifest-Eintrag haben.
    """
    base = Path(extract_root) if extract_root else Path(os.environ.get("TMPDIR", "/tmp"))
    staging = base / VERIFY_STAGING_SUBDIR / str(os.getpid())
    details: dict[str, Any] = {"staging": str(staging), "valid": False, "errors": []}
    ap = Path(archive_path)

    def _fail(key: str, **extra: Any) -> tuple[bool, str, dict[str, Any]]:
        out = {**details, **extra}
        out.setdefault("valid", False)
        out.setdefault("errors", [])
        return False, key, out

    gz_ok, gz_err = _gzip_test_archive(ap, runner)
    if not gz_ok:
        details["errors"] = [{"kind": "gzip_corrupt", "path": str(ap), "detail": gz_err}]
        return _fail(K_ARCHIVE_CORRUPT, gzip_error=gz_err)

    gnu_skip = _gnu_skip_types()
    cont_type = getattr(tarfile, "CONTTYPE", None)

    try:
        staging.mkdir(parents=True, exist_ok=True)
        with tarfile.open(ap, "r:*") as tf:
            ok_members, err = _validate_archive_members(tf)
            if not ok_members:
                details["errors"] = [{"kind": "unsafe_archive_member", "path": None, "detail": err}]
                return _fail(K_EXTRACT_FAILED, error=err)

            arc_keys: set[str] = set()
            manifest_in_tar = False
            for m in tf.getmembers():
                if m.type in gnu_skip:
                    continue
                if cont_type is not None and m.type == cont_type:
                    continue
                mk = _member_arc_key(m.name)
                if not mk:
                    continue
                if mk == _manifest_row_key(MANIFEST_NAME):
                    manifest_in_tar = True
                    continue
                arc_keys.add(mk)

            if not manifest_in_tar:
                details["errors"] = [{"kind": "missing_file", "path": MANIFEST_NAME, "detail": "not in archive"}]
                return _fail(K_MISSING_MANIFEST)

            mfo = tf.extractfile(MANIFEST_NAME) or tf.extractfile(f"./{MANIFEST_NAME}")
            if mfo is None:
                for cand in tf.getmembers():
                    if _norm_tar_arcname(cand.name) == MANIFEST_NAME:
                        mfo = tf.extractfile(cand)
                        break
            if mfo is None:
                details["errors"] = [{"kind": "missing_file", "path": MANIFEST_NAME, "detail": "unreadable"}]
                return _fail(K_MISSING_MANIFEST)
            raw_b = mfo.read()

            try:
                manifest = json.loads(raw_b.decode("utf-8"))
            except json.JSONDecodeError as e:
                details["errors"] = [{"kind": "invalid_manifest_json", "path": MANIFEST_NAME, "detail": str(e)}]
                return _fail(K_MISSING_MANIFEST, error=str(e))

            # Runner-Metadaten prüfen (falls vorhanden): Pflichtfelder + Integrität.
            meta_keys = {"job_id", "backup_type", "source", "backup_dir", "created_at", "completed_at", "archive_size", "hash"}
            if meta_keys.issubset(set(manifest.keys())):
                meta_errors: list[dict[str, Any]] = []
                for k in ("job_id", "backup_type", "source", "backup_dir", "created_at", "completed_at"):
                    v = manifest.get(k)
                    if not isinstance(v, str) or not v.strip():
                        meta_errors.append({"kind": "manifest_metadata_missing", "path": MANIFEST_NAME, "detail": f"missing_or_empty:{k}"})
                try:
                    expected_size = int(str(manifest.get("archive_size") or "0"))
                except ValueError:
                    expected_size = -1
                actual_size = int(ap.stat().st_size)
                if expected_size != actual_size:
                    details["archive_size_note"] = f"archive_size manifest={expected_size} actual={actual_size}"
                mh = str(manifest.get("hash") or "")
                if not mh.startswith("sha256:"):
                    meta_errors.append({"kind": "manifest_metadata_missing", "path": MANIFEST_NAME, "detail": "hash_format"})
                else:
                    actual_payload_hash = _sha256_archive_payload_without_manifest(ap)
                    expected_payload_hash = mh.split(":", 1)[1]
                    if expected_payload_hash != actual_payload_hash:
                        meta_errors.append(
                            {
                                "kind": "hash_mismatch",
                                "path": MANIFEST_NAME,
                                "detail": f"manifest={expected_payload_hash} actual={actual_payload_hash}",
                            }
                        )

                job_id = str(manifest.get("job_id") or "").strip()
                if job_id:
                    status_file = Path("/var/lib/setuphelfer/backup-jobs") / job_id / "status.json"
                    if status_file.exists():
                        try:
                            st = json.loads(status_file.read_text(encoding="utf-8") or "{}")
                            if isinstance(st, dict):
                                if str(st.get("backup_type") or "") and str(st.get("backup_type")) != str(manifest.get("backup_type")):
                                    meta_errors.append({"kind": "manifest_metadata_mismatch", "path": MANIFEST_NAME, "detail": "backup_type_vs_status"})
                                if str(st.get("source") or "") and str(st.get("source")) != str(manifest.get("source")):
                                    meta_errors.append({"kind": "manifest_metadata_mismatch", "path": MANIFEST_NAME, "detail": "source_vs_status"})
                                if str(st.get("backup_dir") or "") and str(st.get("backup_dir")) != str(manifest.get("backup_dir")):
                                    meta_errors.append({"kind": "manifest_metadata_mismatch", "path": MANIFEST_NAME, "detail": "backup_dir_vs_status"})
                        except Exception:
                            pass

                if meta_errors:
                    details["errors"] = meta_errors
                    return _fail(K_VERIFY_INTEGRITY_FAILED, error="manifest_metadata_or_hash_mismatch")

            rows = manifest.get("entries") or manifest.get("files") or []
            manifest_keys: set[str] = set()
            entries_by_path: dict[str, dict[str, Any]] = {}
            if isinstance(rows, list):
                for ent in rows:
                    if not isinstance(ent, dict):
                        continue
                    name = ent.get("path") or ent.get("name")
                    if not name:
                        continue
                    rk = _manifest_row_key(str(name))
                    if rk:
                        manifest_keys.add(rk)
                        entries_by_path[rk] = ent

            errors: list[dict[str, Any]] = []
            if verify_checksums and isinstance(rows, list):
                for ent in rows:
                    if not isinstance(ent, dict):
                        continue
                    name = ent.get("path") or ent.get("name")
                    if not name:
                        continue
                    rk = _manifest_row_key(str(name))
                    typ = str(ent.get("type") or "file")
                    if rk and rk not in arc_keys:
                        errors.append({"kind": "missing_file", "path": str(name), "detail": "manifest entry not in archive"})

                if strict_archive_manifest:
                    for ak in arc_keys:
                        if ak not in manifest_keys:
                            errors.append({"kind": "archive_extra_member", "path": ak, "detail": "no manifest entry"})

            if errors:
                details["errors"] = errors
                details["valid"] = False
                return False, K_VERIFY_INTEGRITY_FAILED, details

            try:
                tf.extractall(path=staging, filter="tar")
            except TypeError:
                try:
                    tf.extractall(path=staging, filter="data")
                except TypeError:
                    tf.extractall(path=staging)
    except Exception as e:
        return _fail(K_EXTRACT_FAILED, error=str(e))

    man_path = staging / MANIFEST_NAME
    if not man_path.is_file():
        details["errors"] = [{"kind": "missing_file", "path": MANIFEST_NAME, "detail": "after extract"}]
        return _fail(K_MISSING_MANIFEST)

    try:
        manifest = json.loads(man_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        details["errors"] = [{"kind": "invalid_manifest_json", "path": MANIFEST_NAME, "detail": str(e)}]
        return _fail(K_MISSING_MANIFEST, error=str(e))

    rows = manifest.get("entries") or manifest.get("files") or []
    errors: list[dict[str, Any]] = []
    if verify_checksums and isinstance(rows, list):
        staging_root = staging.absolute()
        entries_by_path = {}
        for ent in rows:
            if isinstance(ent, dict):
                name = ent.get("path") or ent.get("name")
                if name:
                    entries_by_path[_manifest_row_key(str(name))] = ent

        for ent in rows:
            if not isinstance(ent, dict):
                continue
            name = ent.get("path") or ent.get("name")
            if not name:
                continue
            typ = str(ent.get("type") or "file")
            try:
                fp = _manifest_path_to_staging(str(name), staging)
            except ValueError:
                errors.append({"kind": "missing_file", "path": str(name), "detail": "unsafe path / traversal"})
                continue

            if typ == "dir":
                if not fp.is_dir():
                    errors.append({"kind": "missing_file", "path": str(name), "detail": "expected directory"})
                continue

            if typ == "symlink":
                expect_tgt = ent.get("link_target")
                if expect_tgt is None:
                    errors.append({"kind": "invalid_symlink", "path": str(name), "detail": "missing link_target"})
                    continue
                if not fp.is_symlink():
                    errors.append({"kind": "invalid_symlink", "path": str(name), "detail": "expected symlink"})
                    continue
                got_tgt = os.readlink(fp)
                if got_tgt != str(expect_tgt):
                    errors.append(
                        {
                            "kind": "invalid_symlink",
                            "path": str(name),
                            "detail": f"expected {expect_tgt!r}, got {got_tgt!r}",
                        }
                    )
                    continue
                if not tar_symlink_linkname_allowed(got_tgt, _safe_member_name(str(name)), staging_root):
                    errors.append({"kind": "invalid_symlink", "path": str(name), "detail": "target escapes staging root"})
                continue

            if typ == "hardlink":
                lt = ent.get("link_target")
                if lt is None or str(lt).strip() == "":
                    errors.append({"kind": "invalid_hardlink", "path": str(name), "detail": "missing link_target"})
                    continue
                tgt_key = _manifest_row_key(str(lt))
                tgt_ent = entries_by_path.get(tgt_key)
                if tgt_ent is None:
                    errors.append(
                        {
                            "kind": "invalid_hardlink",
                            "path": str(name),
                            "detail": f"target {lt!r} not in manifest",
                        }
                    )
                    continue
                if str(tgt_ent.get("type") or "") != "file":
                    errors.append(
                        {
                            "kind": "invalid_hardlink",
                            "path": str(name),
                            "detail": f"target {lt!r} is not a file entry",
                        }
                    )
                    continue
                expect_sha = tgt_ent.get("sha256")
                if not expect_sha:
                    errors.append(
                        {
                            "kind": "invalid_hardlink",
                            "path": str(name),
                            "detail": f"target {lt!r} has no sha256",
                        }
                    )
                    continue
                if not fp.exists():
                    errors.append({"kind": "missing_file", "path": str(name), "detail": "hardlink path missing after extract"})
                    continue
                if not fp.is_file():
                    errors.append({"kind": "invalid_hardlink", "path": str(name), "detail": "not a regular file"})
                    continue
                got = _sha256_file(fp)
                if got.lower() != str(expect_sha).lower():
                    errors.append(
                        {
                            "kind": "hash_mismatch",
                            "path": str(name),
                            "detail": f"hardlink content vs target manifest sha256 (expected {expect_sha}, got {got})",
                        }
                    )
                continue

            expect = ent.get("sha256")
            if not expect:
                continue
            if not fp.is_file():
                errors.append({"kind": "missing_file", "path": str(name), "detail": "expected regular file"})
                continue
            got = _sha256_file(fp)
            if got.lower() != str(expect).lower():
                errors.append(
                    {
                        "kind": "hash_mismatch",
                        "path": str(name),
                        "detail": f"expected {expect}, got {got}",
                    }
                )

    if errors:
        details["errors"] = errors
        details["valid"] = False
        return False, K_VERIFY_INTEGRITY_FAILED, details

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

    details["valid"] = True
    details["errors"] = []
    return True, K_OPERATION_OK, details


__all__ = ["verify_basic", "verify_deep", "VERIFY_STAGING_SUBDIR"]
