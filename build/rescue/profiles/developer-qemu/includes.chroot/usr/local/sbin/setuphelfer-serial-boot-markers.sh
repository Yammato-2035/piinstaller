#!/bin/bash
# Early serial markers for QEMU developer lab (read-only, no disk writes).
set -u

log_serial() {
  printf '%s\n' "$*" >/dev/ttyS0 2>/dev/null || true
  logger -t setuphelfer-serial "$*" 2>/dev/null || true
}

phase="${1:-early}"
case "$phase" in
  early)
    log_serial "SETUPHELFER_BOOT_MARKER_START"
    ;;
  systemd)
    log_serial "SETUPHELFER_SYSTEMD_MARKER_START"
    ;;
  *)
    log_serial "SETUPHELFER_BOOT_MARKER_UNKNOWN phase=${phase}"
    ;;
esac

exit 0
