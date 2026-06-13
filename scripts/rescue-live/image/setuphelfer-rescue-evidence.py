#!/usr/bin/env python3
"""Setuphelfer Rescue Evidence CLI — invoked from live stick scripts (Phase R.3/R.4)."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_BACKEND = Path(__file__).resolve().parents[3] / "backend"
if _BACKEND.is_dir() and str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

# Live image install path fallback
for candidate in (
    Path("/usr/lib/setuphelfer/backend"),
    Path("/opt/setuphelfer/backend"),
):
    if candidate.is_dir() and str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))


def _cmd_bundle(_: argparse.Namespace) -> int:
    from core.rescue_evidence_bundle import write_rescue_evidence_bundle

    result = write_rescue_evidence_bundle()
    print(json.dumps({"status": result.get("status"), "json": result.get("json", {}).get("path")}, indent=2))
    return 0 if result.get("status") == "ok" else 1


def _cmd_matrix(_: argparse.Namespace) -> int:
    from core.rescue_test_matrix import write_rescue_test_matrix

    result = write_rescue_test_matrix()
    print(json.dumps({"status": result.get("status"), "history": result.get("history_path")}, indent=2))
    return 0 if result.get("status") == "ok" else 1


def _cmd_boot(_: argparse.Namespace) -> int:
    from core.rescue_boot_logger import write_boot_evidence_bundle

    result = write_boot_evidence_bundle()
    print(json.dumps({"status": result.get("status")}, indent=2))
    return 0 if result.get("status") == "ok" else 1


def _cmd_boot_init(_: argparse.Namespace) -> int:
    from core.rescue_persistence import initialize_boot_evidence_marker

    result = initialize_boot_evidence_marker()
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result.get("boot_marker_written") else 1


def _cmd_menu_action(args: argparse.Namespace) -> int:
    from core.rescue_persistence import write_rescue_json_evidence

    payload = {
        "action": args.action,
        "result_status": args.status,
        "detail": args.detail or "",
        "menu_mode": "tui",
    }
    write_rescue_json_evidence("menu", f"menu_action_{args.action}.json", payload)
    return 0


def _cmd_persist_detect(_: argparse.Namespace) -> int:
    from core.rescue_persistence import detect_rescue_stick_mount

    print(json.dumps(detect_rescue_stick_mount(), indent=2))
    return 0


def _cmd_kiosk_report(args: argparse.Namespace) -> int:
    from core.rescue_persistence import write_rescue_json_evidence, write_rescue_text_evidence

    path = Path(args.file)
    if not path.is_file():
        return 1
    payload = json.loads(path.read_text(encoding="utf-8"))
    json_result = write_rescue_json_evidence("rescue-ui", "kiosk_report_latest.json", payload)
    md_lines = [
        "# Kiosk Report",
        f"status: {payload.get('status')}",
        f"reason: {payload.get('reason')}",
        f"probe: {payload.get('probe')}",
    ]
    write_rescue_text_evidence("rescue-ui", "kiosk_report_latest.md", "\n".join(md_lines))
    print(json.dumps({"status": "ok", "path": json_result.get("path")}, indent=2))
    return 0


def _cmd_telemetry_spool(args: argparse.Namespace) -> int:
    from core.rescue_telemetry_spool import record_telemetry_send_failure, write_telemetry_event

    payload_path = Path(args.payload)
    if not payload_path.is_file():
        return 1
    payload = json.loads(payload_path.read_text(encoding="utf-8"))
    event_id = (args.event_id or "").strip() or f"telemetry-{payload.get('boot_id', 'unknown')}"
    event = {
        "reason": args.reason,
        "payload_hash_sha256": payload.get("payload_hash_sha256"),
        "boot_id": payload.get("boot_id"),
        "telemetry": payload,
    }
    result = write_telemetry_event(event, event_id=event_id)
    if args.reason:
        record_telemetry_send_failure(event_id, args.reason)
    print(json.dumps(result, indent=2))
    return 0 if result.get("status") == "ok" else 1


def _cmd_telemetry_mark_sent(args: argparse.Namespace) -> int:
    from core.rescue_telemetry_spool import mark_telemetry_event_sent

    result = mark_telemetry_event_sent(args.event_id, http_status=int(args.http_status))
    print(json.dumps(result, indent=2))
    return 0 if result.get("status") == "ok" else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Setuphelfer Rescue Evidence R.3/R.4")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("bundle", help="Write full evidence bundle").set_defaults(func=_cmd_bundle)
    sub.add_parser("matrix", help="Write test matrix").set_defaults(func=_cmd_matrix)
    sub.add_parser("boot", help="Write boot evidence").set_defaults(func=_cmd_boot)
    sub.add_parser("boot-init", help="Early boot marker + evidence tree (R.6)").set_defaults(func=_cmd_boot_init)
    sub.add_parser("detect", help="Detect stick mount").set_defaults(func=_cmd_persist_detect)

    menu_p = sub.add_parser("menu-action", help="Record TUI menu action")
    menu_p.add_argument("--action", required=True)
    menu_p.add_argument("--status", default="ok")
    menu_p.add_argument("--detail", default="")
    menu_p.set_defaults(func=_cmd_menu_action)

    kiosk_p = sub.add_parser("kiosk-report", help="Write kiosk probe evidence")
    kiosk_p.add_argument("--file", required=True)
    kiosk_p.set_defaults(func=_cmd_kiosk_report)

    tspool_p = sub.add_parser("telemetry-spool", help="Spool telemetry payload to R.3 evidence tree")
    tspool_p.add_argument("--payload", required=True)
    tspool_p.add_argument("--reason", default="")
    tspool_p.add_argument("--event-id", default="")
    tspool_p.set_defaults(func=_cmd_telemetry_spool)

    tmark_p = sub.add_parser("telemetry-mark-sent", help="Mark spooled telemetry event as sent")
    tmark_p.add_argument("--event-id", required=True)
    tmark_p.add_argument("--http-status", default="200")
    tmark_p.set_defaults(func=_cmd_telemetry_mark_sent)

    args = parser.parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
