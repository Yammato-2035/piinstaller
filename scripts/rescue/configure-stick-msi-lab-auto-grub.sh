#!/usr/bin/env bash
# PI-RS-MSI-AUTO-EVIDENCE-001 — Configure FAT32 ESP GRUB for unattended MSI lab boot.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
ESP_MOUNT="${1:-}"
DRY_RUN="${DRY_RUN:-0}"

usage() {
  echo "Usage: $0 [/mount/point/SETUPHELFER]" >&2
  echo "  or:  ESP_DEVICE=/dev/disk/by-id/... $0" >&2
  exit 2
}

resolve_mount() {
  if [[ -n "$ESP_MOUNT" && -f "${ESP_MOUNT%/}/boot/grub/grub.cfg" ]]; then
    printf '%s' "${ESP_MOUNT%/}"
    return 0
  fi
  for cand in /media/*/SETUPHELFER /run/media/*/SETUPHELFER; do
    if [[ -f "${cand}/boot/grub/grub.cfg" ]]; then
      printf '%s' "$cand"
      return 0
    fi
  done
  if [[ -n "${ESP_DEVICE:-}" ]]; then
    local m="/tmp/setuphelfer-esp-grub-$$"
    mkdir -p "$m"
    mount -t vfat -o rw "$ESP_DEVICE" "$m"
    printf '%s' "$m"
    return 0
  fi
  return 1
}

MOUNT="$(resolve_mount)" || usage
GRUB_CFG="${MOUNT}/boot/grub/grub.cfg"
[[ -f "$GRUB_CFG" ]] || { echo "ERROR: missing $GRUB_CFG" >&2; exit 1; }

export SETUPHELFER_GRUB_CFG="$GRUB_CFG"
export PYTHONPATH="${REPO_ROOT}/backend${PYTHONPATH:+:$PYTHONPATH}"
export SETUPHELFER_GRUB_DRY_RUN="${DRY_RUN}"
python3 - <<'PY'
import os
from pathlib import Path
from core.rescue_msi_lab_auto_boot import patch_grub_cfg_for_msi_lab_auto_boot

cfg_path = Path(os.environ["SETUPHELFER_GRUB_CFG"])
dry_run = os.environ.get("SETUPHELFER_GRUB_DRY_RUN", "0").strip() not in ("", "0", "false", "False")
original = cfg_path.read_text(encoding="utf-8")
patched = patch_grub_cfg_for_msi_lab_auto_boot(original)
if patched.strip() == original.strip():
    raise SystemExit("GRUB patch produced no changes")
backup = cfg_path.with_suffix(".cfg.prev-lab-auto")
backup.write_text(original, encoding="utf-8")
if dry_run:
    print("DRY_RUN: would write lab-auto grub.cfg")
    print(patched[:400])
else:
    cfg_path.write_text(patched, encoding="utf-8")
    print(f"OK: lab-auto GRUB -> {cfg_path}")
    print(f"Backup: {backup}")
PY

sync "${GRUB_CFG}" 2>/dev/null || sync
