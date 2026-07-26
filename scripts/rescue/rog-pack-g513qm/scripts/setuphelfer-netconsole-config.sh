#!/usr/bin/env bash
# Configure netconsole module from lab env (does not require Internet/telemetry).
set -euo pipefail
TARGET_IP="${G513QM_NETCONSOLE_TARGET_IP:-}"
TARGET_PORT="${G513QM_NETCONSOLE_TARGET_PORT:-6666}"
SRC_PORT="${G513QM_NETCONSOLE_SRC_PORT:-6665}"
IFACE="${G513QM_NETCONSOLE_IFACE:-}"

mkdir -p /run/setuphelfer
echo "netconsole_config_attempt $(date --iso-8601=seconds)" >>/run/setuphelfer/netconsole-config.log

if [[ -z "$TARGET_IP" ]]; then
  echo "netconsole_skipped=no_target_ip" | tee -a /run/setuphelfer/netconsole-config.log
  exit 0
fi

# Prefer cmdline netconsole= if already set by GRUB.
if grep -qw netconsole /proc/cmdline; then
  echo "netconsole_already_on_cmdline" | tee -a /run/setuphelfer/netconsole-config.log
  exit 0
fi

PARAM="netconsole=${SRC_PORT}@/${IFACE:+${IFACE},}${TARGET_IP}/${TARGET_PORT}"
if modprobe netconsole "$PARAM" 2>>/run/setuphelfer/netconsole-config.log; then
  echo "netconsole_loaded param=$PARAM" | tee -a /run/setuphelfer/netconsole-config.log
else
  echo "netconsole_load_failed (local capture still valid)" | tee -a /run/setuphelfer/netconsole-config.log
  exit 0
fi
