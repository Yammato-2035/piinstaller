#!/usr/bin/env bash
# Read-only: extract validated ISO into FAT32 ESP staging layout.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

ISO=""
OUTPUT_DIR=""
usage() {
  echo "Usage: $0 --iso PATH --output-dir DIR" >&2
  exit 20
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --iso) ISO="$2"; shift 2 ;;
    --output-dir) OUTPUT_DIR="$2"; shift 2 ;;
    -h|--help) usage ;;
    *) echo "Unknown arg: $1" >&2; usage ;;
  esac
done

[[ -n "$ISO" && -n "$OUTPUT_DIR" ]] || usage
[[ -f "$ISO" ]] || { echo "ERROR: ISO missing: $ISO" >&2; exit 21; }

export PYTHONPATH="${REPO_ROOT}/backend${PYTHONPATH:+:$PYTHONPATH}"
python3 - <<PY
import json
import sys
from pathlib import Path

from core.rescue_fat32_esp_usb_writer import extract_iso_files

iso = Path(${ISO@Q})
out = Path(${OUTPUT_DIR@Q})
try:
    result = extract_iso_files(iso, out)
except OSError as exc:
    print(f"ERROR: {exc}", file=sys.stderr)
    raise SystemExit(22) from exc
print(json.dumps(result, indent=2))
print(f"OK: FAT32 ESP staging at {out}")
PY
