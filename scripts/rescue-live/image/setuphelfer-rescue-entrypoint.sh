#!/bin/bash
# Rescue entrypoint — mode from cmdline, text default, GUI optional (RS-P2C).
set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=setuphelfer-rescue-common.sh
source "${SCRIPT_DIR}/setuphelfer-rescue-common.sh"

MODE_ARG="${1:---boot-trigger}"
CMDLINE="$(tr '\0' ' ' </proc/cmdline 2>/dev/null || true)"

setuphelfer_rescue_ensure_state_dir
setuphelfer_rescue_shield_console_early "entrypoint_start" || true
setuphelfer_rescue_write_boot_state "entrypoint_start"

if ! setuphelfer_rescue_cmdline_has_start_assistant && [[ "$MODE_ARG" == "--boot-trigger" ]]; then
  exit 0
fi

if setuphelfer_rescue_prepare_tty1; then
  :
fi
if [[ -c /dev/tty1 ]]; then
  exec </dev/tty1 >/dev/tty1 2>&1
fi

# Diagnostics / hardware modes: collect evidence first, then TUI.
if grep -Eq '(^| )setuphelfer_collect_diagnostics=1( |$)' /proc/cmdline 2>/dev/null \
   || grep -Eq '(^| )setuphelfer_mode=diagnostics( |$)' /proc/cmdline 2>/dev/null; then
  if [[ -x "${SCRIPT_DIR}/collect-rescue-runtime-diagnostics.sh" ]]; then
    "${SCRIPT_DIR}/collect-rescue-runtime-diagnostics.sh" || true
  elif [[ -x "${SCRIPT_DIR}/setuphelfer-rescue-boot-diagnostics" ]]; then
    "${SCRIPT_DIR}/setuphelfer-rescue-boot-diagnostics" || true
  fi
  setuphelfer_rescue_write_boot_state "diagnostics_collected"
fi

if grep -Eq '(^| )setuphelfer_wifi_diag=1( |$)' /proc/cmdline 2>/dev/null \
   || grep -Eq '(^| )setuphelfer_mode=hardware( |$)' /proc/cmdline 2>/dev/null; then
  setuphelfer_rescue_wifi_prepare_radio || true
  setuphelfer_rescue_write_boot_state "hardware_wifi_prepared"
fi

# PI-RS-ASUS-ROOTCAUSE-006: pause aggressive diagnostics while TUI owns console.
if command -v systemctl >/dev/null 2>&1; then
  if setuphelfer_rescue_tui_baseline_active 2>/dev/null \
     || setuphelfer_rescue_xorg_forensic_active 2>/dev/null \
     || ! setuphelfer_rescue_should_start_gui; then
    systemctl stop setuphelfer-rescue-boot-diagnostics.timer 2>/dev/null || true
  fi
fi

if setuphelfer_rescue_xorg_forensic_active 2>/dev/null; then
  setuphelfer_rescue_write_boot_state "xorg_forensic_requested"
  setuphelfer_rescue_quiet_console_for_tui 2>/dev/null || true
  setuphelfer_rescue_console_owner_transition "tui_owned" "xorg_forensic_pre" || true
  if [[ -x "${SCRIPT_DIR}/setuphelfer-rescue-startx-forensic.sh" ]]; then
    "${SCRIPT_DIR}/setuphelfer-rescue-startx-forensic.sh" || true
  elif [[ -x "${SCRIPT_DIR}/setuphelfer-rescue-startx-forensic" ]]; then
    "${SCRIPT_DIR}/setuphelfer-rescue-startx-forensic" || true
  fi
  setuphelfer_rescue_restore_tty1_after_gui_fail || true
  setuphelfer_rescue_write_boot_state "xorg_forensic_done_fallback_tui"
fi

if setuphelfer_rescue_should_start_gui; then
  setuphelfer_rescue_write_boot_state "gui_requested"
  if [[ -x "${SCRIPT_DIR}/setuphelfer-rescue-gui-watchdog" ]]; then
    if "${SCRIPT_DIR}/setuphelfer-rescue-gui-watchdog"; then
      exit 0
    fi
  fi
  setuphelfer_rescue_write_boot_state "gui_failed_fallback_tui"
  setuphelfer_rescue_restore_tty1_after_gui_fail || true
  setuphelfer_rescue_mark_tui_rerender_after_gui_failure || true
fi

setuphelfer_rescue_quiet_console_for_tui 2>/dev/null || true
setuphelfer_rescue_shield_console_early "tui_baseline_entrypoint" || true
setuphelfer_rescue_console_owner_transition "tui_owned" "text_mode_started" || true
setuphelfer_rescue_write_boot_state "text_mode_started"
if [[ -c /dev/tty1 ]]; then
  exec </dev/tty1 >/dev/tty1 2>&1
fi
exec "${SCRIPT_DIR}/setuphelfer-rescue-tui" "$MODE_ARG"
