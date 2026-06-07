#!/usr/bin/env bash
# Build standalone GRUB BOOTX64.EFI for FAT32 ESP rescue USB (not ISO copy).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
export PYTHONPATH="${REPO_ROOT}/backend${PYTHONPATH:+:$PYTHONPATH}"

OUTPUT=""
LABEL="SETUPHELFER"
EVIDENCE_JSON=""

usage() {
  echo "Usage: $0 --output PATH/EFI/BOOT/BOOTX64.EFI [--label SETUPHELFER] [--evidence-json PATH]" >&2
  exit 20
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --output) OUTPUT="$2"; shift 2 ;;
    --label) LABEL="$2"; shift 2 ;;
    --evidence-json) EVIDENCE_JSON="$2"; shift 2 ;;
    -h|--help) usage ;;
    *) echo "Unknown arg: $1" >&2; usage ;;
  esac
done

[[ -n "$OUTPUT" ]] || usage

python3 - <<PY
import json
import sys
from pathlib import Path

from core.rescue_fat32_esp_usb_writer import (
    BOOTX64_ERROR_MKSTANDALONE_MISSING,
    build_fat32_esp_bootx64_efi,
    grub_mkstandalone_tooling,
)

tooling = grub_mkstandalone_tooling()
if not tooling["available"]:
    print(f"{BOOTX64_ERROR_MKSTANDALONE_MISSING}: grub-mkstandalone not found", file=sys.stderr)
    if tooling.get("operator_hint"):
        print(f"Operator: {tooling['operator_hint']}", file=sys.stderr)
    raise SystemExit(25)

out = Path(${OUTPUT@Q})
try:
    meta = build_fat32_esp_bootx64_efi(out, fat_label=${LABEL@Q})
except (FileNotFoundError, OSError) as exc:
    print(str(exc), file=sys.stderr)
    raise SystemExit(25) from exc

evidence_path = ${EVIDENCE_JSON@Q}
if evidence_path:
    p = Path(evidence_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(meta, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

print(json.dumps(meta, indent=2))
print(f"OK: standalone BOOTX64.EFI at {out}")
PY
