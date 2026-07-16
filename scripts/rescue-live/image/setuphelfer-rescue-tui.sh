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

_tui_run_physical_e2e() {
  local py="/opt/setuphelfer-rescue/backend"
  local cli="${SCRIPT_DIR}/setuphelfer-rescue-physical-e2e"
  if [[ ! -x "$cli" ]] && [[ -f "${SCRIPT_DIR}/setuphelfer-rescue-physical-e2e" ]]; then
    chmod +x "${SCRIPT_DIR}/setuphelfer-rescue-physical-e2e" 2>/dev/null || true
  fi
  if [[ ! -f "$cli" ]]; then
    _tui_msg "E2E-Test: CLI setuphelfer-rescue-physical-e2e fehlt."
    return
  fi
  local consent
  consent="$(whiptail --title "Telemetrie-Einwilligung" --menu \
    "Technische Laufinfo senden?" 20 74 3 \
    "granted" "Zustimmen und senden" \
    "local_only" "Nur lokal protokollieren" \
    "aborted" "Abbrechen" \
    3>&1 1>"$_wt" 2>&3)" || return 0
  if [[ "$consent" == "aborted" ]]; then
    _tui_msg "E2E-Test abgebrochen."
    return
  fi
  local base="${SETUPHELFER_RESCUE_STATE_DIR}/e2e-test"
  mkdir -p "${base}/source" "${base}/backup" "${base}/restore"
  if [[ -x "${SCRIPT_DIR}/../../create-e2e-backup-test-data.sh" ]]; then
    "${SCRIPT_DIR}/../../create-e2e-backup-test-data.sh" "${base}/source" >/dev/null 2>&1 || true
  elif [[ -x /opt/setuphelfer-rescue/scripts/create-e2e-backup-test-data.sh ]]; then
    /opt/setuphelfer-rescue/scripts/create-e2e-backup-test-data.sh "${base}/source" >/dev/null 2>&1 || true
  fi
  PYTHONPATH="${py}" "$cli" --show-gate \
    --source-dir "${base}/source" \
    --backup-archive "${base}/backup/e2e-backup.tar.gz" \
    --restore-dir "${base}/restore/data" \
    --consent "$consent" >"${base}/operator-gate.txt" 2>/dev/null || true
  if ! whiptail --title "Operator-Freigabe" --yesno "$(cat "${base}/operator-gate.txt" 2>/dev/null || echo 'E2E Gate')" 24 78; then
    _tui_msg "E2E-Test nicht freigegeben."
    return
  fi
  whiptail --title "E2E-Test" --infobox "Backup → Verify → Restore läuft…" 8 60 3>&1 1>"$_wt" 2>&3 || true
  local result_out="${base}/e2e-result.json"
  if PYTHONPATH="${py}" "$cli" \
    --source-dir "${base}/source" \
    --backup-archive "${base}/backup/e2e-backup.tar.gz" \
    --restore-dir "${base}/restore/data" \
    --consent "$consent" \
    --operator-approved >"$result_out" 2>/dev/null; then
    local status
    status="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1])).get("status","?"))' "$result_out" 2>/dev/null || echo unknown)"
    setuphelfer_rescue_mirror_evidence_file "$result_out" "setuphelfer/evidence/e2e/latest-run-result.json" 2>/dev/null || true
    _tui_msg "E2E-Test abgeschlossen.\nStatus: ${status}\nDetails: ${result_out}"
  else
    _tui_msg "E2E-Test fehlgeschlagen.\nSiehe ${result_out}"
  fi
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

_tui_auto_e2e_active() {
  setuphelfer_rescue_msi_e2e_auto_active
}

_tui_auto_read_state() {
  PYTHONPATH="$(setuphelfer_rescue_backend_pythonpath)" python3 - <<'PY' 2>/dev/null || echo "Automatischer Setuphelfer-Test\n\n(Fortschritt wird geladen…)"
from core.rescue_physical_e2e_auto_e2e_state import (
    PHASE_LABELS_DE,
    refresh_auto_e2e_phase_from_runtime,
)

state = refresh_auto_e2e_phase_from_runtime()
phase = state.get("phase") or "msi_hardware_check"
lines = [
    "Automatischer Setuphelfer-Test",
    "",
    "Ablauf:",
]
for idx, key in enumerate(
    (
        "msi_hardware_check",
        "evidence_collection",
        "test_disk_prepare",
        "test_data_create",
        "backup_create",
        "backup_verify",
        "restore_run",
        "data_compare",
        "telemetry_send",
        "diagnostics_fetch",
        "evidence_save",
        "shutdown",
    ),
    start=1,
):
    label = PHASE_LABELS_DE.get(key, key)
    marker = "→" if key == phase else " "
    done = "✓" if state.get("phase_index", -1) > idx - 1 else " "
    lines.append(f"{marker} {idx:2}. [{done}] {label}")
lines.extend(
    [
        "",
        f"Aktuelle Phase: {PHASE_LABELS_DE.get(phase, phase)}",
        f"Status: {state.get('status', 'wartet')}",
        f"Verstrichene Zeit: {state.get('elapsed_sec', 0)} s",
        f"Letzter Fortschritt: {state.get('last_progress') or '—'}",
        f"Abbruch: {'ja' if state.get('cancel_requested') else 'nein'}",
        f"Shutdown: {'vorgemerkt' if state.get('shutdown_requested') else 'nein'}",
    ]
)
print("\n".join(lines))
PY
}

_tui_shutdown_pending() {
  PYTHONPATH="$(setuphelfer_rescue_backend_pythonpath)" python3 - <<'PY' 2>/dev/null || echo no
from core.rescue_discovery_observability import read_runtime_json
from core.rescue_physical_e2e_auto_e2e_state import read_auto_e2e_state
from core.rescue_session_state import read_session_state
from pathlib import Path
import os
state_dir = Path(os.environ.get("SETUPHELFER_RESCUE_STATE_DIR", "/run/setuphelfer-rescue"))
if (state_dir / "shutdown.requested").is_file():
    print("yes"); raise SystemExit
final = read_runtime_json("boot-finalizer.json") or {}
session = read_session_state() or {}
e2e = read_auto_e2e_state() or {}
if session.get("current_phase") == "shutdown_pending" or session.get("shutdown_safe"):
    print("yes"); raise SystemExit
if final.get("shutdown_safe") and final.get("terminal"):
    print("yes"); raise SystemExit
if e2e.get("shutdown_requested") or e2e.get("phase") == "shutdown":
    print("yes"); raise SystemExit
print("no")
PY
}

_tui_discovery_hold_needed() {
  PYTHONPATH="$(setuphelfer_rescue_backend_pythonpath)" python3 - <<'PY' 2>/dev/null || echo no
from core.rescue_discovery_observability import read_runtime_json
from core.rescue_run_mode import resolve_run_mode
mode = resolve_run_mode()
if not (mode.get("ok") and mode.get("run_mode") == "auto_discovery_only"):
    print("no"); raise SystemExit
gate = read_runtime_json("start-gate.json") or {}
svc = read_runtime_json("service-result.json") or {}
orch = read_runtime_json("orchestrator-exit.json") or {}
final = read_runtime_json("boot-finalizer.json") or {}
if svc.get("exit_code") not in (None, 0):
    print("yes"); raise SystemExit
if orch.get("exit_code") not in (None, 0):
    print("yes"); raise SystemExit
if gate.get("called") and gate.get("start_allowed") is False:
    print("yes"); raise SystemExit
status = str(final.get("status") or svc.get("status") or "")
if status.startswith("failed_") or status in {"discovery_start_gate_skipped"}:
    print("yes"); raise SystemExit
print("no")
PY
}

_tui_auto_e2e_menu() {
  # 001D7C: Keep ownership of tty1 until shutdown_pending / hold shutdown.
  # Auto-display child exit must NOT leave a bare console.
  local display="${SCRIPT_DIR}/setuphelfer-rescue-auto-e2e-tui-display.py"
  local hold="${SCRIPT_DIR}/setuphelfer-rescue-tui-hold"
  local child_rc=0
  while true; do
    PYTHONPATH="$(setuphelfer_rescue_backend_pythonpath)" python3 - <<'PY' 2>/dev/null || true
from core.rescue_component_heartbeat import write_component_heartbeat
write_component_heartbeat("tui", state="auto_menu")
PY
    if [[ "$(_tui_shutdown_pending)" == "yes" ]]; then
      return 0
    fi
    if [[ "$(_tui_discovery_hold_needed)" == "yes" ]]; then
      _log_line_hold="discovery hold needed — delegating to hold service"
      echo "$_log_line_hold" >>"${SETUPHELFER_RESCUE_STATE_DIR}/tui-auto-display.log" 2>/dev/null || true
      systemctl start setuphelfer-rescue-tui-hold.service 2>/dev/null || {
        if [[ -x "$hold" || -f "$hold" ]]; then
          chmod +x "$hold" 2>/dev/null || true
          exec bash "$hold" --hold
        fi
      }
      return 0
    fi
    if [[ -f "$display" ]]; then
      chmod +x "$display" 2>/dev/null || true
      set +e
      PYTHONPATH="$(setuphelfer_rescue_backend_pythonpath)" python3 "$display" <"$_wt"
      child_rc=$?
      set -uo pipefail
      {
        echo "auto_display_exit=${child_rc} $(date -u +%Y-%m-%dT%H:%M:%SZ)"
      } >>"${SETUPHELFER_RESCUE_STATE_DIR}/tui-auto-display.log" 2>/dev/null || true
    else
      local body
      body="$(_tui_auto_read_state)"
      whiptail --title "Setuphelfer — Automatischer Test" --msgbox "${body}" 28 78 \
        --timeout 2 3>&1 1>"$_wt" 2>&3 || true
      child_rc=0
    fi
    if [[ "$(_tui_shutdown_pending)" == "yes" ]]; then
      return 0
    fi
    if [[ "$(_tui_discovery_hold_needed)" == "yes" ]]; then
      systemctl start setuphelfer-rescue-tui-hold.service 2>/dev/null || {
        if [[ -x "$hold" || -f "$hold" ]]; then
          chmod +x "$hold" 2>/dev/null || true
          exec bash "$hold" --hold
        fi
      }
      return 0
    fi
    # Display ended without terminal shutdown — restart child (keep tty1 held).
    sleep 1
  done
}

_tui_main_menu() {
  local choice
  while true; do
    choice="$(whiptail --title "Setuphelfer Rettungsstick — Textmodus" --menu \
      "Sicherer Textmodus (kein Backup/Restore/Wipe)" 22 78 10 \
      "detect" "System erkennen" \
      "wifi" "Hardware/WLAN prüfen" \
      "plan" "Backup-Plan erstellen (dry-run)" \
      "e2e" "E2E Backup-/Restore-Test" \
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
      e2e) _tui_run_physical_e2e ;;
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
setuphelfer_rescue_shield_console_early "tui_start" || true
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
  if _tui_auto_e2e_active; then
    PYTHONPATH="$(setuphelfer_rescue_backend_pythonpath)" python3 - <<'PY' 2>/dev/null || true
from core.rescue_physical_e2e_auto_e2e_state import init_auto_e2e_state
from core.rescue_run_mode import resolve_run_mode
mode = resolve_run_mode()
locked = "auto_discovery_only" if mode.get("run_mode") == "auto_discovery_only" else "auto_physical_e2e_locked"
init_auto_e2e_state(mode=locked)
PY
    _tui_auto_e2e_menu
    # Only leave tty1 after hold/menu decided shutdown is underway.
    if [[ "$(_tui_shutdown_pending)" != "yes" ]] && [[ "$(_tui_discovery_hold_needed)" == "yes" ]]; then
      systemctl start setuphelfer-rescue-tui-hold.service 2>/dev/null || \
        exec bash "${SCRIPT_DIR}/setuphelfer-rescue-tui-hold" --hold
    fi
    exit 0
  fi
  _tui_main_menu
  exit 0
fi

if _tui_auto_e2e_active; then
  _tui_auto_e2e_menu
  if [[ "$(_tui_shutdown_pending)" != "yes" ]] && [[ "$(_tui_discovery_hold_needed)" == "yes" ]]; then
    systemctl start setuphelfer-rescue-tui-hold.service 2>/dev/null || \
      exec bash "${SCRIPT_DIR}/setuphelfer-rescue-tui-hold" --hold
  fi
  exit 0
fi

_tui_main_menu
