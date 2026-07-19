#!/usr/bin/env bash
# Prepare stick for Phase B: GUI Backup/Verify/Restore with TUI watchdog fallback.
# Disables discovery lock so interactive backup is allowed; no auto-shutdown.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SETUP_LOGS="${SETUP_LOGS:-}"
ESP_MOUNT="${ESP_MOUNT:-}"
EXECUTE=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --execute) EXECUTE=true; shift ;;
    --setup-logs) SETUP_LOGS="$2"; shift 2 ;;
    --esp) ESP_MOUNT="$2"; shift 2 ;;
    -h|--help)
      echo "Usage: $0 [--setup-logs PATH] [--esp PATH] --execute" >&2
      exit 0
      ;;
    *) echo "Unknown arg: $1" >&2; exit 2 ;;
  esac
done

if [[ -z "$SETUP_LOGS" ]]; then
  for cand in /media/*/SETUP_LOGS /media/*/SETUP_LOGS2 /run/media/*/SETUP_LOGS*; do
    [[ -d "$cand" ]] && SETUP_LOGS="$cand" && break
  done
fi
[[ -n "$SETUP_LOGS" ]] || { echo "ERROR: SETUP_LOGS not mounted" >&2; exit 1; }

if [[ -z "$ESP_MOUNT" ]]; then
  for cand in /media/*/SETUPHELFER /tmp/setuphelfer-efi-rw; do
    [[ -f "${cand}/boot/grub/grub.cfg" ]] && ESP_MOUNT="$cand" && break
  done
fi

[[ "$EXECUTE" == true ]] || { echo "Plan only — use --execute"; exit 0; }

export PYTHONPATH="${REPO_ROOT}/backend${PYTHONPATH:+:$PYTHONPATH}"
python3 - <<PY
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

logs = Path(${SETUP_LOGS@Q})
ctrl_dir = logs / "setuphelfer/e2e-live-001d"
ctrl_dir.mkdir(parents=True, exist_ok=True)
disc = ctrl_dir / "discovery-run-control.json"
hist = ctrl_dir / "history"
hist.mkdir(parents=True, exist_ok=True)
if disc.is_file():
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    shutil.copy2(disc, hist / f"discovery-run-control-pre-gui-bvr-{stamp}.json")
    data = json.loads(disc.read_text(encoding="utf-8"))
    data["enabled"] = False
    data["consumed"] = True
    data["terminal_status"] = "archived_for_gui_backup_verify"
    data["archived_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    data["allow_backup"] = True
    data["allow_restore"] = True
    disc.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(json.dumps({"discovery_disabled_for_gui_bvr": True, "path": str(disc)}, indent=2))
PY

if [[ -n "$ESP_MOUNT" && -f "${ESP_MOUNT}/boot/grub/grub.cfg" ]]; then
  PYTHONPATH="${REPO_ROOT}/backend" python3 - <<PY
from pathlib import Path
from core.rescue_msi_lab_auto_boot import patch_grub_cfg_for_msi_gui_interactive_boot
cfg = Path(${ESP_MOUNT@Q}) / "boot/grub/grub.cfg"
text = cfg.read_text(encoding="utf-8")
cfg.with_suffix(".cfg.prev-pre-gui-bvr").write_text(text, encoding="utf-8")
patched = patch_grub_cfg_for_msi_gui_interactive_boot(text)
cfg.write_text(patched, encoding="utf-8")
assert "setuphelfer_mode=gui" in patched
assert "setuphelfer_gui_watchdog=1" in patched
assert "setuphelfer_auto_discovery=0" in patched
assert "Lab-Auto (GUI, Backup/Verify)" in patched
print("grub default: Lab-Auto GUI Backup/Verify (watchdog → TUI)")
PY
  sync
else
  echo "WARN: ESP not mounted — GRUB not patched" >&2
fi
