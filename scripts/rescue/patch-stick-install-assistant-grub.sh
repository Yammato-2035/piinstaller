#!/usr/bin/env bash
# Patch Ultra Line SETUPHELFER GRUB for Gabriel Mint install assistant.
# Write to stick is intentional (operator-authorized).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
DEVICE="${1:-/dev/sda1}"
MOUNT="${SETUPHELFER_MOUNT:-/mnt/setuphelfer-rw}"
BACKUP_SUFFIX="prev-pre-install-assistant-$(date -u +%Y%m%dT%H%M%SZ)"

echo "============================================================"
echo "STICK GRUB PATCH — Gabriel Install Assistant"
echo "Device: $DEVICE"
echo "Mount:  $MOUNT"
echo "Repo:   $ROOT"
echo "============================================================"

if [[ ! -b "$DEVICE" ]]; then
  echo "ERROR: not a block device: $DEVICE" >&2
  exit 2
fi

LABEL="$(lsblk -no LABEL "$DEVICE" 2>/dev/null || true)"
if [[ "$LABEL" != "SETUPHELFER" ]]; then
  echo "ERROR: refusing write — label is '$LABEL' (expected SETUPHELFER)" >&2
  exit 3
fi

sudo mkdir -p "$MOUNT"
if findmnt "$MOUNT" >/dev/null 2>&1; then
  sudo umount "$MOUNT" || true
fi
# Also unmount RO diagnosis mount if present
if findmnt /mnt/setuphelfer >/dev/null 2>&1; then
  sudo umount /mnt/setuphelfer || true
fi

sudo mount -o rw "$DEVICE" "$MOUNT"
CFG="$MOUNT/boot/grub/grub.cfg"
[[ -f "$CFG" ]] || { echo "ERROR: missing $CFG" >&2; exit 4; }

sudo cp -a "$CFG" "${CFG}.${BACKUP_SUFFIX}"
echo "Backup: ${CFG}.${BACKUP_SUFFIX}"

export PYTHONPATH="$ROOT/backend${PYTHONPATH:+:$PYTHONPATH}"
NEW_CFG="$(python3 - <<'PY'
from core.rescue_install_assistant_grub import (
    generate_gabriel_install_grub_cfg,
    validate_gabriel_install_grub,
)
cfg = generate_gabriel_install_grub_cfg(fat_uuid="9BB9-A4A6")
v = validate_gabriel_install_grub(cfg)
assert v["ok"], v
print(cfg, end="")
PY
)"

printf '%s\n' "$NEW_CFG" | sudo tee "$CFG" >/dev/null
sync

python3 - <<PY
from pathlib import Path
from core.rescue_install_assistant_grub import validate_gabriel_install_grub
text = Path("$CFG").read_text(encoding="utf-8", errors="replace")
v = validate_gabriel_install_grub(text)
print(v)
assert v["ok"], v
PY

# Marker on ESP
python3 - <<PY
import json
from datetime import datetime, timezone
from pathlib import Path
p = Path("$MOUNT/setuphelfer/rescue/install_assistant_grub.json")
p.parent.mkdir(parents=True, exist_ok=True)
p.write_text(json.dumps({
  "schema_version": 1,
  "patched_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
  "default_entry": "Setuphelfer Linux-Installation (Mint Assistent, GUI)",
  "gabriel_ops_cmdline": "setuphelfer_gabriel_ops_allowed=1",
  "msi_e2e_demoted": True,
  "backup_suffix": "$BACKUP_SUFFIX",
}, indent=2) + "\n", encoding="utf-8")
print("wrote", p)
PY

sync
sudo umount "$MOUNT"
echo "OK: GRUB patched on $DEVICE"
echo "Reboot Gabriel from stick and choose default entry (Linux-Installation GUI)."
