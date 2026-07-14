"""Directory manifest and comparison for physical E2E integrity checks."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any


def _path_token(path: Path, root: Path) -> str:
    rel = path.relative_to(root).as_posix()
    digest = hashlib.sha256(rel.encode("utf-8")).hexdigest()
    return digest[:16]


def build_directory_summary(root: Path, *, exclude_names: frozenset[str] | None = None) -> dict[str, Any]:
    if not root.is_dir():
        raise ValueError("source_not_a_directory")

    excludes = exclude_names or frozenset()
    file_count = 0
    total_bytes = 0
    manifest_lines: list[str] = []

    for dirpath, _dirnames, filenames in os.walk(root):
        for name in filenames:
            if name in excludes:
                continue
            full = Path(dirpath) / name
            try:
                st = full.stat()
            except OSError:
                continue
            if not full.is_file():
                continue
            file_count += 1
            total_bytes += st.st_size
            file_sha = hashlib.sha256()
            with full.open("rb") as handle:
                for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                    file_sha.update(chunk)
            manifest_lines.append(f"{file_sha.hexdigest()}:{st.st_size}")

    manifest_lines.sort()
    manifest_body = "\n".join(manifest_lines)
    manifest_sha256 = hashlib.sha256(manifest_body.encode("utf-8")).hexdigest()

    return {
        "file_count": file_count,
        "total_bytes": total_bytes,
        "manifest_sha256": manifest_sha256,
        "contains_personal_data": False,
    }


def write_source_artifacts(
    root: Path,
    *,
    manifest_path: Path,
    summary_path: Path,
    exclude_names: frozenset[str] | None = None,
) -> dict[str, Any]:
    summary = build_directory_summary(root, exclude_names=exclude_names)
    manifest_lines = []
    excludes = exclude_names or frozenset()
    for dirpath, _dirnames, filenames in os.walk(root):
        for name in filenames:
            if name in excludes:
                continue
            full = Path(dirpath) / name
            if not full.is_file():
                continue
            file_sha = hashlib.sha256()
            with full.open("rb") as handle:
                for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                    file_sha.update(chunk)
            manifest_lines.append(f"{file_sha.hexdigest()}:{full.stat().st_size}")
    manifest_lines.sort()
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text("\n".join(manifest_lines) + ("\n" if manifest_lines else ""), encoding="utf-8")
    summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return summary


def compare_manifest_summaries(source: dict[str, Any], restored: dict[str, Any]) -> dict[str, Any]:
    file_count_match = int(source.get("file_count", -1)) == int(restored.get("file_count", -2))
    total_bytes_match = int(source.get("total_bytes", -1)) == int(restored.get("total_bytes", -2))
    manifest_match = str(source.get("manifest_sha256", "")) == str(restored.get("manifest_sha256", ""))
    passed = file_count_match and total_bytes_match and manifest_match
    return {
        "file_count_match": file_count_match,
        "total_bytes_match": total_bytes_match,
        "manifest_match": manifest_match,
        "restore_integrity_status": "passed" if passed else "failed",
        "source_file_count": source.get("file_count"),
        "restored_file_count": restored.get("file_count"),
        "source_total_bytes": source.get("total_bytes"),
        "restored_total_bytes": restored.get("total_bytes"),
        "source_manifest_sha256": source.get("manifest_sha256"),
        "restored_manifest_sha256": restored.get("manifest_sha256"),
    }
