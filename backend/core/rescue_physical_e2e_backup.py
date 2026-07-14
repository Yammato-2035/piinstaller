"""Real file backup for physical E2E using backup_engine."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Sequence

from unittest.mock import patch

from modules.backup_engine import create_file_backup

from core.rescue_physical_e2e_manifest import build_directory_summary


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def run_physical_e2e_backup(
    *,
    source_dir: Path,
    backup_archive: Path,
    allowed_source_prefixes: Sequence[Path],
    allowed_output_prefixes: Sequence[Path],
    backup_job_id: str | None = None,
    runner: Callable[..., Any] | None = None,
    lab_tmpfs_mode: bool = False,
) -> dict[str, Any]:
    started = _utc_now()
    job_id = backup_job_id or uuid.uuid4().hex[:16]
    source_summary = build_directory_summary(source_dir)

    backup_paths: list[Path] = [entry for entry in sorted(source_dir.iterdir())]
    if not backup_paths:
        return {
            "success": False,
            "backup_job_id": job_id,
            "code": "source_empty",
            "detail": "Testdatenquelle ist leer.",
            "real_operation": True,
        }

    def _run_backup() -> Any:
        return create_file_backup(
            backup_paths,
            archive_path=backup_archive,
            allowed_source_prefixes=allowed_source_prefixes,
            allowed_output_prefixes=allowed_output_prefixes,
            runner=runner,
        )

    if lab_tmpfs_mode:
        with patch("modules.backup_engine.validate_backup_target"):
            result = _run_backup()
    else:
        result = _run_backup()
    completed = _utc_now()

    if not result.ok:
        return {
            "success": False,
            "backup_job_id": job_id,
            "source_type": "synthetic_test_data",
            "target_type": "external_file_archive",
            "started_at": started,
            "completed_at": completed,
            "code": result.message_key,
            "detail": result.detail,
        }

    manifest = result.manifest or {}
    file_count = int(source_summary.get("file_count") or 0)
    total_bytes = int(source_summary.get("total_bytes") or 0)
    manifest_sha256 = str(source_summary.get("manifest_sha256") or "")

    return {
        "success": True,
        "backup_job_id": job_id,
        "source_type": "synthetic_test_data",
        "target_type": "external_file_archive",
        "started_at": started,
        "completed_at": completed,
        "duration_seconds": None,
        "file_count": file_count,
        "total_bytes": total_bytes,
        "manifest_sha256": manifest_sha256,
        "backup_format": "tar.gz+manifest",
        "archive_path": str(backup_archive),
        "manifest_entries": len(manifest.get("files") or manifest.get("backup_entries") or []),
        "real_operation": True,
    }
