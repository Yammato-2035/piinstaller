"""Unattended MSI physical E2E automation (SETUPHELFER-E2E-LIVE-001D / 001D4)."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.backup_target_auto_prepare import discover_external_backup_candidates, setuphelfer_backup_dir
from core.rescue_backup_target_policy import RESCUE_STICK_LABELS
from core.rescue_physical_e2e_dev_automation import create_test_data, resolve_token_file
from core.rescue_physical_e2e_orchestrator import run_physical_e2e_workflow
from core.rescue_physical_e2e_unattended import run_unattended_msi_physical_e2e
from core.rescue_payload_version import rescue_payload_version

FEATURE_ID = "SETUPHELFER-E2E-LIVE-001D"
MSI_E2E_AUTO_RESULT = "msi-e2e-auto-result.json"

TOKEN_CANDIDATES = (
    "/etc/setuphelfer/rescue/telemetry-lab-token",
    "/run/setuphelfer/rescue/telemetry-lab-token",
    "/opt/setuphelfer-rescue/config/telemetry-lab-token",
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def resolve_msi_e2e_token_file() -> str | None:
    explicit = resolve_token_file(None)
    if explicit:
        return explicit
    for candidate in TOKEN_CANDIDATES:
        path = Path(candidate)
        if path.is_file() and path.stat().st_size > 0:
            return str(path)
    for pattern in ("/media/*/SETUP_LOGS", "/run/media/*/SETUP_LOGS", "/run/setuphelfer/esp-rw"):
        for base in Path("/").glob(pattern.lstrip("/")):
            for rel in (
                "setuphelfer/lab/telemetry-lab-token",
                "setuphelfer/config/telemetry-lab-token",
            ):
                path = base / rel
                if path.is_file() and path.stat().st_size > 0:
                    return str(path)
    return None


def _is_rescue_stick_label(label: str | None) -> bool:
    if not label:
        return False
    upper = label.upper()
    return upper in {x.upper() for x in RESCUE_STICK_LABELS} or "SETUPHELFER" in upper


def pick_external_e2e_candidate() -> dict[str, Any] | None:
    for cand in discover_external_backup_candidates():
        label = (cand.label or "").upper()
        if _is_rescue_stick_label(label):
            continue
        mount = cand.existing_mount
        if not mount:
            label_slug = (cand.label or cand.partition_id.rsplit("/", 1)[-1]).lower()
            try:
                work_root = setuphelfer_backup_dir(label_slug) / "e2e-work"
            except ValueError:
                continue
            mount = str(work_root.parent)
        return {
            "partition_id": cand.partition_id,
            "disk_id": cand.disk_id,
            "mount": mount,
            "fstype": cand.fstype,
            "transport": cand.transport,
            "mode": "external_usb",
        }
    return None


def prepare_msi_e2e_paths(
    *,
    state_root: Path | None = None,
    external: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if external:
        base = Path(external["mount"]) / "setuphelfer-e2e-work"
        base.mkdir(parents=True, exist_ok=True)
        source = base / "source"
        backup_dir = base / "backup"
        restore_dir = base / "restore" / "data"
        source.mkdir(parents=True, exist_ok=True)
        backup_dir.mkdir(parents=True, exist_ok=True)
        restore_dir.mkdir(parents=True, exist_ok=True)
        return {
            "layout_mode": "external_usb",
            "lab_tmpfs_mode": False,
            "work_root": base,
            "source": source,
            "backup_archive": backup_dir / "e2e-backup.tar.gz",
            "restore_dir": restore_dir,
            "external": external,
        }

    root = state_root or Path("/run/setuphelfer-rescue/e2e-auto")
    if root.exists():
        import shutil

        shutil.rmtree(root, ignore_errors=True)
    source = root / "source"
    backup_dir = root / "backup"
    restore_dir = root / "restore" / "data"
    source.mkdir(parents=True)
    backup_dir.mkdir(parents=True)
    restore_dir.mkdir(parents=True)
    return {
        "layout_mode": "msi_lab_synthetic",
        "lab_tmpfs_mode": True,
        "work_root": root,
        "source": source,
        "backup_archive": backup_dir / "e2e-backup.tar.gz",
        "restore_dir": restore_dir,
        "external": None,
    }


def run_msi_physical_e2e_auto(
    *,
    repo_root: Path | None = None,
    setup_logs_base: Path | None = None,
    create_data_script: Path | None = None,
    state_root: Path | None = None,
    target_bytes: int = 64 * 1024 * 1024,
    use_legacy_path: bool = False,
) -> dict[str, Any]:
    """Run unattended MSI E2E. Default: 001D4 run-control + registered target path."""
    if not use_legacy_path:
        return run_unattended_msi_physical_e2e(
            repo_root=repo_root,
            setup_logs_base=setup_logs_base,
            create_data_script=create_data_script,
            target_bytes=target_bytes,
        )

    started = _utc_now()
    token = resolve_msi_e2e_token_file()
    consent = "granted" if token else "local_only"
    external = pick_external_e2e_candidate()
    paths = prepare_msi_e2e_paths(external=external, state_root=state_root)

    repo = repo_root or Path("/opt/setuphelfer-rescue")
    script_candidates = [
        create_data_script,
        repo / "scripts" / "create-e2e-backup-test-data.sh",
        Path("/usr/local/sbin/create-e2e-backup-test-data.sh"),
    ]
    data_script = next((p for p in script_candidates if p and p.is_file()), None)
    if data_script is None:
        return {
            "feature": FEATURE_ID,
            "started_at": started,
            "completed_at": _utc_now(),
            "status": "msi_e2e_auto_failed",
            "error": "create_e2e_test_data_script_missing",
        }

    try:
        create_test_data(paths["source"], repo_root=repo, target_bytes=target_bytes)
    except Exception as exc:  # noqa: BLE001
        return {
            "feature": FEATURE_ID,
            "started_at": started,
            "completed_at": _utc_now(),
            "status": "msi_e2e_auto_failed",
            "error": "test_data_creation_failed",
            "detail": str(exc),
            "layout": paths["layout_mode"],
        }

    work_root = paths["work_root"].resolve()
    result = run_physical_e2e_workflow(
        source_dir=paths["source"],
        backup_archive=paths["backup_archive"],
        restore_dir=paths["restore_dir"],
        consent=consent,
        operator_approved=True,
        allowed_source_prefixes=(work_root,),
        allowed_output_prefixes=(work_root,),
        allowed_restore_prefixes=(work_root,),
        setup_logs_base=setup_logs_base,
        token_file=token,
        lab_tmpfs_mode=paths["lab_tmpfs_mode"],
        skip_diagnostics_poll=not bool(token),
    )

    return {
        "feature": FEATURE_ID,
        "schema_version": 1,
        "started_at": started,
        "completed_at": _utc_now(),
        "payload_version": rescue_payload_version(),
        "layout_mode": paths["layout_mode"],
        "external_candidate": paths.get("external"),
        "token_present": bool(token),
        "consent_effective": consent,
        "production_ready": False,
        "workflow": result,
        "status": "msi_e2e_auto_passed" if result.get("success") else "msi_e2e_auto_failed",
    }


def write_msi_e2e_auto_result(result: dict[str, Any], *, evidence_dir: Path) -> Path:
    evidence_dir.mkdir(parents=True, exist_ok=True)
    out = evidence_dir / MSI_E2E_AUTO_RESULT
    out.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return out
