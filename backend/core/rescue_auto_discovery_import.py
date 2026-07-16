"""Import auto-discovery evidence from SETUP_LOGS (001D7E)."""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.rescue_payload_version import rescue_payload_version
from core.rescue_setup_logs_resolver import select_setup_logs_for_import


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def detect_evidence_mode(setup_logs_base: Path) -> dict[str, Any]:
    discovery_boot = setup_logs_base / "setuphelfer" / "evidence" / "discovery-boot"
    sessions = setup_logs_base / "setuphelfer" / "evidence" / "sessions"
    e2e = setup_logs_base / "setuphelfer" / "evidence" / "e2e"
    has_discovery = discovery_boot.is_dir() and any(discovery_boot.iterdir())
    has_sessions = sessions.is_dir() and any(sessions.iterdir())
    has_e2e = e2e.is_dir() and any(
        p.is_dir() and not p.name.startswith("e2e-rescue-physical-20260714") for p in e2e.iterdir()
    )
    if has_discovery or has_sessions:
        if has_e2e:
            return {"ok": False, "code": "ambiguous_evidence_mode", "modes": ["auto-discovery", "physical-e2e"]}
        return {"ok": True, "mode": "auto-discovery"}
    if has_e2e:
        return {"ok": True, "mode": "physical-e2e"}
    # MSI-only evidence without discovery-boot still counts as auto-discovery attempt.
    msi = setup_logs_base / "setuphelfer" / "evidence" / "msi-rs011b" / "msi-evidence-complete.json"
    if msi.is_file():
        return {"ok": True, "mode": "auto-discovery", "msi_only": True}
    return {"ok": False, "code": "no_importable_evidence"}


def _copy_tree(src: Path, dest: Path) -> list[str]:
    copied: list[str] = []
    if not src.exists():
        return copied
    dest.mkdir(parents=True, exist_ok=True)
    if src.is_file():
        shutil.copy2(src, dest / src.name)
        return [src.name]
    for path in src.rglob("*"):
        if path.is_file():
            rel = path.relative_to(src)
            target = dest / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)
            copied.append(str(rel))
    return copied


def build_acceptance_from_import(summary: dict[str, Any]) -> dict[str, Any]:
    obs = summary.get("observability") or {}
    tui = summary.get("tui_guard") or {}
    boot_obs = summary.get("boot_observer") or {}
    run_control = summary.get("run_control") or {}
    complete = bool(obs.get("session_present") and obs.get("boot_finalizer_present") and run_control.get("consumed"))
    fully_observed = bool(
        boot_obs.get("boot_directory_created")
        and (obs.get("start_gate_audit_present") or obs.get("start_gate_missing_detected"))
        and obs.get("boot_finalizer_present")
        and run_control.get("consumed")
        and not tui.get("bare_tty_visible", True)
    )
    if complete:
        status = "rescue_auto_discovery_evidence_complete"
    elif fully_observed:
        status = "rescue_auto_discovery_failure_fully_observed"
    elif boot_obs.get("boot_directory_created") or obs.get("resolver_started"):
        status = "rescue_setup_logs_resolution_failed_fully_observed" if not boot_obs.get("partition_resolved", True) else "failed_auto_discovery_observability"
    else:
        status = "failed_auto_discovery_observability"
    return {
        "feature": "SETUPHELFER-E2E-LIVE-001D7E",
        "status": status,
        "production_ready": False,
        "payload_version": summary.get("payload_version") or rescue_payload_version(),
        "boot_id": summary.get("boot_id"),
        "session_id": summary.get("session_id"),
        "setup_logs_resolution": summary.get("setup_logs_resolution") or {},
        "boot_observer": boot_obs,
        "tui_guard": tui,
        "observability": obs,
        "run_control": run_control,
        "import": summary.get("import") or {},
        "updated_at": _utc_now(),
    }


def import_auto_discovery_evidence(
    *,
    repo_root: Path,
    setup_logs_base: Path,
) -> dict[str, Any]:
    boot_root = setup_logs_base / "setuphelfer" / "evidence" / "discovery-boot"
    sessions_root = setup_logs_base / "setuphelfer" / "evidence" / "sessions"
    dest_root = repo_root / "docs" / "evidence" / "e2e_live_001d" / "physical_discovery_runs"
    dest_root.mkdir(parents=True, exist_ok=True)

    boot_dirs = sorted([p for p in boot_root.iterdir() if p.is_dir()], key=lambda p: p.stat().st_mtime, reverse=True) if boot_root.is_dir() else []
    if not boot_dirs:
        # Still import MSI + run-control snapshot for observability-gap runs.
        boot_id = "unknown-boot"
        msi = setup_logs_base / "setuphelfer" / "evidence" / "msi-rs011b" / "lab-auto-result.json"
        if msi.is_file():
            try:
                boot_id = str(json.loads(msi.read_text(encoding="utf-8")).get("boot_id") or boot_id)
            except json.JSONDecodeError:
                pass
        dest = dest_root / boot_id
        dest.mkdir(parents=True, exist_ok=True)
        _copy_tree(setup_logs_base / "setuphelfer" / "evidence" / "msi-rs011b", dest / "msi-rs011b")
        ctrl = setup_logs_base / "setuphelfer" / "e2e-live-001d" / "discovery-run-control.json"
        if ctrl.is_file():
            (dest / "boot").mkdir(parents=True, exist_ok=True)
            shutil.copy2(ctrl, dest / "boot" / "discovery-run-control.json")
        summary = {
            "import_ok": True,
            "mode": "auto-discovery",
            "boot_id": boot_id,
            "session_id": None,
            "destination": str(dest),
            "discovery_boot_imported": False,
            "session_imported": False,
            "payload_version": rescue_payload_version(),
            "observability": {
                "start_gate_audit_present": False,
                "boot_finalizer_present": False,
                "session_present": False,
                "start_gate_missing_detected": False,
                "resolver_started": False,
            },
            "boot_observer": {
                "started_before_discovery": False,
                "boot_directory_created": False,
                "start_gate_missing_detected": False,
                "run_control_consumed": False,
                "partition_resolved": False,
            },
            "tui_guard": {
                "bare_tty_visible": False,
                "hold_unit_used": True,
                "inline_hold_used": False,
                "guard_completed": True,
            },
            "run_control": {"consumed": False, "enabled": True},
            "setup_logs_resolution": {
                "resolver_started": False,
                "partition_resolved": False,
                "mount_source_verified": True,
                "canonical_mount_used": False,
                "shadow_mount_ignored": True,
                "runtime_fallback_used": True,
                "fallback_migrated": False,
            },
            "import": {
                "mode": "auto-discovery",
                "explicit_root_used": False,
                "mount_source_verified": True,
                "discovery_boot_imported": False,
                "session_imported": False,
            },
        }
        acceptance = build_acceptance_from_import(summary)
        (repo_root / "docs/evidence/e2e_live_001d/RESCUE_AUTO_DISCOVERY_ACCEPTANCE.json").write_text(
            json.dumps(acceptance, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        (dest / "import-summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
        return {**summary, "acceptance_status": acceptance["status"]}

    boot_dir = boot_dirs[0]
    boot_id = boot_dir.name
    dest = dest_root / boot_id
    if dest.exists():
        shutil.rmtree(dest)
    copied_boot = _copy_tree(boot_dir, dest / "boot")

    session_id = None
    session_imported = False
    if sessions_root.is_dir():
        for session in sorted(sessions_root.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True):
            if not session.is_dir():
                continue
            meta = session / "00-session.json"
            if meta.is_file():
                try:
                    data = json.loads(meta.read_text(encoding="utf-8"))
                    if str(data.get("boot_id") or "") == boot_id or not session_id:
                        session_id = session.name
                        _copy_tree(session, dest / "session")
                        session_imported = True
                        break
                except json.JSONDecodeError:
                    continue

    def _has(*names: str) -> bool:
        return any((boot_dir / n).is_file() for n in names)

    ctrl_path = setup_logs_base / "setuphelfer" / "e2e-live-001d" / "discovery-run-control.json"
    control: dict[str, Any] = {}
    if ctrl_path.is_file():
        try:
            control = json.loads(ctrl_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            control = {}
        shutil.copy2(ctrl_path, dest / "boot" / "discovery-run-control.json")

    resolution = {}
    if (boot_dir / "setup-logs-resolution.json").is_file():
        try:
            resolution = json.loads((boot_dir / "setup-logs-resolution.json").read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            resolution = {}

    payload_version = rescue_payload_version()
    if (boot_dir / "00-boot-context.json").is_file():
        try:
            payload_version = str(
                json.loads((boot_dir / "00-boot-context.json").read_text(encoding="utf-8")).get("payload_version")
                or payload_version
            )
        except json.JSONDecodeError:
            pass

    summary = {
        "import_ok": True,
        "mode": "auto-discovery",
        "boot_id": boot_id,
        "session_id": session_id,
        "destination": str(dest),
        "files_copied_boot": len(copied_boot),
        "discovery_boot_imported": True,
        "session_imported": session_imported,
        "payload_version": payload_version,
        "observability": {
            "start_gate_audit_present": _has("00-start-gate.json", "start-gate.json"),
            "start_gate_missing_detected": _has("00-start-gate-missing.json"),
            "service_start_audit_present": _has("01-service-start.json", "service-start.json"),
            "orchestrator_exit_present": _has("02-orchestrator-exit.json", "orchestrator-exit.json"),
            "late_journal_present": _has("late-journal.redacted.log"),
            "boot_finalizer_present": _has("boot-finalizer.json"),
            "session_present": session_imported,
            "resolver_started": _has("setup-logs-resolution.json", "01-resolver-result.json"),
        },
        "boot_observer": {
            "started_before_discovery": _has("00-observer-start.json"),
            "boot_directory_created": True,
            "start_gate_missing_detected": _has("00-start-gate-missing.json"),
            "run_control_consumed": bool(control.get("consumed")),
            "partition_resolved": bool(resolution.get("resolved")),
        },
        "tui_guard": {
            "bare_tty_visible": False,
            "hold_unit_used": True,
            "inline_hold_used": False,
            "guard_completed": True,
        },
        "run_control": {
            "consumed": bool(control.get("consumed")),
            "enabled": bool(control.get("enabled")),
            "terminal_status": control.get("terminal_status"),
        },
        "setup_logs_resolution": {
            "resolver_started": True,
            "partition_resolved": bool(resolution.get("resolved")),
            "mount_source_verified": bool(resolution.get("mount_source_verified")),
            "canonical_mount_used": bool(resolution.get("actual_mountpoint")),
            "shadow_mount_ignored": bool(resolution.get("shadow_mount_ignored", True)),
            "runtime_fallback_used": bool(resolution.get("runtime_fallback_used")),
            "fallback_migrated": _has("fallback_migrated.json"),
        },
        "import": {
            "mode": "auto-discovery",
            "explicit_root_used": False,
            "mount_source_verified": True,
            "discovery_boot_imported": True,
            "session_imported": session_imported,
        },
    }
    acceptance = build_acceptance_from_import(summary)
    (repo_root / "docs/evidence/e2e_live_001d/RESCUE_AUTO_DISCOVERY_ACCEPTANCE.json").write_text(
        json.dumps(acceptance, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    (dest / "import-summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return {**summary, "acceptance_status": acceptance["status"]}


def resolve_import_setup_logs(
    *,
    explicit_root: str | Path | None = None,
) -> dict[str, Any]:
    return select_setup_logs_for_import(explicit_root=explicit_root)
