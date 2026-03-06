"""
CLI für Debug: support-bundle.
Aufruf: python3 -m debug.cli support-bundle (aus backend/) oder ./scripts/support-bundle.sh.
"""

import argparse
import sys
from pathlib import Path

# Stell sicher, dass backend im Pfad ist (Aufruf aus Repo-Root oder backend/)
_backend = Path(__file__).resolve().parent.parent
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend.parent))

from debug.support_bundle import create_support_bundle
from debug.logger import set_run_id


def cmd_support_bundle(args: argparse.Namespace) -> int:
    out_dir = args.out_dir or getattr(args, "out_dir_pos", None)
    out_dir = Path(out_dir) if out_dir else None
    set_run_id()
    try:
        zip_path = create_support_bundle(
            output_dir=out_dir,
            max_log_lines=args.max_log_lines,
            include_system_logs=args.include_system_logs,
            include_debug_logs=args.include_debug_logs,
            include_snapshot=args.include_snapshot,
        )
        print(zip_path)
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def main() -> int:
    parser = argparse.ArgumentParser(description="PI-Installer Debug CLI")
    sub = parser.add_subparsers(dest="command", required=True)
    sb = sub.add_parser("support-bundle", help="Erzeuge Support-Bundle ZIP (Logs, Snapshot, Config)")
    sb.add_argument("out_dir_pos", nargs="?", default=None, help="Ausgabe-Verzeichnis (optional, wie --out-dir)")
    sb.add_argument(
        "--out-dir",
        default=None,
        help="Ausgabe-Verzeichnis (default aus config global.export.output_dir)",
    )
    sb.add_argument(
        "--max-log-lines",
        type=int,
        default=None,
        help="Max. Zeilen Debug-Logs im Bundle (default aus config)",
    )
    sb.add_argument("--no-include-system-logs", action="store_true", help="System-Logs weglassen")
    sb.add_argument("--no-include-debug-logs", action="store_true", help="Debug-JSONL-Logs weglassen")
    sb.add_argument("--no-include-snapshot", action="store_true", help="system_snapshot.json weglassen")
    parsed = parser.parse_args()
    if parsed.command == "support-bundle":
        parsed.include_system_logs = False if parsed.no_include_system_logs else None
        parsed.include_debug_logs = False if parsed.no_include_debug_logs else None
        parsed.include_snapshot = False if parsed.no_include_snapshot else None
        return cmd_support_bundle(parsed)
    return 0


if __name__ == "__main__":
    sys.exit(main())
