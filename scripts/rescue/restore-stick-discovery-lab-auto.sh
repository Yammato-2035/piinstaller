#!/usr/bin/env bash
# After Phase A physical E2E: restore Discovery Lab-Auto as stick default.
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
import json, secrets
from datetime import datetime, timezone
from pathlib import Path
from core.rescue_payload_version import rescue_payload_version
from core.rescue_discovery_run_control import build_discovery_run_control, write_discovery_run_control

logs = Path(${SETUP_LOGS@Q})
payload = rescue_payload_version() or "1.10.0.37"
control = build_discovery_run_control(expected_payload_version=payload)
# ensure non-destructive discovery defaults
control["enabled"] = True
control["consumed"] = False
control["run_mode"] = "auto_discovery_only"
control["allow_destructive_storage_actions"] = False
control["allow_backup"] = False
control["allow_restore"] = False
control["allow_partitioning"] = False
control["allow_format"] = False
control["telemetry_required"] = True
control["auto_shutdown"] = True
control["run_nonce"] = secrets.token_hex(16)
control["created_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
for k in ("consumed_at", "consumed_by_session_id", "terminal_status", "archived_at"):
    control.pop(k, None)
path = write_discovery_run_control(logs, control)
print(json.dumps({"discovery_rearmed": True, "path": str(path), "payload": payload}, indent=2))
PY

if [[ -n "$ESP_MOUNT" && -f "${ESP_MOUNT}/boot/grub/grub.cfg" ]]; then
  PYTHONPATH="${REPO_ROOT}/backend" python3 - <<PY
from pathlib import Path
from core.rescue_msi_lab_auto_boot import patch_grub_cfg_for_msi_lab_auto_boot
cfg = Path(${ESP_MOUNT@Q}) / "boot/grub/grub.cfg"
text = cfg.read_text(encoding="utf-8")
cfg.with_suffix(".cfg.prev-post-physical-e2e").write_text(text, encoding="utf-8")
patched = patch_grub_cfg_for_msi_lab_auto_boot(text)
cfg.write_text(patched, encoding="utf-8")
assert "setuphelfer_auto_discovery=1" in patched
assert "setuphelfer_msi_e2e_auto=0" in patched
assert "Lab-Auto (GUI, Discovery)" in patched
assert "setuphelfer_gui_watchdog=1" in patched
print("grub restored to Lab-Auto GUI Discovery (watchdog → TUI)")
PY
  sync
else
  echo "WARN: ESP not mounted — GRUB not restored" >&2
fi
