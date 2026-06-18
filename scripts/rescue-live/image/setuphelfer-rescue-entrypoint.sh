#!/bin/bash
# Rescue entrypoint — mode from cmdline, text default, GUI optional (RS-P2C).
set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=setuphelfer-rescue-common.sh
source "${SCRIPT_DIR}/setuphelfer-rescue-common.sh"

MODE_ARG="${1:---boot-trigger}"
CMDLINE="$(tr '\0' ' ' </proc/cmdline 2>/dev/null || true)"

setuphelfer_rescue_ensure_state_dir
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

if setuphelfer_rescue_should_start_gui; then
  setuphelfer_rescue_write_boot_state "gui_requested"
  if [[ -x "${SCRIPT_DIR}/setuphelfer-rescue-gui-watchdog" ]]; then
    if "${SCRIPT_DIR}/setuphelfer-rescue-gui-watchdog"; then
      exit 0
    fi
  fi
  setuphelfer_rescue_write_boot_state "gui_failed_fallback_tui"
fi

setuphelfer_rescue_write_boot_state "text_mode_started"
exec "${SCRIPT_DIR}/setuphelfer-rescue-tui" "$MODE_ARG"
