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
    text="$(PYTHONPATH="${py}" python3 - <<'PY'
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

_tui_start_gui() {
  if [[ -x "${SCRIPT_DIR}/setuphelfer-rescue-gui-watchdog" ]]; then
    if "${SCRIPT_DIR}/setuphelfer-rescue-gui-watchdog"; then
      return 0
    fi
    _tui_msg "Grafische Oberfläche konnte nicht gestartet werden.\nFallback: Textmenü."
    return 1
  fi
  _tui_msg "GUI-Watchdog nicht verfügbar."
  return 1
}

_tui_shell() {
  _tui_msg "Shell: Wechsel zu tty2.\nLogin: Benutzer setuphelfer oder root (falls konfiguriert)."
  chvt 2 2>/dev/null || true
}

_tui_main_menu() {
  local choice
  while true; do
    choice="$(whiptail --title "Setuphelfer Rettungsstick — Textmodus" --menu \
      "Sicherer Textmodus (kein Backup/Restore/Wipe)" 22 78 10 \
      "detect" "System erkennen" \
      "wifi" "Hardware/WLAN prüfen" \
      "plan" "Backup-Plan erstellen (dry-run)" \
      "evidence" "Evidence auf Stick speichern" \
      "gui" "Grafische Oberfläche starten" \
      "shell" "Shell öffnen (tty2)" \
      "reboot" "Neustart" \
      "poweroff" "Ausschalten" \
      3>&1 1>"$_wt" 2>&3)" || return 0
    case "$choice" in
      detect) _tui_run_system_detect ;;
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
