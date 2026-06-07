#!/usr/bin/env bash
# FAT32 ESP Rescue USB writer — default dry-run; destructive write only with operator confirm.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

ISO=""
TARGET=""
DRY_RUN=true
CONFIRM_WRITE=false
CONFIRM_PHRASE=""
ESP_SIZE_MIB=4096
STAGING_DIR="${REPO_ROOT}/build/rescue/fat32-esp-staging"
GPT_PARTITION_NAME="SETUPHELFER_RESCUE"
FAT_VOLUME_LABEL="SETUPHELFER"

usage() {
  cat <<EOF
Usage: $0 --iso PATH --target /dev/sdX [--dry-run] [--operator-confirm-write --confirm-phrase "WRITE SETUPHELFER FAT32 ESP USB"]

Default: --dry-run (no partition/format/copy).
Destructive write requires operator evidence + exact confirm phrase.
DCC/Agent must NOT invoke write mode automatically.
EOF
  exit 20
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --iso) ISO="$2"; shift 2 ;;
    --target) TARGET="$2"; shift 2 ;;
    --dry-run) DRY_RUN=true; shift ;;
    --operator-confirm-write) CONFIRM_WRITE=true; DRY_RUN=false; shift ;;
    --confirm-phrase) CONFIRM_PHRASE="$2"; shift 2 ;;
    --esp-size-mib) ESP_SIZE_MIB="$2"; shift 2 ;;
    --staging-dir) STAGING_DIR="$2"; shift 2 ;;
    -h|--help) usage ;;
    *) echo "Unknown arg: $1" >&2; usage ;;
  esac
done

[[ -n "$ISO" && -n "$TARGET" ]] || usage
[[ -f "$ISO" ]] || { echo "ERROR: ISO missing: $ISO" >&2; exit 21; }

export PYTHONPATH="${REPO_ROOT}/backend${PYTHONPATH:+:$PYTHONPATH}"

PLAN_JSON="$(mktemp)"
trap 'rm -f "$PLAN_JSON"' EXIT

if [[ "$DRY_RUN" == true ]]; then
  DRY_PY=True
else
  DRY_PY=False
fi

python3 - <<PY >"$PLAN_JSON"
import json
from pathlib import Path
from core.rescue_fat32_esp_usb_writer import build_write_plan

plan = build_write_plan(
    iso_path=Path(${ISO@Q}),
    target_device=${TARGET@Q},
    staging_dir=Path(${STAGING_DIR@Q}),
    esp_size_mib=int(${ESP_SIZE_MIB}),
    dry_run=${DRY_PY},
    confirm_phrase=${CONFIRM_PHRASE@Q} or None,
)
print(json.dumps(plan, indent=2))
PY

echo "=== FAT32 ESP USB Writer Plan ==="
cat "$PLAN_JSON"

if [[ "$DRY_RUN" == true ]]; then
  echo "OK: dry-run complete — no device write performed"
  exit 0
fi

BLOCKED="$(python3 - <<PY
import json
from pathlib import Path
plan = json.loads(Path(${PLAN_JSON@Q}).read_text())
print("yes" if plan.get("safety", {}).get("blocked") else "no")
PY
)"

if [[ "$BLOCKED" == "yes" ]]; then
  echo "ERROR: write blocked by safety checks — see plan JSON" >&2
  exit 27
fi

if [[ "$CONFIRM_WRITE" != true ]]; then
  echo "ERROR: --operator-confirm-write required for destructive mode" >&2
  exit 27
fi

# Build staging if missing
if [[ ! -f "${STAGING_DIR}/EFI/BOOT/BOOTX64.EFI" ]]; then
  "${SCRIPT_DIR}/build-fat32-esp-usb-layout.sh" --iso "$ISO" --output-dir "$STAGING_DIR"
fi

echo "=== DESTRUCTIVE WRITE PREPARED (operator terminal only) ==="
echo "Target: ${TARGET}"
echo "NOTE: FAT32 has no Unix owner/group/permissions — use FAT-safe rsync (see write_manual below)."
echo ""
python3 - <<PY
from pathlib import Path
from core.rescue_fat32_esp_usb_writer import build_operator_terminal_commands

cmds = build_operator_terminal_commands(
    iso_path=Path(${ISO@Q}),
    target_device=${TARGET@Q},
    workspace=Path(${REPO_ROOT@Q}),
)
print(cmds["write_manual"])
PY
echo ""
echo "NOTE: This script does NOT execute destructive steps automatically."
echo "write_executed=false (operator must run steps manually)"
exit 0
