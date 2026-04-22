"""
Rescue Phase 2C: Restore-Dry-Run-Orchestrierung (kein produktiver Schreibzugriff).

Kombiniert Discovery, Zielbewertung, verify_deep in Sandbox, Boot-Check und Entscheidungslogik.
"""

from __future__ import annotations

import json
import shutil
import tarfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from core.rescue_allowlist import (
    RESCUE_DRYRUN_WRITE_PREFIXES,
    assert_backup_readable_path,
    assert_dryrun_staging_path,
)
from models.diagnosis import RescueFinding, RescueRiskLevel, RestoreDryRunRequest, RestoreDryRunResponse

from modules.backup_verify import verify_basic, verify_deep
from modules.rescue_backup_discovery import read_backup_metadata, validate_backup_for_restore_simulation
from modules.rescue_boot_restore_check import simulate_boot_preconditions
from core.device_identity import build_device_identity
from modules.rescue_target_assessment import (
    assess_preview_directory,
    assess_target_device,
    compare_backup_to_preview_dir,
    compare_backup_to_target,
    detect_restore_blockers,
    recommend_new_target_disk,
)
from modules.restore_engine import restore_files

Runner = Callable[..., Any] | None

DRYRUN_REPORT_JSON = Path("/tmp/setuphelfer-rescue-dryrun.json")
DRYRUN_REPORT_MD = Path("/tmp/setuphelfer-rescue-dryrun.md")

ROOT_RESTORE_ALLOWED_PREFIXES = ("/home", "/mnt/setuphelfer")
ROOT_RESTORE_BLOCKED_PREFIXES = (
    "/etc",
    "/usr",
    "/bin",
    "/sbin",
    "/lib",
    "/lib64",
    "/boot",
    "/dev",
    "/proc",
    "/sys",
    "/run",
    "/var",
)


def analyze_tar_members_for_rescue(backup_file: str) -> dict[str, Any]:
    """Gleiche Logik wie ``app._analyze_tar_members``, mit ``r:*`` für Kompression."""
    info = {
        "total_files": 0,
        "total_dirs": 0,
        "total_other": 0,
        "blocked_entries": [],
        "system_like_entries": [],
    }
    allowed_member_types = {
        tarfile.REGTYPE,
        tarfile.AREGTYPE,
        tarfile.DIRTYPE,
        tarfile.SYMTYPE,
        tarfile.LNKTYPE,
    }
    _ct = getattr(tarfile, "CONTTYPE", None)
    if _ct is not None:
        allowed_member_types.add(_ct)
    gnu_meta_types = set()
    for _attr in ("GNUTYPE_LONGNAME", "GNUTYPE_LONGLINK", "GNUTYPE_SPARSE"):
        if hasattr(tarfile, _attr):
            gnu_meta_types.add(getattr(tarfile, _attr))

    def is_blocked_path(name: str) -> bool:
        n = name.lstrip("./")
        if not n:
            return True
        if n.startswith("/") or n.startswith("../") or "/../" in f"/{n}/":
            return True
        return False

    def is_system_like(name: str) -> bool:
        n = "/" + name.lstrip("/")
        return any(
            n.startswith(p + "/") or n == p for p in ROOT_RESTORE_ALLOWED_PREFIXES + ROOT_RESTORE_BLOCKED_PREFIXES
        )

    with tarfile.open(backup_file, "r:*") as tf:
        for member in tf.getmembers():
            if member.type in gnu_meta_types:
                continue
            name = member.name or ""
            if member.isdir():
                info["total_dirs"] += 1
            elif member.isfile():
                info["total_files"] += 1
            else:
                info["total_other"] += 1
            if is_system_like(name):
                info["system_like_entries"].append(name)
            is_special = bool(getattr(member, "isdev", lambda: False)()) or bool(
                getattr(member, "isfifo", lambda: False)()
            )
            bad_type = member.type not in allowed_member_types
            if is_blocked_path(name) or is_special or bad_type:
                info["blocked_entries"].append(name)
    return info


def simulate_restore_plan(
    backup_path: Path,
    target_device: str | None,
    mode: str,
) -> dict[str, Any]:
    steps = [
        {"order": 1, "code": "rescue.dryrun.step.path_allowlist"},
        {"order": 2, "code": "rescue.dryrun.step.tar_member_policy"},
        {"order": 3, "code": "rescue.dryrun.step.backup_verify_basic"},
    ]
    if mode == "dryrun":
        steps.append({"order": 4, "code": "rescue.dryrun.step.verify_deep_sandbox"})
        steps.append({"order": 5, "code": "rescue.dryrun.step.restore_engine_dry_run"})
        steps.append({"order": 6, "code": "rescue.dryrun.step.bootability_estimate"})
    if target_device:
        steps.insert(2, {"order": 2, "code": "rescue.dryrun.step.target_device_assessment"})
    return {"steps": steps, "mode": mode, "backup_path": str(backup_path), "target_device": target_device}


def simulate_archive_extraction(
    archive_path: Path,
    *,
    mode: str,
    extract_parent: Path,
    runner: Runner = None,
) -> dict[str, Any]:
    out: dict[str, Any] = {
        "simulation_status": "DRYRUN_BLOCKED",
        "codes": [],
        "staging_path": None,
        "verify_message_key": None,
    }
    analysis = analyze_tar_members_for_rescue(str(archive_path))
    out["tar_analysis"] = analysis
    if analysis.get("blocked_entries"):
        out["codes"].append("rescue.dryrun.blocked_tar_entries")
        return out

    ok, key, _detail = verify_basic(archive_path, runner=runner)
    if not ok:
        out["codes"].append("rescue.dryrun.verify_basic_failed")
        out["verify_message_key"] = key
        return out

    if mode == "analyze_only":
        out["simulation_status"] = "DRYRUN_OK"
        out["codes"].append("rescue.dryrun.analyze_only_ok")
        return out

    extract_parent.mkdir(parents=True, exist_ok=True)
    vd_ok, vd_key, details = verify_deep(
        archive_path,
        extract_root=extract_parent,
        verify_checksums=True,
        try_loop_mount_image=False,
        strict_archive_manifest=False,
        runner=runner,
    )
    staging = (details or {}).get("staging")
    out["staging_path"] = staging
    out["verify_deep_details_keys"] = list((details or {}).keys()) if isinstance(details, dict) else []
    if not vd_ok:
        out["simulation_status"] = "DRYRUN_BLOCKED"
        out["codes"].append("rescue.dryrun.verify_deep_failed")
        out["verify_message_key"] = vd_key
        return out

    if isinstance(staging, str) and Path(staging).is_dir():
        ok_rd, rd_key, rd_err = restore_files(
            archive_path,
            Path(staging),
            allowed_target_prefixes=RESCUE_DRYRUN_WRITE_PREFIXES,
            dry_run=True,
            runner=runner,
        )
        if not ok_rd:
            out["simulation_status"] = "DRYRUN_BLOCKED"
            out["codes"].append("rescue.dryrun.restore_engine_dry_run_failed")
            out["restore_engine_key"] = rd_key
            out["restore_engine_detail_type"] = type(rd_err).__name__ if rd_err else None
            return out

    out["simulation_status"] = "DRYRUN_OK"
    out["codes"].append("rescue.dryrun.extract_simulation_ok")
    return out


def simulate_partition_mapping(
    manifest: dict[str, Any] | None,
    target_device: str | None,
    *,
    runner: Runner = None,
) -> dict[str, Any]:
    from modules.inspect_storage import read_partition_table

    out: dict[str, Any] = {
        "codes": [],
        "backup_has_sfdisk_dump": False,
        "target_table_readable": False,
    }
    layout = ""
    if isinstance(manifest, dict):
        layout = str(manifest.get("partition_layout_sfdisk_d") or "").strip()
        out["backup_has_sfdisk_dump"] = bool(layout)
    if not target_device:
        out["codes"].append("rescue.dryrun.partition_skip_no_target")
        return out
    pt = read_partition_table(target_device, runner=runner)
    out["target_table_readable"] = bool(pt.get("ok"))
    if not layout:
        out["codes"].append("rescue.dryrun.partition_layout_not_in_backup")
    elif not pt.get("ok"):
        out["codes"].append("rescue.dryrun.partition_target_unreadable")
    else:
        out["codes"].append("rescue.dryrun.partition_compare_heuristic_ok")
        out["layout_line_counts"] = {
            "backup": len(layout.splitlines()),
            "target": len((pt.get("text") or "").splitlines()),
        }
    return out


def build_restore_risk_report(
    *,
    backup_assessment: dict[str, Any],
    target_assessment: dict[str, Any],
    target_compare: dict[str, Any],
    dryrun: dict[str, Any],
    bootability: dict[str, Any],
) -> list[RescueFinding]:
    findings: list[RescueFinding] = []

    def add(code: str, area: str, evidence: dict[str, Any] | None = None) -> None:
        findings.append(
            RescueFinding(
                code=code,
                area=area,
                risk_level=_restore_finding_risk(code),
                evidence=evidence or {},
            )
        )

    for c in backup_assessment.get("codes") or []:
        if c != "rescue.backup.ok":
            add(c, "backup", {})
    for c in target_assessment.get("codes") or []:
        add(c, "target", {})
    for c in target_compare.get("codes") or []:
        if c not in ("rescue.target.capacity_ok", "rescue.target.preview_space_ok"):
            add(c, "target", {})
    for c in dryrun.get("codes") or []:
        add(c, "dryrun", {})
    est = (bootability or {}).get("estimate") or {}
    bcls = est.get("bootability_class")
    if bcls == "BOOTABLE_UNLIKELY":
        add("rescue.bootability.class_unlikely", "bootability", {})
    elif bcls == "BOOTABLE_UNCERTAIN":
        add("rescue.bootability.class_uncertain", "bootability", {})
    elif bcls == "BOOTABLE_LIKELY":
        add("rescue.bootability.class_likely", "bootability", {})

    if not findings:
        add("rescue.dryrun.no_negative_findings", "dryrun", {})
    return findings


def _restore_finding_risk(code: str) -> RescueRiskLevel:
    red = {
        "rescue.dryrun.blocked_tar_entries",
        "rescue.dryrun.verify_basic_failed",
        "rescue.dryrun.verify_deep_failed",
        "rescue.dryrun.restore_engine_dry_run_failed",
        "rescue.backup.incremental_needs_full",
        "rescue.backup.verify_failed",
        "rescue.backup.manifest_kind_mismatch",
        "rescue.target.smart_critical",
        "rescue.target.capacity_insufficient",
        "rescue.target.preview_space_insufficient",
        "rescue.bootability.class_unlikely",
        "rescue.target.preview_not_allowlisted",
    }
    if code in red:
        return "red"
    green = {
        "rescue.backup.ok",
        "rescue.dryrun.extract_simulation_ok",
        "rescue.dryrun.analyze_only_ok",
        "rescue.bootability.class_likely",
        "rescue.target.capacity_ok",
        "rescue.target.preview_space_ok",
        "rescue.dryrun.no_negative_findings",
    }
    if code in green:
        return "green"
    return "yellow"


def _aggregate_risk(findings: list[RescueFinding]) -> RescueRiskLevel:
    if any(f.risk_level == "red" for f in findings):
        return "red"
    if any(f.risk_level == "yellow" for f in findings):
        return "yellow"
    return "green"


def _compute_decision(
    *,
    mode: str,
    backup_class: str,
    dry_status: str,
    boot_class: str | None,
    blockers: list[str],
    recommend_disk: str | None,
    encryption_key_available: bool,
) -> tuple[RescueRiskLevel, str, list[str]]:
    actions: list[str] = []
    if recommend_disk:
        actions.append(recommend_disk)

    if backup_class == "BACKUP_ENCRYPTED_KEY_REQUIRED":
        if not encryption_key_available:
            return "red", "do_not_restore", actions + ["rescue.decision.action.provide_encryption_key"]
        return "yellow", "proceed_with_explicit_risk_ack", actions + ["rescue.decision.action.encrypted_backup_cannot_simulate"]

    if backup_class == "BACKUP_WARN_INCOMPLETE":
        return "red", "do_not_restore", actions + ["rescue.decision.action.obtain_full_backup"]

    if backup_class == "BACKUP_CORRUPT":
        return "red", "recommend_data_recovery_first", actions

    if backup_class in ("BACKUP_UNSUPPORTED", "BACKUP_VERSION_MISMATCH"):
        return "red", "do_not_restore", actions

    if dry_status == "DRYRUN_BLOCKED":
        return "red", "do_not_restore", actions + ["rescue.decision.action.review_dryrun_blockers"]

    if recommend_disk:
        return "red", "recommend_new_target_disk", actions

    if mode == "analyze_only" and backup_class == "BACKUP_OK" and dry_status == "DRYRUN_OK":
        return "yellow", "proceed_with_explicit_risk_ack", actions + ["rescue.decision.action.run_full_dryrun_for_boot"]

    if boot_class == "BOOTABLE_UNLIKELY":
        return "yellow", "proceed_with_explicit_risk_ack", actions + ["rescue.decision.action.verify_boot_post_restore"]

    if boot_class == "BOOTABLE_UNCERTAIN":
        return "yellow", "proceed_with_explicit_risk_ack", actions + ["rescue.decision.action.boot_uncertain_plan_b"]

    if backup_class == "BACKUP_OK" and dry_status == "DRYRUN_OK" and boot_class == "BOOTABLE_LIKELY":
        risk: RescueRiskLevel = "green"
        for b in blockers:
            if "smart_warning" in b or "duplicate_uuid" in b:
                risk = "yellow"
                break
        if risk == "green":
            return "green", "proceed_possible", actions
        return "yellow", "proceed_with_explicit_risk_ack", actions

    if backup_class == "BACKUP_OK" and dry_status == "DRYRUN_OK":
        return "yellow", "proceed_with_explicit_risk_ack", actions

    return "yellow", "proceed_with_explicit_risk_ack", actions


def run_restore_dryrun_pipeline(
    req: RestoreDryRunRequest,
    *,
    runner: Runner = None,
    auth_session_id: str | None = None,
) -> RestoreDryRunResponse:
    generated = datetime.now(timezone.utc).isoformat()
    rescue_session_id = (auth_session_id or "").strip() or uuid.uuid4().hex
    findings: list[RescueFinding] = []
    try:
        bp = assert_backup_readable_path(req.backup_file)
    except ValueError as e:
        return RestoreDryRunResponse(
            status="error",
            restore_risk_level="red",
            restore_decision="do_not_restore",
            backup_assessment={"path": req.backup_file, "backup_class": "BACKUP_UNSUPPORTED", "codes": ["rescue.dryrun.path_not_allowed"]},
            target_assessment={},
            dryrun={"simulation_status": "DRYRUN_BLOCKED", "codes": ["rescue.dryrun.path_not_allowed"]},
            bootability={},
            findings=[
                RescueFinding(
                    code="rescue.dryrun.path_not_allowed",
                    area="dryrun",
                    risk_level="red",
                    evidence={"error_type": type(e).__name__},
                )
            ],
            recommended_actions=["rescue.decision.action.use_allowed_backup_path"],
            report_paths={"json": str(DRYRUN_REPORT_JSON), "markdown": str(DRYRUN_REPORT_MD)},
            generated_at=generated,
            session_id=rescue_session_id,
        )

    meta = read_backup_metadata(bp)
    manifest = meta.get("manifest") if isinstance(meta.get("manifest"), dict) else None
    backup_assessment = validate_backup_for_restore_simulation(
        bp,
        encryption_key_available=bool(req.encryption_key_available),
        runner=runner,
    )
    backup_assessment["metadata_summary"] = {
        "manifest_kind": (manifest or {}).get("kind"),
        "manifest_version": (manifest or {}).get("version"),
        "created_at": (manifest or {}).get("created_at"),
    }

    target_assessment = assess_target_device(req.target_device, runner=runner)
    if req.target_device:
        target_compare = compare_backup_to_target(bp, target_assessment, runner=runner)
    else:
        target_compare = {"codes": [], "capacity_ok": None, "backup_uncompressed_estimate_bytes": None}

    staging_parent = Path("/tmp/setuphelfer-rescue-dryrun-staging") / uuid.uuid4().hex
    preview_dir = staging_parent / "preview"
    preview_dir.mkdir(parents=True, exist_ok=True)
    assert_dryrun_staging_path(str(preview_dir))

    preview_info = assess_preview_directory(preview_dir, runner=runner)
    prev_cmp = compare_backup_to_preview_dir(bp, preview_info)
    for c in prev_cmp.get("codes") or []:
        if c != "rescue.target.preview_space_ok" and target_compare.get("capacity_ok") is not False:
            target_compare.setdefault("codes", []).append(c)
    if prev_cmp.get("capacity_ok") is False:
        target_compare["capacity_ok"] = False

    blockers = detect_restore_blockers(backup_assessment, target_compare, target_assessment)
    rec_disk = recommend_new_target_disk(target_compare, target_assessment)

    plan = simulate_restore_plan(bp, req.target_device, req.mode)
    dry = simulate_archive_extraction(bp, mode=req.mode, extract_parent=staging_parent, runner=runner)
    part = simulate_partition_mapping(manifest, req.target_device, runner=runner)

    boot_wrap: dict[str, Any] = {}
    staging_path = dry.get("staging_path")
    if req.mode == "dryrun" and dry.get("simulation_status") == "DRYRUN_OK" and staging_path:
        boot_wrap = simulate_boot_preconditions(staging_path, runner=runner)
    else:
        boot_wrap = {
            "boot_status": {},
            "fstab_mapping": {},
            "bootloader": {},
            "estimate": {"bootability_class": "BOOTABLE_UNCERTAIN", "reason_codes": ["rescue.bootability.skipped_no_extract"]},
        }

    boot_est = (boot_wrap.get("estimate") or {}).get("bootability_class")
    dry_status = str(dry.get("simulation_status") or "DRYRUN_BLOCKED")

    findings = build_restore_risk_report(
        backup_assessment=backup_assessment,
        target_assessment=target_assessment,
        target_compare=target_compare,
        dryrun=dry,
        bootability=boot_wrap,
    )
    agg = _aggregate_risk(findings)

    risk, decision, actions = _compute_decision(
        mode=str(req.mode),
        backup_class=str(backup_assessment.get("backup_class")),
        dry_status=dry_status,
        boot_class=boot_est,
        blockers=blockers,
        recommend_disk=rec_disk,
        encryption_key_available=bool(req.encryption_key_available),
    )
    if agg == "red" and risk != "red":
        risk = "red"
    if agg == "yellow" and risk == "green":
        risk = "yellow"
    if decision == "proceed_possible" and risk != "green":
        decision = "proceed_with_explicit_risk_ack"

    dry["partition_mapping"] = part
    dry["plan"] = plan

    allow_restore_flag = (
        str(req.mode) == "dryrun"
        and dry.get("simulation_status") == "DRYRUN_OK"
        and risk != "red"
        and decision in ("proceed_possible", "proceed_with_explicit_risk_ack")
    )
    token_out: str | None = None
    if allow_restore_flag:
        from modules.rescue_restore_gate import persist_dry_run_grant

        token_out = uuid.uuid4().hex
        try:
            st_snap = bp.stat()
            snap_payload = {"size": int(st_snap.st_size), "mtime": float(st_snap.st_mtime)}
        except OSError:
            snap_payload = {}
        tid: dict[str, Any] | None = None
        if req.target_device and str(req.target_device).strip():
            tid = build_device_identity(str(req.target_device).strip(), runner=runner)
        bc = str(backup_assessment.get("backup_class") or "")
        backup_requires = bool(req.encryption_key_available) or str(bp).lower().endswith((".enc", ".gpg"))
        if bc == "BACKUP_ENCRYPTED_KEY_REQUIRED":
            backup_requires = True
        persist_dry_run_grant(
            token_out,
            {
                "token": token_out,
                "session_id": rescue_session_id,
                "session_source": "remote_db" if auth_session_id else "ephemeral",
                "created_at": generated,
                "backup_file": str(bp),
                "target_device": req.target_device,
                "restore_risk_level": risk,
                "restore_decision": decision,
                "allow_restore": True,
                "dryrun_mode": str(req.mode),
                "dryrun_simulation_status": dry.get("simulation_status"),
                "backup_snapshot": snap_payload,
                "target_device_identity": tid,
                "backup_requires_decryption": backup_requires,
            },
        )

    resp = RestoreDryRunResponse(
        status="ok",
        restore_risk_level=risk,
        restore_decision=decision,
        backup_assessment=backup_assessment,
        target_assessment={**target_assessment, "preview": preview_info, "preview_compare": prev_cmp},
        dryrun=dry,
        bootability=boot_wrap,
        findings=findings,
        recommended_actions=sorted(set(actions)),
        report_paths={"json": str(DRYRUN_REPORT_JSON), "markdown": str(DRYRUN_REPORT_MD)},
        generated_at=generated,
        dry_run_token=token_out,
        allow_restore=bool(allow_restore_flag),
        session_id=rescue_session_id,
    )

    try:
        DRYRUN_REPORT_JSON.write_text(resp.model_dump_json(indent=2), encoding="utf-8")
    except OSError:
        pass
    try:
        lines = [
            "# Setuphelfer Rescue Restore Dry-Run",
            "",
            f"generated_at: {generated}",
            f"restore_risk_level: {risk}",
            f"restore_decision: {decision}",
            "",
            "## Findings",
        ]
        for f in findings:
            lines.append(f"- `{f.code}` ({f.risk_level})")
        DRYRUN_REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    except OSError:
        pass

    if staging_parent.is_dir():
        shutil.rmtree(staging_parent, ignore_errors=True)

    return resp


__all__ = [
    "DRYRUN_REPORT_JSON",
    "DRYRUN_REPORT_MD",
    "analyze_tar_members_for_rescue",
    "build_restore_risk_report",
    "run_restore_dryrun_pipeline",
    "simulate_archive_extraction",
    "simulate_partition_mapping",
    "simulate_restore_plan",
]
