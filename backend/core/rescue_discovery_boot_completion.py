"""Boot finalizer + discovery observability validation (001D7C)."""

from __future__ import annotations

import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from core.rescue_component_heartbeat import write_component_heartbeat
from core.rescue_discovery_observability import (
    boot_id,
    discovery_boot_dir,
    persist_boot_finalizer,
    read_runtime_json,
    redact_text,
    runtime_discovery_dir,
)
from core.rescue_discovery_run_control import (
    consume_discovery_run_control,
    load_discovery_run_control,
)
from core.rescue_payload_version import rescue_payload_version
from core.rescue_physical_e2e_evidence_import import find_setup_logs_mount

REQUIRED_OBSERVABILITY = (
    "00-start-gate.json",
    "01-service-start.json",
    "02-orchestrator-exit.json",
    "03-service-result.json",
    "boot-finalizer.json",
)

UNITS = (
    "setuphelfer-rescue-auto-discovery.service",
    "setuphelfer-rescue-tui.service",
    "setuphelfer-rescue-tui-guard.service",
    "setuphelfer-rescue-tui-hold.service",
    "setuphelfer-rescue-auto-msi-evidence.service",
    "setuphelfer-rescue-auto-shutdown.service",
    "setuphelfer-rescue-lab-auto-shutdown-failsafe.service",
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _state_dir() -> Path:
    return Path(os.environ.get("SETUPHELFER_RESCUE_STATE_DIR", "/run/setuphelfer-rescue"))


def _run(cmd: list[str], *, timeout: int = 60) -> str:
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, check=False, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return f"# error: {exc}\n"
    return (proc.stdout or "") + (proc.stderr or "")


def harvest_late_journal(*, setup_logs_base: Path | None = None) -> dict[str, Any]:
    """Collect redacted late journal + systemd show for discovery observability."""
    write_component_heartbeat("boot_finalizer", state="harvesting")
    base = setup_logs_base or find_setup_logs_mount()
    bid = boot_id()
    out_dir = discovery_boot_dir(base, bid)
    runtime_discovery_dir()

    chunks: list[str] = []
    chunks.append("=== journalctl -b -n 800 ===\n")
    chunks.append(redact_text(_run(["journalctl", "-b", "-n", "800", "--no-pager"])))
    for unit in UNITS:
        chunks.append(f"\n=== journalctl -u {unit} -n 200 ===\n")
        chunks.append(redact_text(_run(["journalctl", "-u", unit, "-n", "200", "--no-pager"])))

    status: dict[str, Any] = {"schema": "setuphelfer.rescue.discovery-service-status-late.v1", "boot_id": bid, "units": []}
    for unit in UNITS:
        show = _run(
            [
                "systemctl",
                "show",
                unit,
                "--property=LoadState,ActiveState,SubState,Result,ConditionResult,ExecMainStartTimestamp,ExecMainExitTimestamp,ExecMainCode,ExecMainStatus,InvocationID",
            ]
        )
        status_blob = _run(["systemctl", "status", unit, "--no-pager", "-l"])
        status["units"].append(
            {
                "unit": unit,
                "show": redact_text(show.strip()),
                "status_excerpt": redact_text(status_blob[:4000]),
            }
        )

    journal_path = out_dir / "late-journal.redacted.log"
    journal_path.write_text("".join(chunks), encoding="utf-8")
    status_path = out_dir / "service-status-late.json"
    status_path.write_text(json.dumps(status, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    # Runtime copies for TUI / failsafe.
    runtime = Path(os.environ.get("SETUPHELFER_RESCUE_DISCOVERY_DIR", "/run/setuphelfer-rescue/discovery"))
    runtime.mkdir(parents=True, exist_ok=True)
    (runtime / "late-journal.redacted.log").write_text(journal_path.read_text(encoding="utf-8"), encoding="utf-8")
    (runtime / "service-status-late.json").write_text(
        json.dumps(status, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    write_component_heartbeat("boot_finalizer", state="harvest_done")
    return {
        "boot_id": bid,
        "journal_path": str(journal_path),
        "status_path": str(status_path),
        "ok": True,
    }


def _observability_present(base: Path | None, bid: str) -> tuple[bool, list[str]]:
    missing: list[str] = []
    boot_dir = discovery_boot_dir(base, bid) if base else runtime_discovery_dir()
    for name in (
        "00-start-gate.json",
        "01-service-start.json",
        "02-orchestrator-exit.json",
        "03-service-result.json",
        "service-status-late.json",
        "late-journal.redacted.log",
    ):
        runtime_ok = (runtime_discovery_dir() / name).is_file() or (
            runtime_discovery_dir() / name.replace("00-", "").replace("01-", "").replace("02-", "").replace("03-", "")
        ).is_file()
        persist_ok = (boot_dir / name).is_file() if base else runtime_ok
        # Accept either runtime or persistent for most; late journal prefers persistent.
        if name.startswith("late-") or name.startswith("service-status"):
            if not persist_ok and not (runtime_discovery_dir() / name).is_file():
                missing.append(name)
        elif not persist_ok and not runtime_ok and not read_runtime_json(name):
            # Also check short names.
            short = {
                "00-start-gate.json": "start-gate.json",
                "01-service-start.json": "service-start.json",
                "02-orchestrator-exit.json": "orchestrator-exit.json",
                "03-service-result.json": "service-result.json",
            }.get(name)
            if not (short and read_runtime_json(short)):
                missing.append(name)
    return (not missing, missing)


def evaluate_discovery_boot_completion(
    *,
    setup_logs_base: Path | None = None,
    force_harvest: bool = True,
) -> dict[str, Any]:
    """Validate observability + consume run-control when discovery expected."""
    write_component_heartbeat("boot_finalizer", state="finalizing")
    base = setup_logs_base or find_setup_logs_mount()
    bid = boot_id()

    if force_harvest:
        try:
            harvest_late_journal(setup_logs_base=base)
        except OSError:
            pass

    control = load_discovery_run_control(base) if base else None

    # Deliberately disabled + not consumed → do not force discovery / do not consume.
    if control and control.get("run_mode") == "auto_discovery_only" and not control.get("enabled") and not control.get("consumed"):
        final = persist_boot_finalizer(
            {
                "status": "discovery_control_disabled",
                "observability_complete": True,
                "run_control_consumed": False,
                "shutdown_safe": True,
                "missing": [],
                "notes": ["run_control_disabled_skip_no_consume"],
            }
        )
        return {"action": "none", "reason": "disabled", "finalizer": final}

    if control and control.get("consumed"):
        complete, missing = _observability_present(base, bid)
        final = persist_boot_finalizer(
            {
                "status": control.get("terminal_status") or "already_consumed",
                "observability_complete": complete,
                "run_control_consumed": True,
                "shutdown_safe": True,
                "missing": missing,
                "notes": ["run_control_already_consumed"],
            }
        )
        return {"action": "none", "reason": "already_consumed", "finalizer": final}

    if not control or control.get("run_mode") != "auto_discovery_only":
        final = persist_boot_finalizer(
            {
                "status": "discovery_not_expected",
                "observability_complete": True,
                "run_control_consumed": False,
                "shutdown_safe": True,
                "missing": [],
                "notes": ["no_discovery_run_control"],
            }
        )
        return {"action": "none", "reason": "not_expected", "finalizer": final}

    start_gate = read_runtime_json("start-gate.json") or read_runtime_json("00-start-gate.json")
    service_start = read_runtime_json("service-start.json") or read_runtime_json("01-service-start.json")
    orch_exit = read_runtime_json("orchestrator-exit.json") or read_runtime_json("02-orchestrator-exit.json")
    service_result = read_runtime_json("service-result.json") or read_runtime_json("03-service-result.json")

    complete, missing = _observability_present(base, bid)
    session_dir = None
    if base:
        sessions = base / "setuphelfer" / "evidence" / "sessions"
        if sessions.is_dir() and any(sessions.iterdir()):
            session_dir = str(sessions)

    # Determine terminal status.
    if orch_exit and orch_exit.get("exit_code") == 0 and session_dir:
        status = "rescue_auto_discovery_evidence_complete"
        failure_stage = ""
    elif orch_exit and orch_exit.get("exception_type"):
        status = str(orch_exit.get("status") or "failed_discovery_unhandled_exception")
        failure_stage = "orchestrator_exception"
    elif service_start and not orch_exit:
        status = "failed_discovery_orchestrator_no_exit"
        failure_stage = "orchestrator_missing_exit"
        missing.append("02-orchestrator-exit.json")
        complete = False
    elif start_gate and not start_gate.get("start_allowed"):
        status = str(start_gate.get("decision_code") or "discovery_start_gate_skipped")
        failure_stage = "start_gate"
    elif start_gate and start_gate.get("start_allowed") and not service_start:
        status = "failed_discovery_service_not_started"
        failure_stage = "service_start"
        if "01-service-start.json" not in missing:
            missing.append("01-service-start.json")
        complete = False
    elif not start_gate:
        status = "failed_discovery_start_gate_not_invoked"
        failure_stage = "start_gate_missing"
        complete = False
        if "00-start-gate.json" not in missing:
            missing.append("00-start-gate.json")
    else:
        status = "failed_discovery_session_never_persisted"
        failure_stage = "session_missing"

    if not complete and status not in {
        "rescue_auto_discovery_evidence_complete",
        "discovery_start_gate_skipped",
    }:
        if status == "failed_discovery_session_never_persisted" and missing:
            status = "failed_discovery_observability_incomplete"

    consumed = False
    if base and control and not control.get("consumed"):
        # Consume when terminal for one-shot (including skip due to invalid config / no start).
        # Do not consume when deliberately disabled before boot (enabled=false already).
        if control.get("enabled") or failure_stage:
            consume_discovery_run_control(
                base,
                consumed_by_boot_id=bid,
                terminal_status=status,
                failure_stage=failure_stage,
            )
            consumed = True

    final = persist_boot_finalizer(
        {
            "status": status,
            "observability_complete": complete and bool(orch_exit or start_gate),
            "run_control_consumed": consumed or bool(control and control.get("consumed")),
            "shutdown_safe": True,
            "missing": missing,
            "notes": [
                f"payload={rescue_payload_version()}",
                f"session_dir={'yes' if session_dir else 'no'}",
                f"service_result={(service_result or {}).get('status')}",
            ],
        }
    )
    write_component_heartbeat("boot_finalizer", state="terminal")
    try:
        (_state_dir() / "auto-discovery.done").write_text(status + "\n", encoding="utf-8")
    except OSError:
        pass

    # Compat alias for 001D7B tests: failed path that consumed control.
    action = "finalized"
    if consumed and status.startswith("failed_"):
        action = "failed_and_consumed"

    return {
        "action": action,
        "status": status,
        "observability_complete": final.get("observability_complete"),
        "run_control_consumed": consumed,
        "missing": missing,
        "finalizer": final,
        "failure_fully_observed": bool(
            start_gate and (orch_exit or not (start_gate.get("start_allowed"))) and consumed
        ),
    }


# Backwards-compatible alias used by failsafe / older callers.
FAILED_STATUS = "failed_discovery_service_not_started"
