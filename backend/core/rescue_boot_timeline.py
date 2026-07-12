"""PI-RS-MSI-GUI-003 — rescue boot timeline planning and recording."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from core.rescue_msi_boot_profile import (
    forbidden_gui_progress_phases_under_tui_only,
    is_forbidden_gui_progress_message,
    msi_compat_active,
    resolve_rescue_boot_profile,
)
from core.rescue_session_evidence import load_current_session_meta

TIMELINE_SCHEMA_VERSION = 1
_DEFAULT_TIMELINE_PATH = Path("/run/setuphelfer/evidence/boot/boot-timeline.jsonl")
_DEFAULT_SUMMARY_PATH = Path("/run/setuphelfer/evidence/msi-rs011b/boot-summary.json")

_BASE_STEPS: tuple[tuple[str, str, str], ...] = (
    ("rescue_boot_status_visible", "Setuphelfer Rettungssystem wird geladen …", "rescue.boot.loading"),
    ("hardware_probe_started", "Hardware wird erkannt …", "rescue.boot.hardware_probe"),
    ("disk_probe_started", "Laufwerke werden geprüft …", "rescue.boot.disk_probe"),
    ("setup_logs_probe_started", "Protokollspeicher wird vorbereitet …", "rescue.boot.setup_logs_probe"),
    ("rescue_boot_status_visible", "Bitte warten Sie. Bitte nicht ausschalten.", "rescue.boot.please_wait"),
    ("network_probe_started", "Netzwerk wird geprüft …", "rescue.boot.network_probe"),
)

_GUI_STEP = (
    "x11_starting",
    "Grafische Oberfläche wird gestartet …",
    "rescue.boot.x11_starting",
)

_TUI_STEP = (
    "tui_mode_selected",
    "MSI-Kompatibilitätsmodus: Textoberfläche wird verwendet.",
    "rescue.boot.tui_mode_selected",
)

_BACKEND_STEP = (
    "backend_starting",
    "Backend wird geprüft …",
    "rescue.boot.backend_starting",
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _session_fields() -> dict[str, Any]:
    meta = load_current_session_meta()
    if not meta:
        return {}
    return {
        "session_id": meta.get("session_id"),
        "boot_id": meta.get("boot_id"),
        "payload_version": meta.get("payload_version"),
    }


def plan_boot_progress_steps(cmdline: str, *, dmi_suggests_msi_ge63: bool = False) -> list[dict[str, Any]]:
    profile = resolve_rescue_boot_profile(cmdline, dmi_suggests_msi_ge63=dmi_suggests_msi_ge63)
    steps: list[dict[str, Any]] = []
    for phase, message_de, message_key in _BASE_STEPS:
        steps.append(
            {
                "phase": phase,
                "message_de": message_de,
                "message_en": message_de,
                "message_key": message_key,
                "render_tty": profile.get("gui_progress_allowed", True),
            }
        )
    if profile.get("boot_mode") == "tui_only":
        phase, message_de, message_key = _TUI_STEP
        steps.append(
            {
                "phase": phase,
                "message_de": message_de,
                "message_en": message_de,
                "message_key": message_key,
                "reason_code": profile.get("reason_code"),
                "gui_skipped": True,
                "console_target": "tty1",
                "render_tty": False,
            }
        )
        steps.append(
            {
                "phase": "gui_skipped",
                "message_de": "GUI-Start unter MSI-Compat übersprungen",
                "message_en": "GUI start skipped under MSI compat",
                "message_key": "rescue.boot.gui_skipped",
                "reason_code": profile.get("reason_code"),
                "gui_skipped": True,
                "render_tty": False,
                "audit_only": True,
            }
        )
    else:
        phase, message_de, message_key = _GUI_STEP
        steps.append(
            {
                "phase": phase,
                "message_de": message_de,
                "message_en": message_de,
                "message_key": message_key,
                "render_tty": True,
            }
        )
    phase, message_de, message_key = _BACKEND_STEP
    steps.append(
        {
            "phase": phase,
            "message_de": message_de,
            "message_en": message_de,
            "message_key": message_key,
            "render_tty": profile.get("gui_progress_allowed", True),
        }
    )
    return steps


def plan_boot_progress_steps_json(cmdline: str, *, dmi_suggests_msi_ge63: bool = False) -> str:
    return json.dumps(plan_boot_progress_steps(cmdline, dmi_suggests_msi_ge63=dmi_suggests_msi_ge63), ensure_ascii=False)


def build_timeline_event(
    *,
    phase: str,
    status: str,
    message_de: str,
    message_en: str | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    event: dict[str, Any] = {
        "schema_version": TIMELINE_SCHEMA_VERSION,
        "timestamp": _utc_now(),
        "monotonic_ms": 0,
        "phase": phase,
        "status": status,
        "message_de": message_de,
        "message_en": message_en or message_de,
        "evidence_paths": [],
        "error_code": None,
        "next_step": None,
    }
    event.update(_session_fields())
    if extra:
        event.update(extra)
    return event


def append_timeline_event(
    event: dict[str, Any],
    *,
    timeline_path: Path | None = None,
) -> Path:
    target = timeline_path or _DEFAULT_TIMELINE_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False) + "\n")
    return target


def record_timeline_phase(
    *,
    phase: str,
    status: str,
    message_de: str,
    message_en: str | None = None,
    extra: dict[str, Any] | None = None,
    timeline_path: Path | None = None,
) -> dict[str, Any]:
    event = build_timeline_event(
        phase=phase,
        status=status,
        message_de=message_de,
        message_en=message_en,
        extra=extra,
    )
    append_timeline_event(event, timeline_path=timeline_path)
    return event


def validate_timeline_for_profile(events: list[dict[str, Any]], profile: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    phases = [str(e.get("phase") or "") for e in events]
    messages = [str(e.get("message_de") or "") for e in events]
    if profile.get("boot_mode") == "tui_only":
        forbidden = forbidden_gui_progress_phases_under_tui_only()
        for phase in phases:
            if phase in forbidden:
                errors.append(f"forbidden_phase:{phase}")
        for message in messages:
            if is_forbidden_gui_progress_message(message):
                errors.append(f"forbidden_message:{message}")
        if "tui_mode_selected" not in phases:
            errors.append("missing_phase:tui_mode_selected")
    elif profile.get("boot_mode") == "gui_capable" and "x11_starting" not in phases:
        errors.append("missing_phase:x11_starting")
    return {"ok": not errors, "errors": errors, "phases": phases}


def simulate_msi_compat_boot(
    cmdline: str,
    *,
    dmi_suggests_msi_ge63: bool = False,
) -> dict[str, Any]:
    profile = resolve_rescue_boot_profile(cmdline, dmi_suggests_msi_ge63=dmi_suggests_msi_ge63)
    events: list[dict[str, Any]] = []
    for marker in (
        ("boot_started", "started", "Boot gestartet"),
        ("hardware_detected", "ok", "Hardware erkannt"),
        ("msi_compat_detected", "ok", "MSI-Compat erkannt"),
        ("gui_availability_checked", "ok", "GUI-Verfügbarkeit geprüft"),
    ):
        events.append(build_timeline_event(phase=marker[0], status=marker[1], message_de=marker[2]))
    for step in plan_boot_progress_steps(cmdline, dmi_suggests_msi_ge63=dmi_suggests_msi_ge63):
        if step.get("audit_only"):
            events.append(
                build_timeline_event(
                    phase=str(step["phase"]),
                    status="skipped",
                    message_de=str(step["message_de"]),
                    extra={"audit_only": True, "gui_skipped": True},
                )
            )
            continue
        events.append(
            build_timeline_event(
                phase=str(step["phase"]),
                status="started",
                message_de=str(step["message_de"]),
                extra={
                    key: step[key]
                    for key in ("reason_code", "gui_skipped", "console_target", "message_key")
                    if key in step
                },
            )
        )
    events.append(build_timeline_event(phase="tui_initializing", status="started", message_de="TUI wird initialisiert"))
    events.append(build_timeline_event(phase="tui_owned", status="ok", message_de="TUI übernimmt tty1"))
    validation = validate_timeline_for_profile(events, profile)
    from core.rescue_console_ownership import build_console_ownership_state

    console_state = build_console_ownership_state(owner="tui", lifecycle_state="tui_owned")
    return {
        "physical_boot_verified": False,
        "production_hardware_verified": False,
        "cmdline": cmdline,
        "msi_compat_active": msi_compat_active(cmdline),
        "profile": profile,
        "timeline_phases": [e.get("phase") for e in events],
        "timeline_validation": validation,
        "console_state": {
            "owner": console_state.get("owner"),
            "boot_progress_write_allowed": console_state.get("boot_progress_write_allowed"),
            "boot_progress_clear_allowed": console_state.get("boot_progress_clear_allowed"),
            "gui_transition_allowed": console_state.get("gui_transition_allowed"),
        },
        "events": events,
    }


def write_boot_summary(*, timeline_path: Path | None = None, summary_path: Path | None = None) -> dict[str, Any]:
    timeline = timeline_path or _DEFAULT_TIMELINE_PATH
    summary_target = summary_path or _DEFAULT_SUMMARY_PATH
    phases: list[str] = []
    if timeline.is_file():
        for line in timeline.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            data = json.loads(line)
            if isinstance(data, dict) and data.get("phase"):
                phases.append(str(data["phase"]))
    body = {
        "schema_version": 1,
        "generated_at": _utc_now(),
        "phase_count": len(phases),
        "phases": phases,
    }
    body.update(_session_fields())
    summary_target.parent.mkdir(parents=True, exist_ok=True)
    summary_target.write_text(json.dumps(body, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return body


def _cli_record(args: argparse.Namespace) -> int:
    extra = {}
    if args.reason_code:
        extra["reason_code"] = args.reason_code
    if args.gui_skipped:
        extra["gui_skipped"] = True
    record_timeline_phase(
        phase=args.phase,
        status=args.status,
        message_de=args.message_de,
        message_en=args.message_en,
        extra=extra or None,
    )
    return 0


def _cli_plan(args: argparse.Namespace) -> int:
    cmdline = args.cmdline
    if cmdline is None:
        try:
            cmdline = Path("/proc/cmdline").read_text(encoding="utf-8", errors="replace")
        except OSError:
            cmdline = ""
    payload = {
        "profile": resolve_rescue_boot_profile(cmdline),
        "steps": plan_boot_progress_steps(cmdline),
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def _cli_simulate(args: argparse.Namespace) -> int:
    result = simulate_msi_compat_boot(args.cmdline)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["timeline_validation"]["ok"] else 2


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Rescue boot timeline helper")
    sub = parser.add_subparsers(dest="command", required=True)

    record = sub.add_parser("record")
    record.add_argument("--phase", required=True)
    record.add_argument("--status", default="started")
    record.add_argument("--message-de", required=True)
    record.add_argument("--message-en")
    record.add_argument("--reason-code")
    record.add_argument("--gui-skipped", action="store_true")
    record.set_defaults(func=_cli_record)

    plan = sub.add_parser("plan")
    plan.add_argument("--cmdline")
    plan.set_defaults(func=_cli_plan)

    simulate = sub.add_parser("simulate")
    simulate.add_argument("--cmdline", required=True)
    simulate.set_defaults(func=_cli_simulate)

    summary = sub.add_parser("summary")
    summary.set_defaults(func=lambda _a: (write_boot_summary(), 0)[1])

    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
