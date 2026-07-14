"""PI-RS-MSI-AUTO-EVIDENCE-001 — Evaluate late MSI boot evidence (no PII)."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

_FORBIDDEN_TIMELINE_PHASES = frozenset({"x11_starting", "gui_starting"})
_FORBIDDEN_PROCESSES = frozenset({"openvt", "startx", "Xorg", "Xorg.bin", "chromium"})
_MIN_LATE_UPTIME_SEC = 120.0


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def _read_uptime_sec() -> float | None:
    try:
        raw = Path("/proc/uptime").read_text(encoding="utf-8").split()[0]
        return float(raw)
    except (OSError, ValueError, IndexError):
        return None


def _timeline_phases(timeline_path: Path) -> list[str]:
    if not timeline_path.is_file():
        return []
    phases: list[str] = []
    for line in timeline_path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        phase = str(row.get("phase") or "")
        if phase:
            phases.append(phase)
    return phases


def _late_evidence_present(evidence_dir: Path) -> bool:
    if not evidence_dir.is_dir():
        return False
    return any(
        p.name.startswith("late-evidence-") and p.suffix == ".txt"
        for p in evidence_dir.iterdir()
        if p.is_file()
    )


def _processes_running() -> set[str]:
    import subprocess

    try:
        proc = subprocess.run(
            ["ps", "-ef"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return set()
    found: set[str] = set()
    for name in _FORBIDDEN_PROCESSES:
        if re.search(rf"\b{re.escape(name)}\b", proc.stdout or ""):
            found.add(name)
    return found


def evaluate_msi_lab_evidence(
    *,
    evidence_dir: Path | None = None,
    console_ownership_path: Path | None = None,
    timeline_path: Path | None = None,
    session_meta_path: Path | None = None,
    payload_version: str = "",
    min_late_uptime_sec: float = _MIN_LATE_UPTIME_SEC,
    uptime_sec: float | None = None,
    check_processes: bool = False,
    lab_auto_unattended: bool = False,
) -> dict[str, Any]:
    ev_dir = evidence_dir or Path("/run/setuphelfer/esp-rw/setuphelfer/evidence/msi-rs011b")
    ownership = _read_json(console_ownership_path or Path("/run/setuphelfer/console-ownership.json")) or {}
    session = _read_json(session_meta_path or Path("/run/setuphelfer/current-session.json")) or {}
    timeline_candidates = [
        timeline_path,
        Path("/run/setuphelfer-rescue/boot-timeline.jsonl"),
        Path("/var/log/setuphelfer/boot-timeline.jsonl"),
        ev_dir / "boot-timeline.jsonl",
    ]
    timeline_file = next((p for p in timeline_candidates if p and p.is_file()), None)
    phases = _timeline_phases(timeline_file) if timeline_file else []

    owner = str(ownership.get("owner") or "")
    lifecycle = str(ownership.get("lifecycle_state") or "")
    tui_owned = lifecycle in {"tui_initializing", "tui_owned"} or owner == "tui"
    capture_uptime = uptime_sec if uptime_sec is not None else _read_uptime_sec()

    warnings: list[str] = []
    errors: list[str] = []

    if capture_uptime is None:
        errors.append("uptime_unavailable")
    elif capture_uptime < min_late_uptime_sec:
        errors.append("capture_uptime_below_120s")
        warnings.append(f"Capture at ~{capture_uptime:.1f}s uptime — below {min_late_uptime_sec:.0f}s gate")

    if not tui_owned:
        msg = f"console-ownership shows owner={owner!r} lifecycle={lifecycle!r}"
        if lab_auto_unattended:
            warnings.append(msg)
        else:
            errors.append("console_owner_not_tui")
            warnings.append(msg)

    if "tui_mode_selected" not in phases:
        if lab_auto_unattended:
            warnings.append("tui_mode_selected_missing (lab auto unattended — non-blocking)")
        else:
            errors.append("tui_mode_selected_missing")

    forbidden_in_timeline = sorted(_FORBIDDEN_TIMELINE_PHASES.intersection(phases))
    if forbidden_in_timeline:
        errors.append("forbidden_timeline_phase_present")
        warnings.append(f"Timeline contains forbidden phases: {', '.join(forbidden_in_timeline)}")

    running = _processes_running() if check_processes else set()
    if running:
        errors.append("forbidden_process_running")
        warnings.append(f"Forbidden processes running: {', '.join(sorted(running))}")

    late_file = _late_evidence_present(ev_dir)
    if not late_file:
        errors.append("late_evidence_file_missing")

    boot_progress_write = bool(ownership.get("boot_progress_write_allowed"))
    if tui_owned and boot_progress_write:
        errors.append("boot_progress_write_allowed_under_tui")
        warnings.append("boot_progress_write_allowed still true after TUI handoff")

    result_status = "passed" if not errors else "failed"
    if errors and capture_uptime is not None and capture_uptime >= min_late_uptime_sec and tui_owned:
        result_status = "review_required"

    return {
        "schema_version": 1,
        "evaluation_id": "PI-RS-MSI-AUTO-EVIDENCE-001",
        "result_status": result_status,
        "session_id": str(session.get("session_id") or ""),
        "boot_id": str(session.get("boot_id") or ownership.get("boot_id") or ""),
        "payload_version": payload_version,
        "capture_uptime_s": capture_uptime,
        "capture_after_120s": bool(capture_uptime is not None and capture_uptime >= min_late_uptime_sec),
        "console_owner": owner or lifecycle or "unknown",
        "tui_owned": tui_owned,
        "boot_progress_write_allowed": boot_progress_write,
        "boot_progress_clear_allowed": bool(ownership.get("boot_progress_clear_allowed")),
        "gui_transition_allowed": bool(ownership.get("gui_transition_allowed")),
        "tui_mode_selected_in_timeline": "tui_mode_selected" in phases,
        "x11_starting_present": "x11_starting" in phases,
        "forbidden_processes": sorted(running),
        "manual_late_evidence_file_present": late_file,
        "lab_auto_unattended": lab_auto_unattended,
        "evidence_complete": result_status == "passed",
        "warnings": warnings,
        "errors": errors,
    }
