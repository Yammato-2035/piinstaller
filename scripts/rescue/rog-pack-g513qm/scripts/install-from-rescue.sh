#!/usr/bin/env bash
# install-from-rescue.sh — G513QM hybrid-safe modes (STRICT).
# Always invoke: bash <resolved-path>/scripts/install-from-rescue.sh ...
# Never assumes VFAT +x. Never writes internal NVMe. Never auto-selects install target.
set -euo pipefail

PACK_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MODE="inspect"
DRY_RUN=0
WIPE_PHRASE_EXPECTED="WIPE LINUX TARGET"
LINUX_WIPE_CONFIRM=""
RESULT_DIR=""
CAPTURE_BIN="$PACK_ROOT/scripts/setuphelfer-g513qm-capture.sh"
CONTRACT_JSON="${PACK_ROOT}/../../../config/hardware/asus/g513qm-hybrid-graphics.json"
# Contract may live in pack copy or repo; prefer pack-local override
[[ -f "$PACK_ROOT/config/g513qm-hybrid-graphics.json" ]] && CONTRACT_JSON="$PACK_ROOT/config/g513qm-hybrid-graphics.json"

usage() {
  cat <<EOF
Usage: bash $(basename "$0") --mode MODE [options]

Modes:
  inspect | apply-pack | graphics-preflight | start-desktop
  installer-preflight | ubiquity | capture-only | finalize-capture

Options:
  --dry-run
  --wipe-linux-phrase PHRASE   (ack only; no automated wipe)
  --help
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --mode) MODE="${2:-}"; shift ;;
    --dry-run) DRY_RUN=1 ;;
    --wipe-linux-phrase) LINUX_WIPE_CONFIRM="${2:-}"; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown: $1" >&2; usage; exit 2 ;;
  esac
  shift
done

run_capture() {
  local phase="$1"
  if [[ -f "$CAPTURE_BIN" ]]; then
    bash "$CAPTURE_BIN" "$phase" || true
  fi
}

dmi_ok() {
  local p
  p="$(cat /sys/class/dmi/id/product_name 2>/dev/null || true)$(cat /sys/class/dmi/id/board_name 2>/dev/null || true)"
  [[ "$p" == *G513QM* ]]
}

resolve_active_x11() {
  # Prefer existing X socket; do not invent DISPLAY=:0 blindly.
  local sock user display auth
  for sock in /tmp/.X11-unix/X*; do
    [[ -S "$sock" ]] || continue
    display=":${sock##*/X}"
    # Find process owning X
    local pid
    pid="$(pgrep -f "X(org)? .*${display}" | head -1 || true)"
    [[ -n "$pid" ]] || continue
    user="$(ps -o user= -p "$pid" 2>/dev/null | awk '{print $1}')"
    auth=""
    if [[ -n "$user" && "$user" != "root" ]]; then
      local home
      home="$(getent passwd "$user" | cut -d: -f6)"
      [[ -f "$home/.Xauthority" ]] && auth="$home/.Xauthority"
    fi
    [[ -z "$auth" && -f /root/.Xauthority ]] && auth=/root/.Xauthority
    echo "DISPLAY=$display"
    echo "XUSER=${user:-root}"
    echo "XAUTHORITY=${auth:-}"
    return 0
  done
  return 1
}

write_result() {
  local status="$1"
  local msg="$2"
  RESULT_DIR="${RESULT_DIR:-/run/setuphelfer-capture/${SETUPHELFER_RUN_ID:-local}/installer}"
  mkdir -p "$RESULT_DIR"
  printf '{"mode":"%s","status":"%s","message":"%s","utc":"%s","run_id":"%s"}\n' \
    "$MODE" "$status" "$msg" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "${SETUPHELFER_RUN_ID:-}" \
    >"$RESULT_DIR/result-${MODE}.json"
  echo "RESULT status=$status msg=$msg"
}

mode_inspect() {
  run_capture boot_early
  echo "PACK_ROOT=$PACK_ROOT"
  echo "DMI_OK=$(dmi_ok && echo yes || echo no)"
  echo "product=$(cat /sys/class/dmi/id/product_name 2>/dev/null || true)"
  echo "cmdline=$(cat /proc/cmdline)"
  lsmod | egrep 'amdgpu|nouveau|nvidia' || true
  command -v ubiquity || echo 'ubiquity_absent'
  command -v startx || echo 'startx_absent'
  ls /tmp/.X11-unix 2>/dev/null || echo 'no_x11_socket'
  mokutil --sb-state 2>/dev/null || echo 'sb_unknown'
  write_result ok inspect_complete
}

mode_apply_pack() {
  run_capture graphics_modules_loading
  if [[ "$DRY_RUN" -eq 1 ]]; then
    bash "$PACK_ROOT/scripts/apply-rog-pack.sh" --dry-run --i-understand-no-windows-wipe || true
  else
    bash "$PACK_ROOT/scripts/apply-rog-pack.sh" --i-understand-no-windows-wipe
  fi
  write_result ok apply_pack_finished
}

mode_graphics_preflight() {
  run_capture drm_ready
  local ok=1
  modinfo amdgpu >/dev/null 2>&1 || { echo "WARN: amdgpu modinfo failed"; ok=0; }
  if grep -qw nomodeset /proc/cmdline; then
    echo "WARN: nomodeset active — GUI installer not recommended on this profile"
    ok=0
  fi
  if grep -E 'amdgpu.modeset=0|modprobe.blacklist=.*amdgpu' /proc/cmdline >/dev/null 2>&1; then
    echo "WARN: amdgpu disabled on cmdline"
    ok=0
  fi
  ls /sys/class/drm/card*-* 2>/dev/null | head || echo "WARN: no drm connectors yet"
  if [[ "$ok" -eq 1 ]]; then write_result ok graphics_preflight_green; else write_result blocked graphics_preflight_red; return 1; fi
}

mode_start_desktop() {
  run_capture x11_starting
  if resolve_active_x11 >/tmp/g513qm-x11.env; then
    echo "Existing X11 session found — not starting another"
    cat /tmp/g513qm-x11.env
    write_result ok existing_x11
    return 0
  fi
  if grep -qw nomodeset /proc/cmdline; then
    write_result blocked start_desktop_under_nomodeset
    echo "ERROR: refuse startx under nomodeset (historical black screen)." >&2
    return 1
  fi
  if [[ "$DRY_RUN" -eq 1 ]]; then
    write_result ok dry_start_desktop
    return 0
  fi
  # Controlled start without openvt -s (keep current VT)
  mkdir -p /var/log/setuphelfer
  if command -v startx >/dev/null; then
    startx >/var/log/setuphelfer/start-desktop.stdout 2>/var/log/setuphelfer/start-desktop.stderr &
    echo $! >/var/log/setuphelfer/start-desktop.pid
    sleep 3
    if resolve_active_x11 >/tmp/g513qm-x11.env; then
      run_capture x11_ready
      write_result ok desktop_started
    else
      write_result failed desktop_not_confirmed
      return 1
    fi
  else
    write_result blocked startx_missing
    return 1
  fi
}

installer_preflight_checks() {
  run_capture installer_preflight
  local errors=()
  dmi_ok || errors+=("dmi_not_g513qm")
  command -v ubiquity >/dev/null || errors+=("ubiquity_missing")
  if grep -qw nomodeset /proc/cmdline; then errors+=("nomodeset_active"); fi
  if ! resolve_active_x11 >/tmp/g513qm-x11.env; then errors+=("no_active_x11"); fi
  [[ -d /tmp/.X11-unix ]] || errors+=("no_x11_unix")
  # SETUP_LOGS writable?
  bash "$CAPTURE_BIN" installer_preflight >/dev/null 2>&1 || true
  if [[ ${#errors[@]} -gt 0 ]]; then
    echo "PREFLIGHT_FAIL: ${errors[*]}"
    printf '%s\n' "${errors[@]}" >"${RESULT_DIR:-/tmp}/preflight.errors"
    return 1
  fi
  echo "PREFLIGHT_OK"
  cat /tmp/g513qm-x11.env
  return 0
}

mode_installer_preflight() {
  mkdir -p /run/setuphelfer-capture/local/installer
  RESULT_DIR=/run/setuphelfer-capture/local/installer
  if installer_preflight_checks; then
    write_result ok installer_preflight_green
  else
    write_result blocked installer_preflight_red
    return 1
  fi
}

watchdog_loop() {
  local xpid instpid end=$((SECONDS + 120))
  mkdir -p /var/log/setuphelfer
  while (( SECONDS < end )); do
    if ! pgrep -x Xorg >/dev/null && ! pgrep -x X >/dev/null; then
      echo "WATCHDOG: Xorg lost" | tee /var/log/setuphelfer/watchdog.event
      run_capture gui_lost
      chvt 1 2>/dev/null || true
      echo "Setuphelfer hat die grafische Installationssitzung verloren."
      echo "Es wurden keine internen Laufwerke verändert."
      echo "Diagnosedaten unter SETUP_LOGS/setuphelfer/runs/ (falls gemountet)."
      echo "Run-ID: ${SETUPHELFER_RUN_ID:-unknown}"
      return 1
    fi
    if ! pgrep -f '[u]biquity' >/dev/null; then
      # installer may exit normally; only flag if X also dead shortly
      sleep 2
      if ! pgrep -f '[u]biquity' >/dev/null; then
        echo "WATCHDOG: ubiquity exited"
        run_capture installer_failed
        return 0
      fi
    fi
    date -u +%Y-%m-%dT%H:%M:%SZ >/run/setuphelfer-capture/${SETUPHELFER_RUN_ID:-local}/meta/heartbeat_utc.txt 2>/dev/null || true
    sleep 2
  done
  return 0
}

mode_ubiquity() {
  if [[ -n "$LINUX_WIPE_CONFIRM" && "$LINUX_WIPE_CONFIRM" != "$WIPE_PHRASE_EXPECTED" ]]; then
    write_result blocked wipe_phrase_mismatch
    exit 3
  fi
  echo "POLICY: Windows/BitLocker NVMe must not be selected. No automatic disk selection."
  if ! installer_preflight_checks; then
    write_result blocked ubiquity_preflight_red
    echo "ERROR: --mode ubiquity requires green installer-preflight (active X11, no nomodeset)." >&2
    echo "Boot GRUB profile: G513QM AMD Safe Display or Hybrid Auto, start desktop, then retry." >&2
    chvt 1 2>/dev/null || true
    exit 10
  fi
  # shellcheck disable=SC1091
  source /tmp/g513qm-x11.env
  export DISPLAY XAUTHORITY
  [[ -n "${XAUTHORITY:-}" ]] && export XAUTHORITY
  run_capture installer_starting
  mkdir -p /var/log/setuphelfer
  local cmd=(ubiquity)
  if [[ "$DRY_RUN" -eq 1 ]]; then
    write_result ok dry_ubiquity
    return 0
  fi
  # Do NOT openvt -s; do NOT startx; do NOT kill X
  printf 'DISPLAY=%s XAUTHORITY=%s cmd=%s\n' "${DISPLAY:-}" "${XAUTHORITY:-}" "${cmd[*]}" \
    >/var/log/setuphelfer/ubiquity.command
  if [[ "${XUSER:-root}" != "root" ]] && command -v sudo >/dev/null; then
    sudo -u "$XUSER" env DISPLAY="$DISPLAY" XAUTHORITY="${XAUTHORITY:-}" \
      "${cmd[@]}" >/var/log/setuphelfer/ubiquity.stdout 2>/var/log/setuphelfer/ubiquity.stderr &
  else
    env DISPLAY="$DISPLAY" XAUTHORITY="${XAUTHORITY:-}" \
      "${cmd[@]}" >/var/log/setuphelfer/ubiquity.stdout 2>/var/log/setuphelfer/ubiquity.stderr &
  fi
  echo $! >/var/log/setuphelfer/ubiquity.pid
  sleep 2
  if pgrep -f '[u]biquity' >/dev/null; then
    run_capture installer_visible
    write_result started ubiquity_process_alive
  else
    write_result failed ubiquity_not_alive
    run_capture installer_failed
    chvt 1 2>/dev/null || true
    exit 11
  fi
  watchdog_loop || true
}

mode_capture_only() {
  run_capture capture_finalizing
  bash "$CAPTURE_BIN" capture_complete || true
  write_result ok capture_only_done
}

mode_finalize_capture() {
  bash "$CAPTURE_BIN" capture_finalizing || true
  bash "$CAPTURE_BIN" capture_complete || true
  # Telemetry: queue only — never claim accepted without server ack
  local qdir="/run/setuphelfer-capture/${SETUPHELFER_RUN_ID:-local}/final"
  mkdir -p "$qdir"
  echo '{"upload_status":"queued_offline_or_not_configured","note":"runtime_gate_blocked_live_send"}' >"$qdir/upload-status.json"
  write_result ok finalize_done_upload_not_accepted
}

# --- main ---
if [[ "$(id -u)" -ne 0 && "$MODE" != "inspect" && "$MODE" != "installer-preflight" && "$MODE" != "graphics-preflight" ]]; then
  echo "NOTE: many modes expect root in Rescue; continuing anyway for inspect-like modes." >&2
fi

run_capture boot_early
export SETUPHELFER_RUN_ID="${SETUPHELFER_RUN_ID:-g513qm-hybrid-$(date -u +%Y%m%d-%H%M%S)-$$}"

case "$MODE" in
  inspect) mode_inspect ;;
  apply-pack) mode_apply_pack ;;
  graphics-preflight) mode_graphics_preflight ;;
  start-desktop) mode_start_desktop ;;
  installer-preflight) mode_installer_preflight ;;
  ubiquity) mode_ubiquity ;;
  capture-only) mode_capture_only ;;
  finalize-capture) mode_finalize_capture ;;
  prepare-only)
    # back-compat
    MODE=inspect; mode_inspect ;;
  *)
    echo "Unknown mode: $MODE" >&2
    usage
    exit 2
    ;;
esac
