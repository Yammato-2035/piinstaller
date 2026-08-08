#!/bin/bash
# Setuphelfer rescue text TUI — default path, no backup execute (RS-P2C).
set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=setuphelfer-rescue-common.sh
source "${SCRIPT_DIR}/setuphelfer-rescue-common.sh"

MODE="${1:---interactive}"
_wt="$(setuphelfer_rescue_whiptail_tty)"

_tui_msg() {
  whiptail --title "Setuphelfer Rettungsstick" --msgbox "$1" 18 74 3>&1 1>"$_wt" 2>&3 || true
}

_tui_run_system_detect() {
  whiptail --title "Setuphelfer" --infobox "System wird erkannt…" 8 50 3>&1 1>"$_wt" 2>&3 || true
  local out="${SETUPHELFER_RESCUE_STATE_DIR}/disk-discovery.json"
  if "${SCRIPT_DIR}/setuphelfer-rescue-disk-discovery" >"$out" 2>/dev/null; then
    local summary
    summary="$(python3 -c 'import json,sys; d=json.load(open(sys.argv[1])); r=d.get("recommendation") or {}; print("Empfehlung:", r.get("summary_de") or "—")' "$out" 2>/dev/null || echo "Erkennung abgeschlossen.")"
    _tui_msg "Systemerkennung\n\n${summary}\n\nDetails: ${out}"
  else
    _tui_msg "Systemerkennung fehlgeschlagen.\nSiehe Journal / SETUP_LOGS."
  fi
}

_tui_run_wifi_diag() {
  whiptail --title "Setuphelfer" --infobox "WLAN/Hardware wird geprüft…" 8 50 3>&1 1>"$_wt" 2>&3 || true
  setuphelfer_rescue_wifi_prepare_radio || true
  local py="/opt/setuphelfer-rescue/backend"
  local text="WLAN-Diagnose nicht verfügbar (Backend fehlt)."
  if [[ -d "$py" ]]; then
    local pybin
    pybin="$(setuphelfer_rescue_backend_python 2>/dev/null || command -v python3 || echo python3)"
    text="$(PYTHONPATH="$(setuphelfer_rescue_backend_pythonpath 2>/dev/null || echo "$py")" "$pybin" - <<'PY'
import json
from core.rescue_wifi_diagnostics import classify_wifi_status
w = classify_wifi_status()
lines = [
    f"Status: {w.get('status')}",
    f"Hardware: {'ja' if w.get('wifi_hardware_present') else 'nein'}",
    f"Treiber: {w.get('driver') or '—'}",
    f"Firmware: {w.get('firmware_status') or '—'}",
    f"rfkill: {w.get('rfkill_state') or '—'}",
    f"NetworkManager: {w.get('networkmanager_active')}",
    f"HDD-Backup WLAN nötig: {'nein' if not w.get('blocks_local_hdd_backup') else 'ja'}",
    f"Cloud-Backup WLAN nötig: {'ja' if w.get('blocks_cloud_backup') else 'nein'}",
]
print("\n".join(lines))
PY
)"
  fi
  if command -v nmcli >/dev/null 2>&1; then
    text="${text}

nmcli radio:
$(nmcli radio all 2>/dev/null | head -5)

Interfaces:
$(nmcli -t -f DEVICE,TYPE,STATE device status 2>/dev/null | head -8)"
  fi
  _tui_msg "$text"
}

_tui_run_backup_plan() {
  whiptail --title "Setuphelfer" --infobox "Backup-Plan (nur Vorschau)…" 8 55 3>&1 1>"$_wt" 2>&3 || true
  local disc="${SETUPHELFER_RESCUE_STATE_DIR}/disk-discovery.json"
  "${SCRIPT_DIR}/setuphelfer-rescue-disk-discovery" >"$disc" 2>/dev/null || true
  local py="/opt/setuphelfer-rescue/backend"
  local plan_out="${SETUPHELFER_RESCUE_STATE_DIR}/backup-plan-dry-run.json"
  if [[ ! -d "$py" ]]; then
    _tui_msg "Backup-Plan: Backend fehlt (contract_error_disk_discovery_null)."
    return
  fi
  PYTHONPATH="${py}" python3 - <<PY >"$plan_out" 2>/dev/null || true
import json
from pathlib import Path
from core.rescue_backup_plan_contract import build_rescue_backup_plan

disc_path = Path(${disc@Q})
disc = {}
if disc_path.is_file():
    disc = json.loads(disc_path.read_text(encoding="utf-8"))
body = {
    "disk_discovery": disc,
    "devices_detected": bool(disc.get("devices")),
    "target_mode": "external_hdd",
}
plan = build_rescue_backup_plan(body)
print(json.dumps(plan, indent=2, ensure_ascii=False))
PY
  local msg
  msg="$(python3 -c 'import json,sys; p=json.load(open(sys.argv[1])); e=[x.get("code") for x in (p.get("errors") or [])]; w=[x.get("code") for x in (p.get("warnings") or [])]; print("Status:", p.get("plan_status"), "\nExecute:", p.get("execute_allowed"), "\nFehler:", ", ".join(e) or "—", "\nHinweise:", ", ".join(w) or "—")' "$plan_out" 2>/dev/null || echo "Plan konnte nicht erstellt werden.")"
  setuphelfer_rescue_mirror_evidence_file "$plan_out" "setuphelfer/evidence/backup/backup-plan-dry-run.json" 2>/dev/null || true
  _tui_msg "Backup-Plan (dry-run, keine Ausführung)\n\n${msg}\n\nGespeichert: ${plan_out}"
}

_tui_collect_evidence() {
  whiptail --title "Setuphelfer" --infobox "Evidence wird gesammelt…" 8 50 3>&1 1>"$_wt" 2>&3 || true
  if [[ -x "${SCRIPT_DIR}/collect-rescue-runtime-diagnostics" ]]; then
    "${SCRIPT_DIR}/collect-rescue-runtime-diagnostics" >/dev/null 2>&1 || true
  elif [[ -x /opt/setuphelfer-rescue/scripts/rescue-live/collect-rescue-runtime-diagnostics.sh ]]; then
    /opt/setuphelfer-rescue/scripts/rescue-live/collect-rescue-runtime-diagnostics.sh >/dev/null 2>&1 || true
  fi
  setuphelfer_rescue_write_boot_state "evidence_collected"
  _tui_msg "Diagnose/Evidence gesammelt.\nPrüfen Sie SETUP_LOGS/setuphelfer/evidence/."
}

_tui_run_partitions() {
  whiptail --title "Setuphelfer" --infobox "Partitionshelfer (nur Lesen)…" 8 55 3>&1 1>"$_wt" 2>&3 || true
  local disc="${SETUPHELFER_RESCUE_STATE_DIR}/disk-discovery.json"
  local out="${SETUPHELFER_RESCUE_STATE_DIR}/partitions-preview.json"
  "${SCRIPT_DIR}/setuphelfer-rescue-disk-discovery" >"$disc" 2>/dev/null || true
  local pybin
  pybin="$(setuphelfer_rescue_backend_python 2>/dev/null || command -v python3 || echo python3)"
  PYTHONPATH="$(setuphelfer_rescue_backend_pythonpath 2>/dev/null || echo /opt/setuphelfer-rescue/backend)" \
    "$pybin" - "$disc" "$out" <<'PY' 2>/dev/null || true
import json, sys
from pathlib import Path
from rescue.rescue_partitions_tui_preview import (
    build_partitions_tui_preview,
    format_partitions_tui_message,
    write_partitions_preview_json,
)
disc = {}
p = Path(sys.argv[1])
if p.is_file():
    try:
        disc = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        disc = {}
preview = build_partitions_tui_preview(disk_discovery=disc if isinstance(disc, dict) else None)
write_partitions_preview_json(Path(sys.argv[2]), preview)
print(format_partitions_tui_message(preview))
PY
  local msg
  msg="$(cat "$out" >/dev/null 2>&1; PYTHONPATH="$(setuphelfer_rescue_backend_pythonpath 2>/dev/null || true)" "$pybin" -c 'import json,sys; from rescue.rescue_partitions_tui_preview import format_partitions_tui_message; print(format_partitions_tui_message(json.load(open(sys.argv[1]))))' "$out" 2>/dev/null || echo "Partitionsvorschau fehlgeschlagen.")"
  setuphelfer_rescue_mirror_evidence_file "$out" "setuphelfer/evidence/partitions/partitions-preview.json" 2>/dev/null || true
  setuphelfer_rescue_mirror_evidence_file "$disc" "setuphelfer/evidence/partitions/disk-discovery.json" 2>/dev/null || true
  _tui_msg "${msg}"
}

_tui_start_gui() {
  # PI-RS-ASUS-ROOTCAUSE-006: TUI-baseline / forensic must not enter startx via menu.
  if setuphelfer_rescue_tui_baseline_active 2>/dev/null \
     || setuphelfer_rescue_xorg_forensic_active 2>/dev/null \
     || ! setuphelfer_rescue_should_start_gui 2>/dev/null; then
    _tui_msg "Grafische Oberfläche in diesem Boot-Profil gesperrt.\nBitte ASUS-TUI-BASELINE ohne GUI belassen."
    return 0
  fi
  if setuphelfer_rescue_should_disable_gui_for_msi_compat; then
    setuphelfer_rescue_write_gui_blocked_msi_status true
    _tui_msg "$(setuphelfer_rescue_gui_disabled_message)"
    return 0
  fi
  if [[ -x "${SCRIPT_DIR}/setuphelfer-rescue-gui-watchdog" ]]; then
    if "${SCRIPT_DIR}/setuphelfer-rescue-gui-watchdog"; then
      return 0
    fi
    setuphelfer_rescue_mark_tui_rerender_after_gui_failure
    _tui_msg "Grafische Oberfläche konnte nicht gestartet werden.\nFallback: Textmenü."
    return 0
  fi
  _tui_msg "GUI-Watchdog nicht verfügbar."
  return 0
}

_tui_shell() {
  _tui_msg "Shell: Wechsel zu tty2.\nLogin: Benutzer setuphelfer oder root (falls konfiguriert)."
  chvt 2 2>/dev/null || true
}

_tui_show_autocapture_banner() {
  local summary="${SETUPHELFER_RESCUE_STATE_DIR:-/run/setuphelfer}/tui-baseline-autocapture-summary.json"
  [[ -f "$summary" ]] || return 0
  local line
  line="$(python3 - "$summary" <<'PY' 2>/dev/null || true
import json, sys
p = json.load(open(sys.argv[1], encoding="utf-8"))
print(
    f"Autocapture OK\n"
    f"diag_rc={p.get('boot_diagnostics_rc')}  "
    f"hw={p.get('hardware_baseline_status')} (rc={p.get('hardware_baseline_rc')})\n"
    f"CPU/RAM/NVMe: read-only quick baseline\n"
    f"GUI/startx/Chromium: nicht gestartet"
)
PY
)"
  [[ -n "$line" ]] || return 0
  _tui_msg "$line"
}

_tui_main_menu() {
  local choice
  local gui_allowed=1
  if setuphelfer_rescue_tui_baseline_active 2>/dev/null \
     || setuphelfer_rescue_xorg_forensic_active 2>/dev/null \
     || ! setuphelfer_rescue_should_start_gui 2>/dev/null; then
    gui_allowed=0
  fi
  _tui_show_autocapture_banner || true
  while true; do
    if [[ "$gui_allowed" -eq 1 ]]; then
      choice="$(whiptail --title "Setuphelfer Rettungsstick — Textmodus" --menu \
        "Sicherer Textmodus (kein Backup/Restore/Wipe)" 22 78 11 \
        "detect" "System erkennen" \
        "partitions" "Partitionshelfer (nur Lesen)" \
        "wifi" "Hardware/WLAN prüfen" \
        "plan" "Backup-Plan erstellen (dry-run)" \
        "evidence" "Evidence auf Stick speichern" \
        "gui" "Grafische Oberfläche starten" \
        "shell" "Shell öffnen (tty2)" \
        "reboot" "Neustart" \
        "poweroff" "Ausschalten" \
        3>&1 1>"$_wt" 2>&3)" || return 0
    else
      choice="$(whiptail --title "Setuphelfer Rettungsstick — Textmodus" --menu \
        "TUI-Baseline: Auto-Evidence aktiv (kein GUI/startx)" 22 78 10 \
        "detect" "System erkennen" \
        "partitions" "Partitionshelfer (nur Lesen)" \
        "wifi" "Hardware/WLAN prüfen" \
        "plan" "Backup-Plan erstellen (dry-run)" \
        "evidence" "Evidence auf Stick speichern" \
        "shell" "Shell öffnen (tty2)" \
        "reboot" "Neustart" \
        "poweroff" "Ausschalten" \
        3>&1 1>"$_wt" 2>&3)" || return 0
    fi
    case "$choice" in
      detect) _tui_run_system_detect ;;
      partitions) _tui_run_partitions ;;
      wifi) _tui_run_wifi_diag ;;
      plan) _tui_run_backup_plan ;;
      evidence) _tui_collect_evidence ;;
      gui) _tui_start_gui ;;
      shell) _tui_shell ;;
      reboot) systemctl reboot 2>/dev/null || reboot ;;
      poweroff) systemctl poweroff 2>/dev/null || poweroff ;;
    esac
  done
}

setuphelfer_rescue_ensure_state_dir
setuphelfer_rescue_init_boot_session || true
setuphelfer_rescue_console_owner_transition "tui_initializing" "tui_start" || true
setuphelfer_rescue_quiet_console_for_tui 2>/dev/null || true
setuphelfer_rescue_shield_console_early "tui_start" || true
setuphelfer_rescue_console_owner_transition "tui_owned" "tui_start" || true
setuphelfer_rescue_tui_mark_active
setuphelfer_rescue_console_owner_transition "tui_owned" "tui_owned" || true
setuphelfer_rescue_write_boot_state "tui_start"

if ! command -v whiptail >/dev/null 2>&1; then
  setuphelfer_rescue_show_branding
  cat <<'EOF'
Textmenü benötigt whiptail. Bitte installieren oder Shell nutzen:
  setuphelfer-rescue-disk-discovery
  setuphelfer-rescue-boot-diagnostics
EOF
  exit 30
fi

if [[ "$MODE" == "--boot-trigger" ]] || [[ "$MODE" == "--interactive" ]]; then
  setuphelfer_rescue_prepare_tty1 || true
  _tui_main_menu
  exit 0
fi

_tui_main_menu
