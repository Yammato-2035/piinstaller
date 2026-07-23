#!/bin/bash
# Setuphelfer rescue text TUI — default path, no backup execute (RS-P2C).
set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=setuphelfer-rescue-common.sh
source "${SCRIPT_DIR}/setuphelfer-rescue-common.sh"

MODE="${1:---interactive}"
_wt="$(setuphelfer_rescue_whiptail_tty)"

# whiptail/newt: UI on stdout, selection tag on stderr (see man whiptail).
# Under command substitution stdout starts as a pipe — swap so UI hits the tty
# and the tag is what $() captures. Painting UI to stderr left a blank screen
# with whiptail spinning ~30% CPU (MSI 1.10.0.57).
_tui_whiptail() {
  local tty="${_wt:-/dev/tty1}"
  [[ -c "$tty" && -w "$tty" ]] || tty="/dev/tty1"
  [[ -c "$tty" ]] || tty="/dev/tty"
  TERM="${TERM:-linux}" whiptail "$@" <"$tty" 3>&1 1>"$tty" 2>&3
}

_tui_msg() {
  _tui_whiptail --title "Setuphelfer Rettungsstick" --msgbox "$1" 18 74 || true
}

_tui_input_diag_active() {
  grep -Eq '(^| )setuphelfer_tui_input_diag=1( |$)' /proc/cmdline 2>/dev/null
}

_tui_diag_blocked_action() {
  _tui_msg "Diese Funktion ist während der Eingabediagnose gesperrt.
This function is disabled during input diagnostics.

Code: RESCUE_TUI_INPUT_DIAGNOSTIC_MODE_READ_ONLY"
}

_tui_run_wifi_diag() {
  # Hard wall-clock: MSI WiFi/nmcli can enter D-state; never block the menu.
  local out="${SETUPHELFER_RESCUE_STATE_DIR}/wifi-diag-tui.txt"
  local secs=8
  whiptail --title "Setuphelfer" --infobox "WLAN/Hardware wird geprüft… (max. ${secs}s)" 8 55 \
    3>&1 1>"$_wt" 2>&3 || true
  setuphelfer_rescue_ensure_state_dir
  rm -f "$out"
  (
    export SETUPHELFER_WIFI_PREPARE_LIGHT=1
    setuphelfer_rescue_wifi_prepare_radio || true
    local py="/opt/setuphelfer-rescue/backend"
    local text="WLAN-Diagnose: Timeout oder Backend fehlt."
    if [[ -d "$py" ]]; then
      text="$(
        SETUPHELFER_WIFI_DIAG_LIGHT=1 PYTHONPATH="${py}" python3 - <<'PY'
from core.rescue_wifi_diagnostics import classify_wifi_status
w = classify_wifi_status(light=True)
lines = [
    f"Status: {w.get('status') or w.get('ui_status') or '—'}",
    f"Hardware: {'ja' if w.get('wifi_hardware_detected') or w.get('wifi_interface_present') else 'nein'}",
    f"Treiber iwlwifi: {'geladen' if w.get('driver_loaded') else 'nein/unbekannt'}",
    f"Interfaces: {', '.join(w.get('interfaces') or []) or '—'}",
    f"rfkill soft-block: {'ja' if w.get('rfkill_soft_blocked') else 'nein'}",
    f"WLAN-Radio an: {'ja' if w.get('wifi_radio_on') else 'nein/unbekannt'}",
    f"HDD-Backup WLAN nötig: nein",
    f"Cloud-Backup WLAN nötig: {'ja' if w.get('blocks_cloud_backup') else 'nein'}",
]
print("\n".join(lines))
PY
      )" || text="WLAN-Diagnose: Python-Fehler (offline fortfahren)."
    fi
    if command -v nmcli >/dev/null 2>&1; then
      text="${text}

nmcli radio:
$(timeout 2 nmcli radio all 2>/dev/null | head -5 || echo '(timeout)')

Interfaces:
$(timeout 2 nmcli -t -f DEVICE,TYPE,STATE device status 2>/dev/null | head -8 || echo '(timeout)')"
    fi
    printf '%s\n' "$text" >"$out"
  ) >/dev/null 2>&1 &
  local pid=$!
  local end=$((SECONDS + secs))
  while kill -0 "$pid" 2>/dev/null && (( SECONDS < end )); do
    sleep 0.2
  done
  if kill -0 "$pid" 2>/dev/null; then
    kill -TERM "$pid" 2>/dev/null || true
    kill -KILL "$pid" 2>/dev/null || true
  fi
  if [[ -s "$out" ]]; then
    _tui_msg "$(cat "$out")"
  else
    _tui_msg "WLAN-Diagnose abgebrochen (Timeout ${secs}s).\n\nOffline fortfahren ist möglich — lokales HDD-Backup braucht kein WLAN."
  fi
}

_tui_run_system_detect() {
  whiptail --title "Setuphelfer" --infobox "System wird erkannt… (max. 8s)" 8 50 3>&1 1>"$_wt" 2>&3 || true
  local out="${SETUPHELFER_RESCUE_STATE_DIR}/disk-discovery.json"
  _tui_run_bounded 8 "${SCRIPT_DIR}/setuphelfer-rescue-disk-discovery" || true
  if [[ -s "$out" ]]; then
    local summary
    summary="$(python3 -c 'import json,sys; d=json.load(open(sys.argv[1])); r=d.get("recommendation") or {}; print("Empfehlung:", r.get("summary_de") or "—")' "$out" 2>/dev/null || echo "Erkennung abgeschlossen.")"
    _tui_msg "Systemerkennung\n\n${summary}\n\nDetails: ${out}"
  else
    _tui_msg "Systemerkennung fehlgeschlagen oder Timeout.\nSiehe Journal / SETUP_LOGS — Menü bleibt nutzbar."
  fi
}

_tui_run_backup_plan() {
  whiptail --title "Setuphelfer" --infobox "Backup-Plan (nur Vorschau)…" 8 55 3>&1 1>"$_wt" 2>&3 || true
  setuphelfer_rescue_ensure_state_dir
  # Wrapper writes JSON to STATE_DIR (not stdout) — do not redirect stdout into the file.
  local disc="${SETUPHELFER_RESCUE_STATE_DIR}/disk-discovery.json"
  "${SCRIPT_DIR}/setuphelfer-rescue-disk-discovery" >/dev/null 2>&1 || true
  local plan_out="${SETUPHELFER_RESCUE_STATE_DIR}/backup-plan-dry-run.json"
  local plan_err="${SETUPHELFER_RESCUE_STATE_DIR}/backup-plan-dry-run.err"
  local py_backend="/opt/setuphelfer-rescue/backend"
  if [[ ! -d "$py_backend" ]]; then
    _tui_msg "Backup-Plan: Backend fehlt (contract_error_disk_discovery_null)."
    return
  fi
  local pybin
  pybin="$(setuphelfer_rescue_backend_python 2>/dev/null || command -v python3)"
  PYTHONPATH="$(setuphelfer_rescue_backend_pythonpath)" "$pybin" - <<PY >"$plan_out" 2>"$plan_err" || true
import json
import traceback
from pathlib import Path

from core.rescue_backup_plan_contract import build_rescue_backup_plan
from core.rescue_tui_backup_plan_body import build_tui_backup_plan_body_from_discovery

disc_path = Path(${disc@Q})
disc: dict = {}
try:
    if disc_path.is_file() and disc_path.stat().st_size > 0:
        disc = json.loads(disc_path.read_text(encoding="utf-8"))
except Exception as exc:  # noqa: BLE001
    print(json.dumps({
        "plan_status": "blocked",
        "execute_allowed": False,
        "errors": [{"code": "disk_discovery_invalid", "message": f"{type(exc).__name__}: {exc}"}],
        "warnings": [],
    }, indent=2, ensure_ascii=False))
    raise SystemExit(0)
body = build_tui_backup_plan_body_from_discovery(disc, target_mode="external_hdd")
try:
    plan = build_rescue_backup_plan(body)
    plan["tui_auto_mapped"] = {
        "source_device": body.get("source_device"),
        "target_device": body.get("target_device"),
        "target_mount": body.get("target_mount"),
    }
    print(json.dumps(plan, indent=2, ensure_ascii=False))
except Exception as exc:  # noqa: BLE001
    traceback.print_exc()
    print(json.dumps({
        "plan_status": "blocked",
        "execute_allowed": False,
        "errors": [{"code": "plan_exception", "message": f"{type(exc).__name__}: {exc}"}],
        "warnings": [],
    }, indent=2, ensure_ascii=False))
PY
  local msg
  msg="$(
    PYTHONPATH="$(setuphelfer_rescue_backend_pythonpath)" "$pybin" -c '
import json,sys
from pathlib import Path
p=Path(sys.argv[1])
if not p.is_file() or p.stat().st_size==0:
    err=Path(sys.argv[2]).read_text(encoding="utf-8", errors="replace")[:400] if Path(sys.argv[2]).is_file() else ""
    print("Plan konnte nicht erstellt werden.")
    if err:
        print("Detail:", err)
    raise SystemExit(0)
doc=json.loads(p.read_text(encoding="utf-8"))
e=[x.get("code") for x in (doc.get("errors") or [])]
w=[x.get("code") for x in (doc.get("warnings") or [])]
mapped=doc.get("tui_auto_mapped") or {}
print("Status:", doc.get("plan_status"))
print("Execute:", doc.get("execute_allowed"))
print("Quelle:", mapped.get("source_device") or "—")
print("Ziel:", mapped.get("target_device") or "—", mapped.get("target_mount") or "")
print("Fehler:", ", ".join(e) or "—")
print("Hinweise:", ", ".join(w) or "—")
' "$plan_out" "$plan_err" 2>/dev/null || echo "Plan konnte nicht erstellt werden."
  )"
  setuphelfer_rescue_mirror_evidence_file "$plan_out" "setuphelfer/evidence/backup/backup-plan-dry-run.json" 2>/dev/null || true
  setuphelfer_rescue_mirror_evidence_file "$plan_err" "setuphelfer/evidence/backup/backup-plan-dry-run.err" 2>/dev/null || true
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

_tui_run_bounded() {
  # Wall-clock bound: never wait on USB D-state children (timeout/kill can't abort them).
  local secs="${1:-5}"
  shift
  "$@" >/dev/null 2>&1 &
  local pid=$!
  local end=$((SECONDS + secs))
  while kill -0 "$pid" 2>/dev/null && (( SECONDS < end )); do
    sleep 0.2
  done
  if kill -0 "$pid" 2>/dev/null; then
    kill -TERM "$pid" 2>/dev/null || true
    kill -KILL "$pid" 2>/dev/null || true
  fi
  return 0
}

_tui_boot_progress_steps() {
  # Cosmetic walk only — never call wifi/media/disk I/O here (USB D-state / NM hang).
  # Heavy checks stay in interactive menu items with hard wall-clock aborts.
  local _wt_local
  _wt_local="$(setuphelfer_rescue_whiptail_tty)"
  whiptail --title "Setuphelfer" --infobox "Schritt 1/4: Live-Medium prüfen…" 8 55 \
    3>&1 1>"$_wt_local" 2>&3 || true
  sleep 0.5
  setuphelfer_rescue_write_boot_state "tui_step_media"

  whiptail --title "Setuphelfer" --infobox "Schritt 2/4: System erkennen…" 8 55 \
    3>&1 1>"$_wt_local" 2>&3 || true
  sleep 0.5
  setuphelfer_rescue_write_boot_state "tui_step_detect"

  whiptail --title "Setuphelfer" --infobox "Schritt 3/4: Hardware-Hinweis…" 8 55 \
    3>&1 1>"$_wt_local" 2>&3 || true
  sleep 0.5
  setuphelfer_rescue_write_boot_state "tui_step_wifi"

  whiptail --title "Setuphelfer" --infobox "Schritt 4/4: Textmenü wird vorbereitet…" 8 55 \
    3>&1 1>"$_wt_local" 2>&3 || true
  sleep 0.5
  setuphelfer_rescue_write_boot_state "tui_steps_done"

  # Reclaim console if a failed GUI attempt left chromium/openvt on another VT.
  setuphelfer_rescue_kill_gui_leftovers || true
  chvt 1 2>/dev/null || true
  setuphelfer_rescue_write_boot_state "tui_menu_ready"
}

_tui_run_asus_rog_gate() {
  if [[ -x "${SCRIPT_DIR}/setuphelfer-rescue-asus-rog-bios-gate" ]]; then
    "${SCRIPT_DIR}/setuphelfer-rescue-asus-rog-bios-gate" || true
  fi
  local gate="${SETUPHELFER_RESCUE_STATE_DIR}/asus-rog-bios-gate.json"
  local body="ASUS ROG BIOS/Win11-Gate (nur Lesen, keine BIOS-Änderung).\n\n"
  if [[ -f "$gate" ]] && command -v python3 >/dev/null 2>&1; then
    body="$(python3 - <<PY
import json
from pathlib import Path
p = Path("${gate}")
d = json.loads(p.read_text(encoding="utf-8"))
lines = [
    "ASUS ROG erkannt: " + str(d.get("asus_rog_detected")),
    "Schwere: " + str(d.get("severity")),
    "",
    "Nächste Schritte:",
]
for a in (d.get("operator_next_actions") or [])[:8]:
    lines.append("- " + str(a))
print("\\n".join(lines))
PY
)"
  else
    body+="Evidence fehlt — Gate-Skript ausführen."
  fi
  whiptail --title "ASUS ROG — BIOS / Win11" --msgbox "$body" 22 74 3>&1 1>"$_wt" 2>&3 || true
}

_tui_run_hardware_discovery() {
  local banner="============================================================
GERÄTEBINDUNG
============================================================
Profil: asus_rog_gabriel
Hersteller: ASUS
Modell: ROG Strix G513QM
Board: G513QM
BIOS: G513QM.331 (Update 335 verfügbar, kein Flash)
Diagnosezugriff: erlaubt nach Bestätigung
Storage-Write: gesperrt
Firmware-Write: gesperrt
Installation: gesperrt
Run-Type: hardware_discovery
============================================================"
  whiptail --title "Hardwarediagnose (nur Lesen)" --msgbox "$banner" 22 74 3>&1 1>"$_wt" 2>&3 || true
  if ! whiptail --title "Gabriel-Bestätigung" --yesno \
    "Dies ist Gabriels ASUS ROG Strix G513QM.\n\nNur lesen — keine Schreibfreigabe.\nFortfahren?" 12 70 \
    3>&1 1>"$_wt" 2>&3; then
    return 0
  fi
  local hw="${SCRIPT_DIR}/setuphelfer-rescue-hardware-discovery"
  if [[ ! -x "$hw" ]]; then
    hw="/usr/local/sbin/setuphelfer-rescue-hardware-discovery"
  fi
  if [[ -x "$hw" ]]; then
    whiptail --title "Hardwarediagnose" --infobox \
      "Diagnose wird finalisiert…\nStick noch nicht entfernen.\nGrafische Oberfläche für diesen Diagnosemodus deaktiviert." \
      10 70 3>&1 1>"$_wt" 2>&3 || true
    # Background capture with phase polling for TUI progress (text profile — no GUI).
    "$hw" --operator-confirmed \
      --operator-phrase "Dies ist Gabriels ASUS ROG Strix G513QM." &
    local hw_pid=$!
    local prog="/run/setuphelfer-rescue/hardware-discovery-progress.json"
    local waited=0
    while kill -0 "$hw_pid" 2>/dev/null; do
      local phase_line="Capture läuft (nur Lesen)…"
      if [[ -f "$prog" ]] && command -v python3 >/dev/null 2>&1; then
        phase_line="$(python3 - <<'PY' 2>/dev/null || true
import json
from pathlib import Path
p = Path("/run/setuphelfer-rescue/hardware-discovery-progress.json")
d = json.loads(p.read_text(encoding="utf-8")) if p.is_file() else {}
print(f"{d.get('phase_label') or 'Capture'}: {d.get('phase_status') or 'running'}")
print(d.get("stick_remove_hint") or "Stick noch nicht entfernen")
PY
)"
      fi
      whiptail --title "Hardwarediagnose — Fortschritt" --infobox "$phase_line\n\nBitte warten…" 12 70 \
        3>&1 1>"$_wt" 2>&3 || true
      sleep 2
      waited=$((waited + 2))
      if [[ "$waited" -gt 900 ]]; then
        whiptail --title "Hardwarediagnose" --msgbox "Timeout: Capture >15 Min. Bitte Logs prüfen." 10 60 \
          3>&1 1>"$_wt" 2>&3 || true
        break
      fi
    done
    wait "$hw_pid" || true
  else
    whiptail --title "Hardwarediagnose" --msgbox "Skript fehlt: setuphelfer-rescue-hardware-discovery" 10 60 \
      3>&1 1>"$_wt" 2>&3 || true
    return 0
  fi
  local last="${SETUPHELFER_RESCUE_STATE_DIR}/../hardware-discovery-last.json"
  [[ -f /run/setuphelfer-rescue/hardware-discovery-last.json ]] && last=/run/setuphelfer-rescue/hardware-discovery-last.json
  local body="Hardwarediagnose beendet (write_allowed=false).\n"
  if [[ -f "$last" ]] && command -v python3 >/dev/null 2>&1; then
    body="$(python3 - <<PY
import json
from pathlib import Path
d = json.loads(Path("${last}").read_text(encoding="utf-8"))
panther = d.get("panther_found")
rollback = d.get("rollback_found")
copied = d.get("copied_file_count")
win_st = d.get("windows_setup_logs_status")
lines = [
    "Run-ID: " + str(d.get("run_id")),
    "Boot-ID: " + str(d.get("boot_id")),
    "Status: " + str(d.get("status")) + " terminal=" + str(d.get("terminal")),
    "Endstatus: " + str(d.get("endstatus")),
    "NVMe count: " + str(d.get("device_count")),
    "Windows-Logs Status: " + str(win_st),
    "Panther gefunden: " + str(panther),
    "Rollback gefunden: " + str(rollback),
    "Kopierte Log-Dateien: " + str(copied),
    "GUI: " + str(d.get("gui_status") or "not_applicable_for_text_hardware_discovery"),
    "Schreibzugriffe: gesperrt",
]
if panther or rollback:
    lines.append("ERGEBNIS: Windows-Setup-Logs OK — Stick nach Shutdown entfernen.")
else:
    lines.append("ERGEBNIS: KEINE Panther/Rollback-Logs — Stick zurückgeben.")
    lines.append("Hinweis: OPERATOR_WIN11_LOG_STATUS.txt auf dem Stick prüfen.")
lines.append(str(d.get("stick_remove_hint") or "Diagnose abgeschlossen – Stick kann nach dem Herunterfahren entfernt werden."))
print("\\n".join(lines))
PY
)"
  fi
  whiptail --title "Hardwarediagnose — Ergebnis" --msgbox "$body" 22 74 3>&1 1>"$_wt" 2>&3 || true
}

_tui_run_pi5_lab() {
  if [[ -x "${SCRIPT_DIR}/setuphelfer-rescue-pi5-lab" ]]; then
    "${SCRIPT_DIR}/setuphelfer-rescue-pi5-lab" || true
  fi
  local usb="${SETUPHELFER_RESCUE_STATE_DIR}/pi5-usb-boot-check.json"
  local body="Pi5 Lab: USB-Boot-Check und Install-Plan.\n\n"
  if [[ -f "$usb" ]] && command -v python3 >/dev/null 2>&1; then
    body="$(python3 - <<PY
import json
from pathlib import Path
d = json.loads(Path("${usb}").read_text(encoding="utf-8"))
det = d.get("detection") or {}
lines = [
    "Modell: " + str(det.get("model") or "n/a"),
    "Pi5: " + str(det.get("is_raspberry_pi_5")),
    "BOOT_ORDER: " + str(d.get("boot_order")),
    "usb_boot_ok: " + str(d.get("usb_boot_ok")),
    "",
    "Hinweise:",
]
for a in (d.get("operator_next_actions") or [])[:8]:
    lines.append("- " + str(a))
print("\\n".join(lines))
PY
)"
  else
    body+="Siehe docs/test-plans/PI_RS_PI5_RESCUE_USB_LAB.md"
  fi
  whiptail --title "Raspberry Pi 5 Lab" --msgbox "$body" 22 74 3>&1 1>"$_wt" 2>&3 || true
}

_tui_main_menu() {
  setuphelfer_rescue_kill_gui_leftovers || true
  chvt 1 2>/dev/null || true
  # Refresh tty target in case early boot resolved a bad /dev/tty.
  _wt="$(setuphelfer_rescue_whiptail_tty)"
  # Prove the console is alive before newt (blank FB otherwise looks like a hang).
  {
    printf '\033[0m\033[2J\033[H'
    printf 'Setuphelfer Textmodus — Menue startet...\n'
  } >"${_wt}" 2>/dev/null || true
  local choice
  local asus_hint=""
  local pi_hint=""
  if [[ -f "${SETUPHELFER_RESCUE_STATE_DIR}/asus-rog-bios-gate.json" ]]; then
    asus_hint="ASUS-BIOS-Checkliste"
  fi
  if [[ -f "${SETUPHELFER_RESCUE_STATE_DIR}/pi5-usb-boot-check.json" ]] \
     || grep -Eq '(^| )setuphelfer_pi5_lab=1( |$)' /proc/cmdline 2>/dev/null; then
    pi_hint="Pi5-Lab"
  fi
  while true; do
    choice="$(_tui_whiptail --title "Setuphelfer Rettungsstick - Textmodus" --menu \
      "Sicherer Textmodus (kein Backup/Restore/Wipe ohne Freigabe)" 24 78 13 \
      "detect" "System erkennen" \
      "wifi" "Hardware/WLAN prüfen" \
      "plan" "Backup-Plan erstellen (dry-run)" \
      "e2e" "E2E Backup-/Restore-Test" \
      "hwdisc" "Hardwarediagnose (nur Lesen / Gabriel)" \
      "asus" "ASUS ROG: BIOS/Win11-Checkliste${asus_hint:+ ($asus_hint)}" \
      "pi5" "Raspberry Pi 5: USB-Boot / Install-Lab${pi_hint:+ ($pi_hint)}" \
      "evidence" "Evidence auf Stick speichern" \
      "gui" "Grafische Oberfläche starten" \
      "shell" "Shell öffnen (tty2)" \
      "reboot" "Neustart" \
      "poweroff" "Ausschalten")" || return 0
    case "$choice" in
      detect) _tui_run_system_detect ;;
      wifi) _tui_run_wifi_diag ;;
      plan)
        if _tui_input_diag_active; then _tui_diag_blocked_action; else _tui_run_backup_plan; fi
        ;;
      e2e)
        if _tui_input_diag_active; then _tui_diag_blocked_action; else _tui_run_physical_e2e; fi
        ;;
      hwdisc) _tui_run_hardware_discovery ;;
      asus) _tui_run_asus_rog_gate ;;
      pi5) _tui_run_pi5_lab ;;
      evidence) _tui_collect_evidence ;;
      gui)
        if _tui_input_diag_active; then _tui_diag_blocked_action; else _tui_start_gui; fi
        ;;
      shell) _tui_shell ;;
      reboot)
        if _tui_input_diag_active; then _tui_diag_blocked_action; else systemctl reboot 2>/dev/null || reboot; fi
        ;;
      poweroff)
        if _tui_input_diag_active; then _tui_diag_blocked_action; else systemctl poweroff 2>/dev/null || poweroff; fi
        ;;
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
  if [[ "$MODE" == "--boot-trigger" ]]; then
    # No cosmetic 1–4 walk — labels froze the operator when the shell stalled.
    # Go straight to the interactive menu after reclaiming the console.
    setuphelfer_rescue_kill_gui_leftovers || true
    chvt 1 2>/dev/null || true
    setuphelfer_rescue_write_boot_state "tui_menu_ready"
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
