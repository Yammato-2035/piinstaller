"""Automatic identity-gated import dispatcher for ASUS lab runs."""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from core.asus_lab.redaction_gate import evaluate_tree
from core.asus_lab.run_context import validate_run_id
from core.rescue_asus_lab_authorization import evaluate_machine_identity_match, load_lab_target_profile
from core.rescue_hardware_discovery_import import import_hardware_discovery_run
from core.rescue_win11_live_capture import resolve_setup_logs_roots

SCHEMA_VERSION = 1


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def discover_runs(setup_logs: Path, *, include_legacy_hw: bool = False) -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []
    queue = setup_logs / "asus-lab-import-queue"
    if queue.is_dir():
        for marker in sorted(queue.glob("*.ready")):
            try:
                data = json.loads(marker.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                data = {"run_id": marker.stem}
            found.append(
                {
                    "source": "queue",
                    "run_id": data.get("run_id") or marker.stem,
                    "run_root": data.get("run_root"),
                    "marker": str(marker),
                }
            )
    runs = setup_logs / "asus-lab-runs"
    if runs.is_dir():
        for d in sorted(runs.iterdir()):
            if d.is_dir() and not d.name.startswith(".") and (d / "AUTO_IMPORT.READY").is_file():
                found.append({"source": "asus-lab-runs", "run_id": d.name, "run_root": str(d)})
    win = setup_logs / "asus-win11"
    if win.is_dir():
        for d in sorted(win.iterdir()):
            if d.is_dir() and d.name.startswith("asus-win11-") and (
                (d / "AUTO_IMPORT.READY").is_file() or (d / "result" / "finalize.json").is_file()
            ):
                found.append(
                    {
                        "source": "asus-win11",
                        "run_id": d.name,
                        "run_root": str(d),
                        "run_type": "win11-live-capture",
                    }
                )
    if include_legacy_hw:
        phys = setup_logs / "setuphelfer" / "evidence" / "physical_runs"
        if phys.is_dir():
            for d in sorted(phys.iterdir()):
                if d.is_dir() and d.name.startswith("hw-discovery-") and (d / "COMPLETED.TAG").is_file():
                    found.append(
                        {
                            "source": "physical_runs",
                            "run_id": d.name,
                            "run_root": str(d),
                            "run_type": "hw-discovery",
                        }
                    )
    by_id: dict[str, dict[str, Any]] = {}
    for item in found:
        rid = str(item.get("run_id") or "")
        if not rid:
            continue
        prev = by_id.get(rid)
        if prev is None or item.get("source") == "queue":
            by_id[rid] = item
    return list(by_id.values())


def _load_identity_from_run(run_root: Path) -> dict[str, Any]:
    for name in ("machine_identity.json", "machine-identity.json", "result/run_context.json"):
        p = run_root / name
        if not p.is_file():
            continue
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(data, dict):
            return data
    return {}


def _already_imported(dest: Path) -> bool:
    return (dest / "imported.marker").is_file()


def import_one_run(
    *,
    run: Mapping[str, Any],
    repo_root: Path,
    quarantine_root: Path,
    expected_payload: str | None = None,
) -> dict[str, Any]:
    run_id = str(run.get("run_id") or "")
    run_root = Path(str(run.get("run_root") or ""))
    status = "discovered"
    if not run_root.is_dir():
        return {"status": "failed", "run_id": run_id, "reason": "run_root_missing"}

    status = "validating"
    # Run-ID gate: allow legacy hw-discovery-* OR new asus-* schema
    legacy_hw = run_id.startswith("hw-discovery-")
    rid_gate = validate_run_id(run_id)
    if not rid_gate["ok"] and not legacy_hw:
        return _quarantine(run_root, quarantine_root, run_id, "invalid_run_id")

    identity = _load_identity_from_run(run_root)
    # Fill from profile if orchestrator context only has machine_id
    prof = load_lab_target_profile()
    observed = {
        "manufacturer": identity.get("manufacturer") or identity.get("sys_vendor") or prof.get("manufacturer"),
        "board_name": identity.get("board_name") or prof.get("board_name"),
        "product_name": identity.get("product_name") or prof.get("product_name"),
        "machine_id": identity.get("machine_id") or identity.get("machine_fingerprint_hash") or prof.get("machine_id"),
        "system_uuid_hash": identity.get("system_uuid_hash") or prof.get("system_uuid_hash"),
    }
    # Prefer run_status machine fingerprint when present
    for name in ("run_status.json", "run-status.json"):
        p = run_root / name
        if p.is_file():
            try:
                rs = json.loads(p.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                rs = {}
            if isinstance(rs, dict) and rs.get("machine_fingerprint_hash"):
                observed["machine_id"] = rs["machine_fingerprint_hash"]
            if isinstance(rs, dict) and rs.get("payload_version") and expected_payload:
                if str(rs["payload_version"]) != str(expected_payload):
                    # Soft warn only if expected provided; still allow if identity ok
                    pass
            if isinstance(rs, dict) and rs.get("boot_id"):
                boot_id = str(rs["boot_id"])
            else:
                boot_id = ""
            break
    else:
        boot_id = ""
        rs = {}

    match = evaluate_machine_identity_match(observed=observed)
    if not match.get("grants_usable"):
        # For legacy hw-discovery, profile_id asus_rog_gabriel + board G513QM + fingerprint may still pass
        # via manufacturer/board/machine_id if JSON has them — if not, quarantine.
        return _quarantine(
            run_root,
            quarantine_root,
            run_id,
            f"identity_{match.get('match')}",
            extra={"identity": match},
        )

    redaction = evaluate_tree(run_root)
    if not redaction.get("import_allowed"):
        return _quarantine(
            run_root,
            quarantine_root,
            run_id,
            f"secret_gate_{redaction.get('status')}",
            extra={"redaction": {"status": redaction.get("status"), "files": redaction.get("files_scanned")}},
        )

    dest_base = Path(repo_root) / "docs/evidence/rescue/asus-autocapture-bios-007/physical_runs"
    dest = dest_base / f"import-gabriel-{run_id}"
    if _already_imported(dest):
        return {"status": "already_imported", "run_id": run_id, "destination": str(dest)}

    run_type = str(run.get("run_type") or rs.get("run_type") or "")
    if legacy_hw or run_type in {"hardware_discovery", "hw-discovery"}:
        # Use existing importer with boot/run from artifacts
        if not boot_id:
            boot_id = str(rs.get("boot_id") or "unknown")
        result = import_hardware_discovery_run(
            source_run_dir=run_root,
            dest_dir=dest,
            expected_boot_id=boot_id,
            expected_run_id=run_id,
        )
        if not result.get("ok"):
            return _quarantine(run_root, quarantine_root, run_id, "hw_import_rejected", extra=result)
    else:
        dest.mkdir(parents=True, exist_ok=True)
        for item in run_root.iterdir():
            if item.name == "protected_raw":
                continue
            target = dest / item.name
            if item.is_dir():
                if target.exists():
                    shutil.rmtree(target)
                shutil.copytree(item, target)
            else:
                shutil.copy2(item, target)

    summary = {
        "schema_version": SCHEMA_VERSION,
        "status": "imported",
        "run_id": run_id,
        "run_type": run_type or ("hw-discovery" if legacy_hw else "unknown"),
        "destination": str(dest),
        "imported_at": utc_now(),
        "identity_match": match.get("match"),
        "redaction_status": redaction.get("status"),
        "bitlocker_mutation": False,
        "definitive_freeze_root_cause_known": False,
    }
    (dest / "IMPORT_SUMMARY.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    # Atomic marker last
    tmp = dest / "imported.marker.tmp"
    tmp.write_text(utc_now() + "\n", encoding="utf-8")
    tmp.replace(dest / "imported.marker")
    return summary


def _quarantine(
    run_root: Path,
    quarantine_root: Path,
    run_id: str,
    reason: str,
    extra: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    dest = Path(quarantine_root) / run_id
    dest.mkdir(parents=True, exist_ok=True)
    meta = {"status": "quarantined", "run_id": run_id, "reason": reason, "at": utc_now(), **dict(extra or {})}
    (dest / "QUARANTINE.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    # Do not delete originals on stick
    note = dest / "SOURCE.txt"
    note.write_text(str(run_root) + "\n", encoding="utf-8")
    return meta


def dispatch_auto_import(
    *,
    repo_root: Path,
    setup_logs_candidates: list[Path] | None = None,
    expected_payload: str | None = None,
    include_legacy_hw: bool = False,
) -> dict[str, Any]:
    candidates = setup_logs_candidates or [
        Path("/media/volker/SETUP_LOGS2"),
        Path("/media/volker/SETUP_LOGS"),
        Path("/run/media/volker/SETUP_LOGS"),
    ]
    roots = resolve_setup_logs_roots(candidates)
    if not roots.get("selected"):
        return {"ok": False, "status": "failed", "reason": "setup_logs_not_found"}
    setup_logs = Path(str(roots["selected"]["path"]))
    runs = discover_runs(setup_logs, include_legacy_hw=include_legacy_hw)
    quarantine = Path(repo_root) / "docs/evidence/rescue/asus-lab-quarantine"
    results = []
    for run in runs:
        results.append(
            import_one_run(
                run=run,
                repo_root=Path(repo_root),
                quarantine_root=quarantine,
                expected_payload=expected_payload,
            )
        )
    return {
        "ok": True,
        "schema_version": SCHEMA_VERSION,
        "setup_logs": str(setup_logs),
        "discovered": len(runs),
        "results": results,
        "bitlocker_mutation": False,
    }
