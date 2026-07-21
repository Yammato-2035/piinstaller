#!/usr/bin/env bash
# Prepare stick for PI-RS-MSI-GUI-AUTO-BVR-001:
# Default GRUB = Lab-Auto (GUI, Physical E2E) — unattended SABRENT BVR with GUI.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
ESP_MOUNT="${ESP_MOUNT:-}"
EXECUTE=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --execute) EXECUTE=true; shift ;;
    --esp) ESP_MOUNT="$2"; shift 2 ;;
    -h|--help)
      echo "Usage: $0 [--esp PATH] --execute" >&2
      exit 0
      ;;
    *) echo "Unknown arg: $1" >&2; exit 2 ;;
  esac
done

if [[ -z "$ESP_MOUNT" ]]; then
  for cand in /media/*/SETUPHELFER /tmp/setuphelfer-efi-rw; do
    [[ -f "${cand}/boot/grub/grub.cfg" ]] && ESP_MOUNT="$cand" && break
  done
fi

[[ "$EXECUTE" == true ]] || { echo "Plan only — use --execute"; exit 0; }
[[ -n "$ESP_MOUNT" && -f "${ESP_MOUNT}/boot/grub/grub.cfg" ]] || {
  echo "ERROR: ESP grub.cfg not found" >&2
  exit 1
}

export PYTHONPATH="${REPO_ROOT}/backend${PYTHONPATH:+:$PYTHONPATH}"
python3 - <<PY
from pathlib import Path
from core.rescue_msi_lab_auto_boot import (
    LAB_GUI_PHYSICAL_E2E_MENU_TITLE,
    LAB_PHYSICAL_E2E_MENU_TITLE,
    patch_grub_cfg_for_msi_gui_physical_e2e_boot,
)

cfg = Path(${ESP_MOUNT@Q}) / "boot/grub/grub.cfg"
text = cfg.read_text(encoding="utf-8")
cfg.with_suffix(".cfg.prev-pre-gui-physical-e2e").write_text(text, encoding="utf-8")
patched = patch_grub_cfg_for_msi_gui_physical_e2e_boot(text)
cfg.write_text(patched, encoding="utf-8")
assert "setuphelfer_mode=gui" in patched
assert "setuphelfer_gui_watchdog=1" in patched
assert "setuphelfer_msi_e2e_auto=1" in patched
assert "setuphelfer_auto_discovery=0" in patched
assert "setuphelfer_auto_shutdown=1" in patched
assert LAB_GUI_PHYSICAL_E2E_MENU_TITLE in patched
assert LAB_PHYSICAL_E2E_MENU_TITLE in patched
assert patched.index(LAB_GUI_PHYSICAL_E2E_MENU_TITLE) < patched.index(LAB_PHYSICAL_E2E_MENU_TITLE)
print(f"grub default: {LAB_GUI_PHYSICAL_E2E_MENU_TITLE}")
PY
sync
