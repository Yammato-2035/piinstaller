#!/usr/bin/env python3
"""Setuphelfer Rescue Evidence CLI — invoked from live stick scripts (Phase R.3)."""
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


def main() -> int:
    parser = argparse.ArgumentParser(description="Setuphelfer Rescue Evidence R.3")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("bundle", help="Write full evidence bundle").set_defaults(func=_cmd_bundle)
    sub.add_parser("matrix", help="Write test matrix").set_defaults(func=_cmd_matrix)
    sub.add_parser("boot", help="Write boot evidence").set_defaults(func=_cmd_boot)
    sub.add_parser("detect", help="Detect stick mount").set_defaults(func=_cmd_persist_detect)

    menu_p = sub.add_parser("menu-action", help="Record TUI menu action")
    menu_p.add_argument("--action", required=True)
    menu_p.add_argument("--status", default="ok")
    menu_p.add_argument("--detail", default="")
    menu_p.set_defaults(func=_cmd_menu_action)

    args = parser.parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
