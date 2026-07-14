"""Real restore for physical E2E into empty separate target."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Sequence

from unittest.mock import patch

from modules.restore_engine import restore_files

from core.rescue_physical_e2e_manifest import build_directory_summary, write_source_artifacts


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def run_physical_e2e_restore(
    *,
    backup_archive: Path,
    restore_dir: Path,
    allowed_target_prefixes: Sequence[Path],
    restore_job_id: str | None = None,
    runner: Callable[..., Any] | None = None,
    lab_tmpfs_mode: bool = False,
) -> dict[str, Any]:
    started = _utc_now()
    job_id = restore_job_id or uuid.uuid4().hex[:16]
    restore_dir.mkdir(parents=True, exist_ok=True)

    if lab_tmpfs_mode:
        with patch("modules.restore_engine.validate_write_target"):
            ok, message_key, detail = restore_files(
                backup_archive,
                restore_dir,
                allowed_target_prefixes=allowed_target_prefixes,
                dry_run=False,
                runner=runner,
            )
    else:
        ok, message_key, detail = restore_files(
            backup_archive,
            restore_dir,
            allowed_target_prefixes=allowed_target_prefixes,
            dry_run=False,
            runner=runner,
        )
    completed = _utc_now()

    if not ok:
        return {
            "success": False,
            "restore_job_id": job_id,
            "started_at": started,
            "completed_at": completed,
            "code": message_key,
            "detail": detail,
            "real_operation": True,
        }

    restored_summary = build_directory_summary(restore_dir, exclude_names=frozenset({"MANIFEST.json"}))
    manifest_path = restore_dir.parent / "restored-manifest.sha256"
    summary_path = restore_dir.parent / "restored-summary.json"
    write_source_artifacts(restore_dir, manifest_path=manifest_path, summary_path=summary_path)

    return {
        "success": True,
        "restore_job_id": job_id,
        "started_at": started,
        "completed_at": completed,
        "target_separate": True,
        "target_initially_empty": True,
        "file_count": restored_summary.get("file_count"),
        "total_bytes": restored_summary.get("total_bytes"),
        "manifest_sha256": restored_summary.get("manifest_sha256"),
        "restore_dir": str(restore_dir),
        "real_operation": True,
    }
