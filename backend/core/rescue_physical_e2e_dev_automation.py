"""Dev-workstation automation for SETUPHELFER-E2E-LIVE-001D."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.rescue_physical_e2e_diagnostics import query_diagnostics_case
from core.rescue_physical_e2e_evidence_import import (
    find_setup_logs_mount,
    import_e2e_run_evidence,
    list_e2e_run_dirs,
)
from core.rescue_physical_e2e_orchestrator import run_physical_e2e_workflow
from core.rescue_payload_version import rescue_payload_version

DEFAULT_TOKEN_CANDIDATES = (
    "~/.config/setuphelfer/rescue/telemetry-lab-token",
    "~/.config/setuphelfer/rescue/telemetry-lab-token",
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def resolve_token_file(explicit: str | None = None) -> str | None:
    if explicit:
        path = Path(explicit).expanduser()
        return str(path) if path.is_file() and path.stat().st_size > 0 else None
    env_path = os.getenv("SETUPHELFER_RS_TELEMETRY_LAB_TOKEN_FILE") or os.getenv("SETUPHELFER_RS_LAB_TOKEN_FILE")
    if env_path:
        path = Path(env_path).expanduser()
        if path.is_file() and path.stat().st_size > 0:
            return str(path)
    for candidate in DEFAULT_TOKEN_CANDIDATES:
        path = Path(candidate).expanduser()
        if path.is_file() and path.stat().st_size > 0:
            return str(path)
    return None


def prepare_lab_workspace(work_root: Path) -> dict[str, Path]:
    if work_root.exists():
        shutil.rmtree(work_root)
    source = work_root / "source"
    backup_dir = work_root / "backup"
    restore_dir = work_root / "restore" / "data"
    source.mkdir(parents=True)
    backup_dir.mkdir(parents=True)
    restore_dir.mkdir(parents=True)
    return {
        "work_root": work_root,
        "source": source,
        "backup_archive": backup_dir / "e2e-backup.tar.gz",
        "restore_dir": restore_dir,
    }


def create_test_data(source_dir: Path, *, repo_root: Path, target_bytes: int = 64 * 1024 * 1024) -> None:
    script = repo_root / "scripts" / "create-e2e-backup-test-data.sh"
    if not script.is_file():
        raise FileNotFoundError("create-e2e-backup-test-data.sh missing")
    env = {**os.environ, "TARGET_BYTES": str(target_bytes)}
    subprocess.run(
        ["bash", str(script), str(source_dir)],
        check=True,
        env=env,
        cwd=str(repo_root),
    )


def run_dev_lab_e2e(
    *,
    repo_root: Path,
    work_root: Path | None = None,
    setup_logs_base: Path | None = None,
    consent: str = "granted",
    token_file: str | None = None,
    ingest_url: str | None = None,
    target_bytes: int = 64 * 1024 * 1024,
) -> dict[str, Any]:
    logs_base = setup_logs_base or find_setup_logs_mount()
    root = work_root or Path("/tmp/setuphelfer-e2e-lab-work")
    paths = prepare_lab_workspace(root)
    create_test_data(paths["source"], repo_root=repo_root, target_bytes=target_bytes)

    token = resolve_token_file(token_file)
    effective_consent = consent if token else "local_only"

    result = run_physical_e2e_workflow(
        source_dir=paths["source"],
        backup_archive=paths["backup_archive"],
        restore_dir=paths["restore_dir"],
        consent=effective_consent,
        operator_approved=True,
        allowed_source_prefixes=(root.resolve(),),
        allowed_output_prefixes=(root.resolve(),),
        allowed_restore_prefixes=(root.resolve(),),
        setup_logs_base=logs_base,
        token_file=token,
        ingest_url=ingest_url,
        lab_tmpfs_mode=True,
        skip_diagnostics_poll=not bool(token),
    )

    diagnostics: dict[str, Any] = {}
    if token and result.get("e2e_run_id"):
        diagnostics = query_diagnostics_case(str(result["e2e_run_id"]))

    return {
        "mode": "dev_lab_e2e",
        "started_at": _utc_now(),
        "payload_version": rescue_payload_version(),
        "setup_logs_base": str(logs_base) if logs_base else None,
        "token_present": bool(token),
        "consent_effective": effective_consent,
        "work_root": str(root),
        "workflow": result,
        "diagnostics_poll": diagnostics,
    }


def run_full_dev_automation(
    *,
    repo_root: Path,
    import_evidence: bool = True,
    run_lab: bool = True,
    setup_logs_base: Path | None = None,
    token_file: str | None = None,
) -> dict[str, Any]:
    logs = setup_logs_base or find_setup_logs_mount()
    out: dict[str, Any] = {
        "feature": "SETUPHELFER-E2E-LIVE-001D",
        "automation_at": _utc_now(),
        "setup_logs_mounted": logs is not None,
        "setup_logs_base": str(logs) if logs else None,
        "production_ready": False,
    }

    if run_lab:
        out["lab_run"] = run_dev_lab_e2e(
            repo_root=repo_root,
            setup_logs_base=logs,
            token_file=token_file,
        )

    if import_evidence:
        if logs is None:
            out["import"] = {"import_ok": False, "error": "setup_logs_not_mounted"}
        else:
            runs = list_e2e_run_dirs(logs)
            if not runs and out.get("lab_run", {}).get("workflow", {}).get("journal_dir"):
                journal = Path(out["lab_run"]["workflow"]["journal_dir"])
                if journal.is_dir():
                    runs = [journal]
            if not runs:
                out["import"] = {"import_ok": False, "error": "no_e2e_runs_found"}
            else:
                out["import"] = import_e2e_run_evidence(runs[0], repo_root=repo_root, setup_logs_base=logs)

    workflow = (out.get("lab_run") or {}).get("workflow") or {}
    import_ok = (out.get("import") or {}).get("import_ok")
    success = bool(workflow.get("success")) if run_lab else bool(import_ok)
    if run_lab and import_evidence:
        success = bool(workflow.get("success")) and bool(import_ok)

    out["status"] = "dev_automation_passed" if success else "dev_automation_failed"
    return out
