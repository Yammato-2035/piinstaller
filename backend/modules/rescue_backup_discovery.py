"""
Rescue Phase 2A: Backup-Kandidaten finden, Metadaten lesen, Restore-Simulation klassifizieren.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, Callable

import tarfile

from core.install_paths import get_config_dir
from core.rescue_allowlist import RESCUE_BACKUP_READ_PREFIXES, path_under_prefixes
from modules.backup_engine import MANIFEST_KIND, MANIFEST_NAME, _norm_tar_arcname

Runner = Callable[..., Any] | None

BACKUP_GLOB_PATTERNS = (
    "pi-backup-full-*.tar.gz",
    "pi-backup-inc-*.tar.gz",
    "pi-backup-data-*.tar.gz",
    "pi-backup-personal-full-*.tar.gz",
    "pi-backup-personal-inc-*.tar.gz",
)


def _safe_glob_dir(base: Path, pattern: str, *, limit: int = 200) -> list[Path]:
    out: list[Path] = []
    try:
        if not base.is_dir():
            return []
        for p in sorted(base.glob(pattern), key=lambda x: x.stat().st_mtime if x.is_file() else 0, reverse=True):
            if p.is_file() and str(p).endswith(".tar.gz"):
                out.append(p)
            if len(out) >= limit:
                break
    except OSError:
        return []
    return out


def discover_backup_candidates(
    *,
    extra_scan_dirs: list[str] | None = None,
    max_per_pattern: int = 50,
) -> list[dict[str, Any]]:
    """
    Sucht typische Setuphelfer-Archive unter bekannten Wurzeln und optional ``backup.json``-Ziel.

    ``source_kind``: setuphelfer_config | local_mount | extra_scan
    """
    seen: set[str] = set()
    rows: list[dict[str, Any]] = []

    def add_row(p: Path, source_kind: str) -> None:
        k = str(p.resolve())
        if k in seen:
            return
        seen.add(k)
        try:
            st = p.stat()
            sz = st.st_size
        except OSError:
            return
        rows.append(
            {
                "path": k,
                "basename": p.name,
                "size_bytes": sz,
                "mtime_epoch": int(getattr(st, "st_mtime", 0) or 0),
                "source_kind": source_kind,
            }
        )

    cfg = get_config_dir() / "backup.json"
    if cfg.is_file():
        try:
            data = json.loads(cfg.read_text(encoding="utf-8") or "{}")
        except json.JSONDecodeError:
            data = {}
        bd = data.get("backup_dir")
        if isinstance(bd, str) and bd.strip():
            bpath = Path(bd.strip())
            if bpath.is_dir():
                for pat in BACKUP_GLOB_PATTERNS:
                    for p in _safe_glob_dir(bpath, pat, limit=max_per_pattern):
                        if path_under_prefixes(p, RESCUE_BACKUP_READ_PREFIXES):
                            add_row(p, "setuphelfer_config")

    for root in RESCUE_BACKUP_READ_PREFIXES:
        if not root.is_dir():
            continue
        for pat in BACKUP_GLOB_PATTERNS:
            for p in _safe_glob_dir(root, pat, limit=max_per_pattern):
                if path_under_prefixes(p, RESCUE_BACKUP_READ_PREFIXES):
                    add_row(p, "local_mount")
        try:
            for child in root.iterdir():
                if not child.is_dir():
                    continue
                for pat in BACKUP_GLOB_PATTERNS:
                    for p in _safe_glob_dir(child, pat, limit=max_per_pattern):
                        add_row(p, "local_mount")
        except OSError:
            continue

    for raw in extra_scan_dirs or []:
        try:
            ep = Path(raw).resolve()
        except OSError:
            continue
        if ep.is_dir() and path_under_prefixes(ep, RESCUE_BACKUP_READ_PREFIXES):
            for pat in BACKUP_GLOB_PATTERNS:
                for p in _safe_glob_dir(ep, pat, limit=max_per_pattern):
                    add_row(p, "extra_scan")

    rows.sort(key=lambda r: r.get("mtime_epoch", 0), reverse=True)
    return rows


def read_backup_metadata(archive_path: str | Path) -> dict[str, Any]:
    """
    Liest ``MANIFEST.json`` aus dem Archiv (nur Metadaten, kein Voll-Extract).
    """
    p = Path(archive_path)
    out: dict[str, Any] = {
        "path": str(p),
        "file_size_bytes": None,
        "manifest_present": False,
        "manifest": None,
        "read_error_code": None,
    }
    try:
        st = p.stat()
        out["file_size_bytes"] = st.st_size
    except OSError as e:
        out["read_error_code"] = "rescue.backup.file_stat_failed"
        out["read_error_detail_type"] = type(e).__name__
        return out
    if not p.is_file():
        out["read_error_code"] = "rescue.backup.file_missing"
        return out
    low = p.name.lower()
    if low.endswith(".gpg") or low.endswith(".enc"):
        out["read_error_code"] = "rescue.backup.encrypted_container"
        return out
    try:
        with tarfile.open(p, "r:*") as tf:
            names = {_norm_tar_arcname(n) for n in tf.getnames()}
            if MANIFEST_NAME not in names:
                out["read_error_code"] = "rescue.backup.manifest_missing_in_tar"
                return out
            m = tf.extractfile(MANIFEST_NAME) or tf.extractfile(f"./{MANIFEST_NAME}")
            if m is None:
                for cand in tf.getmembers():
                    if _norm_tar_arcname(cand.name) == MANIFEST_NAME:
                        m = tf.extractfile(cand)
                        break
            if m is None:
                out["read_error_code"] = "rescue.backup.manifest_missing_in_tar"
                return out
            raw = m.read()
            manifest = json.loads(raw.decode("utf-8"))
            if not isinstance(manifest, dict):
                out["read_error_code"] = "rescue.backup.manifest_not_object"
                return out
            out["manifest_present"] = True
            out["manifest"] = manifest
    except tarfile.TarError:
        out["read_error_code"] = "rescue.backup.tar_invalid"
    except json.JSONDecodeError:
        out["read_error_code"] = "rescue.backup.manifest_json_invalid"
    except OSError as e:
        out["read_error_code"] = "rescue.backup.tar_open_failed"
        out["read_error_detail_type"] = type(e).__name__
    return out


def classify_backup_type(manifest: dict[str, Any] | None, basename: str) -> str:
    """
    Grobe Klassifikation: full | incremental | data_only | personal | unknown

    Inkrementell wird primär über Dateinamen erkannt (Setuphelfer-Runner-Konvention).
    """
    bn = basename.lower()
    if "pi-backup-inc-" in bn or "personal-inc-" in bn:
        return "incremental"
    if "pi-backup-data-" in bn:
        return "data_only"
    if "personal-full" in bn or "personal-inc" in bn:
        return "personal"
    if "pi-backup-full-" in bn:
        return "full"
    if manifest:
        entries = manifest.get("entries") or manifest.get("files") or []
        if isinstance(entries, list) and len(entries) > 5000:
            return "full"
    return "unknown"


def validate_backup_for_restore_simulation(
    archive_path: str | Path,
    *,
    encryption_key_available: bool = False,
    runner: Runner = None,
) -> dict[str, Any]:
    """
    Liefert u. a. ``backup_class``: BACKUP_OK | BACKUP_WARN_INCOMPLETE | …
    Nutzt ``verify_basic`` aus der Verify-Engine (kein Extract).
    """
    from modules.backup_verify import verify_basic

    p = Path(archive_path)
    result: dict[str, Any] = {
        "path": str(p),
        "backup_class": "BACKUP_UNSUPPORTED",
        "codes": [],
        "verify_basic_ok": False,
        "verify_message_key": None,
    }
    name = p.name.lower()
    if name.endswith(".gpg") or name.endswith(".enc"):
        result["backup_class"] = "BACKUP_ENCRYPTED_KEY_REQUIRED"
        result["codes"].append("rescue.backup.encrypted_container")
        if not encryption_key_available:
            result["codes"].append("rescue.backup.key_required")
        else:
            result["codes"].append("rescue.backup.encrypted_simulation_only")
        return result

    meta = read_backup_metadata(p)
    manifest = meta.get("manifest") if isinstance(meta.get("manifest"), dict) else None
    btype = classify_backup_type(manifest, p.name)

    if meta.get("read_error_code"):
        if meta["read_error_code"] == "rescue.backup.manifest_missing_in_tar":
            result["backup_class"] = "BACKUP_WARN_INCOMPLETE"
        else:
            result["backup_class"] = "BACKUP_CORRUPT"
        result["codes"].append(meta["read_error_code"])
        return result

    ok, key, detail = verify_basic(p, runner=runner)
    result["verify_basic_ok"] = bool(ok)
    result["verify_message_key"] = key
    if not ok:
        result["backup_class"] = "BACKUP_CORRUPT"
        result["codes"].append("rescue.backup.verify_failed")
        if key:
            result["verify_message_key"] = key
        if detail:
            result["verify_detail_type"] = "gzip_or_tar"
        return result

    if manifest and str(manifest.get("kind") or "") != MANIFEST_KIND:
        result["backup_class"] = "BACKUP_VERSION_MISMATCH"
        result["codes"].append("rescue.backup.manifest_kind_mismatch")
        return result

    if btype == "incremental":
        result["backup_class"] = "BACKUP_WARN_INCOMPLETE"
        result["codes"].append("rescue.backup.incremental_needs_full")
        return result

    result["backup_class"] = "BACKUP_OK"
    result["codes"].append("rescue.backup.ok")
    return result


__all__ = [
    "BACKUP_GLOB_PATTERNS",
    "classify_backup_type",
    "discover_backup_candidates",
    "read_backup_metadata",
    "validate_backup_for_restore_simulation",
]
