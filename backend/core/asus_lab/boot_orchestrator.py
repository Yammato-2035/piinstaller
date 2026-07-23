"""ASUS lab boot orchestrator — identity-gated autonomous capture path."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

from core.asus_lab.bios_control import build_capability_inventory, write_inventory
from core.asus_lab.carrier_consistency import (
    collect_workspace_carriers,
    evaluate_carrier_consistency,
)
from core.asus_lab.hardware_capture import run_baseline_hardware_capture
from core.asus_lab.run_context import build_run_context, create_run_directory, generate_run_id, utc_now
from core.asus_lab.windows_capture import prepare_windows_live_capture
from core.rescue_asus_lab_authorization import (
    PROFILE_ID,
    evaluate_machine_identity_match,
    load_lab_target_profile,
)
from core.rescue_win11_live_capture import resolve_setup_logs_roots

SCHEMA_VERSION = 1


def _default_boot_id() -> str:
    for cand in (Path("/proc/sys/kernel/random/boot_id"),):
        if cand.is_file():
            return cand.read_text(encoding="utf-8").strip()
    return "unknown-boot-id"


def _payload_version(repo_root: Path) -> str:
    cfg = repo_root / "config" / "rescue_payload_version.json"
    try:
        data = json.loads(cfg.read_text(encoding="utf-8"))
        return str(data.get("rescue_payload_version") or "")
    except (OSError, json.JSONDecodeError):
        return ""


def run_boot_orchestrator(
    *,
    repo_root: Path,
    setup_logs_candidates: Sequence[Path],
    observed_identity: Mapping[str, Any],
    run_type: str = "full-lab-capture",
    boot_id: str | None = None,
    skip_hardware_cmds: bool = False,
    identity_fn: Callable[..., dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Execute the autonomous boot capture sequence for ASUS_ROG_GABRIEL_LAB."""
    phases: list[dict[str, Any]] = []
    repo = Path(repo_root)
    expected = _payload_version(repo)

    # 1) Carrier consistency (workspace-level)
    carriers = collect_workspace_carriers(repo)
    carrier_gate = evaluate_carrier_consistency(carriers, expected_version=expected)
    phases.append({"phase": "carrier_check", **carrier_gate})
    if not carrier_gate.get("build_allowed"):
        # Workspace may intentionally differ project_version vs rescue payload — only enforce
        # rescue payload carriers when they disagree with expected rescue version.
        rescue_only = {
            k: v
            for k, v in carriers.items()
            if "rescue_payload_version" in k
        }
        carrier_gate = evaluate_carrier_consistency(rescue_only, expected_version=expected)
        phases[-1] = {"phase": "carrier_check", **carrier_gate, "scoped": "rescue_payload_only"}
        if not carrier_gate.get("build_allowed"):
            return {
                "ok": False,
                "blocked_reason": "carrier_version_inconsistency",
                "phases": phases,
                "bitlocker_mutation": False,
            }

    # 2-4) Boot + identity
    bid = boot_id or _default_boot_id()
    match_fn = identity_fn or evaluate_machine_identity_match
    match = match_fn(observed=observed_identity)
    phases.append({"phase": "identity", "match": match.get("match"), "grants_usable": match.get("grants_usable")})
    if not match.get("grants_usable"):
        return {
            "ok": False,
            "blocked_reason": "identity_not_exact_match",
            "identity": match,
            "phases": phases,
            "bitlocker_mutation": False,
        }

    # 5-6) SETUP_LOGS
    roots = resolve_setup_logs_roots(list(setup_logs_candidates))
    phases.append({"phase": "setup_logs", **{k: roots.get(k) for k in ("setup_capture_ready", "selected", "candidates")}})
    if not roots.get("setup_capture_ready"):
        return {
            "ok": False,
            "blocked_reason": "setup_logs_not_ready",
            "phases": phases,
            "bitlocker_mutation": False,
        }
    setup_logs = Path(str(roots["selected"]["path"]))

    # Free space probe
    usage = shutil_disk_usage(setup_logs)
    phases.append({"phase": "disk_space", **usage})
    if usage.get("free_bytes", 0) < 64 * 1024 * 1024:
        return {
            "ok": False,
            "blocked_reason": "insufficient_setup_logs_space",
            "phases": phases,
            "bitlocker_mutation": False,
        }

    # 7-9) Run context + directory
    prof = load_lab_target_profile()
    machine_id = str(prof.get("machine_id") or observed_identity.get("machine_id") or "")
    ctx = build_run_context(
        run_type=run_type,
        boot_id=bid,
        machine_id=machine_id,
        payload_version=expected,
    )
    runs_root = setup_logs / "asus-lab-runs"
    runs_root.mkdir(parents=True, exist_ok=True)
    run_root = create_run_directory(runs_root, ctx["run_id"])
    (run_root / "result" / "run_context.json").write_text(json.dumps(ctx, indent=2) + "\n", encoding="utf-8")
    phases.append({"phase": "run_created", "run_id": ctx["run_id"], "run_root": str(run_root)})

    # 10-12) Baseline capture
    if skip_hardware_cmds:
        hw = {"status": "skipped_in_unit_test", "warnings": 0}
    else:
        hw = run_baseline_hardware_capture(run_root)
    phases.append({"phase": "hardware_capture", **hw})

    bios_inv = build_capability_inventory(
        observed={
            "SecureBoot": observed_identity.get("secure_boot_state") or "unknown",
        }
    )
    write_inventory(run_root / "bios" / "bios_capability_inventory.json", bios_inv)
    phases.append({"phase": "bios_inventory", "settings": len(bios_inv.get("settings") or [])})

    # 13) Windows live capture readiness (always prepare tree for win11 / full)
    win_prep = {"ok": False, "skipped": True}
    if run_type in {"win11-live-capture", "full-lab-capture"}:
        win_run_id = ctx["run_id"] if ctx["run_id"].startswith("asus-win11-") else generate_run_id("win11-live-capture")
        win_prep = prepare_windows_live_capture(
            setup_logs_candidates=[setup_logs],
            run_id=win_run_id,
        )
        (run_root / "windows" / "live_capture_prepare.json").write_text(
            json.dumps(win_prep, indent=2) + "\n", encoding="utf-8"
        )
    phases.append({"phase": "windows_prepare", "ok": win_prep.get("ok"), "run_id": win_prep.get("run_id")})

    # 14-15) Finalize + auto-import marker
    summary = {
        "schema_version": SCHEMA_VERSION,
        "profile_id": PROFILE_ID,
        "run_id": ctx["run_id"],
        "boot_id": bid,
        "payload_version": expected,
        "status": "capture_finalized",
        "phases": phases,
        "windows_live_capture_prepared": bool(win_prep.get("ok")),
        "definitive_freeze_root_cause_known": False,
        "bitlocker_mutation": False,
        "completed_at": utc_now(),
    }
    (run_root / "result" / "orchestrator_summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    (run_root / "AUTO_IMPORT.READY").write_text(ctx["run_id"] + "\n", encoding="utf-8")
    (setup_logs / "asus-lab-import-queue" / f"{ctx['run_id']}.ready").parent.mkdir(parents=True, exist_ok=True)
    (setup_logs / "asus-lab-import-queue" / f"{ctx['run_id']}.ready").write_text(
        json.dumps({"run_id": ctx["run_id"], "run_root": str(run_root), "queued_at": utc_now()}, indent=2)
        + "\n",
        encoding="utf-8",
    )

    return {"ok": True, **summary, "run_root": str(run_root)}


def shutil_disk_usage(path: Path) -> dict[str, Any]:
    import shutil

    usage = shutil.disk_usage(path)
    return {"free_bytes": usage.free, "total_bytes": usage.total, "used_bytes": usage.used}
